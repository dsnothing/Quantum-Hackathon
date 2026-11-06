"""Small Qiskit engine and deterministic 2048 reducer shared by UI and notebook."""
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from itertools import product
import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix


class QuantumGroup:
    def __init__(self, linked=False, seed=0):
        self.circuit = QuantumCircuit(2 if linked else 1)
        self.circuit.h(0)
        if linked:
            self.circuit.cx(0, 1)
        self.state = Statevector.from_instruction(self.circuit)
        self.state.seed(seed)

    def probabilities(self):
        return self.state.probabilities_dict()

    def measure(self, qubit):
        result, self.state = self.state.measure([qubit])
        return int(result)

    def marginal(self, qubit):
        return self.state.probabilities([qubit])


def interference():
    """Same engine primitives; preserve or remove phase coherence before H."""
    plus = QuantumGroup().state
    h = QuantumCircuit(1)
    h.h(0)
    coherent = plus.evolve(h).probabilities()
    dephased = DensityMatrix(np.diag(plus.probabilities())).evolve(h).probabilities()
    return {'coherent': coherent.tolist(), 'dephased': dephased.tolist()}


@dataclass
class Tile:
    id: int
    value: int | None = None
    group: int | None = None
    qubit: int = 0


class Game:
    def __init__(self, seed=1, scenario=None):
        self.rng = random.Random(seed)
        self.board = [None] * 16
        self.groups = {}
        self.next_id = 1
        self.next_group = 1
        self.score = self.turn = 0
        self.last = []
        if scenario in ('linked', 'independent', 'tradeoff'):
            if scenario == 'independent':
                self.add_quantum([0]); self.add_quantum([1])
            elif scenario == 'linked':
                self.add_quantum([0, 1])
            else:
                self.add_quantum([0, 6]); self.add_classic(1, 2)
                self.add_classic(4, 8)
            self.add_classic(15 if scenario == 'tradeoff' else 12, 8)
        else:
            self.add_classic(5, 2); self.add_classic(10, 2)
            self.add_quantum([0, 3])

    def add_classic(self, pos, value):
        self.board[pos] = Tile(self.next_id, value)
        self.next_id += 1

    def add_quantum(self, positions):
        gid = self.next_group; self.next_group += 1
        self.groups[gid] = QuantumGroup(len(positions) == 2, self.rng.randrange(2**32))
        for q, pos in enumerate(positions):
            self.board[pos] = Tile(self.next_id, None, gid, q)
            self.next_id += 1

    def support(self, tile):
        if tile.value is not None:
            return {tile.value}
        return {2 << b for b, p in enumerate(self.groups[tile.group].marginal(tile.qubit)) if p > 1e-10}

    def resolve(self, tile, assignment=None):
        if tile.value is not None:
            return False
        if assignment is None:
            bit = self.groups[tile.group].measure(tile.qubit)
            # Conditional state persists, including the distant linked partner.
            for other in self.board:
                if other and other.group == tile.group and other.value is None:
                    p = self.groups[other.group].marginal(other.qubit)
                    if max(p) > 1 - 1e-10:
                        other.value = 2 << int(np.argmax(p))
        else:
            bit = (assignment[tile.group] >> tile.qubit) & 1
            # Branch evaluation emulates conditional Bell collapse without sampling.
            for other in self.board:
                if other and other.group == tile.group and other.value is None:
                    other.value = 2 << ((assignment[other.group] >> other.qubit) & 1)
        tile.value = 2 << bit
        return True

    @staticmethod
    def lines(direction):
        if direction not in ('left', 'right', 'up', 'down'):
            raise ValueError('Unknown direction')
        rows = [[4*r+c for c in range(4)] for r in range(4)]
        cols = [[4*r+c for r in range(4)] for c in range(4)]
        lines = rows if direction in ('left', 'right') else cols
        return [list(reversed(x)) for x in lines] if direction in ('right', 'down') else lines

    def _reduce(self, direction, assignment=None):
        before = [(t.id, t.value) if t else None for t in self.board]
        events, measured = [], False
        for line in self.lines(direction):
            tiles = [self.board[i] for i in line if self.board[i]]
            out, locked = [], set()
            for tile in tiles:
                target = out[-1] if out else None
                if target and target.id not in locked and self.support(target) & self.support(tile):
                    measured = self.resolve(target, assignment) or measured
                    measured = self.resolve(tile, assignment) or measured
                    if target.value == tile.value:
                        events.append((target.id, tile.id, target.value * 2))
                        merged = Tile(self.next_id, target.value * 2)
                        self.next_id += 1
                        self.score += merged.value
                        out[-1] = merged
                        locked.add(merged.id)
                        continue
                out.append(tile)
            for n, i in enumerate(line):
                self.board[i] = out[n] if n < len(out) else None
        after = [(t.id, t.value) if t else None for t in self.board]
        return before != after or measured, events

    def branches(self):
        active = sorted({t.group for t in self.board if t and t.value is None})
        options = [[(int(k, 2), float(p)) for k, p in self.groups[g].probabilities().items() if p > 1e-10] for g in active]
        for combo in product(*options):
            yield dict(zip(active, [x[0] for x in combo])), float(np.prod([x[1] for x in combo]))

    def preview(self, direction):
        events, outcomes = {}, {}
        expected, activity = 0., 0.
        for assignment, p in self.branches():
            copy = deepcopy(self)
            changed, merges = copy._reduce(direction, assignment)
            activity += p * changed
            expected += p * (copy.score - self.score)
            for a, b, v in merges:
                key = (a, b, v)
                events[key] = events.get(key, 0) + p
            key = tuple((t.id, t.value) if t else None for t in copy.board)
            if key not in outcomes:
                outcomes[key] = {'probability': 0., 'board': copy.view()['board']}
            outcomes[key]['probability'] += p
        # Sum both possible output values for a pair's merge probability.
        pairs = {}
        for (a, b, v), p in events.items():
            row = pairs.setdefault((a, b), {'tiles': [a, b], 'probability': 0., 'values': []})
            row['probability'] += p; row['values'].append(v)
        return {'direction': direction, 'merges': list(pairs.values()),
                'expected_score': expected, 'activity': activity,
                'outcomes': sorted(outcomes.values(), key=lambda x: -x['probability'])}

    def move(self, direction, spawn=True):
        changed, events = self._reduce(direction)
        self.last = events
        if changed:
            self.turn += 1
            if spawn: self.spawn()
        return changed

    def spawn(self):
        empty = [i for i, t in enumerate(self.board) if t is None]
        if not empty: return
        unresolved = sum(t is not None and t.value is None for t in self.board)
        if self.turn % 4 == 0 and len(empty) >= 2 and unresolved <= 2:
            self.add_quantum(self.rng.sample(empty, 2))
        elif self.turn % 4 == 2 and unresolved < 4:
            self.add_quantum([self.rng.choice(empty)])
        else:
            self.add_classic(self.rng.choice(empty), 4 if self.rng.random() < .1 else 2)
        active = {t.group for t in self.board if t and t.group is not None}
        self.groups = {g: s for g, s in self.groups.items() if g in active}

    def status(self):
        if any(t and t.value and t.value >= 2048 for t in self.board): return 'won'
        if any(t is None for t in self.board): return 'playing'
        # Any positive-probability active swipe avoids loss, even a resolving collision.
        if any(self.preview(d)['activity'] > 1e-10 for d in ('left','right','up','down')): return 'playing'
        return 'lost'

    def view(self, with_status=False):
        board = []
        for t in self.board:
            if not t: board.append(None); continue
            board.append({'id': t.id, 'value': t.value, 'group': t.group,
                          'linked': t.group is not None and self.groups[t.group].state.num_qubits == 2,
                          'possible': sorted(self.support(t))})
        data = {'board': board, 'score': self.score, 'turn': self.turn, 'last': self.last}
        if with_status: data['status'] = self.status()
        return data
