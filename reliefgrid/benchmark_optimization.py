"""Reproducible quality/runtime comparison, including all predefined cases."""
import argparse
import json
from pathlib import Path

from reliefgrid.backend.domain import PlanningRequest, QaoaOptions, scenario_revision
from reliefgrid.backend.graph import load_scenario, prepare_problem
from reliefgrid.backend.solvers.classical import solve_exact, solve_greedy, solve_random
from reliefgrid.backend.solvers.qaoa import solve_qaoa


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--evaluations', type=int, default=24)
    parser.add_argument('--starts', type=int, default=1)
    parser.add_argument('--phase-scale', type=float, default=1)
    parser.add_argument('--warm-start', action='store_true')
    args = parser.parse_args()
    rows = []
    for scenario_id in ('riverbend', 'upland'):
        scenario = load_scenario(scenario_id)
        bridge = next(e.id for e in scenario.edges if 'bridge' in e.id)
        for closed in ((), (bridge,)):
            for seed in (42, 7):
                request = PlanningRequest(scenarioId=scenario_id, scenarioRevision=scenario_revision(scenario),
                    hubCount=3, responseTimeMinutes=12, closedEdgeIds=closed, solver='qaoa', seed=seed,
                    qaoa=QaoaOptions(layers=1, shots=256, maxEvaluations=args.evaluations, starts=args.starts,
                                     phaseScale=args.phase_scale, warmStartGreedy=args.warm_start))
                problem = prepare_problem(scenario, request)
                results = {name: solver(problem, request) for name, solver in
                           [('exact', solve_exact), ('greedy', solve_greedy), ('random', solve_random), ('qaoa', solve_qaoa)]}
                row = {'scenario': scenario_id, 'closures': closed, 'seed': seed,
                       'request': request.model_dump(mode='json'), 'problemHash': problem.problemHash,
                       'results': {name: r.model_dump(mode='json') for name, r in results.items()}}
                rows.append(row)
                print(scenario_id, closed, seed,
                      {name: (r.weightedCoverage, round(r.timing.totalMs, 2)) for name, r in results.items()}, flush=True)
    target = Path(__file__).parent / 'benchmarks' / f'optimization-{args.label}.json'
    target.write_text(json.dumps({'label': args.label, 'rows': rows}, indent=2), encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
