"""Fixed-cardinality maximum-coverage baselines on one frozen problem."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from math import comb, fsum
import platform
import random
from time import perf_counter

from ..domain import PlanResult, PlanningRequest, PreparedProblem, Provenance, Timing, canonical_hash, run_hash
from ..objective import evaluate_plan

MAX_EXACT_COMBINATIONS = 100_000


def _request(problem: PreparedProblem, request: PlanningRequest, solver: str) -> PlanningRequest:
    if (request.scenarioRevision != problem.scenarioRevision
            or request.hubCount != problem.hubCount
            or request.responseTimeMinutes != problem.responseTimeMinutes
            or tuple(sorted(set(request.closedEdgeIds))) != problem.closedEdgeIds):
        raise ValueError("Request does not match the prepared problem")
    return request.model_copy(update={"solver": solver})


def _score(problem: PreparedProblem, indices: tuple[int, ...] | list[int]) -> float:
    return fsum(weight for weight, row in zip(problem.demandWeights, problem.coverageMatrix)
                if any(row[j] for j in indices))


def _result(problem, request, selected, started, diagnostics, *, sampling=False):
    metrics = evaluate_plan(problem, selected)
    elapsed = (perf_counter() - started) * 1000
    return PlanResult(
        solver=request.solver, problemHash=problem.problemHash,
        runHash=canonical_hash({"requestRunHash": run_hash(problem, request),
                                "parameters": diagnostics.get("parameters", {})}), **metrics,
        timing=Timing(totalMs=elapsed, samplingMs=elapsed if sampling else 0,
                      optimizationMs=0 if sampling else elapsed),
        provenance=Provenance(scenarioRevision=problem.scenarioRevision,
                              modelVersion=problem.modelVersion, seed=request.seed,
                              versions={"python": platform.python_version()},
                              parameters=diagnostics.get("parameters", {})),
        diagnostics=diagnostics,
    )


def solve_exact(problem: PreparedProblem, request: PlanningRequest, *,
                max_combinations: int = MAX_EXACT_COMBINATIONS) -> PlanResult:
    """Enumerate every k-subset, selecting the lexicographically first optimum.

    Count all optima; retain at most 256 tied sets to bound evidence size.
    An over-limit instance raises before enumeration, never a heuristic result.
    """
    started = perf_counter()
    request = _request(problem, request, "exact")
    count = comb(len(problem.hubIds), problem.hubCount)
    if max_combinations < 1 or count > max_combinations:
        raise ValueError(f"Exact enumeration requires {count} combinations; limit is {max_combinations}")
    best_score, best = -1.0, ()
    optimum_count, optimal_sets = 0, []
    for choice in combinations(range(len(problem.hubIds)), problem.hubCount):
        score = _score(problem, choice)
        ids = tuple(problem.hubIds[j] for j in choice)
        if score > best_score:
            best_score, best = score, ids
            optimum_count, optimal_sets = 1, [ids]
        elif score == best_score:
            optimum_count += 1
            if len(optimal_sets) < 256:
                optimal_sets.append(ids)
    return _result(problem, request, best, started, {
        "evaluations": count, "combinationCount": count, "provenOptimal": True,
        "optimalWeightedCoverage": best_score, "optimumCount": optimum_count,
        "optimalHubSets": optimal_sets, "tieSetsTruncated": optimum_count > len(optimal_sets),
        "parameters": {"maxCombinations": max_combinations},
    })


def solve_greedy(problem: PreparedProblem, request: PlanningRequest) -> PlanResult:
    """Choose greatest uncovered weighted gain, breaking ties by stable hub ID."""
    started = perf_counter()
    request = _request(problem, request, "greedy")
    selected, covered, steps = [], set(), []
    evaluations = 0
    for _ in range(problem.hubCount):
        gains = []
        for j in range(len(problem.hubIds)):
            if j not in selected:
                gain = fsum(weight for i, (weight, row) in enumerate(
                    zip(problem.demandWeights, problem.coverageMatrix)) if i not in covered and row[j])
                gains.append((gain, j))
                evaluations += 1
        gain, chosen = min(gains, key=lambda item: (-item[0], problem.hubIds[item[1]]))
        selected.append(chosen)
        covered.update(i for i, row in enumerate(problem.coverageMatrix) if row[chosen])
        steps.append({"hubId": problem.hubIds[chosen], "marginalWeightedCoverage": gain})
    return _result(problem, request, [problem.hubIds[j] for j in selected], started, {
        "evaluations": evaluations, "provenOptimal": problem.hubCount in (0, len(problem.hubIds)),
        "steps": steps, "parameters": {"tieBreak": "hubId"},
    })


def solve_random(problem: PreparedProblem, request: PlanningRequest, *, samples: int | None = None) -> PlanResult:
    """Sample uniform k-subsets with replacement and recommend the best sample."""
    started = perf_counter()
    request = _request(problem, request, "random")
    samples = samples if samples is not None else (request.qaoa.shots if request.qaoa else 512)
    if isinstance(samples, bool) or not isinstance(samples, int) or not 1 <= samples <= 100_000:
        raise ValueError("samples must be an integer from 1 through 100000")
    rng = random.Random(request.seed)
    counts = Counter(tuple(sorted(rng.sample(range(len(problem.hubIds)), problem.hubCount)))
                     for _ in range(samples))
    scores = {choice: _score(problem, choice) for choice in counts}
    best = min(counts, key=lambda choice: (-scores[choice], choice))
    # Printed bitstrings follow the canonical Qiskit convention: hub index 0 is rightmost.
    bit_counts = {"".join("1" if j in choice else "0" for j in reversed(range(len(problem.hubIds)))): count
                  for choice, count in sorted(counts.items())}
    expected = fsum(scores[choice] * count / samples for choice, count in counts.items())
    return _result(problem, request, [problem.hubIds[j] for j in best], started, {
        "evaluations": len(counts), "sampleCount": samples, "counts": bit_counts,
        "feasibleFraction": 1.0, "expectedWeightedCoverage": expected,
        "bestSampleWeightedCoverage": scores[best], "provenOptimal": False,
        "parameters": {"samples": samples, "distribution": "uniform fixed-k subsets with replacement"},
    }, sampling=True)
