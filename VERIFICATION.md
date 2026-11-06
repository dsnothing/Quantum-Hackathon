# Verification record

Local build completed November 6, 2026 (Waterloo). Only simulator results are claimed.

## Milestones

1. Inspected the initially empty workspace and public organizer sources. Recorded missing requirements and conflicting session times.
2. Defined contact-triggered measurement and one-merge-per-tile rules. Built the shared Qiskit core, local server, browser UI and notebook.
3. Passed 10 focused tests. Sampled committed games: independent 198/400 merges, linked 400/400. Exact forecasts are 0.5 and 1.0.
4. Fresh-kernel notebook execution caught a poor tradeoff fixture: its vertical contacts also collapsed the pair. Moved the second partner and bottom blocker, then re-executed successfully. Added a preservation assertion.
5. Desktop inspection caught unequal grid row heights. Set explicit equal rows, added stable tile IDs, visible connection lines and keyboard focus after forecasting.
6. Exercised mobile layout at 390 × 844, direction/commit controls, and restart. DOM width check: content width = viewport width = 390, with no horizontal overflow.
7. Browser terminal fixtures caught a win message overwritten by generic merge feedback. Preserved terminal feedback and checked winning/loss screens and restart.
8. Created nine editable slides with speaker notes, a four-minute default talk and optional appendix. Inspected every slide PNG. PPTX package, geometry, font policy and first-party re-import checks passed with zero findings.
9. Native PDF export lacked a bundled font module. Created a faithful raster viewing PDF from rendered slide PNGs, rendered all nine pages with Poppler, and inspected endpoint pages alongside the source renders. Editable text remains in the PPTX. A portable HTML preview gallery is also supplied.

## Repeatable checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe execute_notebook.py
node --check web/app.js
```

Notebook outputs include the actual test result. All code cells have execution counts and no error outputs. Central examples run without the HTTP server. Python source compiles. No frontend framework, TypeScript build, or configured lint pipeline applies.

## Browser evidence

- `evidence/desktop-linked.jpg`: exact guaranteed forecast and two possible result boards.
- `evidence/desktop-independent.jpg`: 50% forecast and four possible boards.
- `evidence/mobile-forecast.jpg`: mobile layout with forecast.
- `evidence/win.jpg`, `evidence/loss.jpg`: real terminal UI driven by local test fixtures. These are engineered test positions, not full successful human playthroughs.
- `tests/ui_fixture_server.py`: repeat terminal screens at separate local ports. Example: `python tests/ui_fixture_server.py win 8001`, then preview left and commit. `loss 8002` shows the full-board loss case.

The introduction was clicked through all three steps. Independent and linked scenario buttons, preview, commit, arrow-key input, Enter commit, New game, and terminal restart were exercised in the actual browser. The tradeoff fixture's left/up distinction is additionally asserted in core/notebook tests.

## Limits of verification

Automated pointer dragging did not confirm the swipe path in this browser environment. On-screen mobile controls work. Physical touch hardware, screen-reader behavior, external participant usability, a full human playthrough to 2048, native PowerPoint rendering, strategic balance and educational impact were not tested. The PPTX was rendered and re-imported with Artifact Tool, not opened in PowerPoint. No physical quantum hardware was used. No event registration or organizer upload has been performed.

GitHub publication is separately authorized by the user and occurs only after these core checks. Git credentials, Gmail contents, private correspondence and session tokens are excluded from the project.

## Startup and connection fix

Directly opening `web/index.html` used a `file://` URL, so relative API requests could not reach Python. Added a Windows double-click launcher and a Python launcher that starts the engine, opens its HTTP address, and reuses a healthy running game without resetting it. A health endpoint identifies the running game. Server startup now reports readiness after binding succeeds.

The frontend renders 16 waiting cells immediately, avoids API calls entirely under `file://`, shows explicit launch guidance, guards input until state loads, times out unavailable requests, and offers reconnection. Reconnection fetches the current board without replaying an uncertain move.

Validation: all 10 quantum/game tests still pass; JavaScript syntax and Python compilation pass. `node tests/test_web_startup.mjs` verifies direct-file guidance without any fetch, disabled input while disconnected, friendly offline feedback, and successful reconnect with rendered tiles. A real running-server check verifies that the launcher reuses the game without changing state. Browser verification at `http://127.0.0.1:8000/` loaded tiles, displayed a linked forecast, committed a merge, and displayed the next forecast. Screenshot: `evidence/startup-fixed.jpg`. The browser automation policy prevented inspecting the `file://` tab directly; that branch was exercised by the JavaScript regression test.

## Five-minute presentation

The detailed presentation follows `output/Five_Minute_Outline.md`: six timed main slides and four optional appendix slides. Every slide includes a spoken script, presenter cues and sources in its notes. The coherence chart and analytical comparison table remain native editable PowerPoint objects. Data were checked against the executed notebook outputs; no new hardware, usability or learning results are claimed.

All ten slide renders were visually inspected. The final PPTX passed package integrity, geometry/font checks, native-chart validation, table checks and first-party re-import with zero layout findings. The final archive contains ten speaker-note parts, each with script, cues and sources, and one embedded chart workbook. The PDF is a raster viewing export of the same slide renders; Poppler rendered all ten pages, with comparison checks on the demo, evidence and reference pages. Native PowerPoint application rendering was not tested. This deck targets five minutes and still requires rehearsal.
