# ReliefGrid verification record

Record date: November 6, 2026. This record describes the local `codex/reliefgrid` checkout; nothing from this session was committed or pushed.

## Official project requirements

The [Waterloo Qiskit Fall Fest page](https://uwquantum.com/qiskit-fall-fest) says the goal is a Python notebook implementing a tool or abstraction that bridges quantum computing with a non-quantum field. It calls for a project notebook and explanatory slides. Judges may use a simulator; hardware use is optional. The public page does not publish a weighted judging rubric or an individual presentation duration. The event and signup pages list conflicting Friday schedule windows, so the deck avoids schedule claims.

The six-slide deck uses PresentationGO's [Natural Intelligence template](https://www.presentationgo.com/presentation/natural-intelligence-powerpoint-template/), which combines teal network imagery with leaf details. Visible attribution is retained as the template requires.

## Standalone notebook and measured evidence

- `output/ReliefGrid_Submission.ipynb` is 315,589 bytes. All 12 code cells have execution counts, there are no error outputs, and metadata records a fresh Python 3.12.12 kernel, a temporary working directory outside the repository, `PYTHONPATH` removed, and no repository source imports.
- The notebook embeds only the Riverbend and Upland synthetic scenarios and readable shared implementation source. Its evidence JSON matches `reliefgrid/benchmarks/notebook-evidence.json`; notebook tests verify the embedded scenario IDs and revisions against the backend loader.
- At `k=3`, `T=12` minutes, nominal exact, greedy and seeded-random best coverage is 9,060 synthetic population. The primary QAOA run (`p=1`, seed 42) sampled 8,680, 380 below exact; expected weighted coverage was 6,579.5525. The current executed notebook recorded 993.33 ms solver time for this run.
- With the main bridge closed, exact, greedy and seeded-random best coverage is 8,140. The primary QAOA run sampled 8,140 with expected weighted coverage 6,497.8649 and recorded 546.44 ms solver time.
- Eight QAOA comparisons used `p=1/2`, seeds 42/7, up to 24 objective evaluations and 256 final shots. Every run was feasible. Nominal QAOA gaps to exact were 380, 0, 0 and 560; all bridge-closed gaps were zero. Seeded random best-sampled plans matched exact in all eight comparisons. Largest QAOA benchmark time was 1,445.10 ms on this machine.
- Tiny coherence ablations gave expected scores 6.06643 (coherent), 5.74005 (gamma zero) and 5.40935 (dephased), with total-variation differences 0.159372 and 0.158618. Held-out fixed deployments lost up to 540 population relative to their corresponding nominal deployment; the largest gap to the closure-specific optimum was 720. These held-out closures were not optimized against.
- Runtime versions were Qiskit 2.6.2, NumPy 2.5.4, SciPy 1.18.1, Pydantic 2.14.3 and NetworkX 3.7. Timings are local observations, not performance guarantees.

## Backend and interactive workbench

- The current full suite passed **66 tests in 15.63 seconds** from `reliefgrid` using the dedicated Python 3.12.12 environment. It covers graph directionality and closure paths, independent scoring, classical solvers, QAOA construction/ablations, notebook structure and source/evidence consistency, API validation, and real Windows process-spawn runs.
- Queued and terminal run hashes now remain consistent for classical and QAOA jobs, including omitted/default QAOA options. A real exact run over 13 candidate hubs completed; the same instance remains available for preview while QAOA returns the explicit 12-qubit limit error.
- Fixed-plan stress tests use the scenario's named frozen variations. They report the all-roads-open baseline as nominal and retain the current input closure as a separate row; this is evaluation of a fixed deployment, not robust optimization.
- The workbench exports the selected displayed result. Editing inputs clears completed stress results and suppresses late responses. TypeScript and production builds passed; a focused Chromium test with controlled API responses exercised switching between greedy/exact runs, export selection, and stale stress-response suppression. That harness used API fixtures and does not replace the separate Flask process tests.
- The earlier live desktop check exercised greedy coverage of 9,060, closed the main bridge, reran at 8,140, observed Civic Hall added and Ridge Station removed, and inspected a 4.5-minute Bridgeview-to-Civic-Hall path. The initial 1440x900 CSS viewport showed no horizontal overflow.
- The final Windows frontend build used Node 24.21.0 and pnpm 11.25.0. TypeScript passed and Vite built the current 1,588-module frontend; Vite reported its existing chunk-size warning above 500 KB.
- The integration review identified a remaining storage failure-path risk: if persistence fails during dispatch, jobs may be stranded or the worker thread may stop while health still reports ready. Healthy-storage lifecycle tests pass; persistence-failure recovery was not changed or verified.

## Presentation and submission archive

- `output/ReliefGrid_Presentation.pptx` is an editable six-slide deck with visible PresentationGO credit, cited speaker notes, and a QAOA diagram covering coherent fixed-`k` initialization, direct coverage-neighborhood cost phases, and the ordered XY mixer. It labels the scenarios synthetic and results as ideal-simulator evidence, with no hardware, quantum-advantage or operational-use claim.
- The finalizer reported six slides, package integrity pass, zero layout findings and successful Artifact Tool import. All six final slides were rendered and visually inspected; the section-header zero-width placeholders from the first draft were removed.
- `output/ReliefGrid_Submission.zip` contains 70 checksummed payload files plus `SHA256SUMS.json`, including the standalone notebook, six-slide deck, app source and built frontend. ZIP CRC and all 70 manifest hashes pass. A fresh extraction's frozen frontend install/build reproduced all three compiled assets byte-for-byte. On Windows, extract to a short path before running the build; a deeply nested path caused an esbuild executable path error.

## Interpretation limits

Both scenarios and populations are synthetic. Quantum results are simulator measurements; they establish no speedup or quantum advantage. The hub model does not include capacity, inventory, live data or dispatch. The local Flask service is a demonstration workbench, not a production emergency-planning system.
