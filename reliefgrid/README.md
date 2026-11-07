# ReliefGrid

ReliefGrid selects exactly **k emergency supply hub sites** to maximize population covered within a road travel-time threshold. Closing a road changes directed shortest paths and may change the best deployment. Both bundled regions and all populations are **synthetic**. This is a preparedness prototype, not an emergency dispatch system.

The **primary submission is [ReliefGrid_Submission.ipynb](../output/ReliefGrid_Submission.ipynb)** in the repository, or [at the root of the submission zip](../ReliefGrid_Submission.ipynb) after extraction. It contains readable implementation cells, embedded scenarios, measured results, figures and verification. It runs independently of this repository and the optional web app. The Flask/React companion provides an interactive map and evidence exports.

## Run the primary notebook

Use Python 3.12. In a fresh environment, install the pinned dependencies:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r reliefgrid/requirements-lock.txt
```

Open the notebook in Jupyter or VS Code, select that environment, and run all cells. No repository imports, web server, account, map tiles, credentials or external data files are needed by the notebook. Installation requires internet access; subsequent execution uses installed packages and embedded data. A notebook viewer is separate from the runtime dependencies (for example `python -m pip install jupyterlab`, then `python -m jupyterlab`). Do not interrupt notebook execution if a fresh full evidence run is required.

## Run the optional workbench

Prerequisites: Python 3.12, Node.js **20.19+ or 22.12+**, and pnpm available on PATH. On Windows, run from the extracted project folder:

```powershell
python reliefgrid/launch.py --setup
```

This creates `reliefgrid/.venv`, installs `requirements-lock.txt`, runs `pnpm install --frozen-lockfile` and `pnpm build`, starts Flask, verifies the ReliefGrid health identity, and opens [the local workbench](http://127.0.0.1:8010). The compiled frontend is included in the zip; users with an installed Python environment can launch without Node. For manual installation:

```powershell
python -m venv reliefgrid/.venv
reliefgrid/.venv/Scripts/python.exe -m pip install -r reliefgrid/requirements-lock.txt
# Only when rebuilding the frontend:
cd reliefgrid/frontend
pnpm install --frozen-lockfile
pnpm build
cd ../..
reliefgrid/.venv/Scripts/python.exe reliefgrid/launch.py
```

After setup, double-click **Launch ReliefGrid.cmd** or run `python reliefgrid/launch.py`. Use `--no-browser` for a headless launch or `--port 8011` if 8010 is occupied. The launcher reuses a healthy ReliefGrid service and refuses an unrelated service. It never stops another application. The app is served over HTTP, so opening frontend files with `file://` is unnecessary.

On Windows the background service has no extra console window. Its PID is printed and recorded at `build/reliefgrid/server-8010.pid`; logs are in `build/reliefgrid/server.log`. To stop a service you started, verify that PID belongs to the ReliefGrid Python command, then use Task Manager or `Stop-Process -Id <PID>`. Server jobs are local, bounded, and terminate on cancellation or timeout. Browser closure does not stop the server.

For frontend development, run `pnpm dev` from `reliefgrid/frontend` while Flask runs on 8010. Vite proxies `/api` to Flask. `PNPM_CLI` may point to a local `pnpm.cjs` when pnpm is bundled rather than on PATH.

## Reproduce evidence and package

From the repository root:

```powershell
reliefgrid/.venv/Scripts/python.exe -m reliefgrid.build_notebook --execute
reliefgrid/.venv/Scripts/python.exe -m reliefgrid.package_submission
```

The builder executes the notebook in a temporary working directory. Packaging requires a fully executed notebook without errors, notebook evidence, and the compiled companion. It writes `output/ReliefGrid_Submission.zip` with the standalone notebook, source, scenarios, compiled UI and SHA256 manifest. It excludes environments, node_modules, private build files and the original Quantum 2048 artifacts. Original Quantum 2048 submission files remain separate.

Run tests from `reliefgrid`: `.venv/Scripts/python.exe -m pytest tests -q`. See [verification](docs/VERIFICATION.md) for recorded checks and limitations and [the slide content draft](docs/Presentation_Draft.md) for the presentation story. Final PowerPoint formatting awaits the user's template.

## Model and interpretation

The score is the sum of covered community population multiplied by explicit policy weights, counting each community once. Coverage follows directed shortest road travel times after removing closed edges. Default weights are 1. Each selected hub has equal cost; capacity, inventory and vehicle routing are outside the model.

Classical methods include exact enumeration, greedy coverage, and seeded random feasible plans. Qiskit implements a direct neighborhood cost phase, coherent fixed-k initialization, an ordered XY mixer, bounded parameter optimization and separately seeded finite-shot evaluation. One qubit represents one candidate hub; the rightmost displayed bit corresponds to `hubIds[0]`. Exact enumeration is a separate baseline/audit, not a quantum gate oracle. Statevector instances are capped at 12 hubs and density-matrix coherence ablations at 8.

All quantum runs are local simulations. Reported measurements do not establish quantum advantage. Stress testing evaluates a fixed chosen plan across closures and does not perform robust optimization. No operational benefit is established by synthetic population coverage. Scenario provenance/license fields describe the bundled synthetic data; third-party runtime libraries retain their respective licenses.
