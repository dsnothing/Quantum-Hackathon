# Quantum 2048: speaker notes

Six main slides target five minutes. Slides 7–10 are optional appendix material.

## 1. Quantum 2048

**0:00–0:25  ·  The idea**

### Spoken script

Quantum 2048 keeps the familiar sliding-number puzzle: combine equal numbers and work toward 2048. Some tiles can become either 2 or 4, and some share a joint state. Before you commit a move, our forecast shows what can merge and with what probability. That makes the relationship between tiles something you can plan around.

### Presenter cues and optional detail

Keep this introduction to 25 seconds. Point to the diamond and link ID, not every control. Explain the normal puzzle objective once. The right-hand image is an actual game screenshot crop. Five minutes is the user's presentation target, not a confirmed organizer limit. The team identity has not been supplied, so no names are invented.

### Sources

https://uwquantum.com/qiskit-fall-fest
https://uwquantum.com/fall-fest-signup
Project: Quantum_2048.ipynb, section 1; evidence/mobile-board.png

## 2. Same tiles. Different merge chances.

**0:25–1:35  ·  Live demo or screenshot fallback**

### Spoken script

These two situations look similar. Each tile has an equal chance of becoming 2 or 4. First, the independent tiles: a left move has a 50 percent chance of merging. Now the linked pair: the same individual probabilities produce a guaranteed match. We still do not know whether the merge will make 4 or 8. The forecast shows both possibilities before the next spawn. I will commit once. Qiskit calculates the probabilities and measurement outcomes behind this interaction. The player sees ordinary language instead of needing to interpret a circuit.

### Presenter cues and optional detail

Demo order: Independent button, preview left, point to 50%; Linked button, preview left, point to Guaranteed merge and the 4/8 outcomes; Commit left once. Allow about 25–30 seconds for clicks and audience attention. Do not play a full game. The two images are real forecast crops and serve as the fallback if the live demo fails. Resume on slide 3 by 1:35. Exact probabilities are simulator results, not sampled estimates. Independent expected gain is +3; linked is +6, but those extra statistics are optional Q&A material.

### Sources

Quantum_2048.ipynb, section 2
quantum2048.py: Game.preview, QuantumGroup
evidence/desktop-independent.jpg
evidence/desktop-linked.jpg

## 3. A choice between points and preserving the pair

**1:35–2:20  ·  The player’s decision**

### Spoken script

A guaranteed pair is useful, but you still have to position it. In our harder-choice fixture, a left move contacts an outside 2. That gives an expected gain of two points, and the contact reveals the distant linked partner as well. An up move earns no immediate points and preserves both uncertain tiles while repositioning them. The screenshot shows the pair still uncertain after that up move. Preserving the connection costs space and extra turns. This creates a decision to evaluate, although we have not yet tested whether players find it well balanced.

### Presenter cues and optional detail

The expected +2 and +0 refer to the starting A harder choice fixture, before spawning. The screenshot shows the state AFTER committing up, including the new ordinary tile; do not present it as the starting board. If demonstrating live, load A harder choice and compare left/up forecasts before committing. Avoid the phrase 'guaranteed strategic depth': there is no player-study evidence. A pair spawn takes two cells and no special score bonus is awarded. In outside contacts that fail to merge, measurement can still reveal both tiles.

### Sources

Quantum_2048.ipynb, section 5
tests/test_core.py: partner collapse and preservation assertion
evidence/tradeoff-preserved.jpg

## 4. What Qiskit does

**2:20–3:15  ·  One shared Python core**

### Spoken script

A single uncertain tile starts with a Hadamard preparation. A linked pair uses a Hadamard followed by CNOT, producing a Bell state. When a possible matching contact occurs, Qiskit performs a computational-basis measurement and returns the updated joint state. A distant partner can therefore become certain, and a revealed value does not reroll. For a preview, we read exact probabilities and evaluate copies of the game through the same merge rules. We never measure the live state during a preview. The browser calls this Python engine, while the notebook imports it directly. Four unresolved qubits keep exact forecasting small enough to run locally.

### Presenter cues and optional detail

Point to preparation, measurement, then forecasting. No code walkthrough is needed. Group states have at most two qubits and groups are independent of each other. With at most four unresolved qubits there are at most 16 basis branches. Preview equivalence relies on computational-basis measurements and no intervening gameplay gates. Persistent measurement uses the returned Qiskit Statevector. Controls and ordinary tile spawning use classical code; quantum tile probabilities/outcomes come from Qiskit. Simulator only; no IBM credentials or Aer required.

### Sources

https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info
quantum2048.py: QuantumGroup, Game._reduce, Game.preview, Game.resolve
Quantum_2048.ipynb, sections 3–4

## 5. Evidence from the executed notebook

**3:15–4:20  ·  Correctness and coherence**

### Spoken script

The notebook executes from a fresh kernel without the browser or IBM credentials. Ten core tests check ordinary merge behavior, normalized states, partial measurement, repeated outcomes, and forecasts that leave the live state and RNG unchanged. The exact match probabilities are one half and one. Actual committed-game samples gave 198 merges out of 400 independent trials and 400 out of 400 linked trials. Matching correlations can also arise from classical shared randomness, so they alone do not demonstrate a quantum advantage or certify entanglement. Separately, our coherence comparison applies a second Hadamard to the prepared plus state. It gives zero with probability one. If we dephase first, that probability becomes one half. Both results come from Qiskit simulation.

### Presenter cues and optional detail

Spend roughly 25 seconds on execution/tests, then 35 seconds on the scientific distinction and chart. The chart shows exact P(0), not the sampled matching results. 'Coherent' means H|0> followed by H. 'Dephased' means remove off-diagonal entries of that prepared density matrix before the final H. This one-qubit test isolates coherence; it is not an entanglement test. The ten-test claim is from the executed notebook and documented core checks. Do not imply these are hardware data or a new run during the talk. Notebook has seven successfully executed code cells.

### Sources

Quantum_2048.ipynb, sections 2, 6–7
quantum2048.py: interference
https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info

## 6. Joint probabilities become game decisions

**4:20–5:00  ·  Contribution and close**

### Spoken script

Quantum 2048 has prior implementations, which we acknowledge. Our contribution is accurate visual merge forecasting tied to linked-tile decisions, with one reproducible core behind the game and notebook. We make the effect of a joint distribution visible before the player acts. Everything shown uses a local simulator, with no demonstrated speedup. Usability, balance, and learning benefits still need real player testing. The result is a concrete bridge from quantum state simulation to game development: players can see how relationships change the consequences of their next move.

### Presenter cues and optional detail

Finish the spoken talk here at five minutes. Slides 7–10 are optional Q&A material only. Suggested final sentence: 'Our contribution is turning joint quantum probabilities into understandable game decisions.' If judges ask what is new, discuss this implementation's forecasting/measurement contract and interaction design, not a global first. AI assisted implementation, writing and validation; disclose that accurately if asked. No source or visual assets were copied from the credited earlier games.

### Sources

https://github.com/nirbhaykwatra/Quantum2048
https://github.com/gabrielecirulli/2048
Quantum_2048.ipynb, sections 8 and sources

## 7. Appendix: exact outcomes and measured trials

**Optional Q&A  ·  Outside the five-minute talk**

### Spoken script

Independent tiles have four equally likely basis outcomes. Two of them match, so the match chance is one half. The Bell pair supports only the two matching outcomes, so its chance is one.

### Presenter cues and optional detail

Bit labels are printed with qubit 0 on the right. Map 0 to tile 2 and 1 to tile 4. Pairs 22 and 44 merge into 4 and 8. Independent expected score is 0.25*4 + 0.25*8 = 3. Linked expected score is 0.5*4 + 0.5*8 = 6. The 198/400 sample is 49.5%, not exactly 50%, while 400/400 linked is 100%. Finite samples illustrate committed execution; the exact probabilities come directly from the statevector.

### Sources

Quantum_2048.ipynb, sections 2 and 7

## 8. Appendix: the measurement and forecast contract

**Optional Q&A  ·  Implementation detail**

### Spoken script

The measurement rule is fixed before the forecast runs, so the preview and the committed move describe the same game.

### Presenter cues and optional detail

Process rows top-to-bottom for horizontal moves, columns left-to-right for vertical moves, and each line from the destination edge. Compress and compare candidates. Measure only when candidate supports overlap, destination tile then incoming tile. Failed uncertain contacts still resolve tiles and consume a turn. Returned post-measurement states condition remaining partners. Identities survive movement. A merge consumes both identities and creates a fixed tile that cannot merge again that swipe. A true no-op neither scores nor spawns. Win at 2048. A full board loses when all directions have zero probability of an active move. Reconnect reads state and does not replay a failed request. The model is an ideal statevector simulator, with at most two qubits per group and four unresolved tile qubits total.

### Sources

Quantum_2048.ipynb, section 1
quantum2048.py: Game.lines, Game._reduce, Game.resolve, Game.preview, Game.status

## 9. Appendix: demo sequence and judge questions

**Optional Q&A  ·  Practical fallback**

### Spoken script

Use the notebook or supplied screenshots if the live application is unavailable.

### Presenter cues and optional detail

Before the talk: double-click Launch Quantum 2048.cmd, or run .venv\Scripts\python.exe launch.py, and keep the server running. Use the HTTP URL, not file://. Sequence: Independent > preview left > Linked > preview left > commit once > A harder choice > compare left/up. Fallback: screenshots on slide 2 and notebook sections 2–6. Q: Is this entanglement certification? A: The preparation is a Bell state, but its computational-basis correlations also occur in a classical mixture. Q: Is there an advantage? A: No advantage demonstrated. Q: Why Qiskit? A: It computes the actual state preparation, probabilities, evolution and collapse used by the game and notebook. Q: Are usability gains measured? A: No. A test protocol is provided. Q: What about hardware? A: No hardware runs are claimed. Q: Why no gate button in the game? A: Interference remains a notebook demonstration so the puzzle stays understandable.

### Sources

README.md
Quantum_2048.ipynb, sections 2–8
VERIFICATION.md

## 10. Appendix: sources and event alignment

**Optional reference  ·  Not part of the timed close**

### Spoken script

The official project goal is a Python notebook that bridges quantum computing and a non-quantum field. Our field is game development.

### Presenter cues and optional detail

The official site requires a notebook and explanatory slides, and says judges use a simulator. No public scoring weights or rubric were found on the accessible event/registration pages when the outline was reviewed November 6, 2026. The five-minute length is the user's target, not a verified organizer limit. The event page and registration form disagree on presentation session times. Cutoff, upload destination, exact slide formats, AI/reuse eligibility and team identity still require human confirmation. Individual registration and live presentation for certificate eligibility remain human actions. AI assisted code, slides, notebook writing and verification. Credit the original 2048 concept and prior Quantum2048 implementation without claiming first-ever novelty.

### Sources

https://uwquantum.com/qiskit-fall-fest
https://uwquantum.com/fall-fest-signup
https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info
https://github.com/nirbhaykwatra/Quantum2048
https://github.com/gabrielecirulli/2048