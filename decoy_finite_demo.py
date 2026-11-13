"""Basis-resolved decoy count experiments; no raw bits or distilled keys."""
import json
from pathlib import Path
import numpy as np
from qkd_sdn.physics import Channel,gain_error
from qkd_sdn.decoy_finitekey import budget


def counts(pulses,seed,noise=.015,intercept=0):
    rng=np.random.default_rng(seed);px=.7;probs=np.array([.75,.20,.05])
    # Both bases are independently selected; unmatched events are discarded.
    populations=rng.multinomial(pulses,np.r_[probs*px**2,probs*(1-px)**2,2*px*(1-px)])
    ns=[];ms=[]
    for i,emitted in enumerate(populations[:6]):
        gain,error=gain_error([.6,.12,0][i%3],Channel(misalignment=noise))
        n=int(rng.binomial(emitted,gain))
        # Illustrative symmetric disturbance. No ground truth enters the bound.
        error=error+intercept/4*(1-2*error)
        ns.append(n);ms.append(int(rng.binomial(n,error)))
    return ns[:3],ns[3:],ms[3:]


def main():
    rows=[]
    for pulses in [100000,1000000,10000000,100000000,1000000000]:
        for eve in [0,.8]:
            for seed in range(5):
                nx,nz,mz=counts(pulses,seed,intercept=eve)
                # Predeclared one-third raw-block syndrome cap, plus ack.
                # This experiment computes a bound; it does not execute decoding.
                r=budget(nx,nz,mz,sum(nx)//3+1)
                rows.append(dict(pulses=pulses,seed=seed,intercept=eve,nx=nx,nz=nz,mz=mz,**r))
    out=Path('results/decoy-finite');out.mkdir(parents=True,exist_ok=True)
    (out/'runs.json').write_text(json.dumps(rows,indent=2))
    for pulses in sorted({r['pulses'] for r in rows}):
        for eve in [0,.8]:
            group=[r for r in rows if r['pulses']==pulses and r['intercept']==eve]
            print(pulses,eve,[r['length'] for r in group],group[0]['status'])


if __name__=='__main__':main()
