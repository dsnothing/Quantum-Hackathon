# ReliefGrid implementation plan

Status: implementation authorized; build and verification in progress. Working name subject to availability review. Prepared for this repository on November 6, 2026.

## 1. Product decision and positioning

Build a disruption-aware emergency supply hub planning workbench. Given a road network, communities, candidate hub sites, a response-time threshold, and a fixed number of deployable hubs, produce a deployment recommendation and explain its consequences. A planner can close a bridge, rerun optimization, and see which communities lose access and why moving a hub restores coverage.

The primary output is a geographically explained deployment plan. Quantum circuits, distributions, and convergence are supporting evidence, not the main experience.

### What already exists

- Esri location-allocation already supports facility selection, travel-time coverage, and capacity objectives: https://doc.arcgis.com/en/arcgis-online/analyze/how-choose-best-facilities-works-mv.htm
- anyLogistix describes humanitarian stockpile positioning, network design, and disaster-response simulation: https://www.anylogistix.com/case-studies/logistics-preparedness-for-disaster-response-in-indonesia/
- The Logistics Cluster provides operational coordination and access information: https://logcluster.org/en/what-we-do/emergency-response
- Quantum emergency hub placement has research precedent, including a neutral-atom minimum-dominating-set approach. That differs from our proposed Qiskit maximum-coverage formulation: https://arxiv.org/abs/2606.19589

Do not claim invention of hub placement, disruption analysis, or quantum facility optimization. The proposed differentiation is their combination with transparent, reproducible decision evidence; market-wide uniqueness has not been established.

### Differentiating features

1. Explain a changed decision using network paths and contribution calculations: which closure broke access, which replacement restores it, and who remains uncovered.
2. Audit QAOA, greedy, exact enumeration, and random feasible sampling against one frozen problem and independent scorer.
3. Expose isolated communities and access tradeoffs alongside aggregate coverage. Policy weights are explicit inputs, not invented vulnerability estimates.
4. Replay a chosen plan under other closures, distinguishing robustness evaluation from robust optimization.
5. Export scenario, assumptions, selected sites, metrics, seeds, circuit resources, and provenance as a reproducible evidence bundle.
6. Run the bundled demonstration without accounts, live tiles, API keys, or external network access after installation.

### Scope and non-goals

MVP is preparedness decision support on explicitly synthetic scenarios, not operational dispatch. No flood prediction, live traffic, patient information, medical triage, vehicle routing, supply inventory, capacities, or aid-delivery guarantees. No claim that QAOA outperforms classical methods unless a specific measured comparison supports it; small-instance results cannot establish quantum computational advantage. No hardware execution claims from a simulator.

## 2. Primary workflow and features

### F1: Understand the scenario

Load a bundled scenario with a bottleneck bridge, overlapping coverage, disconnected locations, and a genuine hub-count tradeoff. Show road directions, travel times, communities, candidate hubs, source/license, and assumptions. Synthetic geography and populations must be labeled prominently, including in exports.

Acceptance: a user can identify the planning question, input units, and data limitations before running a solver. Unreachable communities are visible immediately.

### F2: Change the access network

Close/reopen roads through map selection and an equivalent keyboard-accessible list. Set deployable hub count k and maximum response time T. Preview reachability quickly; optimization runs only on an explicit action. A closure removes graph edges, not just changes their color. Bidirectional closure semantics must be explicit.

Acceptance: a closed road never appears in a service path; directed paths respect one-way roads. Input changes immediately mark previous results stale.

### F3: Recommend and compare deployments

Show selected hubs, covered population, uncovered communities, objective score, and nearest selected hub travel times. Compare greedy and QAOA, with exact optimum available on bounded instances. A comparison must use identical problem hashes, weights, threshold, and closures.

Acceptance: overlapping coverage counts a community once. Show weighted score separately from population served. Exact unavailability is explicit; greedy is never labeled optimal without proof.

### F4: Explain the change

Compare a saved baseline against a new closure state. Display added/removed hubs, gained/lost community access, and before/after service paths. Calculate marginal contribution by reevaluating removal of each selected hub; a replacement explanation must evaluate the proposed replacement, not infer it from a map animation.

Acceptance: every narrative statement has IDs and computed quantities in the result data. “This bridge caused loss of access” requires a controlled comparison with only that closure changed; multiple changes are described as a combined scenario effect.

### F5: Audit quantum computation

Secondary evidence drawer: cost/mixer circuit, convergence, top sampled configurations, feasible mass, exact-optimum probability, seeds, shots, objective evaluations, execution mode, and resource counts. Show selected best sample separately from expected performance.

Acceptance: results come from current circuit execution or a visibly labeled replay. No canned numbers presented as live runs.

### F6: Stress-test and export

Evaluate one fixed deployment under a small named set of closures; report nominal and worst observed coverage. Export JSON evidence and community/hub CSV tables. The primary deliverable is a standalone executed Python notebook containing the complete domain, graph, classical and quantum solver logic, embedded scenario data, and reproducible calculations. Flask serves the optional frontend using the identical exported Python definitions.

Acceptance: UI says “evaluated across these scenarios,” not “robustly optimized,” unless an additional robust objective is implemented and verified.

## 3. Mathematical model and quantum algorithm

### 3.1 Domain model

Let G be a directed graph with positive edge travel times. Remove closed edges, compute shortest travel times from each candidate hub to demand nodes, and define a_ij = 1 if demand i is reachable from hub j within T. Let N_i be the set of covering hubs. There are n candidate hubs and m communities.

Choose x_j in {0,1}, with sum_j x_j = k, maximizing:

```
C(x) = sum_i w_i * (1 - product_{j in N_i}(1 - x_j))
w_i = population_i * priorityMultiplier_i
```

Default multiplier is 1; multipliers are disclosed policy choices. A demand with empty N_i contributes zero. Population and weighted objective are separate metrics. Assign covered communities to the closest selected reachable hub within T, breaking ties by stable hub ID. This assignment is for explanation, not a capacity constraint.

MVP “budget” means exactly k equal-cost deployable hubs, not dollars. For this monotone objective, exactly k has the same optimum coverage as at most k when enough usable candidates exist. Heterogeneous opening costs, capacity, forced-open sites, and inventory require a revised formulation; do not silently add them to this solver.

### 3.2 Cost circuit

Use one qubit per hub, initially 8–12; any larger simulator limit must be measured and configured. With x_j = (I-Z_j)/2 and W = sum_i w_i > 0:

```
H_C = -(1/W) sum_i w_i [I - product_{j in N_i} (I+Z_j)/2]
eigenvalue(H_C, x) = -C(x)/W
```

Ignoring a global phase, implement the cost evolution as all-zero-neighbourhood phases of angle -gamma*w_i/W. Apply X to those neighbourhood qubits, a phase conditioned on all ones, then undo X. Handle singleton neighbourhoods separately and combine identical neighbourhoods by adding their weights. Empty neighbourhoods have no decision-dependent contribution.

Do not build the cost oracle by exhaustively enumerating all 2^n objective values. Enumeration belongs only in separate verification/baseline code. Do not truncate reachable hub neighbourhoods to reduce gate count; report synthesis cost instead.

### 3.3 Feasible mixing and initialization

Prepare a deterministic k-excitation basis state, then apply a published fixed sequence of XY exchanges to create coherent feasible support before the first cost layer. Verify nonzero support on multiple feasible configurations for nontrivial cases.

Each optimization layer applies cost phases followed by ordered even/odd ring XY exchanges:

```
U_ab(beta) = exp[-i beta (X_a X_b + Y_a Y_b)/2]
Qiskit XXPlusYYGate(theta=2*beta, beta=0)
```

Deduplicate ring edges for n=1/2; define ordering for odd n. This ordered product is not exact evolution under the summed ring Hamiltonian. Exchanges conserve hub count. Starting from an unmodified basis state would make the first cost angle a global phase; that is explicitly prohibited as the default p=1 experiment.

Depths p=1,2,3; seeded, bounded SciPy optimization; multiple disclosed starts. Train with exact statevector expectation, then perform a separately seeded finite-shot evaluation. Label this “ideal-simulator optimization with sampled evaluation,” not hardware/noisy training. k=0 and k=n have deterministic solutions and bypass optimization. W=0 produces a defined trivial result with no division.

### 3.4 Baselines and evidence

- Exact enumeration of all choose(n,k) feasible subsets within a configured limit.
- Deterministic marginal-gain greedy, with stable ties and completion to k sites even when gains vanish.
- Uniform random feasible sampling with the same final sample count.
- Optional local search with disclosed computation budget.

All use the same prepared problem and scorer. Never feed an exact optimum into QAOA initialization or tune only on the showcased scenario. Freeze benchmark fixtures and seeds before final evaluation; include held-out closure perturbations and failures.

Report best and expected coverage / exact optimum, optimum probability including all ties, feasible fraction, raw counts, timing breakdown, evaluation count, qubits, preparation cost, transpiled depth and two-qubit gates with compilation basis documented. If optimum is zero, ratios are not applicable. Use repeated seeds and spread, not only the best run. Classical and quantum runtime budgets need disclosure, not a misleading claim of equal resources.

Required ablations: gamma=0 with identical preparation/mixer; complete computational-basis dephasing after each cost layer on small fixtures; p=1 vs p=2/3 with effort disclosed; finite-shot variation. These test whether coherent cost evolution affects output. Improvement is measured, never assumed. Density-matrix experiments have a stricter size cap than statevector experiments. Optional noise results must retain infeasible samples; any repair is labeled separate classical postprocessing.

Quantum references:

- IBM QAOA workflow: https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm
- Alternating Operator Ansatz: https://arxiv.org/abs/1709.03489
- XY mixer research: https://arxiv.org/abs/1904.09314
- Gate convention: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.XXPlusYYGate

## 4. Stack and repository boundaries

Create an independent `reliefgrid/` application. Preserve the existing Quantum 2048 source, environment, notebook, decks, and untracked submission artifacts. Do not repurpose its stateful API or port 8000. New app uses loopback port 8010, configurable and checked before startup.

| Layer | Decision | Reason |
|---|---|---|
| UI | React, TypeScript, Vite, CSS variables | Typed contracts, component ownership, reproducible build |
| Geography | MapLibre GL JS, local GeoJSON, bundled background style | Real map interaction without dependence on external tiles |
| Service | Python 3.12, Flask, Pydantic | Validation, typed API, shared scientific engine |
| Network | NetworkX shortest paths | Explicit directed network reachability |
| Solvers | Qiskit, NumPy, SciPy | Circuit execution and bounded classical optimization |
| Data | Versioned scenario JSON; ignored local run files | No database/account overhead for local MVP |
| Verification | pytest, Vitest, Playwright, fresh Jupyter execution | Model, API, UI and reproducibility checks |

Stage 0 validates and pins compatible versions and commits frontend/Python locks. Existing Qiskit 2.6.2 is a starting compatibility check, not proof that all proposed APIs work together. New application gets its own environment. Install-time network is allowed; ordinary bundled-scenario execution must work offline.

Same-origin production: Flask serves the Vite build. Development: Vite proxies `/api`. Avoid hardcoded browser API origins. One bounded process worker isolates solver CPU work; queue capped, immutable inputs, cancellation/timeout. No cloud credentials needed. Store run artifacts in ignored `build/reliefgrid/`; never include private mail ledgers or correspondence in exports.

```
reliefgrid/
  contracts/                    # schema, generated TS, golden requests/results
  scenarios/                    # scenario JSON, local geometry, provenance
  backend/
    domain.py
    graph.py
    objective.py
    solvers/classical.py
    solvers/qaoa.py
    jobs.py
    api.py
  frontend/src/
    api/ map/ planning/ results/ quantum/
  notebooks/
  tests/
  docs/
```

## 5. Frozen integration contracts

Stage 0 owns canonical Pydantic models and generated JSON Schema/TypeScript. Include valid and invalid golden fixtures. Breaking changes require lead coordination, version bump, regenerated clients, and migration of every fixture before merging.

### Scenario v1

```
schemaVersion, id, title, crs: "EPSG:4326",
provenance: {kind: "synthetic"|"open-data", sources[], license,
             retrievedAt?, transformationNotes},
nodes: [{id, lon, lat}],
edges: [{id, fromNodeId, toNodeId, travelMinutes, bidirectional, geometry?}],
communities: [{id, nodeId, population, priorityMultiplier}],
candidateHubs: [{id, nodeId}]
```

Unique stable IDs; positive times; nonnegative population/multipliers; valid coordinates and references; no silently snapped nodes. A bidirectional edge closes in both directions under its one ID. Reject unsupported schema versions and invalid closures. No opening-cost field implying a supported knapsack model.

### Request and prepared model

```
PlanningRequest: {scenarioId, scenarioRevision, closedEdgeIds[], hubCount,
  responseTimeMinutes, solver: "exact"|"greedy"|"qaoa"|"random",
  seed, qaoa?: {layers, shots, maxEvaluations, starts}}

PreparedProblem: {modelVersion, scenarioRevision, problemHash,
  hubIds[], communityIds[], hubCount, demandWeights[], populations[],
  coverageMatrix[community][hub], travelMinutes[community][hub]}
```

Scenario revision hashes content. Problem hash covers normalized closure set, weights, hub ordering, k, threshold and model version, excluding solver/seed. A separate run hash covers solver parameters and seeds. This lets different solvers be compared on identical problems. Unreachable times serialize as null, never Infinity. Return sorted canonical IDs and define Qiskit bitstring ordering explicitly.

### Result

```
PlanResult: {solver, problemHash, runHash, selectedHubIds[], feasible,
  deployedHubCount, coveredPopulation, totalPopulation, weightedCoverage,
  uncoveredCommunityIds[],
  assignments: [{communityId, hubId|null, travelMinutes|null, covered}],
  timing: {preprocessMs, constructionMs, optimizationMs, samplingMs, totalMs},
  provenance: {scenarioRevision, modelVersion, codeRevision, versions,
               executionMode, seed, parameters},
  diagnostics: {... solver-specific evidence ...}}
```

Shared evaluator recomputes feasibility and all plan metrics independent of solver internals. Unreachable or outside-threshold demand has null assignment; optionally return its nearest outside-threshold travel time in a separately named field. Infeasible results cannot be recommended. Quantum diagnostics retain full small-instance counts and invalid mass; the UI may show only top configurations.

### API v1

- `GET /api/v1/health`: app identity/version and readiness.
- `GET /api/v1/scenarios`; `GET /api/v1/scenarios/{id}`.
- `POST /api/v1/preview`: bounded reachability/model preview; returns problem hash and communities affected.
- `POST /api/v1/runs`: 202 with run ID, status and hashes.
- `GET /api/v1/runs/{runId}`: queued/running/succeeded/failed/cancelled/timed_out plus result/error.
- `DELETE /api/v1/runs/{runId}`: idempotent cancellation request.
- `GET /api/v1/runs/{runId}/export`: reproducible JSON evidence package.

Error envelope: `{error:{code,message,field?,retryable}}`. Cap input size, worker time, queue length, n, layers, shots and evaluations server-side. Persist terminal state atomically; cancellation must terminate/recycle the process rather than merely hide a running computation. Unknown run IDs return 404. Polling is sufficient; do not add SSE initially. Old completed jobs remain viewable as historical results but cannot overwrite current inputs.

## 6. UI/UX direction and reference research

Research performed by a dedicated GPT-6 Luna subagent at medium effort, as requested. References below are primary product documentation/design articles; descriptions reflect documented interface patterns. Proposed adaptations and palette are our design recommendations. These are not claims of hands-on usability testing or pixel-level visual inspection. Builders must inspect current reference screenshots and actual app renders before visual sign-off.

### Reference shortlist and what to adopt

| Reference | Documented pattern | ReliefGrid adaptation |
|---|---|---|
| Felt | Map canvas, interactive layer/legend list, contextual details, searchable attribute table | Persistent map; selected community/hub inspector; layer visibility and map/table cross-highlighting |
| ArcGIS Urban | Named scenarios, baseline duplication, scenario switcher, map editor and dashboard modes | Explicit baseline/candidate selector; scenario descriptions and change history; stable comparison context |
| CARTO Builder | Cross-filtering widgets, map/table interactions, contextual right information panel | Compact metrics strip, searchable unmet-demand table, contextual plan inspector |
| CARTO dual map | Side-by-side maps and parameter-preserving report snapshots | Synchronized before/after comparison with identical camera, legends and run parameters |
| Mapbox Studio | Layer panel, central map, feature inspection, style comparison and color-blindness simulation | Clear layer hierarchy and feature selection; inspect all map symbology under color-vision simulations |
| Linear | Hoverable project graphs and chronological updates | Compact change/evidence timeline; exact values on hover and keyboard focus; restrained secondary chrome |

Direct source pages:

- Felt interface: https://help.felt.com/getting-started/tour-the-interface
- Felt map design rationale: https://felt.com/blog/how-to-design-a-beautiful-map
- Felt mobile panel behavior: https://help.felt.com/field-app/tour-the-field-app
- ArcGIS Urban workspace: https://doc.arcgis.com/en/urban/11.3/help/help-intro.htm
- ArcGIS Urban scenarios: https://doc.arcgis.com/en/urban/11.3/help/help-projects-scenarios.htm
- CARTO widgets: https://docs.carto.com/carto-user-manual/maps/widgets
- CARTO feature interactions: https://docs.carto.com/carto-user-manual/maps/interactions
- CARTO table: https://docs.carto.com/carto-user-manual/maps/widgets/table-widget
- CARTO comparison: https://docs.carto.com/carto-user-manual/maps/map-view-modes
- CARTO report state: https://docs.carto.com/carto-user-manual/maps/download-pdf-reports
- Mapbox Studio interface: https://docs.mapbox.com/console-tools/studio/studio-interface/
- Linear graphs: https://linear.app/docs/project-graph
- Linear update history: https://linear.app/docs/initiative-and-project-updates

Do not copy branding or imply affiliations. These products supply interaction references, not evidence of our product's uniqueness.

### Art direction: calm planning workspace

Use a coherent, utilitarian light workspace. Avoid glowing quantum graphics, purple gradients, large marketing headings, floating glass panels and decorative card grids. Visual sophistication comes from geographic hierarchy, precise alignment, clear type and meaningful transitions.

Proposed initial tokens (verify contrast in implementation, including hover/disabled states):

| Token | Value | Use |
|---|---|---|
| Canvas | `#F5F4F0` | Warm neutral map surround |
| Panel | `#FFFFFF` | Inspector and controls |
| Ink | `#172B3A` | Main text and navigation |
| Muted ink | `#53636D` | Secondary labels |
| Divider | `#D8DEDE` | Panel boundaries and table rules |
| Deployment | `#087F78` | Selected hubs and main Run action |
| Closure | `#B9402F` | Closed-road marks and errors |
| Unserved | `#8A5A0A` | Uncovered labels and hatched areas |
| Roads | `#AAB5BC` | Background network, increased emphasis on selection |

Use local/system sans-serif typography, 14–16px readable body, compact 12–13px metadata only where necessary, tabular numerals for metrics. Use 4/8px spacing increments, modest corner radii, fine separators and limited shadows. Avoid uppercase text everywhere. Colors are semantic: solver methods use labels/line styles rather than a competing rainbow.

### Screen structure

1. Slim header: ReliefGrid, scenario name, synthetic/open-data badge, scenario version, save baseline and export.
2. Left pane (~260px at desktop): planning parameters, road-closure list and layer legend. Settings remain visible when selecting a map feature.
3. Central map: dominant flexible canvas; candidate/selected hubs, communities and actual road/service paths. Show selected-community context without resetting camera.
4. Right inspector (~320px): selected entity details or current plan, coverage summary, unmet communities, explicit Run/Cancel control and solver selection.
5. Collapsible lower tray: method comparison table, decision changes, then detailed quantum evidence. Main map retains adequate height when tray opens.

At narrow widths, use map plus a resizable bottom sheet with named tabs and an accessible location list. Do not squeeze three desktop columns into a phone. Preserve parameters and selections across panel changes.

### Interaction specifications

- Click a community or table row to cross-highlight it and display its nearest selected hub, actual travel time, and served/unserved reason.
- Road closure is a reversible edit with Undo; preview and solver results have different labels. Do not automatically launch expensive optimization on every drag.
- Baseline/candidate comparison synchronizes map cameras; legends state which plan each layer represents. Side-by-side mode is optional after a single-map delta mode works.
- Coverage metrics are global unless explicitly labeled viewport-filtered. Panning must not silently change the optimization objective or global denominator.
- Show a concise result summary above a comparison table; reserve plots for convergence and distribution evidence with units and exact-value access.
- Timeline entries record actual edits and runs; explanations derive from model deltas, not generated claims.
- Optional animation highlights a changed path or hub, never suggests vehicles or supplies were actually dispatched.

### Visual acceptance gate before broad UI implementation

Deliver one high-fidelity implemented vertical slice using fixed golden data: baseline map, selected community, bridge-closed state, comparison tray and backend-error state. Inspect desktop 1440px, laptop 1280px and mobile 390px screenshots. Check readable labels, focus order, contrast, non-color status cues, overflow, map/table correspondence and no remote-tile dependency. Agree on tokens and panel behavior at this gate, then extend components. Reference collection alone is not visual validation.

Functional layout contract: map is the central canvas; compact scenario controls at left, deployment/decision inspector at right, comparison tray below. Quantum evidence opens on demand. Keep global navigation shallow: Planner, Experiments, Evidence. Avoid a grid of decorative KPI cards dominating the map.

States to design: initial scenario, edited/uncomputed, preview loading, queued, running, complete, stale result, cancelled, timeout, backend unavailable, invalid input, no coverage, and quantum unavailable above limit. Each gets a useful next action. Do not show raw “Failed to fetch.” WebGL failure needs a local SVG/list alternative, not a blank page. Geometry remains useful without a basemap.

Communities need status labels/shapes in addition to color. Selected hubs, candidate hubs, closed edges and service paths must remain visually distinct. Use a subdued base and reserve saturated color for decisions and disruptions. Explicit legend, accessible control labels, keyboard road list, reduced-motion support, readable contrast, responsive stacked layout; desktop planning is the primary experience.

## 7. Parallel implementation stages and ownership

The user authorized implementation of these stages and stage-specific GPT-6.1 Sol agents at medium effort. Felt is the primary visual reference, superseding the multi-reference palette where they differ: thin toolbar, soft map, floating legend and inspector, bottom attribute table. Use original branding/assets. Each owner edits its assigned files; shared contracts, locks, root launch scripts, exports and documentation have single owners. Use `codex/reliefgrid-*` branches if isolated branches are needed. Avoid broad dependency upgrades or root-game changes.

### Stage 0 — Contract and scaffold freeze (integration lead)

Own: contracts, package manifests/locks, scaffold, launch scripts, canonical evaluator interface, golden fixture and CI commands. Dependencies: none.

Deliver: runnable minimal API/UI on 8010; generated TS types; immutable prepared fixture; mocked success/failure jobs; algorithm function signatures; bit-order example; problem/run hashing specification; written performance caps and timing instrumentation. Validate clean installation and existing artifact preservation. Freeze the boundary before parallel work.

### Stage 1A — Scenario and road engine (data/graph owner)

Own: scenarios, provenance, graph.py, graph tests. Depends: Stage 0; can use fixture solver results.

Deliver: shortest-path preparation, closure handling, deterministic path reconstruction and preview data; two small clearly synthetic scenarios plus benchmark variations. Acceptance: one-way roads, disconnected components, bridge removal, threshold boundaries and null serialization verified. No live-data dependency.

### Stage 1B — Shared evaluator and classical solvers (optimization owner)

Own: objective.py, classical.py, solver-domain tests. Depends: Stage 0 prepared fixture; need not wait for graph engine.

Deliver: score/feasibility/assignment calculations; exact, greedy and random solvers; contribution and before/after comparison utilities. Acceptance: independent tiny enumerations match; no double-counting; deterministic ties; k=0/n; invalid k; zero weights; exact work-limit handling. Do not modify quantum internals or frontend.

### Stage 1C — Quantum engine (quantum owner)

Own: qaoa.py, circuit compiler, preparation, ablations, quantum tests. Depends: Stage 0 prepared fixture and scorer contract; can start before graph/API.

Deliver: direct coverage phase compiler, coherent feasible preparation, XY layers, bounded training, finite-shot evaluation, resources and raw diagnostics. Acceptance: exhaustive tiny Hamiltonian/phase agreement; bit order/sign checks; Hamming-weight preservation; nontrivial angle response; returned scores recomputed by domain evaluator; resource limits enforced. Failure to beat greedy is a valid recorded result, not reason to alter fixtures.

### Stage 1D — Application interface (UI owner)

Own: frontend except generated API types. Depends: Stage 0 mocked contract; visual research direction.

Deliver: offline map/layers, controls, keyboard road list, comparison and change explanation, evidence drawer, all loading/error/stale states. Acceptance: full workflow using deterministic mocked jobs; no live tile requests; map and inspector selections synchronize; stale hashes blocked; responsive layout and contrast checked. Screenshots document actual states.

### Stage 1E — API and job lifecycle (service owner)

Own: jobs.py, api.py, storage adapter, API tests. Depends: Stage 0 solver interfaces; use bounded fake solvers until real modules land.

Deliver: validation, process worker, queue, cancellation/timeout, polling, same-origin static build and evidence endpoint. Acceptance: useful failure envelopes, immutable snapshots, atomic terminal runs, rejected excess work, no orphan solver on cancellation, no late-result overwrite. Coordinate manifest changes with lead.

### Stage 2 — Early integration (lead plus module owners)

Depends: 1A–1E. Merge thin slices as each passes contracts: preview first, greedy result next, exact comparison, then live QAOA. Do not defer every integration until the last day.

Acceptance: same prepared problem reaches every solver; actual closure changes reachability and result; frontend handles backend restart; missing WebGL/network does not erase planning data; completed historical jobs are clearly labeled. Record any model/API change across all consumers.

### Stage 3 — Independent evidence and notebook (evidence owner)

Depends: Stage 2 stable engine. Own: benchmarks, notebook, replay fixtures and verification record.

Deliver: predefined suite and multiple seeds; full baseline tables including losses; ablations; timing/resource reports; fresh-kernel standalone notebook containing shared module definitions and embedded scenarios; evidence JSON schema validation. Notebook setup is explicit and execution works without the app server or repository source files. Notebook prose and metadata contain no mentions of AI, per user request. The notebook is the primary submission; the Flask interface is optional. Replay mode is visually labeled and links to source run metadata.

Acceptance: UI export and notebook evaluate the same scenario/hash to identical deterministic metrics; all code cells execute without errors; simulator/hardware distinction is visible. No extrapolated operational benefit or quantum speedup claims.

### Stage 4 — Demonstration and package (delivery owner)

Depends: Stage 3. Own: final launch flow, concise deck, README and packaging with lead review.

Deliver: one-command local startup, offline demonstration, five-minute story, editable slides plus viewing export, notebook, run evidence and license/provenance. Presentation sequence: planning problem → bridge closure → changed deployment → baseline comparison → quantum mechanism/evidence → limitations.

Acceptance: rehearse from clean launch; 30-second solve target measured rather than assumed; if not met, reduce documented defaults and retain labeled replay for presentation. Verify package contains no private correspondence, credentials, environment directories or unrelated artifacts. Existing user authorization permits eventual completed-code push, but this planning task does not require publishing or replacing the current submission.

### Required handoff from every builder

- Exact files changed, contract/schema version, dependency changes and integration instructions.
- Commands executed and results; distinguish unrun checks from passes.
- Golden fixture request/result and known limitations.
- Any blocking decision or unfinished requirement, without silently changing scope.

## 8. Release gates and risk controls

| Risk | Required control / release gate |
|---|---|
| Cosmetic quantum use | Real cost compiler, feasible mixer, angle and dephasing ablations; no precomputed oracle |
| Classical methods win | Show measured outcome honestly; retain useful classical planning workflow |
| Too many covering hubs | Report controlled-phase synthesis cost; never silently change coverage |
| Exponential simulation | Measured small-n defaults, strict caps, classical-only larger mode |
| Demo fetch/tile failure | Same-origin API, offline geometry, startup health check, retry guidance |
| Stale recommendations | Immutable snapshots; current problem hash checked before display |
| Misleading geographic story | Path-based calculations, synthetic labels, explicit units/source licenses |
| Aggregate coverage hides exclusion | Uncovered list, population vs weighted score, documented policy weights |
| Existing submission damage | Isolated new app; preserve root and untracked notebook/zip |

Minimum end-to-end checks: road closure changes access; overlap counts once; exact-k feasibility; null/unreachable paths; small-instance objective/circuit agreement; preparation coherence; all cost angles effective where expected; cancellation/timeout; stale job rejection; offline geometry; notebook/export consistency; legacy launch/tests unaffected when relevant integration files change.

## 9. Later extensions, gated separately

1. Open-data importer with source license, retrieval timestamp, validated road directions, travel-time assumptions and attribution. Do not call synthetic fixtures Waterloo emergency data.
2. Robust optimization of an explicit scenario-weighted or worst-case objective, compared against nominal optimization. Evaluating stress cases alone is not this feature.
3. Variable monetary costs/capacities/forced hubs with a separately proved feasible encoding and revised contracts.
4. IBM hardware adapter: server-side credential handling, queue/cost expectations, calibration metadata, hardware-specific resource and infeasibility reporting. Optional; never required for local startup.
5. Larger-instance classical planning and stronger local-search baselines; honest quantum size limits remain visible.

Do not add accounts, collaboration, live emergency feeds or public hosting before the local decision loop, mathematical validation and evidence are complete.

## Architecture amendment

The user explicitly changed the backend to Flask and made a standalone Python notebook the primary submission. Notebook cells must expose real implementation code, not just call an external service. Generate those readable code cells from the same Python sources used by Flask, embedding scenario data so the upload works independently. Verify fresh-kernel execution outside the repository and compare notebook results against shared module results. The user will provide a presentation template; draft slide content first and defer PowerPoint formatting until that template arrives.
