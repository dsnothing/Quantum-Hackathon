# ReliefGrid presentation draft

**Format:** six slides, about five minutes. The standalone Python notebook remains the primary reproducible artifact; the map interface is a companion demonstration. All scenarios and populations shown are synthetic.

## Slide 1 — ReliefGrid

Emergency hub planning with QAOA. Introduce the planning question: how does a road closure change who can reach a selected hub?

## Slide 2 — A bridge closure changes coverage

- Synthetic directed-road network
- Three hubs per plan
- Nominal best coverage: 9,060 people
- Bridge-closed best coverage: 8,140 people

Explain that this is a modeled synthetic scenario, not live emergency data.

## Slide 3 — A small, explicit planning model

- Directed roads with travel times
- Synthetic community populations
- Choose three hubs
- Count each community once if a selected hub is reachable within 12 minutes

The model does not include capacity or dispatch constraints.

## Slide 4 — Nominal case results

- Exact, greedy, and seeded random best: 9,060
- Primary QAOA run (p=1, seed 42): best sampled plan 8,680
- Expected score: 6,579.5525
- The sampled plan is 380 below the optimum

State that QAOA ran on an ideal simulator. The expected score and best sampled plan are separate reported quantities.

## Slide 5 — Bridge closed

- Closure-specific optimum: 8,140
- QAOA best sampled plan: 8,140; expected score: 6,497.8649
- App demonstration coverage changed from 9,060 to 8,140, a decrease of 920
- Civic Hall replaced Ridge Station; Bridgeview to Civic Hall took 4.5 minutes

## Slide 6 — How the QAOA circuit works

The editable three-stage diagram shows coherent fixed-k initialization, direct coverage neighborhood cost phases, and an ordered XY mixer that exchanges selected and unselected hubs while preserving k.

The primary run used bounded ideal-simulator optimization (up to 24 evaluations, seed 42), then a separate 256-shot evaluation with sampling seed 383,329,928. These are simulator results, not a hardware result or quantum-advantage claim.

## Sources

- `reliefgrid/benchmarks/notebook-evidence.json` — primary and benchmark values.
- `reliefgrid/docs/VERIFICATION.md` — app demonstration evidence, verification status, and interpretation limits.
- Qiskit Fall Fest — https://uwquantum.com/qiskit-fall-fest
- Qiskit QAOA guide — https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm
- PresentationGO Natural Intelligence template — https://www.presentationgo.com/presentation/natural-intelligence-powerpoint-template/
