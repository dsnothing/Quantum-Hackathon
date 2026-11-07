"""Build a curated, reproducible ReliefGrid zip without private or environment files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
NOTEBOOK = REPO / "output/ReliefGrid_Submission.ipynb"
PRESENTATION = REPO / "output/ReliefGrid_Presentation.pptx"
DESTINATION = REPO / "output/ReliefGrid_Submission.zip"


def validated_notebook():
    if not NOTEBOOK.is_file() or NOTEBOOK.stat().st_size >= 20_000_000:
        raise RuntimeError("Primary notebook must exist and be smaller than 20 MB.")
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code" and "".join(cell["source"]).strip()]
    if not cells or any(cell.get("execution_count") is None for cell in cells):
        raise RuntimeError("Execute every primary notebook code cell before packaging.")
    if any(output.get("output_type") == "error" for cell in cells for output in cell.get("outputs", [])):
        raise RuntimeError("Notebook contains an execution error.")


def files(presentation):
    yield NOTEBOOK, "ReliefGrid_Submission.ipynb"
    yield presentation, presentation.name
    yield REPO / "Launch ReliefGrid.cmd", "Launch ReliefGrid.cmd"
    # Explicit source roots prevent accidental inclusion of build/private files.
    for name in ("README.md", "__init__.py", "requirements.txt", "requirements-lock.txt", "pytest.ini", "launch.py", "package_submission.py", "build_notebook.py"):
        yield ROOT / name, "reliefgrid/" + name
    for directory in ("backend", "contracts", "scenarios", "tests", "docs", "benchmarks"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(ROOT).parts) and path.suffix != ".pyc":
                yield path, "reliefgrid/" + path.relative_to(ROOT).as_posix()
    for name in ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "index.html", "sync-data.mjs", "vite.config.ts", "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json"):
        path = ROOT / "frontend" / name
        if path.exists():
            yield path, "reliefgrid/frontend/" + name
    for directory in ("src", "public", "dist"):
        for path in sorted((ROOT / "frontend" / directory).rglob("*")):
            if path.is_file():
                yield path, "reliefgrid/" + path.relative_to(ROOT).as_posix()


def main():
    validated_notebook()
    presentation = PRESENTATION if PRESENTATION.is_file() else REPO / PRESENTATION.name
    if not presentation.is_file():
        raise RuntimeError("Build the final PowerPoint before packaging.")
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise RuntimeError("Build the optional companion frontend before packaging.")
    if not (ROOT / "benchmarks/notebook-evidence.json").is_file():
        raise RuntimeError("Fresh notebook evidence is required before packaging.")
    entries = list(files(presentation))
    manifest = {name: hashlib.sha256(path.read_bytes()).hexdigest() for path, name in entries}
    readme = ("# ReliefGrid submission\n\n"
              "The primary deliverable is [ReliefGrid_Submission.ipynb](ReliefGrid_Submission.ipynb). "
              "Its implementation, scenarios and measured outputs are self-contained.\n\n"
              "The five-minute presentation is [ReliefGrid_Presentation.pptx](ReliefGrid_Presentation.pptx).\n\n"
              "See [setup, model and reproduction instructions](reliefgrid/README.md) and "
              "[recorded verification](reliefgrid/docs/VERIFICATION.md). "
              "The optional Flask workbench includes a compiled frontend. "
              "Install its Python dependencies, then use Launch ReliefGrid.cmd.\n\n"
              "SHA256SUMS.json covers the notebook, presentation, and every other submission file.\n").encode("utf-8")
    manifest["README.md"] = hashlib.sha256(readme).hexdigest()
    destination = DESTINATION.with_suffix(".zip.tmp")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, name in entries:
            archive.write(path, name)
        archive.writestr("README.md", readme)
        archive.writestr("SHA256SUMS.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    destination.replace(DESTINATION)
    with zipfile.ZipFile(DESTINATION) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Zip integrity check failed.")
    print(f"{DESTINATION} ({DESTINATION.stat().st_size:,} bytes; {len(manifest)} files plus SHA256 manifest)")


if __name__ == "__main__":
    main()
