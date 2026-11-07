"""Flask contracts and real Windows-spawn worker integration."""
import json
import multiprocessing as mp
import time

import pytest

from backend.api import create_app
from backend.domain import Hub, PlanningRequest, PreparedProblem, scenario_revision
from backend.graph import load_scenario, prepare_problem
from backend.jobs import JobManager, QueueFullError, TERMINAL, execute_job
from backend.objective import evaluate_plan


def slow_executor(snapshot):
    time.sleep(10)
    return {"late": True}


def failing_executor(snapshot):
    raise ValueError("deliberate worker failure")


def payload(**changes):
    scenario = load_scenario("riverbend")
    return dict(scenarioId=scenario.id, scenarioRevision=scenario_revision(scenario),
                hubCount=3, responseTimeMinutes=12, solver="exact", **changes)


def snapshot(**changes):
    data = payload(**changes)
    scenario = load_scenario(data["scenarioId"])
    prepared = prepare_problem(scenario, PlanningRequest.model_validate(data))
    return dict(request=data, scenario=scenario.model_dump(mode="json"),
                preparedProblem=prepared.model_dump(mode="json"))


def wait_for(manager, run_id, statuses=TERMINAL, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = manager.get(run_id)
        if job["status"] in statuses:
            return job
        time.sleep(.02)
    pytest.fail(f"Run did not reach {statuses}: {manager.get(run_id)}")


@pytest.fixture
def service(tmp_path):
    manager = JobManager(tmp_path / "runs", timeout_seconds=25)
    app = create_app(job_manager=manager, static_dir=tmp_path / "frontend")
    app.config["TESTING"] = True
    yield app.test_client(), manager
    manager.close()


def test_health_scenarios_unknown_routes_and_static(service, tmp_path):
    client, _ = service
    assert client.get("/api/v1/health").json == dict(app="reliefgrid", version="1", ready=True)
    summaries = client.get("/api/v1/scenarios").json["scenarios"]
    assert {s["id"] for s in summaries} == {"riverbend", "upland"}
    scenario = client.get("/api/v1/scenarios/riverbend").json
    assert scenario["scenarioRevision"] == payload()["scenarioRevision"]
    assert scenario["provenance"]["kind"] == "synthetic"
    for url in ("/api/v1/scenarios/missing", "/api/v1/runs/missing", "/api/missing"):
        assert client.get(url).status_code == 404
    assert client.get("/").json["error"]["code"] == "frontend_not_built"
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<h1>ReliefGrid</h1>")
    assert b"ReliefGrid" in client.get("/planner").data
    assert client.get("/api/v1/missing").status_code == 404


@pytest.mark.parametrize("changes", [
    {"hubCount": 9}, {"hubCount": -1}, {"responseTimeMinutes": -1},
    {"scenarioRevision": "stale"}, {"closedEdgeIds": ["missing-road"]},
    {"qaoa": {"layers": 4}}, {"qaoa": {"shots": 8193}},
    {"qaoa": {"maxEvaluations": 301}}, {"unknownField": True},
])
def test_invalid_planning_requests(service, changes):
    client, _ = service
    data = payload()
    data.update(changes)
    for endpoint in ("preview", "runs"):
        response = client.post(f"/api/v1/{endpoint}", json=data)
        assert response.status_code == 400
        assert response.json["error"]["message"]
        assert response.json["error"]["retryable"] is False


def test_malformed_json_size_limit_and_missing_scenario(service):
    client, _ = service
    assert client.post("/api/v1/preview", data="{", content_type="application/json").status_code == 400
    assert client.post("/api/v1/preview", json=None).status_code in (400, 415)
    assert client.post("/api/v1/preview", data=" " * (2 * 1024 * 1024 + 1),
                       content_type="application/json").status_code == 413
    data = payload()
    data["scenarioId"] = "missing"
    assert client.post("/api/v1/preview", json=data).status_code == 404


def test_preview_closure_changes_hash_reachability_and_nulls(service):
    client, _ = service
    before = client.post("/api/v1/preview", json=payload()).json
    after = client.post("/api/v1/preview", json=payload(closedEdgeIds=["bridge-main"])).json
    assert before["problemHash"] != after["problemHash"]
    assert after["affectedCommunityIds"]
    assert before["preparedProblem"]["coverageMatrix"] != after["preparedProblem"]["coverageMatrix"]
    assert before["unreachableCommunityIds"]
    assert any(all(t is None for t in row) for row in after["preparedProblem"]["travelMinutes"])


@pytest.mark.parametrize("solver", ["exact", "greedy", "random", "qaoa"])
def test_real_spawn_results_paths_export_and_independent_score(service, solver):
    client, manager = service
    data = payload(closedEdgeIds=["bridge-main"])
    data.update(solver=solver, qaoa={"layers": 1, "shots": 32, "maxEvaluations": 2})
    response = client.post("/api/v1/runs", json=data)
    assert response.status_code == 202
    run_id = response.json["runId"]
    job = wait_for(manager, run_id)
    assert job["status"] == "succeeded", job
    result = job["result"]
    problem = PreparedProblem.model_validate(manager.get(run_id, include_snapshot=True)["snapshot"]["preparedProblem"])
    score = evaluate_plan(problem, result["selectedHubIds"])
    for key, value in score.items():
        assert result[key] == json.loads(json.dumps(value)), key
    assert result["feasible"] and result["problemHash"] == response.json["problemHash"]
    paths = result["diagnostics"]["servicePaths"]
    for assignment in result["assignments"]:
        if assignment["covered"]:
            path = paths[assignment["communityId"]]
            assert path["travelMinutes"] == assignment["travelMinutes"]
            assert "bridge-main" not in path["edgeIds"]
            assert len(path["nodeIds"]) >= 1 and path["coordinates"]
        else:
            assert assignment["hubId"] is None and assignment["travelMinutes"] is None
    if solver == "exact":
        assert result["coveredPopulation"] == 8140
    if solver == "qaoa":
        assert result["diagnostics"]["resources"]["qubits"] == 8
    exported = client.get(f"/api/v1/runs/{run_id}/export")
    assert exported.status_code == 200 and exported.json["synthetic"] is True
    assert exported.json["snapshot"]["request"] == PlanningRequest.model_validate(data).model_dump(mode="json")
    assert exported.json["result"] == result
    assert "attachment" in exported.headers["Content-Disposition"]
    assert client.delete(f"/api/v1/runs/{run_id}").json["status"] == "succeeded"


def test_stress_tests_fixed_plan_and_rejects_invalid_selection(service):
    client, _ = service
    data = payload()
    data["selectedHubIds"] = ["hub-01", "hub-07", "hub-08"]
    response = client.post("/api/v1/stress-test", json=data)
    assert response.status_code == 200
    result = response.json
    assert result["nominalCoveredPopulation"] == 9060
    assert result["worstCoveredPopulation"] <= result["nominalCoveredPopulation"]
    for variant in result["variants"]:
        request_data = {k: v for k, v in data.items() if k != "selectedHubIds"}
        request_data["closedEdgeIds"] = variant["closedEdgeIds"]
        problem = prepare_problem(load_scenario("riverbend"), PlanningRequest.model_validate(request_data))
        assert variant["problemHash"] == problem.problemHash
        assert variant["coveredPopulation"] == evaluate_plan(problem, data["selectedHubIds"])["coveredPopulation"]
    for selected in (None, [], ["hub-01"] * 3, ["unknown", "hub-01", "hub-02"]):
        data["selectedHubIds"] = selected
        assert client.post("/api/v1/stress-test", json=data).status_code == 400


def test_queue_cancel_timeout_and_immutable_snapshot(tmp_path):
    manager = JobManager(tmp_path, capacity=2, timeout_seconds=15, executor=slow_executor)
    try:
        original = snapshot()
        first = manager.submit(original)
        wait_for(manager, first["runId"], {"running"})
        process = manager._active[1]
        second = manager.submit(original)
        original["request"]["hubCount"] = 0
        assert manager.get(second["runId"], include_snapshot=True)["snapshot"]["request"]["hubCount"] == 3
        with pytest.raises(QueueFullError):
            manager.submit(snapshot())
        client = create_app(job_manager=manager).test_client()
        assert client.post("/api/v1/runs", json=payload()).status_code == 429
        assert client.get(f"/api/v1/runs/{first['runId']}/export").status_code == 409
        assert manager.cancel(second["runId"])["status"] == "cancelled"
        assert manager.cancel(first["runId"])["status"] == "cancelled"
        assert not process.is_alive()
        assert manager.cancel(first["runId"])["status"] == "cancelled"
        manager.timeout_seconds = .2
        third = manager.submit(snapshot())
        job = wait_for(manager, third["runId"])
        assert job["status"] == "timed_out" and "result" not in job
        assert job["error"]["code"] == "solver_timeout"
        assert all(not p.is_alive() for p in mp.active_children())
        manager.executor = execute_job
        manager.timeout_seconds = 25
        recovered = manager.submit(snapshot())
        assert wait_for(manager, recovered["runId"])["status"] == "succeeded"
    finally:
        manager.close()
    restored = JobManager(tmp_path)
    try:
        assert restored.get(first["runId"])["status"] == "cancelled"
        assert restored.get(third["runId"])["status"] == "timed_out"
    finally:
        restored.close()


def test_worker_failure_is_explicit_and_queue_continues(tmp_path):
    manager = JobManager(tmp_path, executor=failing_executor)
    try:
        one = manager.submit(snapshot())
        two = manager.submit(snapshot())
        for job_id in (one["runId"], two["runId"]):
            job = wait_for(manager, job_id)
            assert job["status"] == "failed"
            assert job["error"]["code"] == "solver_failed"
            assert "deliberate worker failure" in job["error"]["message"]
            assert "result" not in job
    finally:
        manager.close()


def test_restart_marks_unfinished_run_failed(tmp_path):
    job = dict(runId="old", status="running", snapshot=snapshot())
    (tmp_path / "old.json").write_text(json.dumps(job))
    manager = JobManager(tmp_path)
    try:
        assert manager.get("old")["error"]["code"] == "server_restarted"
        persisted = json.loads((tmp_path / "old.json").read_text())
        assert persisted["status"] == "failed" and persisted["finishedAt"] > 0
    finally:
        manager.close()


def test_quantum_resource_limit_is_explicit_worker_failure(tmp_path):
    scenario = load_scenario("riverbend")
    hubs = (*scenario.candidateHubs,
            *(Hub(id=f"hub-extra-{i}", nodeId=scenario.nodes[i].id) for i in range(5)))
    scenario = scenario.model_copy(update={"candidateHubs": hubs})
    request = PlanningRequest(scenarioId=scenario.id, scenarioRevision=scenario_revision(scenario),
                              solver="qaoa", hubCount=3, responseTimeMinutes=12)
    problem = prepare_problem(scenario, request)
    manager = JobManager(tmp_path)
    try:
        run = manager.submit(dict(request=request.model_dump(mode="json"),
                                  scenario=scenario.model_dump(mode="json"),
                                  preparedProblem=problem.model_dump(mode="json")))
        job = wait_for(manager, run["runId"])
        assert job["status"] == "failed" and "result" not in job
        assert job["error"]["code"] == "solver_failed"
        assert "limit is 12 hubs" in job["error"]["message"]
    finally:
        manager.close()
