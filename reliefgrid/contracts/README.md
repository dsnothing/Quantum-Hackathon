# ReliefGrid contract v1

Canonical models are in `backend/domain.py`. Regenerate using
`reliefgrid/.venv/Scripts/python.exe -m reliefgrid.contracts.generate` from the
repository root. Names are camelCase in Python and JSON. Sequences are tuples
internally, JSON arrays on the wire. Models prohibit extra fields, nonfinite
numbers, unsupported schema versions, and assignment to model fields.

The graph boundary is `prepare_problem(scenario, request) -> PreparedProblem`.
The independent scorer is `evaluate_plan(problem, selectedHubIds) -> dict` of
`feasible`, `deployedHubCount`, `coveredPopulation`, `totalPopulation`,
`weightedCoverage`, `uncoveredCommunityIds`, and `assignments`.
Solvers receive `(problem, request)` and return `PlanResult`.

IDs in prepared problems are sorted. Each candidate hub maps to one qubit:
qubit j = hubIds[j]. Qiskit printed strings are most-significant-bit first.
For hubs `[a,b,c,d]`, printed `0011` selects `[a,b]`. Counts retain their raw
Qiskit strings, with this ordering documented in diagnostics.

Scenario revision is SHA256 of validated scenario JSON, sorted keys, compact
separators, UTF-8, no omitted values except optional nulls. Problem hashes cover
model version, scenario revision, sorted unique closure IDs, canonical hub and
community ordering, population/weights, k, threshold, coverage and travel times.
Run hashes add solver, seed and QAOA settings (including defaults when supplied).
Hashes are lowercase hex. Solver and seed never affect the problem hash.

Unreachable travel times and unassigned communities are null; Infinity is
prohibited. Covered assignments are to the nearest within-threshold selected
hub, with stable hub-ID ties. Exactly k distinct known hubs is feasible.

Server caps: n <= 12 for statevector QAOA, density-matrix experiments n <= 8;
QAOA layers <= 3, shots <= 8192, starts <= 4, maxEvaluations <= 300 per start.
Exact combinations <= 100000. Worker queue <= 4 pending jobs; one active
process; wall timeout 60 seconds. A 30-second demo target is not a guarantee.
Timing is milliseconds: preprocessing, construction, optimization, sampling,
and total wall time. Defaults are deliberately modest (p=1, shots=512,
40 evaluations, one start). Runtime integration must enforce these caps.
