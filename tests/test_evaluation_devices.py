import pandas as pd
import pytest
from evaluate import evaluate
from qkd_sdn.devices import SimulatedDevice
from qkd_sdn.physics import CANDIDATES


def test_latched_device_rejects_reconfiguration_and_release():
    device = SimulatedDevice()
    device.configure(CANDIDATES[0])
    device.isolate()
    with pytest.raises(RuntimeError):
        device.configure(CANDIDATES[1])
    with pytest.raises(RuntimeError):
        device.apply(CANDIDATES[0], False)


def test_evaluation_separates_false_alarm_and_detection():
    frame = pd.DataFrame([
        dict(action='isolate', interval=2, channel='lambda_1'),
        dict(action='isolate', interval=8, channel='lambda_3')])
    result = evaluate(frame, 'intercept')
    assert result['false_isolation_run']
    assert result['detected'] and result['delay_intervals'] == 2
    assert not evaluate(frame, 'noise')['detection_eligible']


def test_premature_isolation_is_not_a_detection():
    frame = pd.DataFrame([dict(action='isolate', interval=2, channel='lambda_3')])
    result = evaluate(frame, 'intercept')
    assert result['false_isolation_run'] and not result['detected']
