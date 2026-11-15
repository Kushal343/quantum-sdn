"""Reproducible policy comparison, including faults and model mismatch."""
import argparse
import json
from pathlib import Path
import pandas as pd
from run import run_network
from qkd_sdn.noise import NOISE_SCENARIOS, known_contexts
from qkd_sdn.monitoring import calibrate
# Freeze the original six-policy study when new policies are added elsewhere.
POLICIES=('fixed','aggregate','per_wavelength','adaptive','uncertainty','hybrid')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=20)
    p.add_argument('--steps',type=int,default=18)
    p.add_argument('--pulses',type=int,default=100000)
    p.add_argument('--out',type=Path,default=Path('results/hybrid'))
    args=p.parse_args()
    if args.seeds<1 or args.steps<10:p.error('Need positive seeds and at least 10 steps')
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for j in range(args.seeds):
        seed=4100+j
        calibration=calibrate(known_contexts(),seed=9100+j)
        if j==0:calibration.save(args.out/'calibration-example.json')
        for scenario in NOISE_SCENARIOS:
            for policy in POLICIES:
                frame,summary=run_network(scenario,args.steps,seed,args.pulses,policy,engine='binomial',calibration=calibration)
                isolated=frame[frame.action=='isolate']
                target=isolated[isolated.channel=='lambda_3']
                rows.append(dict(scenario=scenario,policy=policy,seed=seed,
                    any_isolation=bool(len(isolated)),target_isolation=bool(len(target)),
                    other_isolation=bool((isolated.channel!='lambda_3').any()),
                    target_delay=int(target.interval.min()-6) if len(target) else None,
                    any_hold=bool((frame.action=='hold').any()),retunes=summary['retunes'],
                    estimated_bits=summary['estimated_released_bits']))
                if j==0 and policy=='hybrid':
                    frame.to_csv(args.out/f'{scenario}-example.csv',index=False)
        print(f'Completed seed {j+1}/{args.seeds}',flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(args.out/'runs.csv',index=False)
    summary=frame.groupby(['scenario','policy']).agg(runs=('seed','size'),
        isolated_runs=('any_isolation','sum'),target_isolated=('target_isolation','sum'),
        other_isolated=('other_isolation','sum'),hold_runs=('any_hold','sum'),
        mean_detection_delay=('target_delay','mean'),mean_estimated_bits=('estimated_bits','mean'),
        mean_retunes=('retunes','mean')).reset_index()
    summary.to_csv(args.out/'summary.csv',index=False)
    records=json.loads(summary.to_json(orient='records'))
    (args.out/'summary.json').write_text(json.dumps(dict(seeds=args.seeds,steps=args.steps,
        pulses=args.pulses,summary=records,scope='Exploratory operational simulation; asymptotic estimated bits, not generated secure keys. Correlated scenario is interval-level drift, not a correlated quantum attack.'),indent=2),encoding='utf-8')


if __name__=='__main__':main()
