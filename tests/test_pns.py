from math import exp
import pytest
from qkd_sdn.pns import multiphoton_signal,forwarding_eta,observe_pns
from qkd_sdn.physics import Channel,Decoy,gain_error
from qkd_sdn.simulation import NetworkSimulator


def test_signal_matching_uses_feasible_common_photon_yield():
    ch=Channel(distance_km=40);cfg=Decoy();eta=forwarding_eta(ch,cfg,True)
    assert ch.eta<eta<=ch.detector_efficiency
    assert multiphoton_signal(cfg.mu,eta)==pytest.approx(1-exp(-cfg.mu*ch.eta),abs=1e-10)
    assert multiphoton_signal(cfg.nu,eta)<1-exp(-cfg.nu*ch.eta)


def test_photon_resolved_law_matches_explicit_poisson_sum():
    from math import factorial
    for mu in (.12,.6):
        for eta in (.03,.2,1.):
            direct=sum(exp(-mu)*mu**n/factorial(n)*(1-(1-eta)**(n-1)) for n in range(2,25))
            assert multiphoton_signal(mu,eta)==pytest.approx(direct,abs=1e-12)


def test_pns_samples_blocked_and_split_classes_without_leaking_labels():
    ch=Channel(distance_km=40);sim=NetworkSimulator(551,2000000,engine='binomial')
    t,audit=observe_pns(sim,ch,Decoy(),1,True)
    assert audit['classes']['signal']['blocked_single_photons']>0
    assert audit['classes']['signal']['split_multiphoton_pulses']>0
    assert 'classes' not in t and 'forwarding_eta' not in t
    assert t['records']['signal']['gain']==pytest.approx(gain_error(.6,ch)[0],rel=.04)
    assert t['qber']<.03
    for r in t['records'].values():assert 0<=r['errors']<=r['sifted']<=r['detections']<=r['emitted']


def test_infeasible_compensation_rejected():
    with pytest.raises(ValueError):forwarding_eta(Channel(distance_km=0),Decoy(),True)
