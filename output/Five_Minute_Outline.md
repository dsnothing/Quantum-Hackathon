# Quantum 2048: five-minute presentation outline

## Judging guidance reviewed

The public Waterloo event page states the goal: a Python-notebook project implementing a tool or abstraction that bridges quantum computing with a non-quantum field. It requires a notebook and explanatory slides and says judges will run projects on a simulator. I found no publicly published scoring rubric, weights, or confirmed talk duration on the event and registration pages. Five minutes is the requested presentation target, not a verified organizer limit.

Sources checked November 6, 2026:
- https://uwquantum.com/qiskit-fall-fest
- https://uwquantum.com/fall-fest-signup

Recommended priorities, inferred from that goal: demonstrate the quantum/game-development bridge, make Qiskit's role explicit, show a reliable working interaction, and support claims with the executed notebook. These are presentation priorities, not invented official scoring categories.

## Six-slide outline: exactly 5:00

### 1. The idea — 0:00–0:25
**Show:** title and one game screenshot.

**Say:** “Quantum 2048 keeps the familiar sliding puzzle, but some tiles share a joint state. We show the chance of a merge before you commit, so that relationship becomes something you can plan around.”

### 2. The central demonstration — 0:25–1:35
**Show:** the running game. Select Independent, inspect its left forecast, then select Linked, inspect its left forecast, and commit once.

**Say:** “Each tile is equally likely to become 2 or 4. Independent tiles match 50% of the time. These linked tiles match 100% of the time. The merged value is still uncertain: 4 or 8. Qiskit calculates the probabilities and measurement outcomes.”

Let the visible forecasts establish the distinction. Do not spend time playing a full game.

### 3. The player’s decision — 1:35–2:20
**Show:** A harder choice, comparing left and up forecasts. Use prepared screenshots if switching live costs time.

**Say:** “Left offers an expected two points, but its outside contact reveals the distant partner too. Up scores nothing immediately and preserves the pair’s uncertainty while repositioning it. Preserving a pair takes space and extra turns. Whether that feels well balanced still needs player testing.”

### 4. What Qiskit does — 2:20–3:15
**Show:** one simple implementation summary, with the executed notebook available.

**Say:** “A single uncertain tile uses a Hadamard preparation. A linked pair uses Hadamard and CNOT. At possible matching contacts, Qiskit measures and updates the remaining joint state. Those results persist. Forecasts enumerate possible outcomes on copies; they never measure the live game. The notebook and application use the same Python core.”

Avoid source-code walkthroughs, API details and full circuit derivations.

### 5. Evidence and scientific distinction — 3:15–4:20
**Show:** notebook results: 50% independent versus 100% linked; 10 passing core tests; coherent versus dephased interference results.

**Say:** “The notebook runs from a fresh kernel without the browser or IBM credentials. Tests check merge rules, partial measurement, repeated outcomes, and non-mutating forecasts. Matching correlations can also come from classical shared randomness. Separately, applying a second Hadamard to our coherent state gives zero with probability one; dephasing first gives 50/50. That comparison demonstrates coherence in simulation.”

Do not call the interference comparison an entanglement test or claim quantum advantage.

### 6. Contribution and close — 4:20–5:00
**Show:** one sentence: “Joint quantum probabilities become understandable game decisions.”

**Say:** “Quantum 2048 has prior implementations. Our contribution is accurate visual merge forecasting tied to linked-tile decisions, with one reproducible core behind the game and notebook. Everything shown uses a local simulator. Usability and learning gains remain untested. We built a concrete bridge from quantum state simulation to game development.”

Stop at five minutes.

## Keep outside the main talk

Installation, startup troubleshooting, exhaustive rules, HTTP architecture, individual test names, event logistics, long citations, detailed equations, and future-feature lists. Keep sources, full results and technical details in the notebook or appendix.

## Demo fallback

Use the actual independent/linked screenshots and executed notebook outputs if the live browser fails. Launch through `Launch Quantum 2048.cmd` or the HTTP address, rather than opening the HTML file directly. Keep the server running before the talk.
