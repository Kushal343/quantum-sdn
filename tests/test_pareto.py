from dataclasses import replace
import pytest
from qkd_sdn.pareto import Point,front,select
from qkd_sdn.physics import CANDIDATES,Channel,Decoy,expected
from qkd_sdn.controller import select_configuration
from qkd_sdn.monitoring import calibrate
from qkd_sdn.noise import known_contexts,Scenario
from qkd_sdn.hybrid import HybridController
from qkd_sdn.simulation import NetworkSimulator


def test_front_keeps_tradeoffs_removes_dominated_retains_equal_points():
    a,b,c,d=CANDIDATES[:4]
    points=[Point(a,.01,100,100),Point(b,.02,200,200),
            Point(c,.03,90,90),Point(d,.01,100,100)]
    result=front(points)
    assert result==[points[0],points[1],points[3]]


def test_equivalent_selector_matches_old_rule_on_physical_grid():
    for error in (.015,.02,.025,.03,.035,.04,.045,.05):
        for traffic in (.2,4,8):
            ch=Channel(distance_km=24,misalignment=error,traffic=traffic)
            scores=[(c,*expected(c,ch,100000)) for c in CANDIDATES]
            for scenario in ('high_qber','low_skr'):
                picked,_=select(scores,Decoy(),8,'equivalent',scenario)
                assert picked==select_configuration(ch,100000,scenario)


def test_delivered_selector_exposes_error_rate_tradeoff():
    ch=Channel(distance_km=24,misalignment=.03)
    chosen,audit=select([(c,*expected(c,ch,1000000)) for c in CANDIDATES],Decoy(),8)
    assert chosen.name=='C2' and select_configuration(ch,1000000,'high_qber').name=='C3'
    selected=next(p for p in audit['candidates'] if p['config']=='C2')
    current=next(p for p in audit['candidates'] if p['config']=='C3')
    assert selected['on_front'] and selected['qber']>current['qber']
    assert selected['delivered_bits']>current['delivered_bits']*1.01


def test_remaining_horizon_prevents_unverifiable_late_switch():
    ch=Channel(misalignment=.05)
    scores=[(c,*expected(c,ch,100000)) for c in CANDIDATES]
    assert select(scores,Decoy(),1)[0] is None
    assert select(scores,Decoy(),0)[0] is None


def test_cost_can_make_small_rate_improvement_not_worth_switching():
    scores=[(CANDIDATES[2],.03,100),(CANDIDATES[1],.031,102)]
    assert select(scores,Decoy(),8)[0] is None


def test_invalid_and_zero_rate_points_are_not_selected():
    with pytest.raises(ValueError):front([Point(Decoy(),float('nan'),1,1)])
    assert select([(Decoy(),.12,100),(CANDIDATES[0],.01,0)],Decoy(),8)[0] is None


def test_pareto_cannot_override_suspicious_channel_isolation():
    cal=calibrate(known_contexts())
    c=HybridController(cal,12,'pareto')
    sim=NetworkSimulator(42,100000,engine='binomial');scene=Scenario('intercept',42)
    for step in range(9):
        ds=c.decide([scene.observe(sim,c.states[i]['config'],step,i) for i in range(4)])
        if step==6:assert ds[2]['action']=='hold'
        if step==7:assert ds[2]['action']=='isolate'
    assert ds[2]['action']=='isolated'
    assert all(not c.states[i]['isolated'] for i in (0,1,3))
