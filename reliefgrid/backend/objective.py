"""Independent, overlap-safe scoring and deterministic service assignments."""
from __future__ import annotations

from math import fsum
from typing import Iterable

from .domain import PreparedProblem


def evaluate_plan(problem: PreparedProblem, selectedHubIds: Iterable[str]) -> dict:
    """Recompute metrics from a deployment, without trusting solver scores.

    Unknown IDs and duplicate deployments make a plan infeasible. Known unique
    hubs are still scored so invalid samples can be inspected without repair.
    Travel times independently establish inclusive-threshold access; prepared
    graph problems have an equivalent coverage matrix.
    """
    supplied = tuple(selectedHubIds)
    selected = tuple(sorted(set(supplied)))
    indices = {hub: index for index, hub in enumerate(problem.hubIds)}
    known = tuple(hub for hub in selected if hub in indices)
    feasible = (len(supplied) == len(selected) == problem.hubCount
                and len(known) == len(selected))
    covered_indices = []
    assignments = []
    uncovered = []
    for i, community in enumerate(problem.communityIds):
        choices = [(problem.travelMinutes[i][indices[hub]], hub) for hub in known
                   if problem.travelMinutes[i][indices[hub]] is not None
                   and problem.travelMinutes[i][indices[hub]] <= problem.responseTimeMinutes]
        if choices:
            minutes, hub = min(choices)
            covered_indices.append(i)
            assignments.append(dict(communityId=community, hubId=hub,
                                    travelMinutes=minutes, covered=True))
        else:
            uncovered.append(community)
            assignments.append(dict(communityId=community, hubId=None,
                                    travelMinutes=None, covered=False))
    return dict(
        selectedHubIds=selected, feasible=feasible, deployedHubCount=len(known),
        coveredPopulation=fsum(problem.populations[i] for i in covered_indices),
        totalPopulation=fsum(problem.populations),
        weightedCoverage=fsum(problem.demandWeights[i] for i in covered_indices),
        uncoveredCommunityIds=tuple(uncovered), assignments=tuple(assignments),
    )
