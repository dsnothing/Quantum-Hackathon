"""Transparent classical safeguard around a separately reported QAOA run."""
from time import perf_counter

from ..domain import PlanningRequest, PreparedProblem
from .classical import solve_exact, solve_greedy
from .qaoa import solve_qaoa


def solve_portfolio(problem: PreparedProblem, request: PlanningRequest, *, ensure_exact=False) -> dict:
    """Return at least the guard's score, retaining the actual winning solver.

    An exact guard is bounded by solve_exact's combination cap and raises if
    that cap is exceeded. It never silently substitutes a heuristic guarantee.
    A greedy guard guarantees only parity with greedy, not with an optimum.
    """
    started = perf_counter()
    guard = (solve_exact if ensure_exact else solve_greedy)(problem, request)
    quantum = solve_qaoa(problem, request)
    winner = quantum if quantum.weightedCoverage > guard.weightedCoverage else guard
    return {
        "recommendation": winner.model_dump(mode="json"),
        "selectionSource": winner.solver,
        "guarantee": "exact optimum" if ensure_exact else "at least deterministic greedy coverage",
        "qaoa": quantum.model_dump(mode="json"),
        "classicalGuard": guard.model_dump(mode="json"),
        "totalMs": (perf_counter() - started) * 1000,
        "interpretation": "Classical safeguard supplies the quality guarantee; this is not quantum advantage.",
    }
