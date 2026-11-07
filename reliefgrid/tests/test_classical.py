"""Adversarial coverage fixtures, exhaustive reference, and reproducible sampling."""
from itertools import combinations
from math import comb

import pytest

from backend.domain import PlanningRequest, PreparedProblem, scenario_revision
from backend.graph import load_scenario, prepare_problem
from backend.objective import evaluate_plan
from backend.solvers.classical import solve_exact, solve_greedy, solve_random


def fixture(k=2, weights=(10, 9, 8, 0)):
    matrix = ((True, True, False), (True, False, False),
              (False, True, True), (False, False, False))
    return PreparedProblem(scenarioRevision="fixture", problemHash="fixture-hash",
        hubIds=("a", "b", "c"), communityIds=("c1", "c2", "c3", "c4"), hubCount=k,
        demandWeights=weights, populations=(100, 20, 30, 40), coverageMatrix=matrix,
        travelMinutes=((2, 2, 8), (3, None, None), (None, 4, 5), (None, None, None)),
        responseTimeMinutes=5)


def request(problem, **kwargs):
    return PlanningRequest(scenarioId="fixture", scenarioRevision=problem.scenarioRevision,
        hubCount=problem.hubCount, responseTimeMinutes=problem.responseTimeMinutes, **kwargs)


def test_independent_evaluation_overlap_ties_and_unreachable():
    p = fixture()
    score = evaluate_plan(p, ["b", "a"])
    assert score["feasible"] and score["selectedHubIds"] == ("a", "b")
    assert score["weightedCoverage"] == 27
    assert score["coveredPopulation"] == 150 and score["totalPopulation"] == 190
    assert score["assignments"][0]["hubId"] == "a"
    assert score["assignments"][2]["travelMinutes"] == 4
    assert score["assignments"][3] == dict(communityId="c4", hubId=None, travelMinutes=None, covered=False)
    assert score["uncoveredCommunityIds"] == ("c4",)


@pytest.mark.parametrize("selection", [("a",), ("a", "a"), ("a", "missing"), ("a", "b", "c")])
def test_invalid_deployment_is_never_recommended(selection):
    assert not evaluate_plan(fixture(), selection)["feasible"]


def test_scorer_recomputes_from_times_instead_of_trusting_coverage_matrix():
    p = fixture(1).model_copy(update={"coverageMatrix": ((False, False, False),) * 4})
    assert evaluate_plan(p, ["a"])["weightedCoverage"] == 19
    # A reachable community outside the threshold has a null assignment.
    assert evaluate_plan(fixture(1), ["c"])["assignments"][0]["hubId"] is None


@pytest.mark.parametrize("k", [0, 1, 2, 3])
def test_exact_matches_independent_exhaustive_scoring_and_all_ties(k):
    p = fixture(k)
    reference = [(evaluate_plan(p, ids)["weightedCoverage"], ids)
                 for ids in combinations(p.hubIds, k)]
    optimum = max(score for score, _ in reference)
    ties = [ids for score, ids in reference if score == optimum]
    result = solve_exact(p, request(p))
    assert result.feasible and result.weightedCoverage == optimum
    assert result.selectedHubIds == ties[0]
    assert result.diagnostics["optimumCount"] == len(ties)
    assert result.diagnostics["evaluations"] == comb(3, k)
    assert result.solver == "exact"


def test_greedy_weighted_marginal_gain_and_zero_gain_completion():
    p = fixture()
    result = solve_greedy(p, request(p))
    assert result.selectedHubIds == ("a", "b") and result.weightedCoverage == 27
    assert [x["marginalWeightedCoverage"] for x in result.diagnostics["steps"]] == [19, 8]
    zero = fixture(2, (0, 0, 0, 0))
    result = solve_greedy(zero, request(zero))
    assert result.feasible and result.selectedHubIds == ("a", "b")
    assert solve_exact(zero, request(zero)).diagnostics["optimumCount"] == 3


def test_random_reproducibility_raw_counts_expected_value_and_bit_order():
    p = fixture(1)
    a = solve_random(p, request(p, seed=42), samples=6000)
    b = solve_random(p, request(p, seed=42), samples=6000)
    assert a.selectedHubIds == b.selectedHubIds
    assert a.diagnostics == b.diagnostics and a.runHash == b.runHash
    counts = a.diagnostics["counts"]
    assert sum(counts.values()) == 6000 and set(counts) == {"001", "010", "100"}
    assert all(1700 < count < 2300 for count in counts.values())
    expected = (19 * counts["001"] + 18 * counts["010"] + 8 * counts["100"]) / 6000
    assert a.diagnostics["expectedWeightedCoverage"] == pytest.approx(expected)
    assert a.selectedHubIds == ("a",) and a.feasible


@pytest.mark.parametrize("k", [0, 3])
def test_trivial_fixed_cardinality(k):
    p = fixture(k)
    for solver in (solve_exact, solve_greedy, solve_random):
        result = solver(p, request(p))
        assert result.feasible and result.deployedHubCount == k
        assert len(result.selectedHubIds) == k


def test_limits_and_problem_request_mismatch():
    p = fixture()
    with pytest.raises(ValueError, match="limit"):
        solve_exact(p, request(p), max_combinations=2)
    for samples in (0, 100001, 1.5, True):
        with pytest.raises(ValueError, match="samples"):
            solve_random(p, request(p), samples=samples)
    for solver in (solve_exact, solve_greedy, solve_random):
        with pytest.raises(ValueError, match="match"):
            solver(p, request(p).model_copy(update={"hubCount": 1}))


def test_bundled_solvers_share_problem_and_closure_changes_result():
    scenario = load_scenario("riverbend")
    req = PlanningRequest(scenarioId=scenario.id, scenarioRevision=scenario_revision(scenario),
                          hubCount=2, responseTimeMinutes=12)
    p = prepare_problem(scenario, req)
    exact, greedy, random = [solver(p, req) for solver in (solve_exact, solve_greedy, solve_random)]
    assert len({result.problemHash for result in (exact, greedy, random)}) == 1
    assert len({result.runHash for result in (exact, greedy, random)}) == 3
    assert exact.weightedCoverage >= max(greedy.weightedCoverage, random.weightedCoverage)
    closed_req = req.model_copy(update={"closedEdgeIds": ("bridge-main",)})
    closed = prepare_problem(scenario, closed_req)
    after = solve_exact(closed, closed_req)
    assert after.problemHash != exact.problemHash
    assert after.weightedCoverage <= exact.weightedCoverage
    assert exact.model_dump(mode="json")["assignments"][-1]["travelMinutes"] is None
