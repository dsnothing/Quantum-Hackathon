# ReliefGrid verification record

Record date: November 6, 2026. Only observed checks belong here.

## Primary notebook and evidence

- The notebook owner executed all 12 code cells in a fresh Python 3.12.14 environment kernel, with a temporary working directory outside the repository and `PYTHONPATH` removed. The notebook is 315,043 bytes, below 20 MB. It embeds both synthetic scenarios and readable shared implementation definitions; no app server or repository imports are needed.
- Notebook checks passed (3 tests): valid structure, every cell executed without errors, no forbidden wording, no dynamic source execution/repository imports, source synchronization, and prepared hashes / PlanResult schemas / independently scored metrics matching the backend.
- At k=3 and T=12 minutes, nominal exact/greedy/seeded-random best coverage is 9,060 synthetic population. The primary QAOA p=1 seed=42 run covers 8,680 (380 below optimum), with expected score 6,579.5525 and recorded solver time 1,891.21 ms. Bridge-closed coverage is 8,140 for these methods; primary QAOA expected score is 6,497.8649 and solver time 1,419.52 ms.
- Eight QAOA benchmark runs use p=1/2, seeds 42/7, at most 24 evaluations and 256 final shots. All reported feasible fraction 1; the largest solver time was 3,876.77 ms on this machine. Nominal optimality losses are 380, 0, 0 and 560 respectively; all bridge-closed losses are zero. Seeded random best-sampled losses are zero for all eight comparisons. These small simulator measurements establish no speedup or advantage.
- Tiny coherence ablations give expected scores 6.06643 (coherent), 5.74005 (gamma zero) and 5.40935 (dephased), with nonzero total-variation differences 0.159372 / 0.158618. Held-out fixed-deployment closures lose up to 720 population; the plan is not optimized against those closures.
- Runtime versions: Qiskit 2.6.2, NumPy 2.5.4, SciPy 1.18.1, Pydantic 2.14.3 and NetworkX 3.7. Timings are local observations and exclude dependency installation/browser startup.

## Delivery tooling

- The Python lock is the installed dependency closure of the pinned direct requirements, generated through package metadata on Python 3.12 / Windows. It includes Flask and excludes the abandoned FastAPI/Uvicorn service dependencies. A separate clean internet installation has not yet been performed.
- Packaging uses an explicit source-directory allowlist, rejects unexecuted/error notebooks and missing evidence/frontend builds, emits SHA256 checksums, and checks zip integrity.
- Launcher smoke check passed on loopback port 8018 using the dedicated environment: Flask started in a hidden Windows subprocess, the identity/readiness health endpoint passed, and `/` served the compiled frontend with asset references. A second launch reused the same healthy service. A temporary unrelated HTTP service was rejected without termination. The owned smoke-test ReliefGrid process was stopped after testing. Loopback networking required execution outside the restricted sandbox; an earlier sandbox attempt timed out and was cleaned up by the launcher.
- The standalone notebook is the primary deliverable. The Flask workbench is optional. Final presentation formatting remains pending the user's template; the content draft is not a final PowerPoint.

## Backend and integration

The integration owner ran `./.venv/Scripts/python.exe -m pytest tests -q --basetemp=../build/pytest-integration-complete --tb=short` from `reliefgrid`: **61 passed in 58.32 seconds**. This includes graph/classical/quantum checks and 21 API cases: real Windows process-spawn runs for exact, greedy, random and QAOA; shared scoring, road-closure paths, exports and fixed-plan stress evaluation; malformed/invalid/oversized inputs; bounded queue, cancellation, timeout, process recycling, explicit 13-hub QAOA rejection and restart persistence. The API QAOA smoke uses 2 evaluations and 32 shots, so its timing is not evidence of the default-budget runtime.

## Interactive workbench

The root reviewer exercised the live desktop workflow: greedy nominal coverage 9,060, close the main bridge, observe the stale-result guard, rerun greedy to 8,140, and inspect the change of -920 residents, Civic Hall added / Ridge Station removed. Selecting Bridgeview displayed a 4.5-minute service path to Civic Hall. At a CSS viewport of 1440×900, there was no horizontal overflow; browser zoom was 67% and the physical viewport was 965×603. The first production frontend build passed in 19.73 seconds. Later evidence-panel improvements require the final build record below before packaging.

## Interpretation limits

The scenarios are synthetic. Quantum evidence is simulator evidence, without a speedup or hardware claim. Fixed-plan closure evaluation is not robust optimization. The local Flask server is a demonstration service, not a production deployment.
