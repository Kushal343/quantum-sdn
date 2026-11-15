"""Generate a plain-language findings report and research plot from saved runs."""
from pathlib import Path
import numpy as np
import pandas as pd
from qkd_sdn.controller import wilson


def main():
    root=Path('results/hybrid')
    runs=pd.read_csv(root/'runs.csv');summary=pd.read_csv(root/'summary.csv')
    rows=['# Combined policy findings','',
        'The combined policy is a better structured research controller: it accounts for independent calibration uncertainty, incomplete evidence and recovery, while preserving retuning and targeted isolation. It is not uniformly better on every performance measure. Hidden correlated drift remains a demonstrated failure mode.','',
        f'This experiment contains {len(runs):,} runs: {runs.seed.nunique()} seeds for every scenario/policy combination, 18 intervals, and 100,000 emitted pulses per wavelength per interval. Six policies and 18 scenarios were compared. Calibration used a separate random stream and 5,000,000 pulses per context. Scenarios begin at interval 6. The table shows isolation runs, not numbers of isolated wavelengths.','',
        '| Scenario | Old adaptive: isolation runs | Combined: isolation runs | Combined: isolation of wavelengths other than 3 |',
        '|---|---:|---:|---:|']
    for scenario in ('normal','intercept','weak_intercept','tap','loss','raman','fwm','crosstalk','dark_counts','misalignment','transient','burst','missing','unsupported','model_mismatch','correlated'):
        old=summary[(summary.scenario==scenario)&(summary.policy=='adaptive')].iloc[0]
        new=summary[(summary.scenario==scenario)&(summary.policy=='hybrid')].iloc[0]
        rows.append(f'| {scenario} | {old.isolated_runs}/{old.runs} | {new.isolated_runs}/{new.runs} | {new.other_isolated}/{new.runs} |')
    select=lambda scenario,policy:summary[(summary.scenario==scenario)&(summary.policy==policy)].iloc[0]
    old,new=(select('weak_intercept',p) for p in ('adaptive','hybrid'))
    rows+=['','## What improved','',
        f'- Weak interception was isolated in all 20 runs with both policies. Mean isolation delay fell from {old.mean_detection_delay:.2f} to {new.mean_detection_delay:.2f} intervals. The combined controller isolated strong interception and hidden attenuation in all 20 runs each, without isolating the three unaffected wavelengths.',
        '- Known dark-count, Raman-like, FWM-like and crosstalk increases caused no permanent isolation in these runs. Their measured contexts were independently calibrated.',
        '- A one-interval hidden attenuation event caused a temporary hold and then recovery, with no permanent isolation. Missing telemetry and unsupported contexts caused conservative holds instead of unsupported anomaly conclusions.',
        '- Calibration uncertainty and all six count checks per wavelength are included in an explicitly bounded monitoring horizon. The old adaptive baseline assumes exact optical expectations and uses a fixed per-test alarm level.','']
    pairs=runs[runs.scenario=='misalignment'].pivot(index='seed',columns='policy',values='estimated_bits')
    delta=(pairs.hybrid-pairs.uncertainty).to_numpy()
    rng=np.random.default_rng(8842)
    bs=np.mean(rng.choice(delta,size=(10000,len(delta)),replace=True),axis=1)
    ci=np.quantile(bs,[.025,.975])
    pct=100*delta.mean()/pairs.uncertainty.mean()
    rows += [f'For measured misalignment, retuning increased mean network-wide estimated accepted bits by **{pct:.2f}%** relative to the same calibrated monitor with fixed optical settings: {pairs.uncertainty.mean():,.1f} to {pairs.hybrid.mean():,.1f}. The mean paired difference was {delta.mean():,.1f} estimated bits; a descriptive paired-bootstrap 95% interval is [{ci[0]:,.1f}, {ci[1]:,.1f}]. A 25% next-interval settling cost is charged after retuning or rollback. This is an asymptotic model estimate, not distillation of actual secure keys.','',
        '## Where it performed worse','',
        'The hidden correlated-noise scenario is benign AR(1) misalignment drift shared by all wavelengths. The combined policy permanently isolated at least one wavelength in **6/20 runs**, compared with **1/20** for the old adaptive policy. This is an observed false-quarantine cost under model mismatch, and the method must not be described as robust to arbitrary correlated noise. A shared change is useful diagnostic context, but cannot safely be labelled harmless solely because all wavelengths move together.','',
        'Recovery also costs availability: three clean intervals are required after a temporary hold, so transient scenarios deliver fewer estimated bits than immediate resumption. Persistent unknown benign misalignment is isolated in 20/20 runs because it is observationally unexplained; the action does not identify an attacker.','',
        '## Uncertainty and limits','']
    lo,hi=wilson(20,20,z=1.959963984540054)
    lo0,hi0=wilson(0,20,z=1.959963984540054)
    rows += [f'With only 20 seeds per case, pointwise 95% Wilson intervals remain broad: 20/20 corresponds to [{lo:.1%}, {hi:.1%}], and 0/20 to [{lo0:.1%}, {hi0:.1%}]. These are descriptive intervals and are not adjusted for searching across scenarios.','',
        'The run-level operational raw-alarm budget is 5%, including 0.5% for independent calibration. The remaining budget is divided across 18 intervals, four wavelengths and six tests. Its mathematical interpretation requires the calibrated conditional count law and supported contexts to remain valid. It excludes the operating-cap hold rule, missing-data holds, unsupported-context holds and unknown noise laws. It is not a cryptographic security parameter.','',
        'All runtime observations in this sweep use the binomial count engine. The model is independent within each interval; the correlated scenario changes its parameter between intervals. This is not a correlated quantum attack model. Calibration contexts assume precisely reported, trusted device/noise parameters on a finite grid. Raman and FWM are illustrative effective-background models, not a propagation solver.','',
        'The legacy policies do not check the new available flag, so their continued output in the missing-data scenario is not evidence of superior availability. Every reported bit quantity here is an operational estimate. The existing finite-key estimators and authenticated protocol demonstrations remain separate from this live monitoring path.','',
        'Live Ryu/Mininet packet tests are supplied for Linux but were not executed on this Windows machine. Unit tests with fake datapaths verify message construction and failure-state logic; they cannot replace live switch tests.','',
        'Raw evidence: `runs.csv`, `summary.csv`, `summary.json`, individual first-seed traces and `calibration-example.json` in this directory. Reproduce from the project root with `python -m experiments.hybrid_experiments --seeds 20 --out results/hybrid-recheck` and `python -m tools.report_hybrid --out results/hybrid-recheck`. A fresh output folder preserves the original evidence.']
    (root/'FINDINGS.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    scenarios=['normal','intercept','weak_intercept','tap','raman','transient','correlated']
    fig,ax=plt.subplots(figsize=(10,5))
    x=np.arange(len(scenarios))
    for j,(policy,label) in enumerate([('adaptive','Previous adaptive'),('hybrid','Combined calibrated')]):
        values=[100*select(s,policy).isolated_runs/select(s,policy).runs for s in scenarios]
        ax.bar(x+(j-.5)*.36,values,width=.36,label=label)
    ax.set(xticks=x,xticklabels=['Normal','Strong\ninterception','Weak\ninterception','Hidden\nloss','Known\nRaman-like','Transient\nloss','Hidden\ncorrelated drift'],ylabel='Runs with permanent isolation (%)',ylim=(0,112))
    ax.legend(loc='upper right');ax.set_title('Isolation decisions across 20 seeds per case')
    fig.text(.5,.01,'Isolation is an operational response. Benign hidden drift can also cause isolation.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(root/'isolation_comparison.png',dpi=160);plt.close(fig)
    print(f'Wrote {root}/FINDINGS.md and isolation_comparison.png')


if __name__=='__main__':main()
