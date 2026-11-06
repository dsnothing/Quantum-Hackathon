"""Build the primary artifact; execute with execute_notebook.py."""
import nbformat as n
from pathlib import Path
nb=n.v4.new_notebook()
cells=[]
def md(s):cells.append(n.v4.new_markdown_cell(s))
def code(s):cells.append(n.v4.new_code_cell(s))
md('''# Quantum 2048: planning with shared fate
**Waterloo Qiskit Fall Fest 2026 · Primary technical submission**

A sliding-number puzzle that makes the joint distribution useful before a move. The contribution is an exact, non-measuring merge forecast tied to a playable ruleset. Quantum 2048 has prior implementations; we do not claim global novelty, speedup, or measured learning gains.

**Setup:** Python 3.12 recommended. From the project root: `python -m pip install -r requirements.txt`. Select that Python environment in Jupyter, then Run All. These examples import `quantum2048.py` and never require the browser, server, credentials, or hardware. Keep this notebook beside the supplied source files. Re-execute with `python execute_notebook.py`.

All outputs below are actual local simulator results. AI assisted the implementation, writing, and validation. Organizer permission for AI assistance and pre-existing work remains unconfirmed.''')
code('''import sys, pathlib, importlib.metadata as metadata
root = pathlib.Path.cwd()
if not (root / 'quantum2048.py').exists():
    raise RuntimeError('Run from the supplied project root with quantum2048.py beside the notebook.')
from quantum2048 import Game, QuantumGroup, interference
import numpy as np
print('Python', sys.version.split()[0], 'Qiskit', metadata.version('qiskit'))''')
md('''## 1. Rules before circuits

- A 4 × 4 board slides toward the chosen edge. Process rows top to bottom or columns left to right. Within a line, process from the destination edge. Compress, compare consecutive tiles, merge equal values once per swipe. A new merged tile cannot merge again that swipe.
- Fixed tiles hold powers of two. An uncertain tile represents one qubit, with bit 0 mapped to 2 and bit 1 to 4. A linked pair shares a Bell state. Tile IDs survive movement. A merge consumes both IDs and creates one new, fixed tile.
- Measure at a **possible matching contact**: when two candidate supports overlap. Resolve the destination tile then the incoming tile. Measurement updates the joint state and any now-certain partner, wherever it is. The result persists. Disjoint values slide without measurement. A failed uncertain contact still resolves tiles and consumes a turn. Line order matters when partners contact other tiles.
- A swipe is active if positions, values, or measurement state change. A true no-op never spawns or scores. Score is the sum of created merged values. Forecasts exclude the subsequent spawn.
- Start with two ordinary 2s and one linked pair. Each active turn normally spawns a fixed tile in a random empty cell: 90% 2, 10% 4. On turns divisible by four, spawn a Bell pair into two random empty cells if possible and at most four unresolved qubits remain. Otherwise on even turns spawn a single |+⟩ tile if capacity allows. If neither applies, use a fixed tile. Spawn locations and fixed-tile values use classical randomness. Quantum values use Qiskit measurement.
- Reach 2048 to win. A full board loses only when every direction has zero probability of an active move. Restart resets the board and score. The UI stops play after win/loss; the core remains usable for analysis.
- Each quantum group has at most two qubits. Groups are independent of one another. At most four unresolved tile qubits limit forecasts to at most 16 computational-basis branches. Measured qubits stay in their small group until its last tile disappears.

The server holds one local game in memory. Opening a second tab shares that game. No persistence, online multiplayer, accounts, or telemetry.''')
md('''## 2. The same marginals, different merge forecasts

Independent |+⟩ ⊗ |+⟩ has 00, 01, 10, 11 with probabilities 1/4. Matching outcomes 00 and 11 total **1/2**. A Bell pair (|00⟩ + |11⟩)/√2 has only 00 and 11, so its tiles match with probability **1**. Both cases give each tile a 50/50 marginal.

Qiskit uses little-endian qubit indexing: in a printed two-bit label, the rightmost bit is qubit 0.''')
code('''single=QuantumGroup()
bell=QuantumGroup(linked=True)
print('Single:', single.probabilities())
print('Bell:', bell.probabilities())
print(bell.circuit.draw(output='text'))
for scenario in ['independent','linked']:
    g=Game(scenario=scenario)
    p=g.preview('left')
    print(scenario, 'match probability:', round(p['merges'][0]['probability'],6),
          'expected score:', round(p['expected_score'],6))
    assert np.isclose(p['merges'][0]['probability'], .5 if scenario=='independent' else 1)
print('Analytical expectations: independent +3, linked +6')''')
md('''## 3. Partial measurement and persistent outcomes

Measuring qubit 0 of a Bell pair selects 0 or 1 and conditions the remaining state. Qubit 1 then has the same bit with probability one. Repeating measurement cannot re-roll a tile. The engine uses Qiskit's returned post-measurement Statevector, rather than inventing a separate partner outcome.''')
code('''q=QuantumGroup(linked=True,seed=42)
first=q.measure(0)
print('First bit:',first, 'partner probabilities:',q.marginal(1))
print('Repeated:', q.measure(0), 'partner:', q.measure(1))
assert q.state.is_valid()
assert np.isclose(q.marginal(1)[first],1)''')
md('''## 4. Forecasts and committed moves share one reducer

`Game.preview` reads exact Qiskit basis probabilities, clones the game, and enumerates deterministic branches through `_reduce`. It does not call measurement. Uncontacted tiles remain uncertain in branch boards. `Game.move` uses the same `_reduce`, with actual Qiskit partial measurements at contacts. Since gameplay only measures in the computational basis and introduces no intervening gates, this enumeration reproduces the sequential measurement distribution. Moving a qubit changes its tile position, not its state-vector index.

The browser only displays JSON from this Python core. It does not compute quantum probabilities or randomly choose quantum outcomes.''')
code('''from copy import deepcopy
g=Game(seed=17,scenario='independent')
snapshot=deepcopy(g)
forecast=g.preview('left')
assert g.view()==snapshot.view()
assert all(np.array_equal(g.groups[k].state.data,snapshot.groups[k].state.data) for k in g.groups)
print('Forecast branches:', [(round(o['probability'],3),
    [t['value'] if t else None for t in o['board'][:4]]) for o in forecast['outcomes']])
g.move('left',spawn=False)
assert any(g.view()['board']==o['board'] for o in forecast['outcomes'])
print('Actual top row:', [t.value if t else None for t in g.board[:4]], 'score:',g.score)
print('Preview left live board and RNG unchanged: passed')''')
md('''## 5. A decision with a cost

The tradeoff fixture puts linked tiles at (row 1, column 1) and (row 2, column 3), a fixed 2 at (1,2), and an 8 at (2,1). Another 8 sits at (4,4). A left swipe contacts the outside 2 and resolves the distant partner. A right swipe also contacts them. An up swipe avoids that contact and keeps the pair uncertain while changing position. A down swipe can also preserve them. Preserving a pair defers information and may require extra moves/spawns. Consuming one partner can earn points immediately but gives up the opportunity to bring the original pair together while uncertain.

This is a concrete decision structure, **not evidence of balanced or enjoyable play**. A pair's two-cell spawn cost prevents it being only an extra free tile. No extra link-score bonus is awarded. Formal balance and user appeal remain unvalidated.''')
code('''g=Game(scenario='tradeoff')
for d in ['left','up','right','down']:
    p=g.preview(d)
    probe=deepcopy(g);probe.move(d,False)
    unresolved=sum(t is not None and t.value is None for t in probe.board)
    print(d, 'expected score',round(p['expected_score'],3),'unresolved after example move',unresolved)
assert g.preview('left')['expected_score'] > 0
assert g.preview('up')['expected_score'] == 0''')
md('''## 6. Coherence: a comparison that matching odds cannot show

A Bell state's Z-basis matching statistics also occur in the classical mixture ½|00⟩⟨00| + ½|11⟩⟨11|. The prepared pure Bell state is entangled, but matching outcomes alone cannot certify that. The game has no demonstrated quantum computational advantage.

Use the project's `QuantumGroup` engine to prepare |+⟩ = H|0⟩. A second H gives |0⟩ by interference. Remove its off-diagonal density-matrix entries first (complete computational-basis dephasing) and the same H gives a 50/50 mixture. Qiskit computes both evolutions. This one-qubit comparison isolates coherence; it is not an entanglement test. We keep it in the notebook to avoid adding an unexplained gate button to the puzzle.''')
code('''result=interference()
for label,probs in result.items():print(label, 'P(0), P(1):',np.round(probs,6))
np.testing.assert_allclose(result['coherent'],[1,0],atol=1e-12)
np.testing.assert_allclose(result['dephased'],[.5,.5],atol=1e-12)
print('Coherent H-H versus dephased H: verified')''')
md('''## 7. Focused validation and simulator sampling

Analytical probabilities are exact up to floating-point tolerance. The following sample experiment separately measures actual committed games. The test suite checks merge order, no double merges, partial collapse, repeated measurement, preview purity including RNG, branch membership, linked identities, spawning, restart fixtures, win/loss, interference, and a 160-move invariant run.''')
code('''for scenario in ['independent','linked']:
    hits=0
    for seed in range(400):
        trial=Game(seed=seed,scenario=scenario);trial.move('left',False)
        hits+=bool(trial.last)
    print(scenario, f'{hits}/400 swipes merged ({hits/4:.1f}%)')
import unittest, io
suite=unittest.defaultTestLoader.discover(str(root/'tests'))
stream=io.StringIO()
report=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
print(stream.getvalue())
assert report.wasSuccessful()''')
md('''## 8. Contribution, limitations, and usability protocol

**Contribution:** a shared simulator/game reducer with a non-mutating visual forecast, a 50% versus 100% comparison, and a linked-partner positioning cost. An interactive introduction, touch swipe preview, keyboard controls, letter/diamond link markers, and plain-language forecasts aim to make the relationship understandable. These are implemented design choices, not measured usability improvements.

**Limits:** ideal noiseless statevectors; no physical hardware runs; no advantage claim; four unresolved qubits; small hand-designed scenario evaluation rather than balance optimization; preview shows at most four outcome boards in the UI (all outcomes remain in the API); no save game or undo; no measured learning or appeal results. Exact previews condition on the current state and exclude the next spawn. A fixed game seed also fixes classical spawning and Qiskit measurement seeds.

**Short real-user protocol, not yet conducted:** recruit 3–5 volunteers with consent. Ask them to merge ordinary tiles, predict independent odds, predict linked odds, and choose a tradeoff move. Observe whether they find preview/commit, distinguish the link marker without color, and explain distant collapse. Record completion, mistaken predictions, and comments without making learning claims. Ask whether preserving a pair felt costly. Revise instructions or spawning based on actual observations.

**Demo:** load Linked, preview left, show guaranteed merge and 4/8 outcomes, commit. Load Independent and show 50%. Load A harder choice and compare left/up. Show the executed interference comparison. If the browser fails, run sections 2–6 in this notebook.

**Submission status:** public event page requires notebook and explanatory slides, simulator compatible. Presentation required for a chance at a physical certificate. Registration is per person. Public sources do not state cutoff, upload destination, exact slide formats, talk duration, AI rules, or reuse eligibility. Main event page says November 6, 18:30–21:00; registration says 17:30–20:30 (Waterloo). These are conflicting session times, not verified submission deadlines. Default talk: about four minutes with appendix. Confirm unresolved details before submitting. Nothing has been registered, submitted, or published by this project.''')
md('''## Sources and acknowledgments

Accessed November 6, 2026 (Waterloo), starting about 03:36 EST.

- [Waterloo official event and artifact requirements](https://uwquantum.com/qiskit-fall-fest)
- [Individual registration and conflicting session schedule](https://uwquantum.com/fall-fest-signup)
- [IBM Qiskit quantum_info reference](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info): Statevector and DensityMatrix. API behavior additionally verified by execution against the pinned installed version.
- [Prior Quantum2048 by nirbhaykwatra](https://github.com/nirbhaykwatra/Quantum2048), MIT-licensed Unity/C# project. Consulted README as prior art. No code or assets copied.
- [Original 2048 by Gabriele Cirulli](https://github.com/gabrielecirulli/2048), MIT-licensed. Credit for the underlying puzzle concept. This implementation uses original Python/HTML/CSS/JavaScript code and no copied assets.

AI assistance: Codex generated and revised code, tests, notebook, and slides. Human team must review scientific claims, supply team identity, rehearse, and confirm organizer eligibility policies. No participant feedback or hardware data is claimed.''')
nb.cells=cells
nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}}
n.write(nb,'Quantum_2048.ipynb')
print('Wrote Quantum_2048.ipynb')
