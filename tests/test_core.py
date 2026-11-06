import unittest
from copy import deepcopy
import numpy as np
from quantum2048 import Game, QuantumGroup, interference


def empty():
    g = Game(); g.board = [None]*16; g.groups = {}; g.score = 0
    return g

class CoreTests(unittest.TestCase):
    def test_no_double_merge_and_directions(self):
        for d, line in [('left',[0,1,2,3]),('right',[3,2,1,0]),('up',[0,4,8,12]),('down',[12,8,4,0])]:
            g=empty()
            for i in line: g.add_classic(i,2)
            g.move(d,False)
            self.assertEqual([g.board[i].value if g.board[i] else None for i in line],[4,4,None,None])
            self.assertEqual(g.score,8)

    def test_three_tiles(self):
        g=empty()
        for i,v in enumerate([2,2,4]):g.add_classic(i,v)
        g.move('left',False)
        self.assertEqual([t.value for t in g.board if t],[4,4])

    def test_analytical_probabilities(self):
        for scenario,p in [('independent',.5),('linked',1.)]:
            g=Game(scenario=scenario)
            self.assertAlmostEqual(g.preview('left')['merges'][0]['probability'],p)
            self.assertAlmostEqual(sum(o['probability'] for o in g.preview('left')['outcomes']),1)

    def test_normalization_partial_and_repeat(self):
        for seed in range(30):
            q=QuantumGroup(True,seed)
            self.assertTrue(q.state.is_valid())
            b=q.measure(0)
            self.assertAlmostEqual(q.marginal(1)[b],1)
            self.assertEqual(q.measure(0),b)
            self.assertEqual(q.measure(1),b)
            self.assertTrue(q.state.is_valid())

    def test_preview_purity_and_outcome_agreement(self):
        for scenario in ['linked','independent','tradeoff']:
            for d in ['left','right','up','down']:
                original=Game(seed=9,scenario=scenario)
                before=deepcopy(original)
                p=original.preview(d)
                self.assertEqual(original.view(),before.view())
                for gid in original.groups:
                    np.testing.assert_array_equal(original.groups[gid].state.data,before.groups[gid].state.data)
                original.move(d,False);before.move(d,False)
                self.assertEqual(original.view(),before.view()) # RNG also unchanged
                result=original.view()['board']
                self.assertTrue(any(result==o['board'] for o in p['outcomes']))

    def test_sampled_forecast(self):
        for scenario,expected in [('independent',.5),('linked',1)]:
            count=0
            for seed in range(400):
                g=Game(seed=seed,scenario=scenario);g.move('left',False)
                count+=bool(g.last)
            self.assertLess(abs(count/400-expected),.08)

    def test_partner_collapse_and_merge_identity(self):
        preserved=Game(scenario='tradeoff');preserved.move('up',False)
        self.assertEqual(sum(t is not None and t.value is None for t in preserved.board),2)
        g=Game(seed=8,scenario='tradeoff')
        gid=g.board[0].group; partner=g.board[6].id
        g.move('left',False)
        pair=[t for t in g.board if t and t.group==gid]
        self.assertTrue(all(t.value in (2,4) for t in pair))
        self.assertIn(partner,[t.id for t in g.board if t])
        g=Game(scenario='linked');ids={g.board[0].id,g.board[1].id};g.move('left',False)
        self.assertFalse(ids & {t.id for t in g.board if t})
        self.assertIsNone(g.board[0].group)

    def test_noop_spawn_restart_win_loss(self):
        g=empty();g.add_classic(0,2)
        self.assertFalse(g.move('left'));self.assertEqual(g.turn,0)
        self.assertTrue(g.move('right'));self.assertEqual(sum(t is not None for t in g.board),2)
        g=empty();g.add_classic(0,1024);g.add_classic(1,1024);g.move('left',False)
        self.assertEqual(g.status(),'won')
        g=empty()
        for i in range(16):g.add_classic(i,2 if (i//4+i%4)%2 else 4)
        self.assertEqual(g.status(),'lost')
        self.assertEqual(Game(seed=3).view(),Game(seed=3).view())

    def test_spawn_cap_and_long_play(self):
        g=Game(seed=21)
        for turn in range(160):
            d=['left','up','right','down'][turn%4]
            g.move(d)
            self.assertLessEqual(sum(t is not None and t.value is None for t in g.board),4)
            self.assertTrue(all(q.state.is_valid() for q in g.groups.values()))
            self.assertEqual(len({t.id for t in g.board if t}),sum(t is not None for t in g.board))

    def test_interference(self):
        result=interference()
        np.testing.assert_allclose(result['coherent'],[1,0],atol=1e-12)
        np.testing.assert_allclose(result['dephased'],[.5,.5],atol=1e-12)

if __name__=='__main__':unittest.main(verbosity=2)
