"""Matched integrated ML/Pareto evaluation; analytical safety gate retained."""
import argparse,json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from qkd_sdn.ml import train
from qkd_sdn.physics import Channel,CANDIDATES,expected
from qkd_sdn.monitoring import calibrate
from experiments.pareto_experiments import alignment_contexts
from experiments.single_channel_comparison import Conditions
from run import run_network


class Cached:
    def __init__(self,predictor):self.predictor=predictor;self.cache={};self.cold_seconds=0.;self.calls=0
    def predict(self,ch,cfg,clock):
        key=(ch,cfg,clock)
        if key not in self.cache:
            start=perf_counter();self.cache[key]=self.predictor.predict(ch,cfg,clock)
            self.cold_seconds+=perf_counter()-start;self.calls+=1
        return self.cache[key]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=20)
    p.add_argument('--out',type=Path,default=Path('results/ml-pareto-integration'));a=p.parse_args()
    if a.seeds<1:p.error('Positive seeds required')
    a.out.mkdir(parents=True,exist_ok=True)
    models={};training=[];prediction=[]
    for seed in (42,43,44):
        start=perf_counter();model,metrics=train(seed);seconds=perf_counter()-start
        models[seed]=model;training.append(dict(training_seed=seed,training_seconds=seconds,**metrics))
        for error in (.015,.03,.035,.04):
            ch=Channel(distance_km=24,misalignment=error)
            for cfg in CANDIDATES:
                start=perf_counter();q,r=model.predict(ch,cfg,1000000);elapsed=perf_counter()-start
                tq,tr=expected(cfg,ch,1000000)
                prediction.append(dict(training_seed=seed,alignment=error,config=cfg.name,
                    predicted_qber=q,true_qber=tq,predicted_rate=r,true_rate=tr,uncached_seconds=elapsed))
    pd.DataFrame(prediction).to_csv(a.out/'prediction_errors.csv',index=False)
    (a.out/'training.json').write_text(json.dumps(training,indent=2))
    rows=[]
    cases=[('normal',.015,False),('local_3pct',.03,False),('local_3p5pct',.035,False),
           ('local_4pct',.04,False),('shared_4pct',.04,True)]
    for j in range(a.seeds):
        seed=11200+j;cal=calibrate(alignment_contexts(),seed=21200+j)
        for case,alignment,shared in cases:
            for model_seed in (None,42,43,44):
                predictor=Cached(models[model_seed]) if model_seed is not None else None
                start=perf_counter()
                frame,meta=run_network(case,40,seed,1000000,'pareto',predictor,'binomial',cal,Conditions(alignment,shared))
                elapsed=perf_counter()-start
                changed=frame.action.isin(['retune','rollback']).sum()
                # Difference between pre-settling output and the existing charged output.
                usable=~frame.action.isin(['hold','isolate','isolated'])
                before=float(frame.loc[usable,'skr_estimate'].sum())
                rows.append(dict(case=case,seed=seed,arm='analytical' if predictor is None else f'ml_{model_seed}',
                    estimated_bits=meta['estimated_released_bits'],wall_seconds=elapsed,
                    retunes=meta['retunes'],rollbacks=int((frame.action=='rollback').sum()),
                    settling_bits=before-meta['estimated_released_bits'],switches=int(changed),
                    isolated=meta['isolation_events'],cold_prediction_calls=predictor.calls if predictor else 0,
                    cold_prediction_seconds=predictor.cold_seconds if predictor else 0.))
                if j==0:frame.to_csv(a.out/f'{case}-{model_seed}-example.csv',index=False)
        print(f'ML matched seed {j+1}/{a.seeds}',flush=True)
    runs=pd.DataFrame(rows);runs.to_csv(a.out/'runs.csv',index=False)
    runs.groupby(['case','arm']).mean(numeric_only=True).to_csv(a.out/'summary.csv')
    rng=np.random.default_rng(66211);comparisons=[]
    for case,g in runs.groupby('case'):
        pair=g.pivot(index='seed',columns='arm',values='estimated_bits')
        for arm in ('ml_42','ml_43','ml_44'):
            d=(pair[arm]-pair.analytical).to_numpy()
            low,high=np.quantile(rng.choice(d,size=(10000,len(d)),replace=True).mean(axis=1),[.025,.975])
            comparisons.append(dict(case=case,arm=arm,mean_difference=d.mean(),gain_percent=100*d.mean()/pair.analytical.mean(),
                difference_low=low,difference_high=high))
    pd.DataFrame(comparisons).to_csv(a.out/'comparison.csv',index=False)
    (a.out/'metadata.json').write_text(json.dumps(dict(seeds=a.seeds,steps=40,pulses_per_channel_interval=1000000,
        runtime_seed_start=11200,calibration_seed_start=21200,training_seeds=[42,43,44],distance_km=24,
        cache='Exact channel/config/clock memoization, fresh per run; model training excluded from online wall time',
        scope='ML proposes candidates; independent calibration and analytical benefit gate retained. Not a model-free ML controller.',
        uncertainty='Descriptive paired seed bootstrap, no multiple-comparison adjustment; three forests share analytical teacher'),indent=2))


if __name__=='__main__':main()
