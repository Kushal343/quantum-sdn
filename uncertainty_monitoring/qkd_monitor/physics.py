"""Count-level optical link model, not a full quantum device/security simulator."""
import math
import numpy as np
from .telemetry import Telemetry


def probabilities(cfg, wavelength, powers, extra_loss_db=0.0, extra_background=0.0):
    if extra_loss_db < 0 or extra_background < 0 or not all(math.isfinite(v) and v >= 0 for v in powers):
        raise ValueError("Physical disturbances and powers must be finite and nonnegative")
    loss = cfg.attenuation_db_per_km*cfg.fibre_length_km + cfg.insertion_loss_db + extra_loss_db
    eta = cfg.detector_efficiency * 10**(-loss/10)
    mean_background = sum(a*p for a, p in zip(cfg.background_coupling_per_mw[wavelength], powers)) + extra_background
    y0 = -math.expm1(math.log1p(-cfg.dark_probability_per_gate) - mean_background)
    gains, errors = [], []
    for intensity in cfg.intensities:
        signal = -math.expm1(-eta*intensity)
        gain = y0 + (1-y0)*signal
        # Explicit receiver rule: a background hit randomizes the bit,
        # including simultaneous signal/background events.
        error_gain = 0.5*y0 + cfg.misalignment_error*(1-y0)*signal
        if not 0 <= error_gain <= gain <= 1:
            raise ValueError("Invalid physical probability")
        gains.append(gain)
        errors.append(error_gain)
    return np.array(gains), np.array(errors)


def sample_counts(cfg, wavelength, powers, pulses, rng, extra_loss_db=0.0, extra_background=0.0):
    q, t = probabilities(cfg, wavelength, powers, extra_loss_db, extra_background)
    emitted = rng.multinomial(pulses, cfg.intensity_probabilities)
    detections = rng.binomial(emitted, q)
    errors = rng.binomial(detections, np.divide(t, q, out=np.zeros_like(t), where=q > 0))
    return tuple(map(int, emitted)), tuple(map(int, detections)), tuple(map(int, errors))


def observation(cfg, window, wavelength, powers, rng, loss=0.0, background=0.0, available=True):
    counts = sample_counts(cfg, wavelength, powers, cfg.pulses_per_window, rng, loss, background) if available else ((0,0,0),)*3
    row = Telemetry(1, window, wavelength, cfg.config_version,
                    window*cfg.window_seconds, (window+1)*cfg.window_seconds,
                    tuple(powers), *counts, available=available)
    row.validate(cfg)
    return row
