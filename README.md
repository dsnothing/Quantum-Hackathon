# Quantum 2048: planning with shared fate

A playable 2048 variant with uncertain 2/4 tiles, linked pairs, and exact merge forecasts from Qiskit. The primary submission is [the executed notebook](Quantum_2048.ipynb). Slides: [editable PowerPoint](output/Quantum_2048_Slides.pptx) and [viewing PDF](output/Quantum_2048_Slides.pdf).

## Run locally

Python 3.12 recommended. No IBM account, hardware, Aer, paid services, or internet connection needed after dependency installation.

**Windows quick start after setup:** double-click **Launch Quantum 2048.cmd**. It starts the engine and opens the correct browser address, or reuses an already running game. Keep its window open while playing. Opening `web/index.html` directly shows launch instructions because the Python engine supplies the tiles and forecasts.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

The launcher opens http://127.0.0.1:8000. For a server without opening a browser, run `python server.py`. On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows executable. A full tested dependency snapshot is in `requirements-lock.txt`; use it in place of `requirements.txt` to pin transitive packages too.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe execute_notebook.py
node tests/test_web_startup.mjs
```

The notebook runs in a fresh kernel from the project root, imports the same game core, and never launches the web server. Open the executed file in any Jupyter-compatible notebook viewer. To edit and run interactively, install JupyterLab or use an existing notebook editor with this Python environment. `make_notebook.py` regenerates the notebook source and clears its outputs; run `execute_notebook.py` afterward.

## Play

“Swipe to combine matching numbers. Linked tiles share their fate—use the connection to plan your merges.”

Choose a direction with arrow keys, on-screen buttons, or a touch swipe. Inspect chances and possible result boards, then press Enter or Commit. Mini-boards show outcomes before the next spawn. New game restarts. How to play reopens the three-step introduction. Demo buttons replace the board: Independent shows 50%, Linked shows 100%, A harder choice compares outside contact with preserving a pair.

Matching diamonds and link IDs identify shared states without relying on color. A possible matching contact measures tiles, even when the merge fails. A distant linked partner then becomes certain too. A merge consumes both identities and makes one fixed tile. Each tile merges at most once per swipe. No-op swipes do not spawn. Every fourth active turn may spawn two linked tiles, every other even turn a single uncertain tile, under a four-unresolved-qubit cap. Other spawns use ordinary 2048's 90% 2 / 10% 4 distribution. Exact rules, timing, line order, scoring and terminal conditions appear in notebook section 1.

## Architecture

- `quantum2048.py`: Qiskit state preparation, probabilities, partial measurement, shared merge reducer, branch forecasts and interference comparison.
- `server.py`: Python standard-library local HTTP server, single in-memory game, JSON interface.
- `launch.py` and `Launch Quantum 2048.cmd`: start the engine and open its HTTP page, reusing a healthy running game.
- `web/`: original HTML, CSS and JavaScript client. Quantum results always come from Python.
- `Quantum_2048.ipynb`: executed primary artifact, model, actual outputs, checks, limitations and citations.
- `output/`: editable slides, viewing export and slide preview gallery.
- `tests/test_core.py`: focused deterministic, analytical and sampled checks.
- `build_deck.mjs`: editable deck source using the Codex bundled Artifact Tool. Authoring-only, not needed to run game/notebook; expects screenshot evidence and the documented bundled runtime. Runtime location is environment-specific.

At most two qubits per group and four unresolved tile qubits in total bound forecasting to at most 16 basis branches. Previews clone state and never sample, measure or mutate the live game or its RNG. The move reducer performs Qiskit measurements only on committed contact. This equivalence relies on gameplay using computational-basis measurements with no intervening gates.

## Scientific scope and credits

Independent |+⟩ tiles match with probability 1/2. A prepared Bell pair matches with probability 1. The Bell preparation is entangled, but its matching statistics can also be reproduced with classical shared randomness. No quantum advantage, physical hardware run, global novelty, measured learning gain, or participant feedback is claimed. A separate notebook comparison shows coherence by contrasting H–H with a dephased state before the second H. Balance and usability claims remain hypotheses; a short test protocol is included.

Original 2048 concept: [Gabriele Cirulli](https://github.com/gabrielecirulli/2048), MIT. Prior quantum game: [nirbhaykwatra/Quantum2048](https://github.com/nirbhaykwatra/Quantum2048), MIT, Unity/C#. Consulted as prior art, with no source or assets copied. Qiskit documentation: [IBM quantum_info](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info). Dependencies retain their respective licenses. Code and artifacts here were generated/revised with Codex AI assistance; organizer eligibility policy remains unconfirmed.

## Troubleshooting

- Use the virtual environment's Python if imports fail. The tested Qiskit API is 2.6.2.
- Port occupied: stop the previous task server with Ctrl+C, then retry. Bind remains loopback-only. Do not use this development server as a public service.
- Tiles missing or a connection banner: use the launcher and its HTTP address. Direct `file://` access cannot run the game. If the engine stopped, start it again, then select Reconnect to load its current board. A failed move is not automatically replayed.
- Two tabs share one game. Restarting from either tab changes that game. Refresh a stale tab. Closing the server discards progress.
- The environment used for validation required running server/kernel outside sandbox network isolation. Ordinary local Python environments should not need this. Notebook runtime/config folders go into ignored `build/` to avoid modifying user settings.
- If the browser fails during the talk, use notebook sections 2–6. Slides and their PDF work independently of the server.
- Mobile on-screen direction and commit controls were exercised at 390 × 844. Automated pointer dragging did not confirm the swipe path; physical touch hardware, screen readers and external participants were not tested.

## Submission text

**Title:** Quantum 2048: Planning with Shared Fate

**Description:** Quantum 2048 connects Qiskit simulation to a familiar sliding-number puzzle. Uncertain tiles can share a joint state, and an exact non-measuring forecast shows how those relationships affect merge chances. Players compare 50% independent matches with guaranteed linked matches, then decide whether to preserve a pair or consume one partner in an outside merge. A shared Python core powers both the playable interface and an executed notebook demonstrating preparation, persistent partial measurement, forecast validation, and coherent versus dephased evolution. All core examples run locally without IBM credentials. Matching correlations are classically reproducible; no quantum advantage or validated learning benefit is claimed.

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for official requirements, uncertainty, evidence and human actions.
