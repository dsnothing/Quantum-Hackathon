"""Release checks for the independently executable primary artifact."""
import ast
import json
from pathlib import Path
import re

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT.parent / "output" / "ReliefGrid_Submission.ipynb"
if not NOTEBOOK.exists():
    NOTEBOOK = ROOT.parent / "ReliefGrid_Submission.ipynb"


def test_notebook_readable_standalone_and_executed():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    assert NOTEBOOK.stat().st_size < 20_000_000
    assert not re.search(r"\bAI\b|artificial\s+intelligence|GPT|ChatGPT|OpenAI", json.dumps(notebook), re.I)
    definitions = set()
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        tree = ast.parse(cell.source)
        definitions.update(node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not node.level
                assert not (node.module or "").startswith(("reliefgrid", "backend"))
            if isinstance(node, ast.Import):
                assert not any(name.name.startswith(("reliefgrid", "backend")) for name in node.names)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"exec", "eval", "open", "__import__"}
            if isinstance(node, ast.Name):
                assert node.id != "__file__"
        assert cell.execution_count is not None
        assert not any(output.output_type == "error" for output in cell.outputs)
    assert {"Scenario", "PreparedProblem", "evaluate_plan", "prepare_problem", "solve_exact", "solve_greedy", "solve_random", "solve_qaoa", "build_cost_circuit", "build_mixer", "qaoa_probabilities"} <= definitions


def test_notebook_evidence_and_backend_agree():
    from reliefgrid.backend.domain import PlanResult, PlanningRequest
    from reliefgrid.backend.graph import load_scenario, prepare_problem
    from reliefgrid.backend.objective import evaluate_plan
    evidence = json.loads((ROOT / "benchmarks" / "notebook-evidence.json").read_text(encoding="utf-8"))
    assert evidence["schemaVersion"] == "1"
    assert len(evidence["runs"]) == 8
    for run in evidence["runs"]:
        request = PlanningRequest.model_validate(run["request"])
        problem = prepare_problem(load_scenario(request.scenarioId), request)
        assert run["problemHash"] == problem.problemHash
        for method in ("qaoa", "random"):
            result = run[method]
            PlanResult.model_validate(result)
            metrics = evaluate_plan(problem, result["selectedHubIds"])
            assert metrics["feasible"]
            assert metrics["weightedCoverage"] == result["weightedCoverage"]
            assert metrics["coveredPopulation"] == result["coveredPopulation"]
        assert run["qaoa"]["diagnostics"]["feasibleFraction"] == 1
        assert run["qaoa"]["diagnostics"]["evaluations"] <= 24
    assert evidence["ablations"]["coherentGammaZeroTotalVariation"] > 1e-6
    assert evidence["ablations"]["coherentDephasedTotalVariation"] > 1e-6


def test_embedded_implementation_matches_current_sources():
    from reliefgrid.backend.domain import Scenario, scenario_revision
    from reliefgrid.backend.graph import list_scenarios
    from reliefgrid.build_notebook import embedded_source
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    code = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    for relative in ("domain.py", "objective.py", "graph.py", "solvers/classical.py", "solvers/qaoa.py"):
        assert embedded_source(ROOT / "backend" / relative) in code
    scenario_cell = next(source for source in code if source.startswith("SCENARIOS = "))
    scenario_assignment = ast.parse(scenario_cell).body[0]
    scenarios = json.loads(ast.literal_eval(scenario_assignment.value.args[0]))
    assert {key: scenario_revision(Scenario.model_validate(value)) for key, value in scenarios.items()} == {
        entry["id"]: entry["scenarioRevision"] for entry in list_scenarios()
    }
    assert notebook.metadata["standaloneVerification"]["freshKernel"] is True
    assert notebook.metadata["standaloneVerification"]["pythonPathRemoved"] is True
