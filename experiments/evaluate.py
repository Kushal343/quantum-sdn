"""Repeated-seed research evaluation; truth is used only after simulation."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from run import run_network
from qkd_sdn.controller import wilson
from qkd_sdn.simulation import SCENARIOS


def evaluate(frame, scenario, onset=6):
    disturbed = scenario in ('intercept', 'weak_intercept', 'tap')
    events = frame[frame.action == 'isolate']
    false_events = events[(events.interval < onset) | (events.channel != 'lambda_3')] if disturbed else events
    target = events[(events.channel == 'lambda_3') & (events.interval >= onset)]
    premature = bool(((events.channel == 'lambda_3') & (events.interval < onset)).any())
    detected = disturbed and not premature and len(target) > 0
    responses = frame[(frame.channel == 'lambda_3') & (frame.interval >= onset) & frame.action.isin(['hold', 'isolate'])]
    benign = frame if not disturbed else frame[(frame.interval < onset) | (frame.channel != 'lambda_3')]
    return dict(false_isolation_run=bool(len(false_events)),
                false_hold_run=bool((benign.action == 'hold').any()),
                response_delay_intervals=int(responses.interval.min()-onset) if disturbed and not premature and len(responses) else None,
                detection_eligible=disturbed, detected=bool(detected),
                delay_intervals=int(target.interval.min()-onset) if detected else None,
                held_intervals=int((frame.action == 'hold').sum()),
                rollbacks=int((frame.action == 'rollback').sum()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds', type=int, default=20)
    p.add_argument('--steps', type=int, default=16)
    p.add_argument('--pulses', type=int, default=100000)
    p.add_argument('--out', type=Path, default=Path('results/sweeps'))
    p.add_argument('--engine', choices=['aer', 'binomial'], default='aer')
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--scenarios', nargs='+', choices=list(SCENARIOS), default=list(SCENARIOS))
    a = p.parse_args()
    if a.seeds < 2 or a.steps <= 6 or a.pulses < 1000:
        p.error('Require >=2 seeds, >6 intervals and >=1000 pulses.')
    a.out.mkdir(parents=True, exist_ok=True)
    runs = []
    for scenario in a.scenarios:
        for seed in range(a.seed_start, a.seed_start+a.seeds):
            for policy in ('fixed', 'aggregate', 'per_wavelength', 'adaptive'):
                frame, summary = run_network(scenario, a.steps, seed, a.pulses, policy, engine=a.engine)
                frame.to_csv(a.out/f'{scenario}_{policy}_{seed}.csv', index=False)
                runs.append(dict(**summary, **evaluate(frame, scenario)))
                pd.DataFrame(runs).to_csv(a.out/'runs.csv', index=False)
                print(scenario, seed, policy, flush=True)
    summaries = []
    for (scenario, policy), g in pd.DataFrame(runs).groupby(['scenario', 'policy']):
        n = len(g)
        false = int(g.false_isolation_run.sum())
        bits = g.estimated_released_bits.to_numpy()
        # Seed is the independent unit; bootstrap whole runs, never channel rows.
        rng = np.random.default_rng(2026)
        means = rng.choice(bits, size=(5000, n), replace=True).mean(axis=1)
        eligible = int(g.detection_eligible.sum())
        detected = int(g.detected.sum())
        delays = g.delay_intervals.dropna()
        summaries.append(dict(scenario=scenario, policy=policy, runs=n,
            engine=a.engine,
            false_hold_probability=float(g.false_hold_run.mean()),
            false_hold_wilson95=wilson(int(g.false_hold_run.sum()),n,1.96),
            mean_response_delay=float(g.response_delay_intervals.dropna().mean()) if g.response_delay_intervals.notna().any() else None,
            mean_retunes=float(g.retunes.mean()), mean_rollbacks=float(g.rollbacks.mean()),
            false_isolation_probability=false/n,
            false_isolation_wilson95=wilson(false,n,1.96),
            detection_probability=detected/eligible if eligible else None,
            detection_wilson95=wilson(detected,eligible,1.96) if eligible else None,
            missed_runs=eligible-detected if eligible else None,
            mean_delay_detected_only=float(delays.mean()) if len(delays) else None,
            mean_estimated_bits=float(bits.mean()),
            estimated_bits_bootstrap95=np.quantile(means,[.025,.975]).tolist()))
    (a.out/'summary.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
    (a.out/'methodology.txt').write_text(
        'Independent unit: seeded run. Onset: 6. Wilson 95% intervals are pointwise, '
        'not simultaneous guarantees. Delay is conditional on detection; misses are '
        'reported separately. Tap detection means unexplained loss, not attribution '
        'to an attacker. Throughput is asymptotic estimated bits, not secure keys. '
        'Bootstrap intervals with few seeds are exploratory. Shared seeds do not '
        'guarantee identical random draws after policies change configuration.', encoding='utf-8')


if __name__ == '__main__':
    main()
