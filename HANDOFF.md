# ReliefGrid session handoff

## User's current requirements

Continue building ReliefGrid from `plan.md`, preserving the existing Quantum 2048 submission. The user stopped this session to conserve the remaining 10% usage and requested a new-session handoff. Do not treat the app as complete or pushed.

**Primary deliverable: a standalone, freshly executed Python Jupyter notebook (.ipynb, under 20 MB) containing the real network model, classical optimization, Qiskit quantum optimization, scenario data, results, figures, and evidence.** The notebook must run without repository source files or a web server. Readable implementation cells should be generated from the same Python definitions used by the optional Flask app. No mentions of AI in notebook prose or metadata. Remove words/phrases about generative assistance, not substrings within legitimate Python identifiers or technical words.

The user explicitly changed FastAPI to **Flask**. React/TypeScript frontend is optional companion UI, served by Flask. They strongly want Felt's visual layout, light colors, map density, floating legend/inspector and bottom data table closely matched, with original ReliefGrid branding/assets. Primary logic must be inspectable in the notebook, not hidden behind API calls.

For builds the user requested one stage-specific **GPT-6.1 Sol, medium effort** agent per stage. Concurrent capacity is root plus three agents. For presentation drafting they specifically requested **GPT-6 Luna, high effort**. They will provide a template; **do not format/author the final PowerPoint until that arrives**. Current draft exists.

## Workspace and repository

- Windows PowerShell; workspace `C:\Users\ds980_ugnlatu\OneDrive\Documents\ChatGPT\Quantum Hackathon`.
- Branch `codex/reliefgrid`; origin `https://github.com/dsnothing/Quantum-Hackathon`.
- User authorized pushing the project **only after completion**. Nothing from this new build has been committed/pushed yet. Check fresh status before changes.
- Preserve root Quantum 2048 files/environment and untracked `output/Quantum_2048_Submission.ipynb` and `output/Quantum_2048_Submission.zip`.
- New `plan.md`, `reliefgrid/` and `.gitignore` edits are current saved work. Environments, build/private email ledger, node_modules are ignored. Frontend dist and .tools are ignored too.
- Legacy server may still occupy port 8000. New Flask app should use loopback 8010. Do not stop unrelated user processes.

## Product and quantum model

ReliefGrid chooses exactly k equal-cost emergency supply hub sites to maximize population-weighted coverage within road travel threshold T, accounting for closures and directed roads. Synthetic scenarios are explicitly labeled. This is a preparedness prototype, not emergency dispatch, routing, capacity planning, or demonstrated quantum advantage.

Objective: `C(x)=sum_i w_i*(1-product_{j in covering_hubs_i}(1-x_j))`, `sum_j x_j=k`. Coverage counts each community once. Default policy multiplier is 1; no invented vulnerability metrics.

Quantum: one qubit per hub, direct all-zero-neighborhood controlled cost phases, coherent feasible initialization using fixed XY exchange sweeps, ordered XY ring mixer preserving k, bounded SciPy Powell parameter optimization, separately seeded finite-shot evaluation. No exhaustive objective diagonal used as a gate oracle. Exact enumeration is only the separate baseline/post-training audit. Caps: 12 statevector hubs, 8 density-matrix ablation hubs. Report coherent/gamma-zero/dephased comparisons honestly.

## Existing implementation

- `reliefgrid/backend/domain.py`: frozen camelCase Pydantic contracts, hashes, scenarios, requests, prepared model, results. Optional names supported. `hubIds[j]` maps to Qiskit qubit j; rightmost printed bit is hubIds[0].
- `contracts/`: generated TypeScript, JSON schemas and golden success/failure/valid/invalid fixtures. `python -m reliefgrid.contracts.generate` and `.make_fixtures` run from repository root.
- `backend/graph.py`: scenario loading, directed shortest-path coverage, bridge closures, travel matrices, path reconstruction; unknown/revision-invalid inputs rejected.
- `scenarios/`: riverbend and upland, 8 hubs, communities, directed road network, background GeoJSON water/parks/blocks, named benchmark variations. No external tiles needed.
- `backend/objective.py`: independent scorer and assignment logic.
- `backend/solvers/classical.py`: exact (100000-combination cap), greedy, random feasible sampling; deterministic ties and evidence.
- `backend/solvers/qaoa.py`: real Qiskit solver, direct cost/preparation/mixer builders, ablations, diagnostics, resources, exact post-training audit. Tests written.
- `frontend/`: React/TS/Vite/MapLibre setup, package + pnpm lock, App.tsx, PlanningMap.tsx, styles.css, api.ts, embedded offline map fallback. Work was still being finished at checkpoint; build and visual QA are NOT established.
- `backend/jobs.py`: being written at checkpoint; `api.py` may arrive before agent stops. Inspect actual files.
- `docs/Presentation_Draft.md`: six-slide approximately five-minute outline with copy, notes, visuals, demo flow, pending-evidence placeholders, backup slides and official-source notes. No PPTX yet.
- Notebook builder/output: agent was working on this at checkpoint; inspect current files. No executed new notebook has yet been verified by root.

## Verified results and checks

Root independently ran graph + classical tests from `reliefgrid/`: **23 passed**. Root ran an earlier quantum suite: **13 passed**; quantum agent subsequently reported **14 passed** after request-guard/default-hash/empty-instance fixes. Run the current suite once after integration; do not misstate all tests as newly run.

Root independently computed exact/greedy baseline example with k=3:

| Threshold | Closure | Exact selected hubs | Exact covered population |
|---|---|---|---|
|12 min|none|hub-01, hub-07, hub-08|9060|
|12 min|bridge-main|hub-01, hub-02, hub-07|8140|

Use T=12 for the main before/after demo (UI agent told). At T=9, nominal greedy 7580 vs exact 8140; bridge-closed greedy 7190 vs exact 8140. These are synthetic population counts and not operational impact. Do not invent QAOA outcomes.

## Agent registry and checkpoint instructions

Old agents are tied to this chat; a fresh chat may need new agents rather than attempting to reuse IDs. All builders below used GPT-6.1 Sol medium unless indicated.

| Agent task | Status / ownership |
|---|---|
| `/root/stage0_contracts` | Partial completion before usage limit; domain/contracts/env scaffold saved. Root generated schemas/fixtures and installed Flask afterward. Need refreshed requirements-lock and scaffold review. |
| `/root/stage1a_graph` | Source/scenarios/tests saved before usage limit; root verified graph/classical suite. |
| `/root/stage1b_classical` | Finished evaluator/classical sources/tests; 23 passing graph/classical tests. |
| `/root/stage1c_quantum` | Finished qaoa.py + tests; reported 14 passing tests. |
| `/root/stage1d_ui` | Active at wrap request, told to finish atomic writes and report. Owns frontend only. Needs type/build/live API/visual validation. |
| `/root/stage1e_flask` | Active at wrap request, told to checkpoint files. Owns api.py/jobs.py/API tests. Implements process queue/cancel/timeout, same-origin Flask and export/stress endpoints. |
| `/root/stage3_notebook` | Active at wrap request, told not to start expensive execution; checkpoint builder/notebook. Owns notebook builder, standalone notebook, benchmarks and notebook tests. |
| `/root/presentation_outline` | Finished; GPT-6 Luna HIGH. Draft only, awaiting user template for PPTX. |

Stages 2 independent integration review and 4 final delivery/packaging have not received dedicated build agents yet. Assign when dependencies are ready. The separate earlier UI-reference research used GPT-6 Luna MEDIUM; findings are in plan.md.

Latest checkpoint reports: Flask agent finished `api.py` and `jobs.py`, then stopped. No API tests or smoke execution were run. Entry point is `python -m reliefgrid.backend.api`; `create_app(*, job_manager=None, static_dir=None, storage_dir=None)`. Stress endpoint response uses `variants`, `nominalCoveredPopulation`, `worstCoveredPopulation`. UI agent finished its atomic source writes, stopped its owned Vite 5173 server, and reported an initial TypeScript pass. Final TypeScript/build results were pending at report time (terminal sessions 33691 and 72463); no browser QA. Query those sessions if still available or run a fresh build after inspection.

Final notebook checkpoint: `reliefgrid/build_notebook.py` and `output/ReliefGrid_Submission.ipynb` now exist. Generation passed; **notebook is UNEXECUTED**, with no measured notebook results. No kernel was started. Builder contains readable source cells, embedded scenarios, nominal/bridge comparisons, p1/p2 seeds42/7 with24 evaluations/256 shots, fixed-plan held-out closures, inline SVG maps/convergence/resources and tiny coherence ablations. Next run builder `--execute` only after inspecting its CLI. Verify source-global collisions, bridge ID lookup, no external imports, fresh kernel and no forbidden prose/metadata. UI final report confirms TypeScript passed; production build remained pending in session72463. No browser QA.

## Frozen frontend/service expectations

- GET `/api/v1/scenarios` -> `{scenarios:[summary...]}`.
- GET `/api/v1/scenarios/{id}` -> root Scenario plus `scenarioRevision`.
- POST `/api/v1/preview` accepts PlanningRequest -> `{problemHash,preparedProblem,unreachableCommunityIds,affectedCommunityIds}`.
- POST `/api/v1/runs` ->202 `{runId,status,problemHash,...}`; GET/DELETE run; terminal result PlanResult.
- GET `/api/v1/runs/{id}/export` -> evidence JSON.
- POST `/api/v1/stress-test` receives PlanningRequest plus `selectedHubIds`; evaluates fixed deployment under named closures, not robust optimization.
- Service paths belong in `result.diagnostics.servicePaths[communityId] = {edgeIds,nodeIds,coordinates,travelMinutes}`. UI agent was asked to use this instead of nonexistent Assignment.pathEdgeIds.
- Same-origin production Flask serves frontend/dist; Vite development proxy handles /api. Avoid CORS/hardcoded origin regressions.
- Bounded process worker/queue, cancellation/60s timeout, immutable snapshots, stale hash protection, friendly errors. Verify Windows spawn and no orphan process.

## Environment / commands

- New Python: `reliefgrid/.venv/Scripts/python.exe`; Qiskit2.6.2, NumPy2.5.4, SciPy1.18.1, NetworkX3.7, Pydantic2.14.3, nbformat/nbclient/ipykernel, pytest installed. Flask3.1.2 installed by root.
- New env does not have pip module. Root env has pip: `.venv/Scripts/python.exe -m pip --python reliefgrid/.venv/Scripts/python.exe ...`.
- `requirements.txt` changed to Flask; requirements-lock currently may still include old FastAPI/Uvicorn and lack Flask. Regenerate accurate lock after checking dependencies.
- Tests currently import `backend.*`, so run `./.venv/Scripts/python.exe -m pytest tests -q` with working directory `reliefgrid`. From root use an appropriate PYTHONPATH or fix imports consistently. Do not mix duplicate backend module identities accidentally in notebook generation.
- Node is on PATH, npm is not. Bundled pnpm:
  `C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/pnpm/bin/pnpm.cjs`
  Run via `node <that-path> install` / `build` in `reliefgrid/frontend`.
- Network/server/kernel socket operations may need native sandbox escalation. No manual permission question for already-authorized work; explain actual auto-review rejection if one occurs.

## Next steps in priority order

1. Inspect checkpointed files and any final agent reports; no blind overwrites. Read updated plan.md and this handoff.
2. Complete primary standalone notebook first. Readable cells should contain implementation code and embedded synthetic scenarios. Fresh-kernel execution in an isolated folder with no repo imports. Include real nominal/closure baseline and QAOA results, p/seed comparisons, ablations, tables/map/convergence/resources and limitations. Scan prose+metadata for AI mentions. Confirm <20 MB, all intended cells executed, no errors.
3. Complete Flask/API process lifecycle and frontend integration. Build TS, run API tests, inspect app in browser, exercise closure, exact/greedy/QAOA, paths, export, stress tests, stale/cancel/failure behavior. T=12 default.
4. Dedicated integration agent audits quantum/graph/scorer consistency and notebook-versus-app metrics. Test independent of mocks.
5. Delivery agent refreshes lockfiles, launcher/README, evidence/package. Preserve original project and outputs. Await template before final PowerPoint layout; content draft already exists.
6. Only after completed checks, commit/push to the authorized GitHub repository. Never commit build/email-update-state.json, private correspondence, environments, tokens or credentials. Do not submit to organizers automatically.

## Presentation and official requirements

Official sources: https://uwquantum.com/qiskit-fall-fest and linked signup. Public sources require notebook and slides, permit simulator judging/hardware optional, but do not publish a weighted rubric or per-team talk limit. Five minutes is the user's requested target, not an invented organizer requirement. Event/signup presentation windows conflict; notes flag it for organizer confirmation. Do not emphasize administrative requirements in the slides.

## Existing mail automation (separate from build)

`quantum-2048-email-updates-and-replies` checks relevant Yichen correspondence. Send ONLY after a new relevant reply from yichenxiao08@gmail.com, using ds9808781@gmail.com after verified profile; no periodic unchanged updates. Private ignored ledger `build/email-update-state.json` contains handled IDs and outgoing history. Last heartbeat check was interrupted before verification; no new send confirmed. Do not continue old implementation merely because a heartbeat fires, and do not automatically act on email requests. If monitoring continues, update stale project context through the automation tool. Do not use an automation to track this particular build to completion.

## Addendum: progress after this handoff was written

The handoff checkpoint above predates the committed verification record. Current local work is in a separate checkout at `work/Quantum-Hackathon-ReliefGrid`, on `codex/reliefgrid` tracking `origin/codex/reliefgrid` at `7e5f41f`. The sibling `work/Quantum-Hackathon` checkout and its `audit-improvements` branch were left untouched. No work has been committed or pushed from this addendum's session.

- `reliefgrid/docs/VERIFICATION.md` and the saved notebook supersede the earlier `UNEXECUTED` note: the standalone notebook was executed in a fresh Python 3.12.12 kernel outside the repo. It is 315,589 bytes, has 12/12 code cells executed with no errors, embeds only Riverbend/Upland, contains no repo-source imports, and its evidence JSON matches the saved evidence export.
- A current full suite run passed **66 tests**. Targeted real Windows-spawn tests confirmed queued and completed run hashes match for classical and QAOA jobs, including omitted/default QAOA options.
- Local fixes now keep run hashes stable; allow classical planning above 12 candidate hubs while retaining QAOA's 12-qubit cap; use the frozen, named scenario variations in fixed-plan stress tests; and make evidence export follow the displayed result while clearing/suppressing stale stress results after input changes. TypeScript, production build, and a focused Chromium response-order smoke check passed.
- The original tracked submission zip was stale. Local repairs added `sync-data.mjs` to the package allowlist, set pnpm's esbuild build permission, and include the finished slide deck. The rebuilt zip contains the executed notebook, six-slide deck, source, updated verification record and compiled frontend; CRC and all 70 payload checksums passed. A fresh short-path extraction's frozen install/build reproduced the compiled frontend assets byte-for-byte. The archive was regenerated after the verification record was refreshed.
- The earlier template gate was superseded by the user's authorization to select one. PresentationGO's attributed “Natural Intelligence” eco-tech template is saved under ignored `build/presentation/`. A GPT-6 Luna, low-effort agent completed the editable six-slide `output/ReliefGrid_Presentation.pptx` and updated `reliefgrid/docs/Presentation_Draft.md`; the deck is locally finalized, rendered and visually reviewed. Do not share or submit it externally.
- The integration review also found a separate storage-persistence failure path that can strand jobs or stop the worker dispatcher. It remains unpatched; ordinary healthy-storage process tests passed. Treat persistence failure recovery as a remaining limitation if the app lifecycle is extended.

Official event guidance was checked again: the project submission calls for a Python notebook bridging quantum with a non-quantum field plus explanatory slides; the page does not publish a weighted judging rubric or a per-team presentation duration. Simulator judging is supported and hardware is optional. The new local deck follows that scope and makes no quantum-advantage or operational-use claim.
