"""Retuning and robustness studies; independent of finite-key security module."""
import json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from qkd_sdn.simulation import NetworkSimulator
from qkd_sdn.physics import Channel
from qkd_sdn.controller import Controller,wilson


def trial(kind,value,seed,policy,steps=40):
    sim=NetworkSimulator(seed,1000000,engine='binomial'); c=Controller(policy)
    rng=np.random.default_rng(seed+100000); drift=0.; total=0.;retunes=0; previous=[False]*4
    first=None; false=False; holds=0
    for step in range(steps):
        drift=.85*drift+rng.normal(0,.004)
        ts=[]
        for i in range(4):
            ch=Channel(distance_km=20+2*i); actual=ch;eve=0
            if step>=6 and i==2:
                if kind=='retune': ch=actual=replace(ch,misalignment=value)
                if kind=='attack': eve=value
                if kind=='mismatch': actual=replace(ch,misalignment=ch.misalignment*value)
                if kind=='correlated': actual=replace(ch,misalignment=float(np.clip(ch.misalignment+drift,0,.2)))
            t=sim.observe(actual,c.states[i]['config'],eve)
            t['channel']=ch # reported telemetry omits hidden bias/burst realization
            ts.append(t)
        ds=c.decide(ts)
        for i,(t,d) in enumerate(zip(ts,ds)):
            action=d['action'];blocked=c.states[i]['isolated'] or action=='hold'
            total+=0 if blocked else t['skr_estimate']*(.75 if previous[i] else 1)
            previous[i]=action=='retune';retunes+=previous[i];holds+=action=='hold'
            if action=='isolate':
                if kind=='attack' and i==2 and step>=6 and first is None:first=step-6
                else:false=True
    return dict(kind=kind,value=value,seed=seed,policy=policy,estimated_bits=total,
                retunes=retunes,false_isolation=false,detected=first is not None,delay=first,holds=holds)


def main():
    cases=[('retune',.05)]+[('attack',v) for v in [.03,.06,.12,.3,.7]]+[
        ('mismatch',.8),('mismatch',1.2),('correlated',0)]
    out=Path('results/advanced');out.mkdir(parents=True,exist_ok=True);rows=[]
    for kind,value in cases:
        for seed in range(20):
            for policy in ['fixed','adaptive']:
                rows.append(trial(kind,value,seed+3000,policy))
        print(kind,value,flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(out/'runs.csv',index=False)
    summaries=[]
    for (kind,value,policy),g in frame.groupby(['kind','value','policy']):
        summaries.append(dict(kind=kind,value=value,policy=policy,runs=len(g),
            mean_estimated_bits=float(g.estimated_bits.mean()),mean_retunes=float(g.retunes.mean()),
            false_isolation_runs=int(g.false_isolation.sum()),
            detection_runs=int(g.detected.sum()) if kind=='attack' else None,
            detection_wilson95=wilson(int(g.detected.sum()),len(g),1.96) if kind=='attack' else None,
            mean_delay=float(g.delay.dropna().mean()) if g.delay.notna().any() else None))
    (out/'summary.json').write_text(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
