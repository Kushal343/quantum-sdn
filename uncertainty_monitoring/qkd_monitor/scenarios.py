"""External experiment labels never enter Telemetry or monitoring code."""
from dataclasses import dataclass
import numpy as np
from .physics import observation


SCENARIOS = {
    "stable": "Benign stationary sampling variation",
    "classical_power": "Measured, calibrated classical-power increase",
    "local_loss": "3 dB unexplained extra loss on quantum channel 3",
    "local_background": "Unexplained optical background on quantum channel 3",
    "gradual_drift": "Slowly increasing unexplained background on channel 3",
    "common_loss": "2 dB shared unexplained loss",
    "transient": "One-window local background transient",
    "off_grid": "Measured power outside the calibrated context grid",
    "telemetry_gap": "Three missing reports on quantum channel 3",
    "passive_tap": "Observation-equivalent extra attenuation; no leakage claim"
}


@dataclass(frozen=True)
class Truth:
    window: int
    wavelength: int
    event: str
    target: bool
    onset: int | None
    ending: int | None


def simulate(cfg, scenario, seed):
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario}")
    if type(seed) is not int or seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    # Same physical loss and RNG path for local_loss/passive_tap by construction.
    # Independent per-window/channel streams prevent policy or channel coupling.
    rows, truth = [], []
    target_channel = min(2, cfg.channels-1)
    for window in range(cfg.windows):
        active = cfg.event_start <= window < cfg.event_end
        powers = tuple(cfg.nominal_classical_powers_mw)
        if active and scenario == "classical_power":
            powers = (max(cfg.classical_power_grid_mw),)*len(powers)
        if active and scenario == "off_grid":
            powers = (1.5,) + powers[1:]
        for wavelength in range(cfg.channels):
            local = wavelength == target_channel
            target = False
            loss = background = 0.0
            available = True
            end = cfg.event_end
            if active:
                if scenario in ("local_loss", "passive_tap") and local:
                    loss, target = 3.0, True
                elif scenario == "common_loss":
                    loss, target = 2.0, True
                elif scenario == "local_background" and local:
                    background, target = 0.003, True
                elif scenario == "gradual_drift" and local:
                    background = 0.003*(window-cfg.event_start+1)/(cfg.event_end-cfg.event_start)
                    target = True
                elif scenario == "transient" and local and window == cfg.event_start:
                    background, target = 0.003, True
                    end = cfg.event_start+1
                elif scenario == "telemetry_gap" and local and window < cfg.event_start+3:
                    available, target = False, True
                    end = cfg.event_start+3
                elif scenario == "off_grid":
                    target = True
            rng = np.random.default_rng(np.random.SeedSequence([seed, 202, window, wavelength]))
            row = observation(cfg,window,wavelength,powers,rng,loss,background,available)
            rows.append(row)
            truth.append(Truth(window,wavelength,scenario if target else "benign",target,
                               cfg.event_start if target else None, end if target else None))
    return rows, truth
