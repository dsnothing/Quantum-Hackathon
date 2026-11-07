"""Bounded single-process solver queue, independent of Flask request contexts."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
import multiprocessing as mp
from pathlib import Path
import threading
import time
import uuid

from .domain import PlanningRequest, PreparedProblem, Scenario, run_hash
from .graph import shortest_service_path
from .solvers.classical import classical_parameters, solve_exact, solve_greedy, solve_random

TERMINAL = {"succeeded", "failed", "cancelled", "timed_out"}


def execute_job(snapshot: dict) -> dict:
    """Spawn-safe entry point: all scientific inputs are immutable JSON snapshots."""
    request = PlanningRequest.model_validate(snapshot["request"])
    problem = PreparedProblem.model_validate(snapshot["preparedProblem"])
    scenario = Scenario.model_validate(snapshot["scenario"])
    if request.solver == "qaoa":
        from .solvers.qaoa import solve_qaoa
        result = solve_qaoa(problem, request)
    else:
        result = {"exact": solve_exact, "greedy": solve_greedy, "random": solve_random}[request.solver](problem, request)
    paths = {a.communityId: shortest_service_path(scenario, request.closedEdgeIds, a.hubId, a.communityId)
             for a in result.assignments if a.covered and a.hubId is not None}
    result = result.model_copy(update={"diagnostics": {**result.diagnostics, "servicePaths": paths}})
    return result.model_dump(mode="json")


def _child(connection, snapshot, executor):
    try:
        connection.send({"result": executor(snapshot)})
    except Exception as exc:
        connection.send({"error": {"code": "solver_failed", "message": str(exc), "retryable": False}})
    finally:
        connection.close()


class QueueFullError(Exception):
    pass


class JobManager:
    def __init__(self, storage_dir=None, *, capacity=4, timeout_seconds=60,
                 executor=execute_job, process_context=None):
        self.capacity = capacity
        self.timeout_seconds = timeout_seconds
        self.executor = executor
        self.context = process_context or mp.get_context("spawn")
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self._jobs = {}
        self._pending = deque()
        self._condition = threading.Condition(threading.RLock())
        self._active = None
        self._closed = False
        self._thread = None
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            for path in self.storage_dir.glob("*.json"):
                try:
                    job = json.loads(path.read_text(encoding="utf-8"))
                    if job["status"] not in TERMINAL:
                        job.update(status="failed", finishedAt=time.time(), error={"code": "server_restarted", "message": "Server restarted; submit this plan again.", "retryable": True})
                        self._persist(job)
                    self._jobs[job["runId"]] = job
                except (ValueError, KeyError, OSError):
                    continue

    def _persist(self, job):
        if self.storage_dir:
            path = self.storage_dir / (job["runId"] + ".json")
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(job, indent=2, allow_nan=False), encoding="utf-8")
            temporary.replace(path)

    def submit(self, snapshot):
        with self._condition:
            if self._closed:
                raise RuntimeError("Job manager is closed")
            if sum(j["status"] not in TERMINAL for j in self._jobs.values()) >= self.capacity:
                raise QueueFullError("The solver queue is full. Wait for a run to finish.")
            snapshot = deepcopy(snapshot)
            request = PlanningRequest.model_validate(snapshot["request"])
            problem = PreparedProblem.model_validate(snapshot["preparedProblem"])
            parameters = None if request.solver == "qaoa" else classical_parameters(request)
            run_id = uuid.uuid4().hex
            job = dict(runId=run_id, status="queued", problemHash=problem.problemHash,
                       runHash=run_hash(problem, request, parameters=parameters), createdAt=time.time(), snapshot=snapshot)
            self._jobs[run_id] = job
            self._persist(job)
            self._pending.append(run_id)
            if self._thread is None:
                self._thread = threading.Thread(target=self._work, daemon=True, name="reliefgrid-jobs")
                self._thread.start()
            self._condition.notify_all()
            return self.get(run_id)

    def get(self, run_id, *, include_snapshot=False):
        with self._condition:
            if run_id not in self._jobs:
                raise KeyError(run_id)
            job = deepcopy(self._jobs[run_id])
            if not include_snapshot:
                job.pop("snapshot", None)
            return job

    def _stop_active(self):
        if self._active:
            process = self._active[1]
            if process.is_alive():
                process.terminate()
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join(timeout=2)

    def cancel(self, run_id):
        with self._condition:
            job = self._jobs.get(run_id)
            if job is None:
                raise KeyError(run_id)
            if job["status"] not in TERMINAL:
                if self._active and self._active[0] == run_id:
                    self._stop_active()
                job.update(status="cancelled", finishedAt=time.time())
                self._persist(job)
                self._condition.notify_all()
            return self.get(run_id)

    def _work(self):
        while True:
            with self._condition:
                while not self._pending and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                run_id = self._pending.popleft()
                job = self._jobs[run_id]
                if job["status"] in TERMINAL:
                    continue
                parent, child = self.context.Pipe(duplex=False)
                process = self.context.Process(target=_child, args=(child, job["snapshot"], self.executor), daemon=True)
                try:
                    process.start()
                except Exception as exc:
                    parent.close()
                    child.close()
                    job.update(status="failed", finishedAt=time.time(), error={"code": "worker_start_failed", "message": str(exc), "retryable": True})
                    self._persist(job)
                    continue
                child.close()
                self._active = (run_id, process)
                job.update(status="running", startedAt=time.time())
                started = time.monotonic()
                self._persist(job)
            message = None
            while True:
                with self._condition:
                    if job["status"] in TERMINAL:
                        break
                    if time.monotonic() - started >= self.timeout_seconds:
                        self._stop_active()
                        job.update(status="timed_out", error={"code": "solver_timeout", "message": "Solver exceeded the time limit. Reduce its evaluation budget and retry.", "retryable": True})
                        break
                    try:
                        if parent.poll():
                            message = parent.recv()
                            break
                    except (EOFError, OSError):
                        break
                    if not process.is_alive():
                        break
                    self._condition.wait(timeout=0.025)
            with self._condition:
                self._stop_active()
                parent.close()
                self._active = None
                if job["status"] not in TERMINAL:
                    if message and "result" in message:
                        job.update(status="succeeded", result=message["result"])
                    else:
                        job.update(status="failed", error=(message or {}).get("error", {"code": "worker_failed", "message": "Solver process exited unexpectedly.", "retryable": True}))
                job["finishedAt"] = time.time()
                self._persist(job)
                self._condition.notify_all()

    def close(self):
        with self._condition:
            self._closed = True
            for run_id in list(self._jobs):
                if self._jobs[run_id]["status"] not in TERMINAL:
                    self.cancel(run_id)
            self._condition.notify_all()
        if self._thread:
            self._thread.join(timeout=3)
