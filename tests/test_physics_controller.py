from dataclasses import replace
from qkd_sdn.physics import Channel, Decoy, expected, gain_error
from qkd_sdn.simulation import NetworkSimulator, conditions
from qkd_sdn.controller import Controller, wilson


def test_more_loss_reduces_rate_and_gain():
    ch = Channel()
    degraded = replace(ch, extra_loss_db=8)
    assert expected(Decoy(), degraded)[1] < expected(Decoy(), ch)[1]
    assert gain_error(0.6, degraded)[0] < gain_error(0.6, ch)[0]


def test_more_noise_reduces_rate():
    assert expected(Decoy(), Channel(traffic=8))[1] < expected(Decoy(), Channel())[1]


def test_dark_channel_generates_no_key():
    assert expected(Decoy(), Channel(detector_efficiency=0))[1] == 0


def test_wilson_empty_and_perfect():
    assert wilson(0, 0) == (0, 1)
    low, high = wilson(0, 100)
    assert low == 0 and 0 < high < 0.1


def test_controller_detects_target_without_labels():
    sim = NetworkSimulator(seed=10, pulses=100000)
    control = Controller()
    for step in range(2):
        ts = []
        for i in range(4):
            ch, eve, tap = conditions('intercept', step+6, wavelength=i)
            ts.append(sim.observe(ch, intercept=eve, tap=tap))
        decisions = control.decide(ts)
    assert decisions[2]['action'] == 'isolate'
    assert not any(control.states[i]['isolated'] for i in (0, 1, 3))
    assert control.states[2]['isolated']
