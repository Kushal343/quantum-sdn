"""Render saved evaluation summaries without rerunning simulations."""
import json
from pathlib import Path


def main():
    out = Path('results/sweeps-initial')
    data = json.loads((out/'summary.json').read_text())
    lines = ['# Initial repeated-seed results', '',
             'Five seeds per scenario/policy, 12 intervals, 100,000 pulses per wavelength/interval.',
             'This is exploratory evidence. Pointwise 95% Wilson intervals remain wide with five seeds.', '',
             '| Scenario | Policy | Detected | Mean delay (detected only) | Runs with false isolation |',
             '|---|---|---:|---:|---:|']
    for r in data:
        detected = 'N/A' if r['detection_probability'] is None else f"{round(r['detection_probability']*r['runs'])}/{r['runs']}"
        delay = 'N/A' if r['mean_delay_detected_only'] is None else f"{r['mean_delay_detected_only']:.1f}"
        lines.append(f"| {r['scenario']} | {r['policy']} | {detected} | {delay} | {round(r['false_isolation_probability']*r['runs'])}/{r['runs']} |")
    lines += ['', 'Full uncertainty bounds and estimated throughput are in `summary.json`; individual outcomes are in `runs.csv`.',
              'Tap means hidden loss. A detection is not attribution of malicious behaviour.',
              'No actual secure keys are generated. These tests do not validate a composable finite-key proof.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
