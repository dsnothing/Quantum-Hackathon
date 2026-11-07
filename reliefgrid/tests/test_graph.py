import json

import pytest

from backend.domain import PlanningRequest, Scenario, scenario_revision
from backend.graph import build_graph, list_scenarios, load_scenario, prepare_problem, shortest_service_path


@pytest.fixture
def tiny():
    return Scenario.model_validate({
        "id": "tiny", "title": "Directed fixture", "schemaVersion": "1", "crs": "EPSG:4326",
        "provenance": {"kind": "synthetic", "sources": [], "license": "CC0-1.0", "transformationNotes": "Test"},
        "nodes": [{"id": n, "lon": i, "lat": 0} for i, n in enumerate("abcd")],
        "edges": [
            {"id": "bridge", "fromNodeId": "a", "toNodeId": "b", "travelMinutes": 2, "bidirectional": True},
            {"id": "oneway", "fromNodeId": "b", "toNodeId": "c", "travelMinutes": 3, "bidirectional": False}],
        "candidateHubs": [{"id": "h1", "nodeId": "a"}, {"id": "h2", "nodeId": "c"}],
        "communities": [{"id": n, "nodeId": n, "population": 10, "priorityMultiplier": 1} for n in "abcd"],
    })


def request(scenario, **kwargs):
    return PlanningRequest(scenarioId=scenario.id, scenarioRevision=scenario_revision(scenario),
                           hubCount=1, responseTimeMinutes=5, **kwargs)


def test_directed_times_threshold_and_null(tiny):
    prepared = prepare_problem(tiny, request(tiny))
    assert prepared.travelMinutes == ((0, None), (2, None), (5, 0), (None, None))
    assert prepared.coverageMatrix[2][0]  # Inclusive threshold boundary.
    encoded = prepared.model_dump_json()
    assert "null" in encoded and "Infinity" not in encoded
    assert json.loads(encoded)["travelMinutes"][3] == [None, None]
    assert shortest_service_path(tiny, (), "h2", "a") is None


def test_bidirectional_closure_removes_both_arcs(tiny):
    graph = build_graph(tiny, ["bridge"])
    assert not graph.has_edge("a", "b") and not graph.has_edge("b", "a")
    prepared = prepare_problem(tiny, request(tiny, closedEdgeIds=["bridge"]))
    assert prepared.travelMinutes[2][0] is None
    assert shortest_service_path(tiny, ["bridge"], "h1", "c") is None


def test_path_geometry_and_determinism(tiny):
    path = shortest_service_path(tiny, (), "h1", "c")
    assert path["edgeIds"] == ["bridge", "oneway"]
    assert path["nodeIds"] == ["a", "b", "c"]
    assert path["coordinates"] == [[0, 0], [1, 0], [2, 0]]
    assert path["travelMinutes"] == 5
    assert shortest_service_path(tiny, (), "h1", "c") == path


def test_hash_is_solver_seed_independent_and_closure_normalized(tiny):
    a = prepare_problem(tiny, request(tiny, closedEdgeIds=["oneway", "bridge", "bridge"]))
    b = prepare_problem(tiny, request(tiny, closedEdgeIds=["bridge", "oneway"], solver="exact", seed=99))
    assert a.problemHash == b.problemHash
    assert a.closedEdgeIds == ("bridge", "oneway")
    assert a.problemHash != prepare_problem(tiny, request(tiny)).problemHash


def test_bad_closure_revision_and_scenario_rejected(tiny):
    with pytest.raises(ValueError, match="Unknown closed"):
        prepare_problem(tiny, request(tiny, closedEdgeIds=["missing"]))
    with pytest.raises(ValueError, match="revision"):
        prepare_problem(tiny, request(tiny).model_copy(update={"scenarioRevision": "old"}))
    with pytest.raises(ValueError, match="scenarioId"):
        prepare_problem(tiny, request(tiny).model_copy(update={"scenarioId": "wrong"}))
    with pytest.raises(KeyError):
        load_scenario("../domain")


def test_bundled_scenarios_are_offline_valid_and_bridge_matters():
    assert {item["id"] for item in list_scenarios()} == {"riverbend", "upland"}
    scenario = load_scenario("riverbend")
    assert (len(scenario.nodes), len(scenario.candidateHubs), len(scenario.communities)) == (40, 8, 15)
    before = prepare_problem(scenario, request(scenario).model_copy(update={"responseTimeMinutes": 12}))
    after = prepare_problem(scenario, request(scenario, closedEdgeIds=["bridge-main"]).model_copy(update={"responseTimeMinutes": 12}))
    assert before.problemHash != after.problemHash
    assert before.coverageMatrix != after.coverageMatrix
    assert all(value is None for value in before.travelMinutes[-1])
    for community in scenario.communities:
        for hub in scenario.candidateHubs:
            path = shortest_service_path(scenario, ["bridge-main"], hub.id, community.id)
            assert path is None or "bridge-main" not in path["edgeIds"]


def test_upland_slow_crossing_survives_main_bridge_closure():
    scenario = load_scenario("upland")
    path = shortest_service_path(scenario, ["bridge-main"], "hub-01", "community-10")
    assert path is not None and "bridge-north" in path["edgeIds"]
