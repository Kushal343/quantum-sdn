"""Declared illustrative noise scenarios. Hidden changes never enter controller context."""
from dataclasses import replace
import numpy as np
from .physics import Channel, CANDIDATES
from .simulation import SCENARIOS, conditions

NOISE_SCENARIOS = dict(SCENARIOS, dark_counts='Measured detector dark-count increase',
    raman='Measured Raman-like background increase', fwm='Measured FWM-like effective background',
    crosstalk='Measured filter leakage increase', misalignment='Measured polarization/phase misalignment',
    burst='One-window unreported background burst', correlated='Unreported AR(1) misalignment drift',
    transient='One-window hidden attenuation then recovery', model_mismatch='Persistent unreported detector drift',
    missing='Missing telemetry on wavelength 3', unsupported='Measured context outside calibration grid')


def known_contexts():
    for i in range(4):
        base = Channel(distance_km=20+i*2)
        variants = [base, replace(base, extra_loss_db=5), replace(base, traffic=8),
            replace(base, dark_probability=.001), replace(base, traffic=4, raman_coefficient=.0004),
            replace(base, fwm_probability=.0015), replace(base, crosstalk_probability=.0015),
            replace(base, misalignment=.05)]
        for ch in variants:
            for cfg in CANDIDATES:
                yield ch, cfg


class Scenario:
    def __init__(self, name, seed, onset=6):
        if name not in NOISE_SCENARIOS:
            raise ValueError('Unknown scenario')
        self.name, self.onset = name, onset
        self.rng = np.random.default_rng(np.random.SeedSequence([seed, 9871]))
        self.drift = 0.0

    def observe(self, sim, config, step, wavelength):
        ch, eve, tap = conditions(self.name, step, self.onset, wavelength)
        observed = actual = ch
        available = True
        if step >= self.onset:
            if self.name == 'correlated':
                # Update once per interval and apply the same drift to all wavelengths.
                if wavelength == 0:
                    self.drift = .85*self.drift + self.rng.normal(0, .004)
                actual = replace(ch, misalignment=float(np.clip(ch.misalignment+self.drift, 0, .5)))
            elif wavelength == 2:
                changes = dict(dark_counts=dict(dark_probability=.001),
                    raman=dict(traffic=4, raman_coefficient=.0004), fwm=dict(fwm_probability=.0015),
                    crosstalk=dict(crosstalk_probability=.0015), misalignment=dict(misalignment=.05))
                if self.name in changes:
                    actual = observed = replace(ch, **changes[self.name])
                elif self.name == 'burst' and step == self.onset:
                    actual = replace(ch, crosstalk_probability=.02)
                elif self.name == 'transient' and step == self.onset:
                    tap = .35
                elif self.name == 'model_mismatch':
                    actual = replace(ch, misalignment=.05)
                elif self.name == 'unsupported':
                    actual = observed = replace(ch, traffic=3.14159)
                elif self.name == 'missing' and step < self.onset+2:
                    available = False
        t = sim.observe(actual, config, eve, tap)
        t.update(channel=observed, available=available, window=step)
        return t
