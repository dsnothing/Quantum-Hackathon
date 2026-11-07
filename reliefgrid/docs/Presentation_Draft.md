# ReliefGrid — presentation draft

**Format:** six slides, about five minutes. This is a speaking plan, not an official event limit. Keep the standalone Python notebook as the primary submission; show the Flask/React map as a companion interface only if the current build is stable.

**Evidence rule:** The project plan says implementation and verification are in progress. Treat every product behavior below as the intended workflow until confirmed in the current build. Use bracketed fields only for evidence still to be collected; do not fill them with illustrative numbers. The scenario and populations are synthetic and must be labeled on screen.

## Six-slide run of show

### 1. A closed bridge changes the plan — 0:00–0:35

**Slide copy**
- Emergency planners may need to place a limited number of supply hubs when a road link becomes unavailable.
- ReliefGrid explores how a changed road network changes who is reachable.

**Visual plan:** Sparse schematic road map: a bridge link, several communities, and candidate hub markers. Label the map “synthetic example.”

**Speaker outline:** “The question is simple: if this bridge closes, which communities lose access, and does moving a hub help? We built ReliefGrid to make that change visible and checkable.”

**Evidence status:** The planning question and scope come from the project plan. Avoid implying live emergency use or real Waterloo geography.

### 2. Make the planning assumptions visible — 0:35–1:15

**Slide copy**
- Inputs: a directed road network with travel times, communities, candidate hubs, a hub count, and a response-time threshold.
- Coverage means a community can reach a selected hub within the threshold; overlapping service counts once.
- The demonstration data are synthetic.

**Visual plan:** Compact map legend plus a five-item input strip. Mark the synthetic scenario and travel-time units on the map.

**Speaker outline:** “The model uses explicit inputs, not a live feed. For each community and candidate hub, it checks the shortest available road path against a stated time threshold. The objective counts each covered community once.”

**Evidence status:** Formulation is specified in the plan; confirm displayed units, labels, and behavior against the current notebook before presenting.

### 3. Close the bridge and inspect who loses access — 1:15–2:10

**Slide copy**
- Start from a named synthetic scenario.
- Close the bridge edge and recompute reachability.
- Inspect affected communities and before/after paths.

**Visual plan:** Live map or short screen capture: select the bridge, close it, then highlight changed paths and affected communities. Show the same map extent before and after.

**Speaker outline:** “I’m changing one link in the network. The closure removes that road edge from routing. We can then compare the affected communities and paths, rather than infer an impact from a color change.”

**Pending evidence placeholder:** `[Insert one verified closure comparison from the current build: scenario ID, changed road ID, affected community IDs, and before/after reachable counts.]` If that interaction is not reliable, show a static diagram and describe the intended calculation without saying the app completed it.

### 4. Compare candidate deployments on the same case — 2:10–3:05

**Slide copy**
- Compare QAOA with deterministic greedy and bounded exact enumeration where available.
- Keep the scenario, closure, threshold, hub count, and scoring rule fixed.
- Show covered population, weighted score, and uncovered communities separately.

**Visual plan:** Two or three deployment markers on the map plus a small comparison card. Use actual run output only; show “not available” where a solver did not finish.

**Speaker outline:** “The comparison is meaningful only if every method gets the same instance and an independent scorer checks its returned plan. Exact enumeration is limited to small cases. We report population and policy-weighted score separately.”

**Pending evidence placeholder:** `[Insert verified run ID/hash, solver outcomes, covered population, weighted score, exact status, seeds, and runtime—or remove the comparison graphic.]` No winner or performance claim until the evidence is collected.

### 5. Show what the quantum circuit contributes — 3:05–4:10

**Slide copy**
- Each bit represents whether a candidate hub is selected; feasible plans contain exactly the chosen number of hubs.
- QAOA alternates phases based on the coverage objective with exchanges that preserve the hub count.
- Report simulator mode, depth, shots, seed, and resource counts with results.

**Visual plan:** A small circuit sketch beside three feasible hub-selection bitstrings; highlight one objective term for a community covered by multiple candidate hubs.

**Speaker outline:** “The circuit encodes the same coverage objective used by the classical checks. The mixer moves among plans with the required number of hubs. Our planned experiment trains on an ideal simulator and evaluates sampled bitstrings separately; it is not a hardware result.”

**Pending evidence placeholder:** `[Replace with the actual circuit, execution mode, depth, shot count, seed, and measured result from the notebook.]` If the QAOA run or notebook is incomplete, present the encoding as the design and label it accordingly; do not imply a completed experiment.

### 6. A planning aid with clear limits — 4:10–5:00

**Slide copy**
- Intended output: a deployment recommendation with paths, coverage, and uncovered communities.
- This demonstration uses synthetic data and is preparedness decision support, not operational dispatch.
- The notebook is the reproducible project artifact; the map interface is optional.

**Visual plan:** One final map with selected hubs and uncovered communities, alongside a compact “synthetic / no live data / simulator result” disclosure that matches the actual demo.

**Speaker outline:** “The goal is an inspectable planning workflow, not a claim that a quantum method wins or that this is ready for dispatch. The notebook carries the implementation and reproducible calculations. We’ll make the limits visible alongside any result.”

**Pending evidence placeholder:** `[Show notebook filename and current verified execution status.]` Say “in progress” if fresh-kernel execution and evidence checks are not complete.

## Demo sequence

1. Open the standalone notebook first; confirm its scenario is labeled synthetic.
2. If the companion app is stable, open the same scenario in the map, identify the candidate hubs and communities, and close one bridge.
3. Show the resulting reachability/path change, then compare methods only if the current results are verified for the identical problem hash.
4. Show the notebook section with the objective, QAOA circuit and run metadata. State simulator vs hardware accurately.
5. If live computation, map rendering, or comparison fails, use a labeled static schematic and verified notebook output. Never substitute an unverified replay as a live result.

## Backup slides

### A. Objective and constraints

Let `aᵢⱼ = 1` when hub `j` can reach community `i` within threshold `T`. Choose exactly `k` hubs and maximize `Σᵢ wᵢ · 1[community i is covered]`. Default weights use population; any priority multiplier is an explicit policy input. Capacity and inventory are outside this model.

### B. Evidence and limits

| Item | Evidence to show |
|---|---|
| Scenario provenance | Synthetic fixture name and assumptions |
| Reproducibility | Notebook execution status, version/hash, seed |
| Solver comparison | Same prepared problem and independent rescoring |
| Quantum run | Simulator/hardware mode, depth, shots, resources |
| Boundaries | No live traffic, real populations, capacities, dispatch, or quantum advantage claim |

## Private organizer requirements notes — not slide content

- The official event page says teams submit a **project notebook and slides**. A GitHub link, documentation/research paper, or symposium poster is optional. The stated project goal is a Python notebook implementing a tool or abstraction bridging quantum with a non-quantum field.
- The page says presenting live to judges is required for a chance to win a physical certificate; otherwise judging is based on submitted slides. It says IBM hardware use is optional and judges will use a simulator if running projects.
- The official pages do **not** publish a judging rubric or presentation time limit. Five minutes above is our planned story length, not an event rule.
- The event page lists the Friday, November 6 closing presentations as 6:30–9:00 p.m.; the linked signup page lists presentations/judging as 5:30–8:30 p.m. Confirm the actual arrival/presentation schedule with organizers. Do not assume either window is an individual team's slot.

## Sources

- [Qiskit Fall Fest — Waterloo Quantum Club](https://uwquantum.com/qiskit-fall-fest) — event format, goal, submissions, live presentation and hardware notes; accessed November 6, 2026.
- [Qiskit Fall Fest Hackathon registration](https://uwquantum.com/fall-fest-signup) — linked official signup page and its session schedule; accessed November 6, 2026.
- [ReliefGrid implementation plan](../../plan.md) — product scope, mathematical formulation, evidence requirements, and current project status.
