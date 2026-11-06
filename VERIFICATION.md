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
