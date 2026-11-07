"""Same-origin optional Flask workbench; scientific modules also run standalone."""
from __future__ import annotations

import atexit
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from .domain import PlanningRequest, scenario_revision
from .graph import list_scenarios, load_scenario, prepare_problem
from .jobs import JobManager, QueueFullError
from .objective import evaluate_plan

ROOT = Path(__file__).resolve().parents[1]


def create_app(*, job_manager=None, static_dir=None, storage_dir=None):
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    app.json.sort_keys = False
    app.json.compact = False
    manager = job_manager or JobManager(storage_dir or ROOT.parent / "build" / "reliefgrid" / "runs")
    app.extensions["reliefgrid_jobs"] = manager
    if job_manager is None:
        atexit.register(manager.close)
    frontend = Path(static_dir) if static_dir else ROOT / "frontend" / "dist"

    def error(code, message, status=400, field=None, retryable=False):
        detail = dict(code=code, message=message, retryable=retryable)
        if field:
            detail["field"] = field
        return jsonify(error=detail), status

    @app.errorhandler(ValidationError)
    def invalid_model(exc):
        issue = exc.errors()[0]
        return error("validation_error", issue["msg"], 400, ".".join(str(x) for x in issue["loc"]))

    @app.errorhandler(ValueError)
    def invalid_value(exc):
        return error("invalid_request", str(exc))

    @app.errorhandler(KeyError)
    def missing(exc):
        return error("not_found", "The requested scenario or run does not exist.", 404)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return error("http_error", exc.description, exc.code or 500)

    @app.errorhandler(Exception)
    def unexpected(exc):
        app.logger.exception("Unhandled ReliefGrid service error")
        return error("internal_error", "The service could not complete this request.", 500, retryable=True)

    def planning(payload=None):
        payload = request.get_json() if payload is None else payload
        model = PlanningRequest.model_validate(payload)
        scenario = load_scenario(model.scenarioId)
        if len(scenario.candidateHubs) > 12:
            raise ValueError("The optional workbench supports at most 12 candidate hubs")
        problem = prepare_problem(scenario, model)
        return model, scenario, problem

    @app.get("/api/v1/health")
    def health():
        return jsonify(app="reliefgrid", version="1", ready=True)

    @app.get("/api/v1/scenarios")
    def scenarios():
        return jsonify(scenarios=list_scenarios())

    @app.get("/api/v1/scenarios/<scenario_id>")
    def scenario(scenario_id):
        model = load_scenario(scenario_id)
        return jsonify(**model.model_dump(mode="json"), scenarioRevision=scenario_revision(model))

    @app.post("/api/v1/preview")
    def preview():
        model, scenario, problem = planning()
        nominal = prepare_problem(scenario, model.model_copy(update={"closedEdgeIds": ()}))
        affected = [cid for i, cid in enumerate(problem.communityIds)
                    if problem.travelMinutes[i] != nominal.travelMinutes[i]]
        unreachable = [cid for cid, row in zip(problem.communityIds, problem.travelMinutes)
                       if all(value is None for value in row)]
        return jsonify(problemHash=problem.problemHash, preparedProblem=problem.model_dump(mode="json"),
                       unreachableCommunityIds=unreachable, affectedCommunityIds=affected)

    @app.post("/api/v1/runs")
    def submit():
        model, scenario, problem = planning()
        snapshot = dict(request=model.model_dump(mode="json"), scenario=scenario.model_dump(mode="json"),
                        preparedProblem=problem.model_dump(mode="json"))
        try:
            return jsonify(manager.submit(snapshot)), 202
        except QueueFullError as exc:
            return error("queue_full", str(exc), 429, retryable=True)

    @app.get("/api/v1/runs/<run_id>")
    def poll(run_id):
        return jsonify(manager.get(run_id))

    @app.delete("/api/v1/runs/<run_id>")
    def cancel(run_id):
        return jsonify(manager.cancel(run_id))

    @app.get("/api/v1/runs/<run_id>/export")
    def export(run_id):
        job = manager.get(run_id, include_snapshot=True)
        if job["status"] != "succeeded":
            return error("run_not_complete", "Export is available after a successful run.", 409)
        response = jsonify(schemaVersion="1", synthetic=job["snapshot"]["scenario"]["provenance"]["kind"] == "synthetic",
                           **job)
        response.headers["Content-Disposition"] = f'attachment; filename="reliefgrid-{run_id}.json"'
        return response

    @app.post("/api/v1/stress-test")
    def stress_test():
        payload = request.get_json()
        if not isinstance(payload, dict):
            raise ValueError("Expected a planning request object")
        payload = dict(payload)
        selected = payload.pop("selectedHubIds", None)
        model, scenario, problem = planning(payload)
        if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
            raise ValueError("selectedHubIds must be a list of hub IDs")
        if not evaluate_plan(problem, selected)["feasible"]:
            raise ValueError("selectedHubIds must identify exactly hubCount unique candidate hubs")
        variants = [("Current closures", model.closedEdgeIds), ("All roads open", ())]
        # A bounded, disclosed set of individual road closures, evaluated on a fixed plan.
        variants.extend((f"Close {edge.name or edge.id}", tuple(sorted(set(model.closedEdgeIds) | {edge.id})))
                        for edge in sorted(scenario.edges, key=lambda e: e.id)[:8])
        rows = []
        for title, closures in variants:
            prepared = prepare_problem(scenario, model.model_copy(update={"closedEdgeIds": closures}))
            rows.append(dict(title=title, closedEdgeIds=list(closures), problemHash=prepared.problemHash,
                             **evaluate_plan(prepared, selected)))
        return jsonify(selectedHubIds=selected, variants=rows, nominalCoveredPopulation=rows[0]["coveredPopulation"],
                       worstCoveredPopulation=min(row["coveredPopulation"] for row in rows),
                       interpretation="Fixed deployment evaluated across these scenarios; no robust optimization performed.")

    @app.get("/")
    @app.get("/<path:path>")
    def static(path=""):
        if path == "api" or path.startswith("api/"):
            return error("not_found", "Unknown API endpoint.", 404)
        if path and (frontend / path).is_file():
            return send_from_directory(frontend, path)
        if (frontend / "index.html").is_file():
            return send_from_directory(frontend, "index.html")
        return error("frontend_not_built", "Build the optional frontend before opening the workbench.", 404)

    return app


if __name__ == "__main__":
    import os
    create_app().run(host="127.0.0.1", port=int(os.environ.get("RELIEFGRID_PORT", "8010")), debug=False)
