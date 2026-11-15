"""Controlled single-channel versus WDM comparison; no live SDN timing claim."""
import argparse,json
from pathlib import Path
from dataclasses import replace
import numpy as np
import pandas as pd
from qkd_sdn.physics import Channel,Decoy
from qkd_sdn.simulation import NetworkSimulator
from qkd_sdn.monitoring import calibrate
from experiments.pareto_experiments import alignment_contexts
from run import run_network


class Conditions:
    def __init__(self,alignment,shared=False):self.alignment,self.shared=alignment,shared
    def observe(self,sim,config,step,wavelength):
        ch=Channel(distance_km=24)
        if step>=6 and (self.shared or wavelength==2):ch=replace(ch,misalignment=self.alignment)
        t=sim.observe(ch,config);t.update(window=step,available=True)
        return t


def single(seed,pulses,alignment,steps):
    sim=NetworkSimulator(seed,pulses,engine='binomial');bits=0
    for step in range(steps):
        ch=Channel(distance_km=24,crosstalk_probability=0,
                   misalignment=alignment if step>=6 else .015)
        t=sim.observe(ch,Decoy())
        # Fixed optical setting; no anomaly monitor or SDN. These cases are below the cap.
        if t['qber']<=.11:bits+=t['skr_estimate']*t['interval']
    return bits


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=50)
    p.add_argument('--out',type=Path,default=Path('results/single-channel-comparison'))
    args=p.parse_args()
    if args.seeds<1:p.error('Seeds must be positive')
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[('normal',.015,False),('local_3pct',.03,False),('local_3p5pct',.035,False),
           ('local_4pct',.04,False),('shared_4pct',.04,True)]
    rows=[]
    for j in range(args.seeds):
        seed=9100+j;cal=calibrate(alignment_contexts(),seed=19100+j)
        for case,alignment,shared in cases:
            for arm,pulses in [('single_fixed_1M',1000000),('single_fixed_4M',4000000)]:
                rows.append(dict(case=case,seed=seed,arm=arm,estimated_bits=single(seed,pulses,alignment,40),
                    total_pulses=40*pulses,retunes=0,isolations=0))
            for arm,policy in [('wdm_fixed','fixed'),('wdm_pareto','pareto')]:
                frame,meta=run_network(case,40,seed,1000000,policy,engine='binomial',calibration=cal,
                                      scenario_source=Conditions(alignment,shared))
                rows.append(dict(case=case,seed=seed,arm=arm,estimated_bits=meta['estimated_released_bits'],
                    total_pulses=160000000,retunes=meta['retunes'],isolations=meta['isolation_events']))
                if j==0:frame.to_csv(args.out/f'{case}-{arm}-example.csv',index=False)
        print(f'Seed {j+1}/{args.seeds}',flush=True)
    runs=pd.DataFrame(rows);runs['bits_per_million_pulses']=runs.estimated_bits/runs.total_pulses*1e6
    runs.to_csv(args.out/'runs.csv',index=False)
    summary=runs.groupby(['case','arm']).agg(runs=('seed','size'),mean_bits=('estimated_bits','mean'),
        bits_per_million_pulses=('bits_per_million_pulses','mean'),mean_retunes=('retunes','mean'),
        mean_isolations=('isolations','mean')).reset_index()
    summary.to_csv(args.out/'summary.csv',index=False)
    comparisons=[];rng=np.random.default_rng(55231)
    for case,g in runs.groupby('case'):
        pair=g.pivot(index='seed',columns='arm',values='estimated_bits')
        for base in ['single_fixed_1M','single_fixed_4M','wdm_fixed']:
            d=(pair.wdm_pareto-pair[base]).to_numpy()
            ci=np.quantile(rng.choice(d,size=(10000,len(d)),replace=True).mean(axis=1),[.025,.975])
            comparisons.append(dict(case=case,baseline=base,pareto_mean=float(pair.wdm_pareto.mean()),
                baseline_mean=float(pair[base].mean()),gain_percent=float(100*d.mean()/pair[base].mean()),
                difference_low=float(ci[0]),difference_high=float(ci[1])))
    comparison=pd.DataFrame(comparisons);comparison.to_csv(args.out/'comparison.csv',index=False)
    (args.out/'metadata.json').write_text(json.dumps(dict(seeds=args.seeds,steps=40,runtime_seed_start=9100,
        calibration_seed_start=19100,distance_km=24,onset=6,engine='binomial',ml=False,
        scope='Asymptotic estimated output, no secure keys or live SDN; reconstructed fixed-C3 baseline, not recovered historical single-channel implementation',
        single_channel='Crosstalk removed; dark and classical Raman-like background retained; fixed C3, illustrative 11% cap',
        resource_budget='single_1M:40M pulses/run; other arms:160M pulses/run; same 40 intervals',
        disturbance='local affects lambda_3 of WDM and sole single channel; shared affects all WDM channels',
        uncertainty='Descriptive paired bootstrap over seed labels; random streams diverge across architectures; no multiplicity correction'),indent=2))
    print(summary.to_string(index=False));print(comparison.to_string(index=False))


if __name__=='__main__':main()
