from copy import deepcopy
from dataclasses import replace
import pytest
from scipy.stats import binom
from qkd_sdn.monitoring import calibrate, interval_pvalue, count_features
from qkd_sdn.hybrid import HybridController
from qkd_sdn.noise import Scenario, known_contexts
from qkd_sdn.physics import Channel, Decoy
from qkd_sdn.simulation import NetworkSimulator


@pytest.fixture(scope='module')
def calibration():
    return calibrate(known_contexts(), seed=701)


def observations(sim, controller, scenario, step):
    return [scenario.observe(sim,controller.states[i]['config'],step,i) for i in range(4)]


def test_composite_test_size_at_interval_endpoints():
    n=100
    accepted=[k for k in range(n+1) if interval_pvalue(k,n,.1,.2)<=.01]
    for true_rate in (.1,.15,.2):
        assert sum(binom.pmf(k,n,true_rate) for k in accepted)<=.01+1e-12


def test_target_only_persistent_isolation_and_no_release(calibration):
    c=HybridController(calibration,12)
    sim=NetworkSimulator(42,100000,engine='binomial');scenario=Scenario('intercept',42)
    for step in range(9):
        ds=c.decide(observations(sim,c,scenario,step))
        if step==6:assert ds[2]['action']=='hold'
        if step==7:assert ds[2]['action']=='isolate'
    assert ds[2]['action']=='isolated'
    assert all(not c.states[i]['isolated'] for i in (0,1,3))


def test_transient_needs_clean_recovery_not_isolation(calibration):
    c=HybridController(calibration,12)
    sim=NetworkSimulator(42,100000,engine='binomial');scenario=Scenario('transient',42)
    actions=[]
    for step in range(11):
        actions.append(c.decide(observations(sim,c,scenario,step))[2]['action'])
    assert actions[6:9]==['hold']*3
    assert actions[9]=='continue'
    assert not c.states[2]['isolated']


@pytest.mark.parametrize('scenario',['missing','unsupported'])
def test_bad_coverage_withholds_without_attack_claim(calibration,scenario):
    c=HybridController(calibration,12)
    sim=NetworkSimulator(42,100000,engine='binomial');scenario=Scenario(scenario,42)
    for step in range(8):
        ds=c.decide(observations(sim,c,scenario,step))
    assert ds[2]['action']=='hold' and ds[2]['category']=='INCONCLUSIVE'
    assert not c.states[2]['isolated']


def test_horizon_and_stale_counts_do_not_accumulate_evidence(calibration):
    c=HybridController(calibration,1)
    sim=NetworkSimulator(42,100000,engine='binomial');scenario=Scenario('normal',42)
    ts=observations(sim,c,scenario,0);c.decide(ts)
    ds=c.decide(ts)
    assert all(d['category']=='OUT_OF_BUDGET' and d['action']=='hold' for d in ds)
    assert all(s['evidence']==0 for s in c.states.values())


def test_count_validation_rejects_more_errors_than_sifted():
    t=NetworkSimulator(1,1000,engine='binomial').observe(Channel())
    t['records']['signal']['errors']=1001
    with pytest.raises(ValueError):count_features(t)


def test_hidden_noise_not_exposed_in_controller_context():
    scenario=Scenario('model_mismatch',42)
    t=scenario.observe(NetworkSimulator(42,100000,engine='binomial'),Decoy(),6,2)
    assert t['channel'].misalignment==.015
    assert 'scenario' not in t and 'attack' not in t


def test_explained_misalignment_can_retune_without_isolation(calibration):
    c=HybridController(calibration,18)
    sim=NetworkSimulator(42,1000000,engine='binomial');scenario=Scenario('misalignment',42)
    actions=[]
    for step in range(18):
        actions.append(c.decide(observations(sim,c,scenario,step))[2]['action'])
    assert 'retune' in actions and 'keep' in actions
    assert not c.states[2]['isolated']
