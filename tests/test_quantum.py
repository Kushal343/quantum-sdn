import numpy as np
import pytest
from qkd_sdn.bb84 import bb84, run_wdm
from qkd_sdn.quantum import BB84Engine


def test_ideal_bases_recover_bits():
    r = bb84(12000, seed=1)
    assert r["qber"] == 0
    assert r["keys_match"]
    assert 5500 < r["n_sifted"] < 6500
    assert r["n_sifted"] == r["n_sample"] + len(r["alice_key"])


@pytest.mark.parametrize("fraction", [0.2, 0.6, 1.0])
def test_intercept_resend_matches_theory(fraction):
    r = bb84(40000, eve_fraction=fraction, sample_fraction=1, seed=31)
    assert abs(r["qber"]-fraction/4) < 0.015


def test_no_clicks_are_not_zero_bits():
    r = bb84(2000, detection_probability=0)
    assert r["n_detected"] == r["n_sifted"] == r["n_sample"] == 0
    assert r["qber"] is None and r["aborted"]
    assert len(r["alice_key"]) == 0


def test_noise_and_intercept_compose():
    r = bb84(40000, eve_fraction=0.8, channel_noise=0.1, sample_fraction=1, seed=8)
    assert abs(r["qber"] - (0.1+0.8/4*0.8)) < 0.015


def test_wavelength_isolation_and_no_label_leakage():
    rows, truth = run_wdm(intervals=2, attack_start=1, n_qubits=10000, attack_fraction=1)
    for r in rows:
        assert "eve_fraction" not in r and "expected_qber" not in r
        if r["channel"] == "lambda_3" and r["interval"] == 1:
            assert 0.20 < r["qber"] < 0.30
        else:
            assert r["qber"] == 0


def test_reproducibility():
    a, b = bb84(2000, eve_fraction=0.5, seed=9), bb84(2000, eve_fraction=0.5, seed=9)
    assert a["qber"] == b["qber"]
    np.testing.assert_array_equal(a["bob_key"], b["bob_key"])


def test_grouped_detection_engine():
    r = BB84Engine(12).measure(20000, 0, intercept_fraction=1)
    assert abs(r["errors"]/r["sifted"]-0.25) < 0.02


@pytest.mark.parametrize("kwargs", [{"eve_fraction": 1.1}, {"sample_fraction": 0},
                                      {"n_qubits": -1}, {"detection_probability": -0.1}])
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        bb84(**kwargs)
