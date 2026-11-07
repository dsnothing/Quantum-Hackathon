"""Offline scenario loading and directed, closure-aware road preparation.

Road times are minutes from hubs to communities (never the reverse). Parallel
arcs retain the shortest open edge, breaking equal-time ties by stable edge ID.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import networkx as nx

from .domain import (
    MODEL_VERSION, PlanningRequest, PreparedProblem, Scenario,
    problem_hash, scenario_revision,
)

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"
_SCENARIO_IDS = ("riverbend", "upland")


def load_scenario(scenario_id: str) -> Scenario:
    """Load a bundled validated scenario; IDs cannot address arbitrary paths."""
    if scenario_id not in _SCENARIO_IDS:
        raise KeyError(f"Unknown scenario: {scenario_id}")
    return Scenario.model_validate_json((SCENARIO_DIR / f"{scenario_id}.json").read_text(encoding="utf-8"))


def list_scenarios() -> list[dict]:
    """Small list suitable for the scenario selector, with content revisions."""
    result = []
    for scenario_id in _SCENARIO_IDS:
        scenario = load_scenario(scenario_id)
        result.append({"id": scenario.id, "title": scenario.title,
                       "scenarioRevision": scenario_revision(scenario),
                       "provenance": scenario.provenance.model_dump(mode="json"),
                       "communityCount": len(scenario.communities),
                       "hubCount": len(scenario.candidateHubs)})
    return result


def build_graph(scenario: Scenario, closed_edge_ids: Iterable[str] = ()) -> nx.DiGraph:
    closed = set(closed_edge_ids)
    unknown = closed - {edge.id for edge in scenario.edges}
    if unknown:
        raise ValueError(f"Unknown closed edge IDs: {', '.join(sorted(unknown))}")
    graph = nx.DiGraph()
    graph.add_nodes_from(sorted(node.id for node in scenario.nodes))
    # Stable insertion makes Dijkstra's equal-distance path choice reproducible.
    for edge in sorted(scenario.edges, key=lambda edge: edge.id):
        if edge.id in closed:
            continue
        pairs = [(edge.fromNodeId, edge.toNodeId)]
        if edge.bidirectional:
            pairs.append((edge.toNodeId, edge.fromNodeId))
        for source, target in pairs:
            previous = graph.get_edge_data(source, target)
            if previous is None or (edge.travelMinutes, edge.id) < (previous["weight"], previous["edgeId"]):
                graph.add_edge(source, target, weight=edge.travelMinutes, edgeId=edge.id)
    return graph


def prepare_problem(scenario: Scenario, request: PlanningRequest) -> PreparedProblem:
    revision = scenario_revision(scenario)
    if request.scenarioId != scenario.id:
        raise ValueError("Request scenarioId does not match the loaded scenario")
    if request.scenarioRevision != revision:
        raise ValueError("Scenario revision changed; reload the scenario before planning")
    hubs = sorted(scenario.candidateHubs, key=lambda hub: hub.id)
    communities = sorted(scenario.communities, key=lambda community: community.id)
    if request.hubCount > len(hubs):
        raise ValueError("hubCount cannot exceed candidate hub count")
    graph = build_graph(scenario, request.closedEdgeIds)
    distances = [nx.single_source_dijkstra_path_length(graph, hub.nodeId, weight="weight") for hub in hubs]
    travel = [[distance.get(community.nodeId) for distance in distances] for community in communities]
    coverage = [[value is not None and value <= request.responseTimeMinutes for value in row] for row in travel]
    payload = dict(
        modelVersion=MODEL_VERSION, scenarioRevision=revision,
        closedEdgeIds=sorted(set(request.closedEdgeIds)),
        hubIds=[hub.id for hub in hubs], communityIds=[community.id for community in communities],
        hubCount=request.hubCount, responseTimeMinutes=request.responseTimeMinutes,
        demandWeights=[community.population * community.priorityMultiplier for community in communities],
        populations=[community.population for community in communities],
        coverageMatrix=coverage, travelMinutes=travel,
    )
    return PreparedProblem(problemHash=problem_hash(**payload), **payload)


def shortest_service_path(scenario: Scenario, closed_edge_ids: Iterable[str],
                          hub_id: str, community_id: str) -> dict | None:
    """Reconstruct actual service geometry, or None for unreachable demand.

    This helper does not apply the response threshold; callers must check the
    returned minutes before describing a community as covered.
    """
    hubs = {hub.id: hub for hub in scenario.candidateHubs}
    communities = {community.id: community for community in scenario.communities}
    if hub_id not in hubs or community_id not in communities:
        raise ValueError("Unknown hub or community ID")
    graph = build_graph(scenario, closed_edge_ids)
    try:
        minutes, nodes = nx.single_source_dijkstra(
            graph, hubs[hub_id].nodeId, communities[community_id].nodeId, weight="weight")
    except nx.NetworkXNoPath:
        return None
    edge_by_id = {edge.id: edge for edge in scenario.edges}
    node_by_id = {node.id: node for node in scenario.nodes}
    edge_ids = [graph[a][b]["edgeId"] for a, b in zip(nodes, nodes[1:])]
    coordinates = []
    for source, edge_id in zip(nodes, edge_ids):
        edge = edge_by_id[edge_id]
        if edge.geometry:
            points = list(edge.geometry["coordinates"])
            if source != edge.fromNodeId:
                points.reverse()
        else:
            a, b = node_by_id[edge.fromNodeId], node_by_id[edge.toNodeId]
            points = [[a.lon, a.lat], [b.lon, b.lat]]
            if source != edge.fromNodeId:
                points.reverse()
        coordinates.extend(points if not coordinates else points[1:])
    if not coordinates:
        node = node_by_id[nodes[0]]
        coordinates = [[node.lon, node.lat]]
    return {"hubId": hub_id, "communityId": community_id, "nodeIds": nodes,
            "edgeIds": edge_ids, "coordinates": coordinates, "travelMinutes": minutes}


get_service_path = shortest_service_path
