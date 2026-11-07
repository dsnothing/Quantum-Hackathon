"""Independent tiny checks of gates, little-endian bits and coherent role."""
from itertools import combinations

import numpy as np
import pytest
from qiskit.quantum_info import Operator, Statevector
from qiskit.circuit import ParameterVector

from backend.domain import PlanningRequest, PreparedProblem, QaoaOptions
from backend.objective import evaluate_plan
from backend.solvers.qaoa import (
    bitstring_hubs, build_cost_circuit, build_mixer, build_preparation, build_qaoa_circuit,
    coverage_terms, qaoa_probabilities, ring_edges, run_ablations, solve_qaoa,
)


def fixture(n=4, k=2, zero=False):
    rows = ((True, False, False, False), (True, True, False, False),
            (False, False, True, True), (False, False, False, True),
            (False, False, False, False), (True, True, False, False))
    rows = tuple(tuple(row[j] if j < 4 else False for j in range(n)) for row in rows)
    weights = (7., 4., 3., 2., 9., 1.) if not zero else (0.,) * 6
    return PreparedProblem(scenarioRevision="fixture-revision", problemHash="fixture-hash",
        hubIds=tuple(f"h{j:02}" for j in range(n)), communityIds=tuple(f"c{i}" for i in range(6)),
        hubCount=k, demandWeights=weights, populations=(7., 4., 3., 2., 9., 1.),
        coverageMatrix=rows, travelMinutes=tuple(tuple(1. if value else None for value in row) for row in rows),
        responseTimeMinutes=2)


def request(problem, **options):
    return PlanningRequest(scenarioId="fixture", scenarioRevision=problem.scenarioRevision,
        hubCount=problem.hubCount, responseTimeMinutes=2, solver="qaoa", seed=138,
        qaoa=QaoaOptions(**options))


@pytest.mark.parametrize("gamma", [-1.2, 0., 0.73])
def test_direct_cost_matches_every_basis_energy_up_to_global_phase(gamma):
    problem = fixture()
    unitary = Operator(build_cost_circuit(problem, gamma)).data
    assert np.allclose(unitary, np.diag(np.diag(unitary)))
    for index in range(16):
        hubs = tuple(hub for j, hub in enumerate(problem.hubIds) if index & (1 << j))
        coverage = evaluate_plan(problem, hubs)["weightedCoverage"]
        # H_C(x) = -C(x)/W; compare against x=0 to eliminate global phase.
        expected = np.exp(1j * gamma * coverage / sum(problem.demandWeights))
        assert np.allclose(unitary[index, index] / unitary[0, 0], expected)
    assert dict(coverage_terms(problem))[(0, 1)] == 5


def test_bit_order_and_xy_gate_convention():
    problem = fixture(n=2, k=1)
    assert bitstring_hubs(problem, "01") == ("h00",)
    assert bitstring_hubs(problem, "10") == ("h01",)
    beta = .37
    state = Statevector.from_int(1, 4).evolve(build_mixer(problem, beta)).data
    assert np.allclose(state[1], np.cos(beta))
    assert np.allclose(state[2], -1j * np.sin(beta))
    assert ring_edges(1) == ()
    assert ring_edges(2) == ((0, 1),)
    assert len(ring_edges(5)) == len(set(map(frozenset, ring_edges(5)))) == 5


@pytest.mark.parametrize("k", [1, 2, 3])
def test_coherent_preparation_and_mixing_preserve_exact_k(k):
    problem = fixture(k=k)
    prep = Statevector.from_instruction(build_preparation(problem)).probabilities()
    assert np.count_nonzero(prep > 1e-10) > 1
    for gammas, betas in [([.7], [.4]), ([.2, -.8, 1.1], [.3, .9, -.6])]:
        probabilities = qaoa_probabilities(problem, gammas, betas)
        assert sum(probabilities[i] for i in range(16) if i.bit_count() != k) < 1e-12
        assert np.isclose(sum(probabilities), 1)


def test_cost_angles_and_dephasing_have_measurable_effect():
    problem = fixture()
    ablation = run_ablations(problem, [.9], [.51])
    assert ablation["coherentGammaZeroTotalVariation"] > .001
    assert ablation["coherentDephasedTotalVariation"] > .001
    # Complete computational-basis dephasing erases the cost phase information.
    dephased_zero = qaoa_probabilities(problem, [0.], [.51], dephase_after_cost=True)
    assert np.allclose(dephased_zero, ablation["dephased"]["probabilities"])
    # In coherent p=2 both gamma coordinates are active on this fixture.
    full = qaoa_probabilities(problem, [.9, .7], [.51, .31])
    for gammas in ([0., .7], [.9, 0.]):
        assert np.abs(full - qaoa_probabilities(problem, gammas, [.51, .31])).sum() > .001


def test_solver_sampled_results_budget_resources_and_shared_scorer():
    problem = fixture()
    req = request(problem, shots=160, maxEvaluations=15, starts=2)
    result = solve_qaoa(problem, req)
    repeated = solve_qaoa(problem, req)
    assert result.diagnostics["counts"] == repeated.diagnostics["counts"]
    assert sum(result.diagnostics["counts"].values()) == 160
    assert 0 < result.diagnostics["evaluations"] <= 15
    assert result.feasible and result.deployedHubCount == 2
    assert result.diagnostics["feasibleFraction"] == 1
    assert result.diagnostics["resources"]["twoQubitGates"] > 0
    assert result.diagnostics["resources"]["preparationTwoQubitGates"] > 0
    metrics = evaluate_plan(problem, result.selectedHubIds)
    assert result.weightedCoverage == metrics["weightedCoverage"]
    scores = [evaluate_plan(problem, hubs)["weightedCoverage"] for hubs in combinations(problem.hubIds, 2)]
    assert result.diagnostics["optimalWeightedCoverage"] == max(scores)
    assert result.provenance.executionMode == "ideal-simulator optimization with sampled evaluation"


@pytest.mark.parametrize("k,zero", [(0, False), (4, False), (2, True)])
def test_trivial_bypasses(k, zero):
    problem = fixture(k=k, zero=zero)
    result = solve_qaoa(problem, request(problem, shots=10))
    assert result.diagnostics["evaluations"] == 0
    assert result.diagnostics["trivialBypass"]
    assert len(result.diagnostics["counts"]) == 1
    assert result.selectedHubIds == problem.hubIds[:k]
    if zero:
        assert result.diagnostics["expectedApproximationRatio"] is None


def test_resource_caps_and_invalid_parameters():
    with pytest.raises(ValueError, match="12 hubs"):
        build_preparation(fixture(n=13))
    with pytest.raises(ValueError, match="8 hubs"):
        qaoa_probabilities(fixture(n=9), [.2], [.3], dephase_after_cost=True)
    with pytest.raises(ValueError, match="matching"):
        qaoa_probabilities(fixture(), [], [])
    with pytest.raises(ValueError, match="binary"):
        bitstring_hubs(fixture(), "010x")


def test_empty_problem_and_request_validation():
    problem = fixture(n=0, k=0)
    result = solve_qaoa(problem, request(problem, shots=2))
    assert result.feasible and result.selectedHubIds == ()
    assert result.diagnostics["counts"] == {"": 2}
    with pytest.raises(ValueError, match="does not match"):
        solve_qaoa(problem, request(problem).model_copy(update={"responseTimeMinutes": 3}))
    with pytest.raises(ValueError, match="does not match"):
        solve_qaoa(problem, request(problem).model_copy(update={"closedEdgeIds": ("unknown",)}))
    # Omitted options and explicitly default options represent the same run.
    assert result.runHash == solve_qaoa(problem, request(problem, shots=2)).runHash
    implicit = request(problem).model_copy(update={"qaoa": None})
    assert solve_qaoa(problem, implicit).runHash == solve_qaoa(problem, request(problem)).runHash


def test_parameter_binding_matches_direct_circuit_and_scaled_search_is_bounded():
    problem = fixture()
    g, b = ParameterVector('g', 2), ParameterVector('b', 2)
    template = build_qaoa_circuit(problem, g, b)
    binding = {g[0]: 7.3, g[1]: -4.2, b[0]: .8, b[1]: -.6}
    actual = Statevector.from_instruction(template.assign_parameters(binding))
    expected = Statevector.from_instruction(build_qaoa_circuit(problem, [7.3, -4.2], [.8, -.6]))
    assert actual.equiv(expected)
    result = solve_qaoa(problem, request(problem, phaseScale=6, maxEvaluations=9, starts=3, shots=16))
    assert result.diagnostics['evaluations'] <= 9
    assert all(abs(x) <= 6 * np.pi for x in result.diagnostics['gammas'])
    assert result.diagnostics['parameterizedCircuitReuse']
    assert result.runHash != solve_qaoa(problem, request(problem, maxEvaluations=9, starts=3, shots=16)).runHash


def test_greedy_warm_start_is_feasible_coherent_and_disclosed():
    problem = fixture()
    state = Statevector.from_instruction(build_preparation(problem, initial_hub_ids=('h00', 'h03')))
    assert sum(p for i, p in enumerate(state.probabilities()) if i.bit_count() != 2) < 1e-12
    assert np.count_nonzero(state.probabilities() > 1e-10) > 1
    with pytest.raises(ValueError, match='feasible'):
        build_preparation(problem, initial_hub_ids=('h00',))
    result = solve_qaoa(problem, request(problem, warmStartGreedy=True, maxEvaluations=3, shots=16))
    assert result.diagnostics['warmStart']['method'] == 'greedy'
    assert result.provenance.parameters['warmStartGreedy'] is True


@pytest.mark.parametrize('n,k', [(1, 1), (3, 1), (5, 2), (6, 4)])
def test_random_weighted_neighborhood_phases_and_compilation(n, k):
    from qiskit import transpile
    from backend.solvers.qaoa import COMPILATION_BASIS
    rng = np.random.default_rng(900 + n)
    rows = tuple(tuple(bool(x) for x in row) for row in rng.integers(0, 2, size=(7, n)))
    weights = tuple(float(x) for x in rng.uniform(.1, 19, size=7))
    problem = PreparedProblem(scenarioRevision='random-fixture', problemHash='random-fixture',
        hubIds=tuple(f'h{i}' for i in range(n)), communityIds=tuple(f'c{i}' for i in range(7)),
        hubCount=k, responseTimeMinutes=2, coverageMatrix=rows, demandWeights=weights, populations=weights,
        travelMinutes=tuple(tuple(1. if x else None for x in row) for row in rows))
    gamma = 4.7
    unitary = Operator(build_cost_circuit(problem, gamma)).data
    for index in range(2**n):
        ids = [hub for j, hub in enumerate(problem.hubIds) if index & (1 << j)]
        score = evaluate_plan(problem, ids)['weightedCoverage']
        assert np.allclose(unitary[index, index] / unitary[0, 0], np.exp(1j * gamma * score / sum(weights)))
    circuit = build_qaoa_circuit(problem, [gamma, -.8], [.3, -.9])
    compiled = transpile(circuit, basis_gates=COMPILATION_BASIS, optimization_level=1, seed_transpiler=18)
    assert Statevector.from_instruction(compiled).equiv(Statevector.from_instruction(circuit))
