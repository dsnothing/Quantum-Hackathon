"""Exact coverage phases and fixed-weight QAOA on an ideal Qiskit simulator.

Hub j is qubit j (the rightmost printed bit is hubIds[0]). No diagonal
objective oracle is constructed. Cost gates depend only on covering hub sets.
"""
from __future__ import annotations

from collections import Counter
from importlib.metadata import version
from itertools import combinations
from math import comb, pi
from time import perf_counter

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import XXPlusYYGate
from qiskit.quantum_info import DensityMatrix, Statevector
from scipy.optimize import minimize

from ..domain import PlanResult, PlanningRequest, PreparedProblem, Provenance, QaoaOptions, Timing, run_hash
from ..objective import evaluate_plan
from .classical import solve_greedy

MAX_QUBITS = 12
MAX_DENSITY_QUBITS = 8
COMPILATION_BASIS = ["rz", "sx", "x", "cx"]


def _validate(problem: PreparedProblem, density: bool = False) -> int:
    n = len(problem.hubIds)
    cap = MAX_DENSITY_QUBITS if density else MAX_QUBITS
    if n > cap:
        raise ValueError(f"QAOA {'density-matrix' if density else 'statevector'} limit is {cap} hubs")
    return n


def coverage_terms(problem: PreparedProblem) -> tuple[tuple[tuple[int, ...], float], ...]:
    """Combine equal neighborhoods without truncating any coverage relation."""
    terms: Counter = Counter()
    for row, weight in zip(problem.coverageMatrix, problem.demandWeights):
        neighbors = tuple(j for j, covered in enumerate(row) if covered)
        if neighbors and weight:
            terms[neighbors] += weight
    return tuple(sorted(terms.items()))


def ring_edges(n: int) -> tuple[tuple[int, int], ...]:
    """Even path edges, odd path edges, then wrap; deduplicated for n <= 2."""
    edges = [(j, j + 1) for parity in (0, 1) for j in range(parity, n - 1, 2)]
    if n > 2:
        edges.append((n - 1, 0))
    return tuple(edges)


def build_preparation(problem: PreparedProblem, *, initial_hub_ids=None) -> QuantumCircuit:
    """A feasible bitstring followed by two coherent XY ring sweeps.

    Sweep angles pi/7 and pi/11 are fixed independently of problem weights,
    optimum and training seed. The default bitstring excites the first k hubs;
    callers may supply a disclosed classical warm start. Both sweeps follow ring_edges ordering.
    """
    n = _validate(problem)
    circuit = QuantumCircuit(n, name="coherent_feasible_preparation")
    if initial_hub_ids is None:
        initial_indices = range(problem.hubCount)
    else:
        if not evaluate_plan(problem, initial_hub_ids)["feasible"]:
            raise ValueError("initial_hub_ids must identify a feasible fixed-k deployment")
        initial_indices = [problem.hubIds.index(hub) for hub in initial_hub_ids]
    for j in initial_indices:
        circuit.x(j)
    for angle in (pi / 7, pi / 11):
        for a, b in ring_edges(n):
            circuit.append(XXPlusYYGate(2 * angle), [a, b])
    return circuit


def build_cost_circuit(problem: PreparedProblem, gamma: float) -> QuantumCircuit:
    """U=exp(-i gamma H_C), up to a basis-independent global phase.

    H_C=-coverage/W. An uncovered neighborhood receives exp(-i gamma w/W).
    Thus U_x / U_0 = exp(+i gamma coverage(x)/W), fixing the sign.
    """
    n = _validate(problem)
    circuit = QuantumCircuit(n, name="coverage_phase")
    total = sum(problem.demandWeights)
    if total == 0:
        return circuit
    for neighbors, weight in coverage_terms(problem):
        for j in neighbors:
            circuit.x(j)
        angle = -gamma * (weight / total)
        if len(neighbors) == 1:
            circuit.p(angle, neighbors[0])
        else:
            circuit.mcp(angle, list(neighbors[:-1]), neighbors[-1])
        for j in neighbors:
            circuit.x(j)
    return circuit


def build_mixer(problem: PreparedProblem, beta: float) -> QuantumCircuit:
    circuit = QuantumCircuit(len(problem.hubIds), name="ordered_XY_ring")
    for a, b in ring_edges(len(problem.hubIds)):
        circuit.append(XXPlusYYGate(2 * beta), [a, b])
    return circuit


def build_qaoa_circuit(problem: PreparedProblem, gammas, betas, *, initial_hub_ids=None) -> QuantumCircuit:
    if len(gammas) != len(betas) or not 1 <= len(gammas) <= 3:
        raise ValueError("provide matching gamma/beta arrays of length 1..3")
    circuit = build_preparation(problem, initial_hub_ids=initial_hub_ids)
    for gamma, beta in zip(gammas, betas):
        circuit.compose(build_cost_circuit(problem, gamma), inplace=True)
        circuit.compose(build_mixer(problem, beta), inplace=True)
    return circuit


def qaoa_probabilities(problem: PreparedProblem, gammas, betas, *, dephase_after_cost=False, initial_hub_ids=None) -> np.ndarray:
    """Complete basis dephasing after every cost, bounded to eight hubs."""
    _validate(problem, density=dephase_after_cost)
    if not dephase_after_cost:
        return Statevector.from_instruction(build_qaoa_circuit(problem, gammas, betas, initial_hub_ids=initial_hub_ids)).probabilities()
    if len(gammas) != len(betas) or not 1 <= len(gammas) <= 3:
        raise ValueError("provide matching gamma/beta arrays of length 1..3")
    state = DensityMatrix(Statevector.from_instruction(build_preparation(problem, initial_hub_ids=initial_hub_ids)))
    for gamma, beta in zip(gammas, betas):
        state = state.evolve(build_cost_circuit(problem, gamma))
        state = DensityMatrix(np.diag(np.diag(state.data)))
        state = state.evolve(build_mixer(problem, beta))
    return state.probabilities()


def expected_coverage(problem: PreparedProblem, probabilities) -> float:
    """Sum neighborhood coverage probabilities; this is not a gate oracle."""
    indices = np.arange(len(probabilities), dtype=np.uint64)
    value = 0.0
    for neighbors, weight in coverage_terms(problem):
        mask = sum(1 << j for j in neighbors)
        value += weight * float(np.sum(np.asarray(probabilities)[(indices & mask) != 0]))
    return value


def bitstring_hubs(problem: PreparedProblem, bitstring: str) -> tuple[str, ...]:
    if len(bitstring) != len(problem.hubIds) or set(bitstring) - {"0", "1"}:
        raise ValueError("bitstring must have exactly one binary digit per hub")
    return tuple(hub for j, hub in enumerate(problem.hubIds) if bitstring[-1 - j] == "1")


def run_ablations(problem: PreparedProblem, gammas, betas, *, initial_hub_ids=None) -> dict:
    """Same angles/preparation/mixer; remove phases or remove coherence."""
    coherent = qaoa_probabilities(problem, gammas, betas, initial_hub_ids=initial_hub_ids)
    zero = qaoa_probabilities(problem, np.zeros(len(gammas)), betas, initial_hub_ids=initial_hub_ids)
    dephased = qaoa_probabilities(problem, gammas, betas, dephase_after_cost=True, initial_hub_ids=initial_hub_ids)
    return {
        "gammas": list(gammas), "betas": list(betas),
        "coherent": {"expectedWeightedCoverage": expected_coverage(problem, coherent), "probabilities": coherent.tolist()},
        "gammaZero": {"expectedWeightedCoverage": expected_coverage(problem, zero), "probabilities": zero.tolist()},
        "dephased": {"expectedWeightedCoverage": expected_coverage(problem, dephased), "probabilities": dephased.tolist()},
        "coherentGammaZeroTotalVariation": float(np.abs(coherent - zero).sum() / 2),
        "coherentDephasedTotalVariation": float(np.abs(coherent - dephased).sum() / 2),
    }


def solve_qaoa(problem: PreparedProblem, request: PlanningRequest) -> PlanResult:
    start = perf_counter()
    n = _validate(problem)
    if (request.hubCount != problem.hubCount or request.scenarioRevision != problem.scenarioRevision
            or request.responseTimeMinutes != problem.responseTimeMinutes
            or tuple(sorted(set(request.closedEdgeIds))) != problem.closedEdgeIds):
        raise ValueError("request does not match prepared problem")
    options = request.qaoa or QaoaOptions()
    request = request.model_copy(update={"solver": "qaoa", "qaoa": options})
    rng = np.random.default_rng(request.seed)
    sample_seed = int(rng.integers(0, 2**32))
    construction_start = perf_counter()
    warm_start = solve_greedy(problem, request) if options.warmStartGreedy else None
    initial_hub_ids = warm_start.selectedHubIds if warm_start else None
    preparation = build_preparation(problem, initial_hub_ids=initial_hub_ids)
    p = options.layers
    gamma_parameters, beta_parameters = ParameterVector("gamma", p), ParameterVector("beta", p)
    template = build_qaoa_circuit(problem, gamma_parameters, beta_parameters, initial_hub_ids=initial_hub_ids)

    def bound_circuit(angles):
        # Reuse the gate structure. Binding never uses an enumerated energy oracle.
        bindings = dict(zip(gamma_parameters, angles[:p]))
        bindings.update(zip(beta_parameters, angles[p:]))
        return template.assign_parameters(bindings)

    convergence, start_records = [], []
    best_value, best_angles = -1.0, np.zeros(2 * p)
    construction_ms = (perf_counter() - construction_start) * 1000
    optimization_start = perf_counter()
    trivial = problem.hubCount in (0, n) or sum(problem.demandWeights) == 0
    # maxEvaluations is a total circuit expectation budget, split across starts.
    starts = min(options.starts, options.maxEvaluations)
    if not trivial:
        for restart in range(starts):
            budget = options.maxEvaluations // starts + (restart < options.maxEvaluations % starts)
            gamma_bound = pi * options.phaseScale
            initial = np.concatenate([rng.uniform(-gamma_bound, gamma_bound, p), rng.uniform(-pi / 2, pi / 2, p)])
            used = 0

            def loss(angles):
                nonlocal used, best_value, best_angles
                used += 1
                probabilities = Statevector.from_instruction(bound_circuit(angles)).probabilities()
                value = expected_coverage(problem, probabilities)
                if value > best_value:
                    best_value, best_angles = value, np.array(angles)
                convergence.append({"evaluation": len(convergence) + 1, "start": restart,
                                    "expectedWeightedCoverage": value, "bestExpectedWeightedCoverage": best_value})
                return -value / sum(problem.demandWeights)

            fit = minimize(loss, initial, method="Powell", bounds=[(-gamma_bound, gamma_bound)] * p + [(-pi / 2, pi / 2)] * p,
                           options={"maxfev": int(budget), "xtol": 0.01, "ftol": 0.0001})
            start_records.append({"start": restart, "initialAngles": initial.tolist(), "evaluations": used,
                                  "success": bool(fit.success), "message": str(fit.message)})
    optimization_ms = (perf_counter() - optimization_start) * 1000
    sampling_start = perf_counter()
    if trivial:
        # Explicit deterministic bypass, including the W=0 convention.
        probabilities = np.zeros(2**n)
        probabilities[(1 << problem.hubCount) - 1] = 1
        circuit = QuantumCircuit(n)
        for j in range(problem.hubCount):
            circuit.x(j)
    else:
        circuit = bound_circuit(best_angles)
        probabilities = Statevector.from_instruction(circuit).probabilities()
    probabilities = np.maximum(probabilities, 0)
    probabilities /= probabilities.sum()
    raw = np.random.default_rng(sample_seed).multinomial(options.shots, probabilities)
    counts = {format(i, f"0{n}b") if n else "": int(count) for i, count in enumerate(raw) if count}
    scored = [(bits, count, evaluate_plan(problem, bitstring_hubs(problem, bits))) for bits, count in counts.items()]
    valid = [item for item in scored if item[2]["feasible"]]
    if not valid:
        raise RuntimeError("ideal feasible circuit produced no feasible samples")
    selected = min(valid, key=lambda item: (-item[2]["weightedCoverage"], item[2]["selectedHubIds"]))[2]
    sampling_ms = (perf_counter() - sampling_start) * 1000
    # Independent post-training classical audit, never used to choose angles.
    audit_start = perf_counter()
    optimal_value, optimal_sets = None, []
    if comb(n, problem.hubCount) <= 5000:
        for hubs in combinations(problem.hubIds, problem.hubCount):
            score = evaluate_plan(problem, hubs)["weightedCoverage"]
            if optimal_value is None or score > optimal_value:
                optimal_value, optimal_sets = score, [hubs]
            elif score == optimal_value:
                optimal_sets.append(hubs)
    optimum_indices = [sum(1 << problem.hubIds.index(hub) for hub in hubs) for hubs in optimal_sets]
    audit_ms = (perf_counter() - audit_start) * 1000
    compilation_start = perf_counter()
    compiled = transpile(circuit, basis_gates=COMPILATION_BASIS, optimization_level=1, seed_transpiler=request.seed)
    prep_compiled = transpile(circuit if trivial else preparation, basis_gates=COMPILATION_BASIS, optimization_level=1, seed_transpiler=request.seed)
    compilation_ms = (perf_counter() - compilation_start) * 1000
    construction_ms += compilation_ms
    feasible_mask = [i.bit_count() == problem.hubCount for i in range(2**n)]
    diagnostics = {
        "counts": counts, "shots": options.shots, "samplingSeed": sample_seed,
        "bitOrder": "rightmost bit is hubIds[0]; qubit j is hubIds[j]",
        "expectedWeightedCoverage": expected_coverage(problem, probabilities),
        "sampledExpectedWeightedCoverage": sum(count * metrics["weightedCoverage"] for _, count, metrics in scored) / options.shots,
        "feasibleFraction": sum(count for _, count, metrics in scored if metrics["feasible"]) / options.shots,
        "idealFeasibleProbability": float(probabilities[feasible_mask].sum()),
        "infeasibleCounts": {bits: count for bits, count, metrics in scored if not metrics["feasible"]},
        "idealInfeasibleProbability": float(probabilities[np.logical_not(feasible_mask)].sum()),
        "optimalWeightedCoverage": optimal_value, "optimalHubSets": [list(hubs) for hubs in optimal_sets],
        "optimumProbability": float(probabilities[optimum_indices].sum()) if optimal_value is not None else None,
        "sampledOptimumProbability": sum(count for _, count, metrics in scored if metrics["weightedCoverage"] == optimal_value) / options.shots if optimal_value is not None else None,
        "expectedApproximationRatio": expected_coverage(problem, probabilities) / optimal_value if optimal_value else None,
        "evaluations": len(convergence), "convergence": convergence, "starts": start_records,
        "gammas": best_angles[:p].tolist(), "betas": best_angles[p:].tolist(), "trivialBypass": trivial,
        "resources": {"qubits": n, "layers": p, "depth": compiled.depth(),
                      "twoQubitGates": sum(1 for inst in compiled.data if inst.operation.num_qubits == 2),
                      "operationCounts": dict(compiled.count_ops()), "basisGates": COMPILATION_BASIS,
                      "preparationDepth": prep_compiled.depth(), "preparationTwoQubitGates": sum(1 for inst in prep_compiled.data if inst.operation.num_qubits == 2),
                      "uniqueCoverageNeighborhoods": len(coverage_terms(problem)), "compilationOptimizationLevel": 1},
        "preparationRecipe": ("greedy deployment" if warm_start else "first k qubits") + " excited; ordered ring XY sweeps at pi/7 then pi/11",
        "optimizer": "bounded scipy Powell; total maxfev split across starts",
        "gammaBounds": [-pi * options.phaseScale, pi * options.phaseScale],
        "parameterizedCircuitReuse": True,
        "warmStart": {"method": "greedy" if warm_start else "first-k", "hubIds": list(initial_hub_ids or problem.hubIds[:problem.hubCount]),
                      "classicalWeightedCoverage": warm_start.weightedCoverage if warm_start else None},
        "selectionRule": "best feasible finite-shot sample; stable hub-ID ties",
        "audit": "exact feasible enumeration after training; never used by circuit or optimizer",
        "timingBreakdownMs": {"postTrainingExactAudit": audit_ms, "compilation": compilation_ms},
    }
    return PlanResult(solver="qaoa", problemHash=problem.problemHash, runHash=run_hash(problem, request), **selected,
                      timing=Timing(constructionMs=construction_ms, optimizationMs=optimization_ms, samplingMs=sampling_ms,
                                    totalMs=(perf_counter() - start) * 1000),
                      provenance=Provenance(scenarioRevision=problem.scenarioRevision, seed=request.seed,
                          executionMode="ideal-simulator optimization with sampled evaluation",
                          versions={name: version(name) for name in ("qiskit", "numpy", "scipy")},
                          parameters=options.model_dump()), diagnostics=diagnostics)
