"""Ideal photon-number-dependent PNS count model, not a general attack proof.

Eve blocks attacked single-photon pulses and retains one photon from attacked
multiphoton pulses. Bob receives the remaining photons without added encoding
errors. Poisson photon-number classes are sampled explicitly in aggregate.
"""
from math import exp
from scipy.optimize import brentq
from .physics import decoy_rate


def multiphoton_signal(intensity, eta):
    """Unconditional click probability from n>=2 with one photon removed."""
    if eta==1:return 1-exp(-intensity)*(1+intensity)
    return max(0.,1-exp(-intensity)-(exp(-intensity*eta)-exp(-intensity))/(1-eta))


def forwarding_eta(ch,cfg,compensated):
    if not compensated:return ch.eta
    target=1-exp(-cfg.mu*ch.eta)
    if multiphoton_signal(cfg.mu,ch.detector_efficiency)<target:
        raise ValueError('Signal matching infeasible without exceeding Bob detector efficiency')
    return brentq(lambda eta:multiphoton_signal(cfg.mu,eta)-target,0,ch.detector_efficiency)


def observe_pns(sim,ch,cfg,strength=1.,compensated=False):
    if sim.engine.__class__.__name__!='BinomialEngine':raise ValueError('PNS model requires binomial engine')
    if not 0<=strength<=1:raise ValueError('Invalid PNS strength')
    attack_eta=forwarding_eta(ch,cfg,compensated)
    emitted=sim.rng.multinomial(sim.pulses,[cfg.p_signal,cfg.p_decoy,1-cfg.p_signal-cfg.p_decoy])
    records={};audit={}
    for label,x,n in zip(('signal','decoy','vacuum'),(cfg.mu,cfg.nu,0.),emitted):
        p0=exp(-x);p1=x*p0;pm=max(0.,1-p0-p1)
        counts=sim.rng.multinomial(int(n),[p0,p1*(1-strength),p1*strength,pm*(1-strength),pm*strength])
        normal_multi=(1-exp(-x*ch.eta)-p1*ch.eta)/pm if pm else 0.
        attacked_multi=multiphoton_signal(x,attack_eta)/pm if pm else 0.
        detected=errors=sifted=tagged=0
        for group,(count,yield_) in enumerate(zip(counts,[0,ch.eta,0,normal_multi,attacked_multi])):
            photons=int(sim.rng.binomial(int(count),min(1,max(0,yield_))))
            background=int(sim.rng.binomial(int(count)-photons,ch.background))
            a=sim.engine.measure(photons,ch.misalignment)
            b=sim.engine.measure(background,.5)
            detected+=photons+background;sifted+=a['sifted']+b['sifted'];errors+=a['errors']+b['errors']
            if group==4:tagged+=a['sifted']
        records[label]=dict(emitted=int(n),detections=detected,sifted=sifted,errors=errors,
            gain=detected/int(n) if n else 0.,qber=errors/sifted if sifted else .5)
        audit[label]=dict(vacuum_emissions=int(counts[0]),blocked_single_photons=int(counts[2]),
            split_multiphoton_pulses=int(counts[4]),tagged_sifted_signal_clicks=tagged)
    s,d,v=(records[k] for k in ('signal','decoy','vacuum'))
    rate=decoy_rate(cfg,s['gain'],s['qber'],d['gain'],d['qber'],v['gain'],sim.pulses/sim.interval)
    return dict(records=records,qber=s['qber'],skr_estimate=rate,channel=ch,config=cfg,
        interval=sim.interval,clock_hz=sim.pulses/sim.interval),dict(forwarding_eta=attack_eta,classes=audit)
