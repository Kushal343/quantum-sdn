"""PNS versus QBER-only, signal-count and full-decoy monitoring ablations."""
import argparse,json
from pathlib import Path
import pandas as pd
from qkd_sdn.physics import Channel,CANDIDATES
from qkd_sdn.monitoring import calibrate
from qkd_sdn.pns import observe_pns
from run import run_network


class SignalOnly:
    def __init__(self,base):self.base=base;self.calibration_budget=base.calibration_budget;self.cells=base.cells
    def assess(self,t,alpha):
        result=self.base.assess(t,alpha)
        return None if result is None else {k:v for k,v in result.items() if k.startswith('signal_')}


class PNS:
    def __init__(self,strength,compensated):self.strength,self.compensated=strength,compensated;self.audit=[]
    def observe(self,sim,config,step,wavelength):
        active=wavelength==2 and step>=6
        t,latent=observe_pns(sim,Channel(distance_km=40),config,self.strength if active else 0.,
                            self.compensated if active else False)
        t.update(window=step,available=True)
        if active:self.audit.append(dict(interval=step,**latent))
        return t


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=20)
    p.add_argument('--out',type=Path,default=Path('results/pns-decoy'));a=p.parse_args()
    if a.seeds<1:p.error('Positive seeds required')
    a.out.mkdir(parents=True,exist_ok=True);rows=[];features=[]
    cases=[('normal',0.,False)]+[(f'matched_{s:g}',s,True) for s in (.1,.25,.5,1.)]+[('uncompensated_1',1.,False)]
    for j in range(a.seeds):
        seed=13200+j;cal=calibrate([(Channel(distance_km=40),c) for c in CANDIDATES],seed=23200+j)
        for case,strength,matched in cases:
            for arm,policy in [('qber_only','per_wavelength'),('signal_counts','uncertainty'),('full_decoy','uncertainty')]:
                source=PNS(strength,matched)
                frame,meta=run_network(case,18,seed,1000000,policy,engine='binomial',
                    calibration=SignalOnly(cal) if arm=='signal_counts' else cal,scenario_source=source)
                target=frame[(frame.channel=='lambda_3')&(frame.interval>=6)]
                isolated=target[target.action=='isolate']
                other=frame[(frame.channel!='lambda_3')&(frame.action=='isolate')]
                rows.append(dict(case=case,seed=seed,arm=arm,target_isolated=bool(len(isolated)),
                    other_isolated=bool(len(other)),hold=bool((target.action=='hold').any()),
                    delay=int(isolated.interval.min()-6) if len(isolated) else None,
                    signal_qber=float(target.errors.sum()/target.sample_size.sum()),
                    estimated_bits=meta['estimated_released_bits'],
                    blocked_single_photons=sum(x['classes']['signal']['blocked_single_photons'] for x in source.audit),
                    split_multiphoton_pulses=sum(x['classes']['signal']['split_multiphoton_pulses'] for x in source.audit)))
                if j==0:
                    frame.to_csv(a.out/f'{case}-{arm}-example.csv',index=False)
                    if arm=='full_decoy':(a.out/f'{case}-latent-audit.json').write_text(json.dumps(source.audit,indent=2))
                # Separate diagnostic replay at fixed C3, without revealing latent counts to monitoring.
            from qkd_sdn.simulation import NetworkSimulator
            sim=NetworkSimulator(seed,1000000,engine='binomial');source=PNS(strength,matched)
            for step in range(18):
                t=source.observe(sim,CANDIDATES[2],step,2)
                for label,r in t['records'].items():
                    features.append(dict(case=case,seed=seed,interval=step,label=label,**r))
        print(f'PNS seed {j+1}/{a.seeds}',flush=True)
    runs=pd.DataFrame(rows);runs.to_csv(a.out/'runs.csv',index=False)
    runs.groupby(['case','arm']).agg(runs=('seed','size'),target_isolated=('target_isolated','sum'),
        other_isolated=('other_isolated','sum'),hold_runs=('hold','sum'),mean_delay=('delay','mean'),
        mean_signal_qber=('signal_qber','mean'),mean_estimated_bits=('estimated_bits','mean')).to_csv(a.out/'summary.csv')
    f=pd.DataFrame(features);f.to_csv(a.out/'decoy_counts.csv',index=False)
    totals=f[f.interval>=6].groupby(['case','label'])[['emitted','detections','sifted','errors']].sum()
    totals['gain']=totals.detections/totals.emitted;totals['qber']=totals.errors/totals.sifted
    totals.to_csv(a.out/'decoy_statistics.csv')
    (a.out/'metadata.json').write_text(json.dumps(dict(seeds=a.seeds,runtime_seed_start=13200,
        calibration_seed_start=23200,steps=18,onset=6,pulses_per_channel_interval=1000000,distance_km=40,
        model='Poisson photon-number classes: block attacked n=1, split one from attacked n>=2, forward remaining n-1. No encoding error added.',
        compensation='One common forwarding efficiency solves signal-intensity gain matching, bounded by Bob detector efficiency; same photon-number law applies to decoy pulses. Eve replaces some channel loss.',
        ablation='Signal-only and full-decoy share per-feature threshold and finite-horizon budget; signal-only leaves unused budget unspent. No retuning in these uncertainty-monitor arms.',
        scope='Ideal PNS count model, not a coherent quantum memory simulation, universal PNS detector or attack attribution. Latent photon labels never enter controller telemetry.'),indent=2))


if __name__=='__main__':main()
