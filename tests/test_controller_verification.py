from qkd_sdn.controller import Controller
from qkd_sdn.physics import Channel, CANDIDATES, gain_error


def observation(config, rate):
    ch = Channel()
    records = {}
    for label, intensity in [('signal', config.mu), ('decoy', config.nu), ('vacuum', 0)]:
        gain, error = gain_error(intensity, ch)
        records[label] = dict(emitted=10000000, gain=gain, sifted=10000,
                              errors=round(error*10000))
    return dict(config=config, channel=ch, clock_hz=100000,
                records=records, qber=records['signal']['errors']/10000,
                skr_estimate=rate)


def test_failed_retune_rolls_back_only_after_two_measurements():
    c = Controller()
    old, new = CANDIDATES[0], CANDIDATES[2]
    c.states[0]['config'] = new
    c.states[0]['pending'] = dict(old=old, before=100, rates=[])
    ts = [observation(new, 50) for _ in range(4)]
    assert c.decide(ts)[0]['action'] == 'verify'
    assert c.decide(ts)[0]['action'] == 'rollback'
    assert c.states[0]['config'] == old
    assert c.states[0]['pending'] is None
    assert c.states[0]['cooldown'] == 4


def test_successful_retune_is_kept():
    c = Controller()
    old, new = CANDIDATES[0], CANDIDATES[2]
    c.states[0]['config'] = new
    c.states[0]['pending'] = dict(old=old, before=100, rates=[])
    ts = [observation(new, 110) for _ in range(4)]
    c.decide(ts)
    assert c.decide(ts)[0]['action'] == 'keep'
    assert c.states[0]['config'] == new


def test_sparse_vacuum_counts_do_not_trigger_gaussian_false_alarm():
    c = Controller()
    t = observation(CANDIDATES[2], 100)
    t['records']['vacuum'].update(emitted=5000, gain=3/5000, detections=3)
    assert all(d['action'] == 'continue' for d in c.decide([t]*4))


def test_extreme_vacuum_excess_is_held_then_isolated():
    c = Controller()
    t = observation(CANDIDATES[2], 100)
    t['records']['vacuum'].update(emitted=5000, gain=30/5000, detections=30)
    assert c.decide([t]*4)[0]['action'] == 'hold'
    assert c.decide([t]*4)[0]['action'] == 'isolate'
