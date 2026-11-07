"""Build the readable, standalone submission; optionally execute in isolation."""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import sys
import tempfile

import nbformat as nbf

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parent / "output" / "ReliefGrid_Submission.ipynb"


def embedded_source(path: Path) -> str:
    """Remove package-relative imports using parsed source spans, retaining code."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)
    removed = set()
    for node in tree.body:
        remove = isinstance(node, ast.ImportFrom) and node.level > 0
        if path.name == "graph.py":
            remove |= isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {"load_scenario", "list_scenarios"}
            remove |= isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {"SCENARIO_DIR", "_SCENARIO_IDS"} for t in node.targets)
        if remove:
            removed.update(range(node.lineno - 1, node.end_lineno))
    return "\n".join(line for i, line in enumerate(lines) if i not in removed).strip()


def build(*, write=True):
    cells = []
    def md(text): cells.append(nbf.v4.new_markdown_cell(text.strip()))
    def code(text): cells.append(nbf.v4.new_code_cell(text.strip()))
    md("""# ReliefGrid: road-aware relief hub planning

Choose exactly **k** hubs to maximize population-weighted coverage within a road-travel threshold. A bridge closure changes the road graph before every method is evaluated. All geography, populations, and road times here are **synthetic**, released under CC0-1.0. This is an illustrative planning model, with no capacities, traffic prediction, or operational deployment claims.

This notebook contains the complete implementation and both scenarios. Run all cells in order; no application server, repository files, credentials, or remote services are needed. Quantum experiments use an **ideal local simulator**, followed by finite-shot sampling. No hardware results or quantum speedup are claimed.""")
    md("""## Setup and reproducibility

Test environment: Python 3.12.14. Install these packages in your notebook environment before running:

```text
python -m pip install pydantic==2.14.3 networkx==3.7 numpy==2.5.4 scipy==1.18.1 qiskit==2.6.2 ipykernel==7.4.0
```

The notebook uses standard IPython display support and inline SVG, so no plotting or map service is required. Benchmark settings are predefined: eight hubs, k=3, 12-minute response threshold; p=1 and p=2, seeds 42 and 7, 24 expectation evaluations and 256 samples per run. Timings depend on the computer. Exact enumeration audits every feasible subset; its results never choose quantum angles.""")
    for title, relative in [("Validated contracts and canonical hashes", "domain.py"), ("Independent overlap-safe evaluator", "objective.py")]:
        md("## " + title)
        code(embedded_source(ROOT / "backend" / relative))
    scenarios = {
        scenario_id: json.loads((ROOT / "scenarios" / f"{scenario_id}.json").read_text(encoding="utf-8"))
        for scenario_id in ("riverbend", "upland")
    }
    md("## Embedded synthetic scenarios and directed road engine\nRoad travel runs from a hub to a community. Closed roads are removed before shortest paths are calculated; unreachable travel is represented by null. Coverage includes the threshold boundary.")
    code("SCENARIOS = json.loads(" + repr(json.dumps(scenarios, ensure_ascii=False)) + ")\n\ndef load_scenario(scenario_id: str) -> Scenario:\n    if scenario_id not in SCENARIOS:\n        raise KeyError(f'Unknown scenario: {scenario_id}')\n    return Scenario.model_validate(SCENARIOS[scenario_id])\n\ndef list_scenarios() -> list[dict]:\n    return [{'id': key, 'title': load_scenario(key).title, 'scenarioRevision': scenario_revision(load_scenario(key))} for key in sorted(SCENARIOS)]")
    code(embedded_source(ROOT / "backend" / "graph.py"))
    md("## Classical methods\nExact enumerates all k-subsets, greedy takes the largest uncovered gain, and random samples uniform k-subsets with replacement. Every returned deployment is scored by the same independent evaluator. Random and quantum runs use equal sample counts; random has no optimization budget.")
    code(embedded_source(ROOT / "backend" / "solvers" / "classical.py"))
    md("""## Quantum mechanism

For community i with weight wᵢ and covering hubs Nᵢ, coverage is Σᵢ wᵢ[1−∏ⱼ∈Nᵢ(1−xⱼ)]. The phase compiler applies a controlled phase to the all-zero neighborhood, implementing H = −coverage / Σw up to a global phase. It does not load an enumerated objective oracle.

Preparation excites the first k qubits and applies two fixed XY ring sweeps at π/7 and π/11. Cost phases preserve the basis support; ordered XY mixer gates preserve Hamming weight. Hub j is qubit j, the **rightmost** printed bit. Bounded Powell optimization maximizes expected coverage; recommendation selects the best feasible finite-shot sample. The expected score and best-sample score are different quantities. The post-training exact audit supplies approximation ratios and optimum probabilities only.""")
    code(embedded_source(ROOT / "backend" / "solvers" / "qaoa.py"))
    md("## Safeguarded recommendation\nThe portfolio keeps raw QAOA results separate and retains a classical deployment whenever its coverage is higher or tied. The greedy guard guarantees parity with greedy only. An optional bounded exact guard guarantees the optimum on supported small instances. These guarantees come from classical comparison, not quantum advantage.")
    code(embedded_source(ROOT / "backend" / "solvers" / "portfolio.py"))
    md("## Evidence helpers\nTables include losses against the exact optimum. SVG maps use the embedded road geometry and reconstructed shortest service paths; they require no basemap downloads.")
    code('''from html import escape
from IPython.display import display, HTML, SVG
import platform

def show_table(rows):
    if not rows:
        return
    keys = list(rows[0])
    def fmt(value):
        return f"{value:.3f}" if isinstance(value, float) else str(value)
    display(HTML("<table><thead><tr>" + "".join(f"<th>{escape(k)}</th>" for k in keys) +
                 "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{escape(fmt(row[k]))}</td>" for k in keys) + "</tr>" for row in rows) + "</tbody></table>"))

def map_svg(scenario, problem, result, title):
    nodes = {n.id: n for n in scenario.nodes}
    xs, ys = [n.lon for n in scenario.nodes], [n.lat for n in scenario.nodes]
    def point(lon, lat):
        return (35 + 730 * (lon-min(xs))/(max(xs)-min(xs)), 380-330*(lat-min(ys))/(max(ys)-min(ys)))
    def line(coords, color, width, extra=""):
        points = " ".join(f"{x:.1f},{y:.1f}" for x,y in [point(*c) for c in coords])
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width}" {extra}/>'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"><rect width="800" height="450" fill="#f5f4f0"/><text x="20" y="22" font-size="16">{escape(title)}</text>']
    for edge in scenario.edges:
        coords = edge.geometry["coordinates"] if edge.geometry else [[nodes[edge.fromNodeId].lon,nodes[edge.fromNodeId].lat],[nodes[edge.toNodeId].lon,nodes[edge.toNodeId].lat]]
        closed = edge.id in problem.closedEdgeIds
        parts.append(line(coords, "#b9402f" if closed else "#aab5bc", 4 if closed else 1.5, 'stroke-dasharray="5 3"' if closed else ""))
    for assignment in result.assignments:
        if assignment.covered:
            path = shortest_service_path(scenario, problem.closedEdgeIds, assignment.hubId, assignment.communityId)
            parts.append(line(path["coordinates"], "#087f78", 2.5))
    unserved = set(result.uncoveredCommunityIds)
    for community in scenario.communities:
        node = nodes[community.nodeId]; x,y = point(node.lon,node.lat)
        parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{ "#8a5a0a" if community.id in unserved else "#172b3a"}"><title>{escape(community.id)}</title></circle>')
    for hub in scenario.candidateHubs:
        node = nodes[hub.nodeId]; x,y = point(node.lon,node.lat); selected = hub.id in result.selectedHubIds
        parts.append(f'<rect x="{x-6}" y="{y-6}" width="12" height="12" fill="{"#087f78" if selected else "white"}" stroke="#172b3a"/><text x="{x+8}" y="{y-8}" font-size="11">{escape(hub.id)}</text>')
    parts.append('<text x="20" y="425" font-size="12">Square: hub (teal = deployed); circle: community (brown = uncovered); dashed red: closed road.</text></svg>')
    display(SVG("".join(parts)))

def request_for(scenario, closures=(), seed=42, layers=1):
    return PlanningRequest(scenarioId=scenario.id, scenarioRevision=scenario_revision(scenario), closedEdgeIds=tuple(closures), hubCount=3, responseTimeMinutes=12, seed=seed,
                           qaoa=QaoaOptions(layers=layers, shots=256, maxEvaluations=24, starts=1))

def result_row(case, result, optimum):
    d = result.diagnostics
    return {"case": case, "method": result.solver, "hubs": ", ".join(result.selectedHubIds), "score": result.weightedCoverage,
            "loss": optimum-result.weightedCoverage, "expected score": d.get("expectedWeightedCoverage", result.weightedCoverage),
            "population": result.coveredPopulation, "feasible": result.feasible, "total ms": result.timing.totalMs}
''')
    md("## Nominal plan and bridge closure\nThe same request, prepared matrix, and canonical problem hash reach every method. Each deployment uses exactly three hubs. Population and weighted coverage are reported separately, even when fixture weights make them equal.")
    code('''scenario = load_scenario("riverbend")
assert len(scenario.candidateHubs) == 8
bridge = next(edge.id for edge in scenario.edges if "bridge" in (edge.name or "").lower() or "bridge" in edge.id.lower())
cases = {"nominal": (), "bridge closed": (bridge,)}
primary, primary_rows = {}, []
for name, closures in cases.items():
    request = request_for(scenario, closures)
    problem = prepare_problem(scenario, request)
    exact = solve_exact(problem, request)
    results = [exact, solve_greedy(problem, request), solve_random(problem, request), solve_qaoa(problem, request)]
    for result in results:
        assert result.problemHash == problem.problemHash
        assert evaluate_plan(problem, result.selectedHubIds)["weightedCoverage"] == result.weightedCoverage
        assert result.feasible
        primary_rows.append(result_row(name, result, exact.weightedCoverage))
    primary[name] = (problem, results)
show_table(primary_rows)
for name, (problem, results) in primary.items():
    map_svg(scenario, problem, results[0], f"Synthetic Riverbend — {name}; exact deployment")
print("Python", platform.python_version())
print("Scenario revision", scenario_revision(scenario))
print("Problem hashes", {name: problem.problemHash for name,(problem,_) in primary.items()})
''')
    md("## Predefined benchmark and held-out disruptions\nTrain only on each nominal or bridge-closed instance. Then evaluate the selected deployment without retraining under one additional road closure. These stress evaluations are held out from angle optimization; they are not a robust-optimization algorithm. Seeds and depths are fixed before results are observed. Include all outcomes, even when random or greedy wins.")
    code('''benchmark_rows, benchmark_runs, stress_rows = [], [], []
heldout = [edge.id for edge in sorted(scenario.edges, key=lambda e:e.id) if edge.id != bridge][:2]
for case, closures in cases.items():
    for layers in (1, 2):
        for seed in (42, 7):
            request = request_for(scenario, closures, seed, layers)
            problem = prepare_problem(scenario, request)
            exact = solve_exact(problem, request)
            quantum = solve_qaoa(problem, request)
            random_result = solve_random(problem, request)
            benchmark_runs.append({"case": case, "request": request.model_dump(mode="json"), "problemHash": problem.problemHash,
                                   "qaoa": quantum.model_dump(mode="json"), "random": random_result.model_dump(mode="json")})
            for result in (quantum, random_result):
                row = result_row(case, result, exact.weightedCoverage)
                row.update({"p": layers, "seed": seed})
                benchmark_rows.append(row)
            for edge in heldout:
                stress_request = request_for(scenario, tuple(sorted(set(closures) | {edge})), seed, layers)
                stress_problem = prepare_problem(scenario, stress_request)
                stress_optimum = solve_exact(stress_problem, stress_request).weightedCoverage
                score = evaluate_plan(stress_problem, quantum.selectedHubIds)["weightedCoverage"]
                stress_rows.append({"trained case": case, "p": layers, "seed": seed, "extra closure": edge,
                                    "fixed deployment score": score, "stress optimum": stress_optimum, "loss": stress_optimum-score})
show_table(benchmark_rows)
show_table(stress_rows)
''')
    md("## Greedy warm-start experiment\nA classical greedy deployment can replace the arbitrary first-k starting bitstring before the same coherent XY sweeps. This is a fixed-cardinality warm start inspired by classical initialization of quantum optimization, not the continuous-relaxation mixer in the IBM tutorial. Compare both initializations with the same p=1, 24 evaluations, 256 shots and seeds. Both synthetic scenarios and both bridge conditions appear below. Exact answers audit results after training. Finite sampling gives no universal optimum guarantee. Source: https://quantum.cloud.ibm.com/docs/en/tutorials/warm-start-qaoa")
    code('''warm_rows, warm_runs = [], []
for sid in ("riverbend", "upland"):
    warm_scenario = load_scenario(sid)
    warm_bridge = next(edge.id for edge in warm_scenario.edges if "bridge" in edge.id)
    for closures in ((), (warm_bridge,)):
        for seed in (42, 7):
            base_request = request_for(warm_scenario, closures, seed)
            problem = prepare_problem(warm_scenario, base_request)
            exact = solve_exact(problem, base_request)
            for warm in (False, True):
                options = base_request.qaoa.model_copy(update={"warmStartGreedy": warm})
                req = base_request.model_copy(update={"qaoa": options})
                result = solve_qaoa(problem, req)
                assert evaluate_plan(problem, result.selectedHubIds)["weightedCoverage"] == result.weightedCoverage
                row = result_row(sid + (" bridge closed" if closures else " nominal"), result, exact.weightedCoverage)
                row.update({"seed": seed, "initialization": "greedy" if warm else "first-k"})
                warm_rows.append(row)
                warm_runs.append({"request": req.model_dump(mode="json"), "result": result.model_dump(mode="json")})
show_table(warm_rows)
''')
    md("## Convergence and compiled resources\nConvergence records actual expectation evaluations, including evaluations that worsen the score. Compilation uses rz/sx/x/cx at optimization level 1; gate counts depend on synthesis and installed Qiskit version. Statevector simulation and general controlled phases scale exponentially, so these eight-hub measurements do not establish performance on large networks.")
    code('''resource_rows = []
for run in benchmark_runs:
    r = run["qaoa"]; d = r["diagnostics"]; resources = d["resources"]
    resource_rows.append({"case": run["case"], "p": resources["layers"], "seed": r["provenance"]["seed"],
                          "qubits": resources["qubits"], "depth": resources["depth"], "2-qubit gates": resources["twoQubitGates"],
                          "evaluations": d["evaluations"], "feasible fraction": d["feasibleFraction"],
                          "optimum probability": d["optimumProbability"], "expected ratio": d["expectedApproximationRatio"],
                          "total ms": r["timing"]["totalMs"]})
show_table(resource_rows)
trace = primary["nominal"][1][-1].diagnostics["convergence"]
values = [point["expectedWeightedCoverage"] for point in trace]
lo, hi = min(values), max(values)
points = " ".join(f"{40+700*i/max(1,len(values)-1):.1f},{220-170*(v-lo)/max(1,hi-lo):.1f}" for i,v in enumerate(values))
display(SVG(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 280"><text x="35" y="20">Nominal p=1 seed=42: actual expected coverage evaluations</text><polyline points="{points}" fill="none" stroke="#087f78" stroke-width="2"/><text x="35" y="250">Evaluation 1 → {len(values)}; score range {lo:.2f} → {hi:.2f}</text></svg>'))
''')
    md("## Coherence and phase ablations on a tiny independent fixture\nKeep preparation, mixer, and angles fixed. Compare the coherent circuit against zero cost angles and complete computational-basis dephasing after each cost layer. Dephasing removes relative phases, so subsequent mixing can no longer use the same interference. This isolates mechanism, without claiming an advantage against classical optimization.")
    code('''tiny = PreparedProblem(scenarioRevision="tiny-independent", problemHash="tiny-independent", hubIds=("a","b","c"), communityIds=("u","v","w"), hubCount=1,
    demandWeights=(2,5,9), populations=(2,5,9), coverageMatrix=((True,False,False),(False,True,False),(False,False,True)),
    travelMinutes=((1,None,None),(None,1,None),(None,None,1)), responseTimeMinutes=2)
ablation = run_ablations(tiny, [1.1], [0.6])
show_table([{"mode": mode, "expected score": ablation[mode]["expectedWeightedCoverage"]} for mode in ("coherent","gammaZero","dephased")])
print("Coherent / zero-phase total variation:", ablation["coherentGammaZeroTotalVariation"])
print("Coherent / dephased total variation:", ablation["coherentDephasedTotalVariation"])
assert ablation["coherentGammaZeroTotalVariation"] > 1e-6
assert ablation["coherentDephasedTotalVariation"] > 1e-6
for mode in ("coherent","gammaZero","dephased"):
    assert abs(sum(p for i,p in enumerate(ablation[mode]["probabilities"]) if i.bit_count()==1)-1) < 1e-9
''')
    md("## Interpretation and optional interface\nBest-sample recommendations can match the exact optimum even when expected coverage is substantially lower; use the distribution metrics to interpret that distinction. Small fixed-k random search can also find the optimum. The recorded losses, runtimes, and compiled gate counts are the evidence; no operational benefit is extrapolated from them. Uncovered demand may remain because of disconnected roads, thresholds, or limited hub count.\n\nThe optional Flask interface is a separate local application. From the extracted source package, run `python reliefgrid/launch.py --setup`, then open `http://127.0.0.1:8010`. Setup requires Python 3.12, Node.js 20.19+ or 22.12+, and pnpm. After setup, `python reliefgrid/launch.py` starts the local companion. It is not required by any notebook cell. The notebook is the primary submission.")
    code('''evidence = {"schemaVersion":"1", "scenarioRevision":scenario_revision(scenario), "primary":primary_rows,
            "benchmark":benchmark_rows, "runs":benchmark_runs, "heldOut":stress_rows, "ablations":ablation,
            "warmStartComparison":warm_rows, "warmStartRuns":warm_runs,
            "resources":resource_rows, "versions":{name:version(name) for name in ("qiskit","numpy","scipy","pydantic","networkx")}}
print("Verification complete: all deployments independently rescored, fixed-k feasibility checked, and coherence ablations passed.")
display({"application/json": evidence}, raw=True)
''')
    notebook = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec":{"display_name":"Python 3", "language":"python", "name":"python3"}, "language_info":{"name":"python", "version":"3.12"}})
    forbidden = re.compile(r"\bAI\b|artificial\s+intelligence|GPT|ChatGPT|OpenAI", re.I)
    assert not forbidden.search(json.dumps(notebook)), "Forbidden wording in notebook"
    if write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        nbf.write(notebook, OUTPUT)
    return notebook


def execute(notebook):
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpec
    # Clean cwd and remove package search overrides: only installed packages work.
    previous = os.environ.pop("PYTHONPATH", None)
    try:
        with tempfile.TemporaryDirectory(prefix="reliefgrid-notebook-isolated-") as directory:
            environment = dict(os.environ)
            for name in ("IPYTHONDIR", "JUPYTER_CONFIG_DIR", "JUPYTER_DATA_DIR", "JUPYTER_RUNTIME_DIR"):
                environment[name] = str(Path(directory) / name.lower())
            manager = KernelManager(kernel_name="python3")
            manager._kernel_spec = KernelSpec(argv=[sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"], display_name="Python 3", language="python")
            client = NotebookClient(notebook, timeout=180, startup_timeout=60, km=manager,
                                    resources={"metadata":{"path":directory}})
            print("Starting isolated kernel", flush=True)
            client.on_cell_executed = lambda cell, cell_index, **kwargs: print(f"Executed cell {cell_index}", flush=True)
            try:
                client.execute(env=environment)
            finally:
                if manager.has_kernel:
                    manager.shutdown_kernel(now=True)
                manager.cleanup_resources()
            notebook.metadata["standaloneVerification"] = {
                "freshKernel": True, "repositorySourceImports": False,
                "workingDirectory": "temporary directory outside repository", "pythonPathRemoved": True,
                "pythonVersion": sys.version.split()[0],
            }
    finally:
        if previous is not None:
            os.environ["PYTHONPATH"] = previous
    nbf.write(notebook, OUTPUT)
    for output in notebook.cells[-1].outputs:
        if "application/json" in output.get("data", {}):
            target = ROOT / "benchmarks" / "notebook-evidence.json"
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps(output.data["application/json"], indent=2), encoding="utf-8")
    assert OUTPUT.stat().st_size < 20_000_000


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    notebook = build()
    if args.execute:
        execute(notebook)
    print(OUTPUT)
