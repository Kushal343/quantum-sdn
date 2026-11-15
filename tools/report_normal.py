"""Create a professor briefing and matched-normal comparison from saved data."""
import argparse,json
from pathlib import Path
import pandas as pd


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('results/normal-comparison'))
    p.add_argument('--pareto-results',type=Path,default=Path('results/pareto'))
    p.add_argument('--brief',type=Path,default=Path('reports/PROFESSOR_BRIEF.md'))
    args=p.parse_args()
    meta=json.loads((args.out/'summary.json').read_text())
    comparison=pd.DataFrame(meta['comparisons'])
    normal=pd.read_csv(args.out/'summary.csv')
    reference=float(normal[normal.policy=='hybrid'].mean_estimated_bits.iloc[0])
    pareto_meta=json.loads((args.pareto_results/'summary.json').read_text())
    normal_runs=int(normal.runs.sum())
    seeds=int(meta['seeds'])
    expected_policies={'uncertainty','hybrid','pareto_front','pareto'}
    if set(normal.policy)!=expected_policies or not normal.runs.eq(seeds).all():
        raise ValueError('Expected a complete, balanced four-policy normal reference')
    if not normal.mean_estimated_bits.eq(reference).all() or normal[['mean_retunes','mean_rollbacks','isolated_runs','hold_runs']].to_numpy().any():
        raise ValueError('Normal outcomes changed; review the interpretation before generating this briefing')
    lines=['# Normal operation comparison and professor briefing','',
        'The project demonstrates operational monitoring and parameter control in a simulated four-wavelength QKD system. The main contribution is the decision process and its measured trade-offs, rather than a new quantum protocol or a hardware performance claim.','',
        '## Normal operation and degradation','',
        f'A new matched healthy reference uses {seeds} seeds, {meta["steps"]} intervals, {meta["pulses"]:,} pulses per wavelength per interval and the same calibration contexts and runtime/calibration seeds as the existing Pareto alignment grid. This adds {normal_runs:,} normal-reference runs. The referenced Pareto comparison contains {pareto_meta["total_runs"]:,} runs; they are kept as separate evidence files. The inference horizon and pulse budget are the same within this normal/alignment comparison.','',
        f'Healthy operation has nominal misalignment of 1.5%. `uncertainty`, `hybrid`, `pareto_front` and `pareto` all produced **{reference:,.1f} estimated accepted network bits per run**, with zero retunes, holds or isolations in all {seeds} runs per policy. Pareto provided **0% improvement** in healthy operation. This is a useful result: unnecessary reconfiguration would incur cost without improving an already suitable setting.','',
        '| Reported misalignment parameter | Hybrid estimated bits/run | Pareto estimated bits/run | Pareto gain over hybrid | Pareto deficit from healthy operation |',
        '|---|---:|---:|---:|---:|',
        f'| Healthy nominal 1.5% | {reference:,.1f} | {reference:,.1f} | 0.00% | 0.00% |']
    for row in comparison.itertuples():
        label=100*float(row.case.split('_')[1])
        lines.append(f'| {label:g}% | {row.hybrid_mean:,.1f} | {row.pareto_mean:,.1f} | {row.pareto_improvement_percent:+.3f}% | {row.pareto_loss_vs_normal_percent:.2f}% |')
    lines += ['','These percentages answer different questions. Gain over hybrid measures the extra output from the new selection rule under the same disturbance. Deficit from healthy operation measures how much degradation remains. A positive Pareto gain does not mean the physical disturbance has disappeared or normal performance has been restored.','',
        'The alignment value is a model parameter, not exactly the measured QBER. At 3% reported misalignment, mean observed target QBER rose from about 3.0783% under hybrid to 3.0939% under Pareto. The new policy trades that small error increase for higher estimated output. These means include only usable target-channel intervals after onset.','',
        '## What was contributed theoretically','',
        '1. A conditional monitoring method for each wavelength, using independent benign calibration rather than treating normal probabilities as perfectly known. Six detection/error checks are made for each wavelength and setting.',
        '2. Exact count intervals and composite-null binomial tests with an explicit finite-horizon operational alarm budget. This handles sparse observations and accounts for calibration uncertainty under the declared count model.',
        '3. An ordered decision policy: telemetry validity, anomaly evidence, uncertainty holds, persistent quarantine, recovery, then optional adaptation. A low network-average QBER cannot override a local anomaly.',
        '4. Explicit Pareto nondominance between predicted QBER and output, followed by a deterministic operating-point rule that charges settling cost and respects remaining verification time. A front alone does not select an operating point.',
        '5. Separate implementations of published finite-key bounds and classical-protocol demonstrations. These are existing-theorem implementations under stated assumptions, not a new composable security proof for the full monitoring project.','',
        '## What was demonstrated experimentally','',
        '- The original combined-policy study comprised 2,160 simulation runs. Both old adaptive and hybrid isolated tested strong/weak interception and hidden attenuation in 20/20 runs each. Hybrid reduced mean weak-interception isolation delay from 1.80 to 1.15 intervals, without isolating unaffected wavelengths in those cases.',
        f'- The archived follow-up Pareto study comprised 2,480 runs: 1,080 standard-scenario runs and 1,400 alignment-grid runs. It used new evaluation seeds. The normal reference supplied to this report comprises {normal_runs:,} runs.',
        '- Pareto delivered-output selection improved network-wide estimated output over hybrid by 0.62%, 0.33% and 0.75% at reported 3%, 3.5% and 4% misalignment. Fifty seeds were used per alignment/policy case. Descriptive paired-bootstrap intervals for the three mean differences were above zero; other grid cases showed no change.',
        '- Extracting the Pareto front while retaining the old rule produced no improvement. The gain comes from the declared operating-point preference and cost/horizon treatment, not from dominance pruning alone.',
        '- The original eighteen standard scenarios showed no output change after adding Pareto selection. Its attack-detection logic was not improved by the optimizer.',
        '- Separate Aer runs checked circuit-based integration. The larger repeated studies used the binomial count engine for the independent symmetric model. They did not transmit physical photons.',
        '- The reorganized software passes 81 tests. Linux Ryu/Mininet code is supplied; image startup and live packet tests still need Linux execution. A passing software test is not a physical security validation.','',
        '## The failure result that must be presented','',
        'In the earlier hybrid study, hidden benign correlated drift caused unnecessary permanent isolation in 6/20 hybrid runs versus 1/20 previous-adaptive runs. The later Pareto standard cohort used different seeds and had 2/20 false-isolation runs for both hybrid and Pareto. These numbers must not be interpreted as Pareto reducing the earlier 6/20 rate: the seed cohorts differ, and Pareto made no change within its own matched comparison.',
        'The system recognizes a mismatch with its model. It cannot reliably attribute that mismatch to an attacker. Correlated noise, inaccurate context information and physical detector effects remain important limitations.','',
        '## A short explanation to give the professor','',
        'We built a simulation of four independently monitored QKD wavelengths and compared operational control policies under shared experimental conditions. Our controller uses calibrated count uncertainty to decide whether to continue, temporarily hold, isolate or retune one wavelength. We made the Pareto selection rule explicit and included switching and verification costs. Under healthy conditions it made no unnecessary changes. Under three tested alignment conditions it improved estimated accepted output by roughly 0.3% to 0.75% over the existing adaptive controller, while preserving its anomaly checks. The result is partial recovery, with a small error-rate trade-off. Hidden benign drift can still cause false isolation. We have not established physical gains or an independently reviewed end-to-end WDM security proof.','',
        '## What not to claim','',
        'Do not call 20/20 observed successes a guaranteed 100% detection rate. Do not describe asymptotic estimated bits as actually generated secure keys. Do not credit ML for the Pareto study: ML was disabled. Do not call the 11% operating cap a complete security acceptance rule. Do not describe VLAN blocking as optical photon isolation. Do not claim that decoy intensity retuning repairs polarization drift or creates an alternate optical route.','',
        '## How to show the evidence','',
        '1. Show `normal-comparison/comparison.csv` and `normal_vs_degradation.png`: normal operation first, then degradation and partial recovery.',
        '2. Show `pareto/pareto_front.png`: explain why two points can both be nondominated and why a selection rule is needed.',
        '3. Show the held/isolated target trace in `hybrid/intercept-example.csv`: only wavelength 3 is stopped in the demonstrated local case.',
        '4. Show the correlated-drift failure before stating the final scope. Explain that actual finite-key security and live optical control are separate validation tasks.','',
        '## Reproduce on Linux','',
        'Run from the organized project root with its Linux Python environment:','',
        '```bash',
        '.venv-linux/bin/python -m experiments.pareto_experiments --out results/pareto-recheck',
        '.venv-linux/bin/python -m tools.report_pareto --out results/pareto-recheck',
        '.venv-linux/bin/python -m experiments.normal_comparison --seeds 50 \\',
        '  --pareto-results results/pareto-recheck --out results/normal-recheck',
        '.venv-linux/bin/python -m tools.report_normal --out results/normal-recheck \\',
        '  --pareto-results results/pareto-recheck --brief reports/PROFESSOR_BRIEF_RECHECK.md',
        '```','',
        'For installation and live Ryu/Mininet commands, read `linux/README.md`. The existing results can be opened without rerunning anything. The matched normal script reads the saved alignment cohort and writes its own files; it does not modify the earlier experiment.']
    text='\n'.join(lines)+'\n'
    (args.out/'COMPARISON_REPORT.md').write_text(text,encoding='utf-8')
    args.brief.parent.mkdir(parents=True,exist_ok=True);args.brief.write_text(text,encoding='utf-8')
    plot(args.out,comparison,reference,seeds)
    print('Normal reference:',round(reference,1),'estimated network bits/run')
    print(comparison.to_string(index=False))
    print('Wrote',args.brief)


def plot(out,comparison,normal,seeds):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    selected=comparison[comparison.case.isin(['alignment_0.030','alignment_0.035','alignment_0.040'])]
    h=[normal]+selected.hybrid_mean.tolist();p=[normal]+selected.pareto_mean.tolist()
    x=np.arange(4);fig,ax=plt.subplots(figsize=(10,5))
    ax.bar(x-.18,np.array(h)/1000,width=.36,label='Existing hybrid')
    ax.bar(x+.18,np.array(p)/1000,width=.36,label='Pareto delivered-output rule')
    ax.set(xticks=x,xticklabels=['Healthy 1.5%','3% alignment','3.5% alignment','4% alignment'],
        ylabel='Mean estimated accepted network bits per run (thousands)',ylim=(0,900),
        title='Normal operation compared with measured degradation')
    for i in range(4):ax.text(i,max(h[i],p[i])/1000+12,'0%' if i==0 else f'+{100*(p[i]-h[i])/h[i]:.2f}%',ha='center',fontsize=10)
    ax.legend(loc='lower left');ax.grid(axis='y',alpha=.2)
    fig.text(.5,.015,f'{seeds} matched seeds; 40 intervals; 1M pulses/wavelength/interval. Labels are gains over hybrid.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(out/'normal_vs_degradation.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
