"""Write a report separating disturbance detection from benign operation."""
import json
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=Path('results/validation-100'))
    p.add_argument('--seed-start', type=int, default=1000)
    a = p.parse_args()
    out = a.out
    rows = json.loads((out/'summary.json').read_text())
    lines = ['# Expanded validation', '',
        f'100 new seeds ({a.seed_start}–{a.seed_start+99}) per scenario and policy; 16 intervals; 100,000 pulses per channel/interval.',
        '2,800 runs use the binomial count sampler, not Aer circuits. This sampler reproduces the count distribution of the current independent symmetric BB84 model. Four parameter combinations were checked against Aer and the theoretical distribution. The original 140 Aer runs remain separate.', '',
        'The controller and its thresholds were not tuned on these validation seeds.', '',
        '## Disturbance response', '',
        '| Scenario | Policy | Isolated | 95% Wilson interval | First hold/isolate delay | Isolation delay |',
        '|---|---|---:|---:|---:|---:|']
    for r in rows:
        if r['detection_probability'] is None:
            continue
        lo,hi = r['detection_wilson95']
        def delay(v): return 'No response' if v is None else f'{v:.2f}'
        lines.append(f"| {r['scenario']} | {r['policy']} | {r['detection_probability']*100:.0f}/100 | {lo:.1%}–{hi:.1%} | {delay(r['mean_response_delay'])} | {delay(r['mean_delay_detected_only'])} |")
    lines += ['', 'Delays are in simulated intervals and conditional on a response. Misses remain visible in the isolation count. A hold withholds estimated key release; it is not an isolation. Tap is hidden loss, not attribution of an attacker.', '',
              '## Benign operation', '',
              '| Scenario | Policy | Runs with isolation | Runs with hold | Mean estimated released bits |',
              '|---|---|---:|---:|---:|']
    for r in rows:
        if r['detection_probability'] is not None: continue
        lines.append(f"| {r['scenario']} | {r['policy']} | {r['false_isolation_probability']*100:.0f}/100 | {r['false_hold_probability']*100:.0f}/100 | {r['mean_estimated_bits']:,.1f} |")
    lines += ['', 'The false-isolation definition concerns disturbance discrimination, not whether a cap-triggered protective action is justified. All uncertainty bounds and throughput bootstrap intervals are retained in summary.json. Intervals are pointwise; there is no simultaneous or sequential security guarantee.', '',
              '## Interpretation', '',
              'The default C3 configuration is already the best of the five candidates under the tested normal/noise conditions. A retune count of zero does not establish a controller failure or benefit. Wider operating conditions and additional useful control actions are needed to demonstrate adaptation gains.', '',
              'These are simulation estimates. They do not establish finite-key security or produce usable secure keys.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
