"""Frozen Pareto comparisons: existing scenarios plus a declared alignment grid.

No thresholds are fit to these evaluation seeds. The only new intervention is
candidate selection and its remaining-horizon switching decision.
"""
import argparse
import json
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from qkd_sdn.physics import Channel,CANDIDATES,Decoy,expected
from qkd_sdn.controller import select_configuration
from qkd_sdn.monitoring import calibrate
from qkd_sdn.noise import known_contexts,NOISE_SCENARIOS
from qkd_sdn.pareto import select
from run import run_network

ALIGNMENTS=(.02,.025,.03,.035,.04,.045,.05)


class MeasuredAlignment:
    def __init__(self,alignment):self.alignment=alignment

    def observe(self,sim,config,step,wavelength):
        ch=Channel(distance_km=20+wavelength*2)
        if wavelength==2 and step>=6:ch=replace(ch,misalignment=self.alignment)
        t=sim.observe(ch,config)
        t.update(window=step,available=True)
        return t


def alignment_contexts():
    yield from known_contexts()
    for alignment in ALIGNMENTS:
        for cfg in CANDIDATES:
            yield Channel(distance_km=24,misalignment=alignment),cfg


def one_run(suite,case,seed,calibration,policy,steps,pulses,alignment=None):
    start=perf_counter()
    frame,meta=run_network(case,steps,seed,pulses,policy,engine='binomial',calibration=calibration,
        scenario_source=MeasuredAlignment(alignment) if alignment is not None else None)
    elapsed=perf_counter()-start
    isolated=frame[frame.action=='isolate']
    target=isolated[isolated.channel=='lambda_3']
    usable=frame[(frame.channel=='lambda_3') & (frame.interval>=6) &
                 ~frame.action.isin(['hold','isolate','isolated'])]
    row=dict(suite=suite,case=case,seed=seed,policy=policy,alignment=alignment,
        steps=steps,pulses=pulses,estimated_bits=meta['estimated_released_bits'],
        target_qber=float(usable.errors.sum()/usable.sample_size.sum()) if usable.sample_size.sum() else None,
        retunes=meta['retunes'],rollbacks=int((frame.action=='rollback').sum()),
        isolated=bool(len(isolated)),target_isolated=bool(len(target)),
        other_isolated=bool((isolated.channel!='lambda_3').any()),
        hold=bool((frame.action=='hold').any()),
        target_delay=int(target.interval.min()-6) if len(target) else None,
        wall_seconds=elapsed)
    return row,frame


def candidate_audit():
    rows=[]
    for alignment in ALIGNMENTS:
        ch=Channel(distance_km=24,misalignment=alignment)
        scores=[(c,*expected(c,ch,1_000_000)) for c in CANDIDATES]
        chosen,audit=select(scores,Decoy(),8)
        old=select_configuration(ch,1_000_000,'high_qber')
        for point in audit['candidates']:
            rows.append(dict(alignment=alignment,**point,
                current=point['config']=='C3',old_proposal=old.name if old else None,
                pareto_proposal=chosen.name if chosen else None))
    return pd.DataFrame(rows)


def summarize(frame):
    return frame.groupby(['suite','case','policy'],sort=True).agg(
        runs=('seed','size'),mean_estimated_bits=('estimated_bits','mean'),
        mean_target_qber=('target_qber','mean'),mean_retunes=('retunes','mean'),
        mean_rollbacks=('rollbacks','mean'),isolated_runs=('isolated','sum'),
        target_isolated=('target_isolated','sum'),other_isolated=('other_isolated','sum'),
        hold_runs=('hold','sum'),mean_target_delay=('target_delay','mean')).reset_index()


def paired_statistics(frame):
    rng=np.random.default_rng(8843)
    rows=[]
    for (suite,case),group in frame.groupby(['suite','case'],sort=True):
        pairs=group.pivot(index='seed',columns='policy',values='estimated_bits')
        for policy in ('pareto_front','pareto'):
            delta=(pairs[policy]-pairs.hybrid).to_numpy()
            boots=np.mean(rng.choice(delta,size=(10000,len(delta)),replace=True),axis=1)
            lower,upper=np.quantile(boots,[.025,.975])
            rows.append(dict(suite=suite,case=case,policy=policy,seeds=len(delta),
                baseline_mean=float(pairs.hybrid.mean()),new_mean=float(pairs[policy].mean()),
                mean_difference=float(delta.mean()),relative_percent=float(100*delta.mean()/pairs.hybrid.mean()),
                bootstrap_low=float(lower),bootstrap_high=float(upper),
                improved_seeds=int((delta>1e-9).sum()),same_seeds=int((abs(delta)<=1e-9).sum()),
                worse_seeds=int((delta < -1e-9).sum())))
    return rows


def timing():
    ch=Channel(distance_km=24,misalignment=.03)
    current=Decoy()
    # Include identical model scoring in both timed selectors, exclude calibration
    # and controller bookkeeping. These are local microbenchmarks, not SDN latency.
    records={}
    for name in ('hybrid','pareto'):
        samples=[]
        for repeat in range(7):
            start=perf_counter()
            for i in range(1000):
                if name=='hybrid':select_configuration(ch,1_000_000,'high_qber')
                else:select([(c,*expected(c,ch,1_000_000)) for c in CANDIDATES],current,8)
            samples.append((perf_counter()-start)/1000)
        records[name+'_median_microseconds']=float(np.median(samples)*1e6)
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite',choices=['all','alignment','standard'],default='all')
    p.add_argument('--alignment-seeds',type=int,default=50)
    p.add_argument('--standard-seeds',type=int,default=20)
    p.add_argument('--out',type=Path,default=Path('results/pareto'))
    args=p.parse_args()
    if min(args.alignment_seeds,args.standard_seeds)<1:p.error('Seeds must be positive')
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    if args.suite in ('all','standard'):
        for j in range(args.standard_seeds):
            cal=calibrate(known_contexts(),seed=12100+j)
            for case in NOISE_SCENARIOS:
                for policy in ('hybrid','pareto_front','pareto'):
                    row,frame=one_run('standard',case,6100+j,cal,policy,18,100000)
                    rows.append(row)
                    if j==0 and policy=='pareto':frame.to_csv(args.out/f'standard-{case}-example.csv',index=False)
            print(f'Standard seed {j+1}/{args.standard_seeds}',flush=True)
    if args.suite in ('all','alignment'):
        for j in range(args.alignment_seeds):
            cal=calibrate(alignment_contexts(),seed=15100+j)
            if j==0:cal.save(args.out/'alignment-calibration-example.json')
            for alignment in ALIGNMENTS:
                case=f'alignment_{alignment:.3f}'
                for policy in ('uncertainty','hybrid','pareto_front','pareto'):
                    row,frame=one_run('alignment',case,7100+j,cal,policy,40,1000000,alignment)
                    rows.append(row)
                    if j==0:frame.to_csv(args.out/f'{case}-{policy}-example.csv',index=False)
            print(f'Alignment seed {j+1}/{args.alignment_seeds}',flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(args.out/'runs.csv',index=False)
    summary=summarize(frame);summary.to_csv(args.out/'summary.csv',index=False)
    candidate_audit().to_csv(args.out/'candidate_objectives.csv',index=False)
    (args.out/'paired_comparisons.json').write_text(json.dumps(paired_statistics(frame),indent=2),encoding='utf-8')
    metadata=dict(scope='Operational binomial simulation; estimated asymptotic bits, not generated secure keys',
        suite=args.suite,standard_seed_start=6100,standard_calibration_seed_start=12100,
        alignment_seed_start=7100,alignment_calibration_seed_start=15100,
        standard_seeds=args.standard_seeds,alignment_seeds=args.alignment_seeds,
        alignment_grid=ALIGNMENTS,policies=['uncertainty','hybrid','pareto_front','pareto'],
        cost=.25,horizon_cap=8,margin=.01,ml=False,total_runs=len(frame),
        timing=timing(),summary=json.loads(summary.to_json(orient='records')))
    (args.out/'summary.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(f'Saved {len(frame)} runs to {args.out}',flush=True)


if __name__=='__main__':main()
