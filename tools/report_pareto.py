"""Explain the Pareto comparison using saved evidence, with scientific plots."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('results/pareto'))
    args=p.parse_args();root=args.out
    runs=pd.read_csv(root/'runs.csv');summary=pd.read_csv(root/'summary.csv')
    comparisons=pd.DataFrame(json.loads((root/'paired_comparisons.json').read_text()))
    metadata=json.loads((root/'summary.json').read_text())
    candidates=pd.read_csv(root/'candidate_objectives.csv')
    alignment=summary[summary.suite=='alignment']
    changes=comparisons[(comparisons.suite=='alignment')&(comparisons.policy=='pareto')]
    gains=changes[changes.mean_difference>1e-9]
    standard_changes=comparisons[comparisons.suite=='standard'].mean_difference.abs().max()
    get=lambda case,policy:summary[(summary.case==case)&(summary.policy==policy)].iloc[0]
    lines=['# Pareto selection experiment and interpretation','',
        'Pareto selection is now implemented in the project as two explicit policies. `pareto_front` removes dominated candidates and applies the previous 90%-rate/error trade-off rule. `pareto` chooses the largest predicted delivered output on a Pareto front after switching cost, subject to the same illustrative QBER cap and existing isolation checks.','',
        'The method follows the presentation idea of comparing error and key-rate objectives, but specifies a unique operating-point rule. A front is a set of alternatives: by itself it cannot tell the controller which point to use. Better throughput may require accepting a slightly higher error rate within the operating constraints.','',
        f'Observed outcome: the delivered-output policy improved the mean in **{len(gains)} of seven** declared alignment cases, with network-wide gains from **{gains.relative_percent.min():.2f}% to {gains.relative_percent.max():.2f}%** in those cases. The other four alignment cases were unchanged. The greatest absolute mean difference in the original eighteen standard scenarios was {standard_changes:.1f} estimated bits: those results were unchanged. Front extraction while keeping the previous rule produced no throughput improvement.','',
        '## How the algorithm works','',
        '1. Predict QBER and asymptotic key rate for each independently calibrated C1–C5 configuration.',
        '2. Keep positive-rate candidates with predicted QBER no greater than 11%. That cap is an operating rule, not a security proof.',
        '3. Compute output over H future intervals. Staying in the current setting gives rate × H. Switching gives rate × (H − 0.25), charging the modeled settling loss. H is at most eight and cannot exceed the run’s remaining intervals.',
        '4. Remove a setting if another has both no higher predicted QBER and no smaller predicted delivered output, with a strict improvement in at least one objective.',
        '5. Choose the front point with highest delivered output; use lower QBER and then deterministic configuration ordering to break ties. Switch only if predicted delivered output improves by more than 1%, at least two trial intervals remain, and the analytical check agrees.',
        '6. Apply the existing two-window verification, rollback and cooldown. Anomalies, invalid telemetry and latched isolation are handled before selection. Pareto cannot resume a quarantined wavelength.','',
        'The audit in `selection_audit` records all feasible candidate scores, front membership, the chosen setting, horizon and cost. The current setting receives no switching charge. The `pareto_front` ablation deliberately retains the old selection and horizon rules so that front pruning can be tested separately.','',
        '## Experiment design','',
        f'Total: **{len(runs):,} runs**. Two separately reported cohorts were predeclared in `pareto_experiments.py`:','',
        f'- Standard scenarios: {metadata["standard_seeds"]} fresh seeds per case and policy, 18 scenarios, three policies (`hybrid`, `pareto_front`, `pareto`), 18 intervals, 100,000 pulses per wavelength per interval.',
        f'- Measured alignment grid: {metadata["alignment_seeds"]} fresh seeds per case and policy, seven declared alignment-error values (2%, 2.5%, 3%, 3.5%, 4%, 4.5%, 5%), four policies (also `uncertainty`), 40 intervals, 1,000,000 pulses per wavelength per interval.',
        '- Disturbances start at interval 6 and affect wavelength 3 in the alignment grid. Calibration includes every tested configuration/context and uses separate seeds. Runtime labels are not given to the controller.',
        '- All policies share the same per-cohort monitoring budget, observations model, candidate grid and output-accounting convention. ML is disabled; the measurement engine is binomial, not Aer.',
        '- The alignment cohort deliberately tests conditions between the previous study’s nominal and 5% alignment values. This is expanded validation, not a rerun of the exact previous 2,160-run study. Results from the cohorts must not be pooled into an unqualified improvement percentage.','',
        '## Measured output comparisons','',
        'The table reports average estimated accepted bits across all four wavelengths over an entire 40-interval run. Percent changes compare `pareto` with the existing `hybrid`, which already retunes.','',
        '| Reported alignment error | Existing hybrid | Pareto front with old rule | Pareto delivered-output rule | Change versus hybrid |',
        '|---|---:|---:|---:|---:|']
    for case in sorted(alignment.case.unique()):
        h=get(case,'hybrid');f=get(case,'pareto_front');n=get(case,'pareto')
        change=100*(n.mean_estimated_bits-h.mean_estimated_bits)/h.mean_estimated_bits
        label=100*float(case.split('_')[1])
        lines.append(f'| {label:g}% | {h.mean_estimated_bits:,.1f} | {f.mean_estimated_bits:,.1f} | {n.mean_estimated_bits:,.1f} | {change:+.3f}% |')
    lines+=['','The front-only comparison is important: if its result equals hybrid, front extraction itself did not create a throughput gain. Any difference with the delivered-output policy also includes its explicit throughput preference and remaining-horizon switching guard. It must not be attributed to the dominance operation alone.','',
        '## Uncertainty and the error trade-off','',
        '| Alignment error | Mean paired difference in estimated bits | Descriptive bootstrap 95% interval | Seeds better / same / worse | Mean target QBER hybrid → Pareto |',
        '|---|---:|---|---|---|']
    for row in comparisons[(comparisons.suite=='alignment')&(comparisons.policy=='pareto')].itertuples():
        h=get(row.case,'hybrid');n=get(row.case,'pareto')
        label=100*float(row.case.split('_')[1])
        lines.append(f'| {label:g}% | {row.mean_difference:+,.1f} | [{row.bootstrap_low:+,.1f}, {row.bootstrap_high:+,.1f}] | {row.improved_seeds} / {row.same_seeds} / {row.worse_seeds} | {100*h.mean_target_qber:.4f}% → {100*n.mean_target_qber:.4f}% |')
    lines += ['','Target QBER is the observed, count-weighted error fraction over unblocked target-channel intervals after onset, averaged across seeds. It is diagnostic, not a security bound. The bootstrap resamples seed-level paired differences; its intervals are descriptive, not corrected for multiple scenarios. Shared seeds do not guarantee identical draws after different configurations are selected.','',
        'A positive mean with an interval crossing zero is inconclusive for a positive average gain in this experiment. An interval above zero supports a gain within the sampled model and conditions. It does not predict physical hardware performance or demonstrate a finite-key throughput gain.','',
        '## Standard scenarios and isolation','',
        '| Scenario | Hybrid isolation runs | Pareto isolation runs | Hybrid / Pareto hold runs | Hybrid / Pareto mean target isolation delay |',
        '|---|---:|---:|---|---|']
    for case in sorted(summary[summary.suite=='standard'].case.unique()):
        h=get(case,'hybrid');n=get(case,'pareto')
        delay=lambda x:'N/A' if pd.isna(x) else f'{x:.2f}'
        lines.append(f'| {case} | {h.isolated_runs}/{h.runs} | {n.isolated_runs}/{n.runs} | {h.hold_runs} / {n.hold_runs} | {delay(h.mean_target_delay)} / {delay(n.mean_target_delay)} |')
    lines+=['','The isolation rules are unchanged, but different optical settings can change later statistical observations. The saved results, rather than an assumption, determine whether decisions match. A delay for benign model mismatch is anomaly-response timing, not attack identification. Correlated hidden drift is still a benign false-quarantine test. Pareto tuning does not solve that monitoring limitation.','',
        '## Computational efficiency','',
        f'The local selector microbenchmark measured a median of **{metadata["timing"]["hybrid_median_microseconds"]:.2f} microseconds** for the existing selector and **{metadata["timing"]["pareto_median_microseconds"]:.2f} microseconds** for the delivered-output Pareto selector. Each includes analytical scoring of five candidates; the Pareto version also constructs its audit. Calibration, full controller bookkeeping, Ryu and network latency are excluded.',
        'These are seven batches of 1,000 calls on this machine and can vary with scheduling and hardware. With only five candidates, pairwise front extraction is O(K²) and adds work. Do not claim that this implementation accelerates the controller. Its purpose is a visible operating trade-off and cost-aware selection.','',
        '## How to see and interpret the results','',
        '- Open `results/pareto/summary.csv` to compare policies at each alignment value. Check the cohort (`suite`) before comparing rows.',
        '- Open `results/pareto/paired_comparisons.json` for uncertainty intervals and how many seeds improved or worsened.',
        '- Open `results/pareto/candidate_objectives.csv` for predicted candidate errors, rates, delivered output and front membership.',
        '- Open `results/pareto/alignment_0.030-pareto-example.csv` and its `hybrid` counterpart. Follow wavelength 3 at intervals 6 onward; compare `config`, `next_config`, `action` and `selection_audit`.',
        '- `pareto_front.png` explains one declared operating point. `output_comparison.png` shows repeated-run estimated output changes, not secret-key generation.',
        '- Reproduce from the project root with `python -m experiments.pareto_experiments --out results/pareto-recheck`, then `python -m tools.report_pareto --out results/pareto-recheck`. Use the project Python environment. Existing results are preserved by using a new output folder.','',
        'In the first saved 3% alignment seed, the Pareto controller proposes C2 at interval 6, verifies at 7 and rolls back at 8. The noisy two-window test fails even though the analytical model predicts an improvement. This example is deliberately retained: a front prediction is not a guarantee of improvement in every run, and the existing trial rule can reject a beneficial model prediction or incur repeated switching costs.','',
        'For a standard scenario, run `.\\.runtime\\python.exe run.py network --policy pareto --engine binomial --scenario misalignment --steps 40 --pulses 1000000 --out results/pareto-demo`. That named scenario uses 5% alignment; the separate grid script covers the intermediate values. The same `--policy pareto` choice is available in the Linux Mininet/Ryu monitor. Live Linux validation remains pending.','',
        '## Limits of the claim','',
        'The policy chooses among five illustrative decoy intensity settings. It does not correct the physical polarization/phase drift or perform optical rerouting. The error constraint and anomaly tests do not replace finite-key security analysis. The output metric uses the existing asymptotic rate estimator; no final secure keys are generated by these experiments. Raman/FWM and detector physics remain simplified. Positive results here justify testing the operating-point rule further, not promising a physical improvement of the same size.']
    (root/'PARETO_RESULTS_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    plot(root,comparisons,candidates)
    print(f'Wrote {root}/PARETO_RESULTS_REPORT.md and plots')


def plot(root,comparisons,candidates):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    c=candidates[np.isclose(candidates.alignment,.03)]
    fig,ax=plt.subplots(figsize=(9,5.5))
    dominated=c[~c.on_front];efficient=c[c.on_front].sort_values('qber')
    ax.scatter(100*dominated.qber,dominated.delivered_bits,c='gray',marker='x',s=70,label='Dominated')
    ax.plot(100*efficient.qber,efficient.delivered_bits,'o-',label='Pareto front')
    for row in c.itertuples():ax.annotate(row.config,(100*row.qber,row.delivered_bits),xytext=(5,7),textcoords='offset points')
    for name,marker,label in [('C3','s','Current / previous rule: C3'),('C2','*','Delivered-output choice: C2')]:
        row=c[c.config==name].iloc[0]
        ax.scatter(100*row.qber,row.delivered_bits,marker=marker,s=180,facecolors='none',edgecolors='black',label=label)
    ax.set(xlabel='Predicted signal QBER (%) — lower is preferred',ylabel='Predicted accepted bits over next 8 intervals',
           title='Trade-off at reported 3% misalignment on wavelength 3')
    ax.legend(fontsize=9);ax.grid(alpha=.2)
    fig.text(.5,.015,'Analytical predictions at 1M pulses/interval; changed settings pay a 0.25-interval cost.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(root/'pareto_front.png',dpi=160);plt.close(fig)
    comp=comparisons[(comparisons.suite=='alignment') & (comparisons.policy=='pareto')].sort_values('case')
    x=np.arange(len(comp));fig,ax=plt.subplots(figsize=(9,5))
    ax.bar(x,comp.relative_percent,color='#32688e')
    low=100*comp.bootstrap_low/comp.baseline_mean;high=100*comp.bootstrap_high/comp.baseline_mean
    ax.errorbar(x,comp.relative_percent,yerr=[np.maximum(0,comp.relative_percent-low),np.maximum(0,high-comp.relative_percent)],fmt='none',ecolor='black',capsize=4)
    ax.axhline(0,color='black',linewidth=.7)
    ax.set(xticks=x,xticklabels=[f'{100*float(s.split("_")[1]):g}%' for s in comp.case],
        xlabel='Reported misalignment parameter',ylabel='Change in mean estimated accepted network bits (%)',
        title='Pareto delivered-output rule compared with existing hybrid')
    fig.text(.5,.01,'50 seeds per case; descriptive paired-bootstrap 95% intervals; simulation estimates.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(root/'output_comparison.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
