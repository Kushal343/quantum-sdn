"""Normal-operation reference matched to the previously frozen Pareto grid.

Same 50 runtime/calibration seeds, 40 intervals, one million pulses per
wavelength/interval, and the same calibration contexts as the alignment study.
The existing alignment observations are read without modification.
"""
import argparse
import json
from pathlib import Path
import pandas as pd
from qkd_sdn.monitoring import calibrate
from experiments.pareto_experiments import MeasuredAlignment,alignment_contexts,one_run,summarize


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=50)
    p.add_argument('--out',type=Path,default=Path('results/normal-comparison'))
    p.add_argument('--pareto-results',type=Path,default=Path('results/pareto'))
    args=p.parse_args()
    if args.seeds<1:p.error('Seeds must be positive')
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for j in range(args.seeds):
        cal=calibrate(alignment_contexts(),seed=15100+j)
        for policy in ('uncertainty','hybrid','pareto_front','pareto'):
            row,frame=one_run('matched_normal','normal',7100+j,cal,policy,40,1000000,.015)
            rows.append(row)
            if j==0:frame.to_csv(args.out/f'normal-{policy}-example.csv',index=False)
        print(f'Normal reference seed {j+1}/{args.seeds}',flush=True)
    runs=pd.DataFrame(rows);runs.to_csv(args.out/'runs.csv',index=False)
    summary=summarize(runs);summary.to_csv(args.out/'summary.csv',index=False)
    comparisons=[]
    old=pd.read_csv(args.pareto_results/'runs.csv')
    old=old[(old.suite=='alignment') & old.seed.isin(runs.seed.unique())]
    normal=runs.pivot(index='seed',columns='policy',values='estimated_bits')
    for case in sorted(old.case.unique()):
        grid=old[old.case==case].pivot(index='seed',columns='policy',values='estimated_bits')
        if set(grid.index)!=set(normal.index):raise ValueError('Alignment/normal seeds do not match')
        base=float(normal.hybrid.mean())
        h=float(grid.hybrid.mean());n=float(grid.pareto.mean())
        comparisons.append(dict(case=case,normal_mean=base,hybrid_mean=h,pareto_mean=n,
            pareto_improvement_percent=100*(n-h)/h,
            hybrid_loss_vs_normal_percent=100*(base-h)/base,
            pareto_loss_vs_normal_percent=100*(base-n)/base))
    metadata=dict(seeds=args.seeds,steps=40,pulses=1000000,normal_misalignment=.015,
        runtime_seed_start=7100,calibration_seed_start=15100,
        calibration_contexts='same expanded grid as original Pareto alignment cohort',
        scope='Matched operational binomial-model reference; asymptotic estimates, not distilled secure keys',
        summary=json.loads(summary.to_json(orient='records')),comparisons=comparisons)
    (args.out/'summary.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    pd.DataFrame(comparisons).to_csv(args.out/'comparison.csv',index=False)
    print(summary.to_string(index=False),flush=True)


if __name__=='__main__':main()
