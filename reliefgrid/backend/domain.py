"""Canonical v1 contracts. Wire names are also Python attribute names.

Qiskit bit j encodes hubIds[j]; its printed bitstring is reversed relative to
hubIds. For hubIds=(a,b,c), printed '101' means a and c are selected.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1"
MODEL_VERSION = "1"
Solver = Literal["exact", "greedy", "random", "qaoa"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class ScenarioProvenance(Contract):
    kind: Literal["synthetic", "open-data"]
    sources: tuple[str, ...] = ()
    license: str
    retrievedAt: str | None = None
    transformationNotes: str


class Node(Contract):
    id: str = Field(min_length=1)
    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)
    name: str | None = None


class Edge(Contract):
    id: str = Field(min_length=1)
    fromNodeId: str
    toNodeId: str
    travelMinutes: float = Field(gt=0)
    bidirectional: bool
    geometry: dict[str, Any] | None = None
    name: str | None = None


class Community(Contract):
    id: str = Field(min_length=1)
    nodeId: str
    population: float = Field(ge=0)
    priorityMultiplier: float = Field(default=1, ge=0)
    name: str | None = None


class Hub(Contract):
    id: str = Field(min_length=1)
    nodeId: str
    name: str | None = None


class Scenario(Contract):
    schemaVersion: Literal["1"] = "1"
    id: str = Field(min_length=1)
    title: str
    description: str | None = None
    crs: Literal["EPSG:4326"] = "EPSG:4326"
    provenance: ScenarioProvenance
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    communities: tuple[Community, ...]
    candidateHubs: tuple[Hub, ...]

    @model_validator(mode="after")
    def references(self):
        for key in ("nodes", "edges", "communities", "candidateHubs"):
            ids = [item.id for item in getattr(self, key)]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate IDs in {key}")
        nodes = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.fromNodeId not in nodes or edge.toNodeId not in nodes:
                raise ValueError(f"unknown node on edge {edge.id}")
            if edge.geometry is not None:
                geometry = edge.geometry
                if geometry.get("type") != "LineString" or len(geometry.get("coordinates", [])) < 2:
                    raise ValueError(f"invalid LineString on edge {edge.id}")
                for point in geometry["coordinates"]:
                    if len(point) != 2 or not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
                        raise ValueError(f"invalid coordinates on edge {edge.id}")
        for item in (*self.communities, *self.candidateHubs):
            if item.nodeId not in nodes:
                raise ValueError(f"unknown node on {item.id}")
        return self


class QaoaOptions(Contract):
    layers: int = Field(default=1, ge=1, le=3)
    shots: int = Field(default=512, ge=1, le=8192)
    maxEvaluations: int = Field(default=40, ge=1, le=300)
    starts: int = Field(default=1, ge=1, le=4)
    phaseScale: float = Field(default=1, ge=1, le=20)
    warmStartGreedy: bool = False


class PlanningRequest(Contract):
    scenarioId: str
    scenarioRevision: str
    closedEdgeIds: tuple[str, ...] = ()
    hubCount: int = Field(ge=0, le=100)
    responseTimeMinutes: float = Field(ge=0, le=10000)
    solver: Solver = "greedy"
    seed: int = Field(default=42, ge=0, le=4294967295)
    qaoa: QaoaOptions | None = None


class PreparedProblem(Contract):
    modelVersion: Literal["1"] = "1"
    scenarioRevision: str
    problemHash: str
    hubIds: tuple[str, ...]
    communityIds: tuple[str, ...]
    hubCount: int = Field(ge=0)
    demandWeights: tuple[float, ...]
    populations: tuple[float, ...]
    coverageMatrix: tuple[tuple[bool, ...], ...]
    travelMinutes: tuple[tuple[float | None, ...], ...]
    responseTimeMinutes: float = Field(default=0, ge=0)
    closedEdgeIds: tuple[str, ...] = ()

    @model_validator(mode="after")
    def dimensions(self):
        n, m = len(self.hubIds), len(self.communityIds)
        if self.hubCount > n:
            raise ValueError("hubCount exceeds candidate hubs")
        if len(set(self.hubIds)) != n or len(set(self.communityIds)) != m:
            raise ValueError("prepared IDs must be unique")
        if self.hubIds != tuple(sorted(self.hubIds)) or self.communityIds != tuple(sorted(self.communityIds)):
            raise ValueError("prepared IDs must be canonically sorted")
        if any(len(v) != m for v in (self.demandWeights, self.populations, self.coverageMatrix, self.travelMinutes)):
            raise ValueError("community dimension mismatch")
        if any(len(row) != n for row in (*self.coverageMatrix, *self.travelMinutes)):
            raise ValueError("hub dimension mismatch")
        if any(x < 0 for x in (*self.demandWeights, *self.populations)):
            raise ValueError("weights and populations must be nonnegative")
        if any(t is not None and t < 0 for row in self.travelMinutes for t in row):
            raise ValueError("travel times must be nonnegative or null")
        return self


class Assignment(Contract):
    communityId: str
    hubId: str | None
    travelMinutes: float | None
    covered: bool


class Timing(Contract):
    preprocessMs: float = Field(default=0, ge=0)
    constructionMs: float = Field(default=0, ge=0)
    optimizationMs: float = Field(default=0, ge=0)
    samplingMs: float = Field(default=0, ge=0)
    totalMs: float = Field(default=0, ge=0)


class Provenance(Contract):
    scenarioRevision: str
    modelVersion: str = MODEL_VERSION
    codeRevision: str = "working-tree"
    versions: dict[str, str] = Field(default_factory=dict)
    executionMode: str = "classical"
    seed: int
    parameters: dict[str, Any] = Field(default_factory=dict)


class PlanResult(Contract):
    solver: Solver
    problemHash: str
    runHash: str
    selectedHubIds: tuple[str, ...]
    feasible: bool
    deployedHubCount: int = Field(ge=0)
    coveredPopulation: float = Field(ge=0)
    totalPopulation: float = Field(ge=0)
    weightedCoverage: float = Field(ge=0)
    uncoveredCommunityIds: tuple[str, ...]
    assignments: tuple[Assignment, ...]
    timing: Timing = Field(default_factory=Timing)
    provenance: Provenance
    diagnostics: dict[str, Any] = Field(default_factory=dict)


def canonical_hash(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def scenario_revision(scenario: Scenario) -> str:
    return canonical_hash(scenario)


def problem_hash(**payload: Any) -> str:
    payload.setdefault("modelVersion", MODEL_VERSION)
    if "closedEdgeIds" in payload:
        payload["closedEdgeIds"] = sorted(set(payload["closedEdgeIds"]))
    return canonical_hash(payload)


def run_hash(problem: PreparedProblem, request: PlanningRequest, *, parameters: dict | None = None) -> str:
    options = request.qaoa
    if request.solver == "qaoa" and options is None:
        options = QaoaOptions()
    request_hash = canonical_hash({"problemHash": problem.problemHash, "solver": request.solver,
                                   "seed": request.seed, "qaoa": options.model_dump(mode="json") if options else None})
    if parameters is not None:
        return canonical_hash({"requestRunHash": request_hash, "parameters": parameters})
    return request_hash
