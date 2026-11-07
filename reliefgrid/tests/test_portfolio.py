import pytest

from backend.solvers.portfolio import solve_portfolio
from test_qaoa import fixture, request


@pytest.mark.parametrize('ensure_exact', [False, True])
def test_guard_is_never_worse_and_provenance_retains_actual_solver(ensure_exact):
    result = solve_portfolio(fixture(), request(fixture(), maxEvaluations=2, shots=2), ensure_exact=ensure_exact)
    recommendation, guard = result['recommendation'], result['classicalGuard']
    assert recommendation['weightedCoverage'] >= guard['weightedCoverage']
    assert recommendation['solver'] == result['selectionSource']
    assert result['qaoa']['solver'] == 'qaoa'
    if ensure_exact:
        assert recommendation['weightedCoverage'] == guard['weightedCoverage']
        assert result['guarantee'] == 'exact optimum'
    assert result['totalMs'] >= recommendation['timing']['totalMs']
