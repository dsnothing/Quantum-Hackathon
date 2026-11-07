# ReliefGrid optimization and Qiskit review

Review date: November 7, 2026.

Quality parity with the classical optimum is achievable on the tested small synthetic problems. A feasible greedy warm start found an optimal sampled deployment in all eight runs. No method can exceed the exact optimum under the same objective and constraints. This does not establish a quantum runtime advantage. Classical enumeration remained hundreds of times faster on these eight-hub instances. Demonstrating a genuine advantage on larger, realistic instances would be a substantial research problem; this review neither demonstrates one nor proves it impossible.

## Inputs and presentation

Yichen Xiao's November 6 email, “ReliefGrid update and local demo,” linked branch `codex/reliefgrid`, commit `86d1f159`. It contained no attachments. The linked notebook, six-slide PowerPoint, source and submission package were retrieved, inspected, and incorporated by fast-forwarding the clean local checkout. New review changes have not been pushed.

The improved six-slide deck separates text from the detailed teal background, enlarges technical copy, uses native editable comparison tables, corrects travel direction to **hub to community**, and cites the actual experiments in speaker notes. Original template artwork and attribution remain. The original deck is preserved. The installed `slide-readability` skill includes a read-only XML triage helper and a visual review workflow; XML checks cannot establish visual readability or native PowerPoint behavior.

## Controlled comparison

Both scenarios use eight candidate hubs, exactly three selected hubs, a 12-minute threshold, nominal and bridge-closed roads, and seeds 42 and 7. Thus there are four distinct planning instances and eight seeded runs. All matching-budget experiments use p=1, 24 expectation evaluations, 256 final samples, one optimizer start and phaseScale=1. Warm-start selection uses greedy only, without the exact optimum. Exact enumeration audits results independently after training. Each plan uses the same independent coverage scorer.

| Method | Optimal sampled/recommended plans | Observed total solver time |
|---|---:|---:|
| Exact enumeration | 8/8 | 1.1–2.2 ms |
| Uniform feasible random search | 8/8 | 2.6–6.9 ms |
| QAOA, arbitrary first-k initialization | 7/8 | 476.6–1,616.7 ms |
| QAOA, greedy initialization | 8/8 | 632.8–1,700.3 ms |

Timings come from `optimization-cached.json` and `optimization-warm-matched.json`. They include each solver's reported total time. QAOA includes ideal training, final sampling, transpilation and exact audit, rather than physical QPU time. These are local single measurements, not a controlled timing study. Runtime overlap and machine load prevent attributing timing differences to a single implementation change.

For nominal Riverbend, seed 42, best sampled coverage improved from **8,680 to 9,060**, closing the observed 380-person gap. Expected coverage improved from **6,579.55 to 8,590.22**. These are distinct metrics. Across all eight runs, the warm start improved expected coverage. On Upland it also improved best sampled coverage over greedy itself (8,360 versus 7,800 nominal and 7,410 with the bridge closed), although uniform random and exact search already reached 8,360.

This is an in-sample development comparison on synthetic fixtures. Selecting this initialization after comparing alternatives does not establish out-of-sample superiority. Two seeds are insufficient to estimate failure rates confidently. For example, a warm-start Upland nominal circuit has only about 1.81% probability of an optimum on a single shot, despite finding one in these 256-shot trials. Finite sampling never gives a universal optimum guarantee.

## Implemented changes and rejected setting

- `warmStartGreedy=True` in `QaoaOptions` initializes the excited qubits from deterministic greedy before the same two coherent XY sweeps. Default remains false to preserve the original experiment and API behavior. The notebook runs both initializations. This discrete feasible warm start is inspired by classical initialization of QAOA; it is not the continuous-relaxation state and modified mixer in IBM's tutorial.
- A parameterized circuit template is constructed once per solve and bound during optimization. Gate structure still derives from coverage neighborhoods. No enumerated objective diagonal supplies the cost circuit.
- `phaseScale` optionally widens the gamma bounds from ±pi to ±pi times that scale; default remains 1. The scale-6, 120-evaluation, three-start experiment found only **6/8** optimal sampled plans and took roughly 2.5–5.1 seconds. It is retained as a disclosed failed experiment, not adopted as a recommended setting.
- `solve_portfolio(problem, request, ensure_exact=False)` retains the higher coverage of raw QAOA and greedy. `ensure_exact=True` uses bounded exact enumeration instead. Results preserve the winning solver, raw quantum result, guard and total portfolio time. The guard supplies its guarantee classically. An exact guard raises if its explicit combination cap is exceeded.

To reproduce the matched warm-start experiment from the repository root:

```powershell
reliefgrid/.venv/Scripts/python.exe -m reliefgrid.benchmark_optimization --label warm-matched --warm-start
reliefgrid/.venv/Scripts/python.exe -m reliefgrid.benchmark_optimization --label cached
```

The optional web interface continues to use its existing first-k QAOA request. Use the notebook, Python interface, or explicit API options for the warm-start variant. The portfolio is a Python/notebook helper rather than a new web solver type.

## Qiskit audit

The implementation is thorough for its stated **ideal local simulation** scope:

- Coverage phases match independently calculated energies, including sign and global phase, for every basis state of the analytical fixture and additional seeded weighted fixtures up to six qubits.
- Qiskit little-endian bits map back to the correct hub IDs. XY gate-angle conventions, duplicate-neighborhood aggregation, fixed-k feasibility, p=1 and p=3 evolution, disconnected coverage and zero-demand/trivial cases have checks.
- Symbolic parameter binding matches direct circuit construction. Transpilation to rz/sx/x/cx preserves statevectors in independent small fixtures.
- Optimizer restarts respect a total expectation-evaluation cap. Sampling has an independent seed, reproducible counts, shared rescoring and probability/feasibility diagnostics.
- Coherent, gamma-zero and dephased controls distinguish the interference mechanism. Warm-start preparation also remains coherent and in the fixed-k subspace. Ablation functions accept the same optional initial hub IDs.
- Exact post-training audits provide optimum probabilities and approximation ratios. They do not feed circuit phases or optimizer angles. The explicitly separate portfolio may use its classical guard for recommendation.

Important remaining boundaries: optimization reads full statevector probabilities; finite shots are NumPy multinomial samples from Qiskit probabilities, not a Qiskit Runtime Sampler job. There is no QPU execution, target-specific coupling-map routing, noise/readout model, error mitigation, hardware queue cost, or finite-shot/noisy objective training. Generic compiled gate counts are not hardware resource estimates. Statevector and density-matrix caps remain 12 and eight hubs. Depth/shot results do not establish scaling.

## Research sources

- [IBM warm-start QAOA tutorial](https://quantum.cloud.ibm.com/docs/en/tutorials/warm-start-qaoa): classical initialization can improve quantum optimization; its continuous-relaxation method differs from this fixed-k initialization.
- [Qiskit XXPlusYYGate source](https://github.com/Qiskit/qiskit/blob/main/qiskit/circuit/library/standard_gates/xx_plus_yy.py): exchange-gate convention checked against the implementation and analytical tests.
- [IBM introduction to transpilation](https://quantum.cloud.ibm.com/docs/en/guides/transpile): hardware targets add layout and routing considerations absent from the generic compilation audit.
- [OpenAI presentation skills source](https://github.com/openai/plugins/blob/main/plugins/google-drive/skills/google-slides/SKILL.md): reviewed alongside the installed Presentations skill; reused the available authoring/validation workflow instead of installing a competing slide engine.

See `VERIFICATION.md` for completed execution and regression checks. Benchmark JSON files retain individual runs, distributions, angles, convergence and resource counts, including worse outcomes.
