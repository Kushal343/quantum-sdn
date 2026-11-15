"""Explain the controlled single-channel comparison from saved evidence."""
import argparse,json
from pathlib import Path
import pandas as pd


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('results/single-channel-comparison'))
    args=p.parse_args();out=args.out
    s=pd.read_csv(out/'summary.csv');c=pd.read_csv(out/'comparison.csv')
    meta=json.loads((out/'metadata.json').read_text())
    cases=['normal','local_3pct','local_3p5pct','local_4pct','shared_4pct']
    means=s.pivot(index='case',columns='arm',values='mean_bits')
    lines=['# Pareto WDM versus fixed single-channel QKD','',
        'This is a new controlled simulation, not a comparison against recovered historical single-channel code. The standalone baseline uses the same decoy-BB84 estimator with fixed C3 optical settings, no adaptation and no SDN. Its inter-wavelength crosstalk is removed. Dark counts and classical-traffic Raman-like background remain. All links are 24 km, eliminating the unequal-distance confound in the older four-channel study.','',
        f'{meta["seeds"]} seeds per case/arm, 40 intervals, disturbance onset at interval 6; 1,000 runs with the default 50 seeds. Binomial observations; ML disabled. No live Ryu/Mininet timing, optical multiplexing hardware cost, extra WDM insertion loss or measured controller overhead is included.','',
        '## Estimated accepted network bits per run','',
        '| Condition | Single fixed, 1M pulses/interval | Single fixed, 4M | Fixed WDM, 4 x 1M | Pareto WDM, 4 x 1M |',
        '|---|---:|---:|---:|---:|']
    for case in cases:
        r=means.loc[case]
        lines.append(f'| {case} | {r.single_fixed_1M:,.0f} | {r.single_fixed_4M:,.0f} | {r.wdm_fixed:,.0f} | {r.wdm_pareto:,.0f} |')
    lines+=['','The 1M single-channel arm emits 40M pulses per run; all other arms emit 160M. Comparing Pareto with single-1M includes four times the resources and must not be called an algorithmic efficiency gain. Single-4M is an equal-total-pulse comparator; it assumes a single transmitter/detector can support four times the pulse rate without saturation, dead-time or rate-dependent noise. That assumption needs hardware validation.','',
        '## What caused the difference?','',
        '| Condition | Pareto vs single-4M (equal pulses) | Pareto vs fixed WDM (policy effect) |',
        '|---|---:|---:|']
    for case in cases:
        g=c[c.case==case].set_index('baseline')
        lines.append(f'| {case} | {g.loc["single_fixed_4M","gain_percent"]:+.3f}% | {g.loc["wdm_fixed","gain_percent"]:+.3f}% |')
    lines+=['','Local disturbance affects only wavelength 3 in WDM, but affects the sole single-channel link. Its WDM advantage combines diversity (three unaffected channels) with any policy effect. The shared-4% case applies the same disturbance to all four wavelengths, reducing this confound. Compare Pareto with fixed WDM to isolate the control-policy contribution in this model.','',
        'Normal-operation comparisons are especially important: parallel channels alone need not improve bits per emitted pulse. Statistical fluctuations, clipping of negative rate estimates to zero and different count block sizes can affect the plug-in estimator. Resource-normalized output is recorded in summary.csv.','',
        'The bootstrap intervals in comparison.csv describe seed-level mean differences, not a physical confidence guarantee. Shared seed labels do not create identical observations after architecture or settings change. Cases were evaluated as an exploratory comparison, without multiple-comparison correction.','',
        '## What to explain to the professor','',
        'The project adds wavelength-specific monitoring and an explicit Pareto retuning rule. Four channels provide parallel capacity and can retain unaffected capacity during a localized disturbance. The optimizer contributes only the measured difference from fixed-setting WDM. SDN provides a programmable enforcement mechanism; these throughput simulations do not measure an SDN speed gain. A simpler single-channel system may have lower hardware cost and less crosstalk. Neither architecture is universally superior.','',
        'No final secure keys or new security proof are demonstrated here. The fixed baseline is not an attack detector, so this alignment study does not establish superior attack detection. Physical implementation requires WDM insertion-loss/crosstalk measurements, detector constraints, actual setting-change time and separate live SDN packet tests.','',
        '## Reproduction','',
        'From the project root, using the project Python environment:','',
        '```bash',
        'python -m experiments.single_channel_comparison --seeds 50 --out results/single-channel-recheck',
        'python -m tools.report_single_channel --out results/single-channel-recheck',
        '```','',
        'On Linux use .venv-linux/bin/python; on Windows use .\\.runtime\\python.exe. Open REPORT.md, summary.csv and comparison.csv; runs.csv holds individual outcomes. These new conditions use uniform 24 km links and new seeds, so do not splice their bit totals into the earlier unequal-distance Pareto cohort.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print((out/'REPORT.md').resolve())


if __name__=='__main__':main()
