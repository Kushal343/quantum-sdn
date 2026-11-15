"""Weak+vacuum decoy estimates following Ma et al., PRA 72, 012326.

Asymptotic plug-in estimates only: monitoring confidence intervals are not a
composable finite-key proof. Noise coefficients are illustrative model inputs.
"""
from dataclasses import dataclass
from math import exp, log2


@dataclass(frozen=True)
class Decoy:
    name: str = "C3"
    mu: float = 0.6
    nu: float = 0.12
    p_signal: float = 0.75
    p_decoy: float = 0.20

    def __post_init__(self):
        if not (0 < self.nu < self.mu <= 1):
            raise ValueError("Require 0 < nu < mu <= 1")
        if not (self.p_signal > 0 and self.p_decoy > 0
                and self.p_signal + self.p_decoy < 1):
            raise ValueError("Signal, decoy and vacuum probabilities must be positive")


CANDIDATES = tuple(Decoy(f"C{i+1}", mu, nu) for i, (mu, nu) in
                   enumerate([(0.4, 0.08), (0.5, 0.1), (0.6, 0.12),
                              (0.7, 0.14), (0.8, 0.16)]))


@dataclass(frozen=True)
class Channel:
    distance_km: float = 20.0
    attenuation_db_km: float = 0.2
    extra_loss_db: float = 0.0
    detector_efficiency: float = 0.2
    dark_probability: float = 2e-5
    traffic: float = 0.2
    raman_coefficient: float = 2e-4
    crosstalk_probability: float = 1e-5
    misalignment: float = 0.015
    fwm_probability: float = 0.0

    def __post_init__(self):
        if min(self.distance_km, self.attenuation_db_km, self.extra_loss_db,
               self.dark_probability, self.traffic, self.raman_coefficient,
               self.crosstalk_probability, self.fwm_probability) < 0:
            raise ValueError("Channel parameters must be nonnegative")
        if not 0 <= self.detector_efficiency <= 1 or not 0 <= self.misalignment <= 0.5:
            raise ValueError("Invalid efficiency or misalignment")

    @property
    def eta(self):
        return self.detector_efficiency * 10 ** (-(self.distance_km *
               self.attenuation_db_km + self.extra_loss_db) / 10)

    @property
    def background(self):
        return min(1.0, self.dark_probability + self.traffic *
                   self.raman_coefficient + self.crosstalk_probability + self.fwm_probability)


def gain_error(intensity, ch):
    """Click probability and conditional bit error probability.

    A background click dominates only when no signal click occurred; double
    click treatment is simplified. No-click is an optical erasure, not |0>.
    """
    signal = 1 - exp(-ch.eta * intensity)
    bg_only = (1 - signal) * ch.background
    gain = signal + bg_only
    error = (signal * ch.misalignment + 0.5 * bg_only) / gain if gain else 0.5
    return gain, error


def entropy(p):
    if p <= 0 or p >= 1:
        return 0.0
    return -p * log2(p) - (1 - p) * log2(1 - p)


def decoy_rate(cfg, q_mu, e_mu, q_nu, e_nu, y0, clock_hz):
    """Estimated bits/s per total emitted pulses (including p_signal and q=1/2)."""
    mu, nu = cfg.mu, cfg.nu
    y1 = mu / (mu * nu - nu**2) * (q_nu * exp(nu) -
         q_mu * exp(mu) * nu**2 / mu**2 - (mu**2 - nu**2) / mu**2 * y0)
    y1 = max(0.0, min(1.0, y1))
    if y1 <= 0:
        return 0.0
    e1 = max(0.0, min(0.5, (e_nu * q_nu * exp(nu) - 0.5 * y0) / (nu * y1)))
    fraction = 0.5 * cfg.p_signal * (mu * exp(-mu) * y1 * (1 - entropy(e1)) -
                                    q_mu * 1.16 * entropy(e_mu))
    return max(0.0, fraction * clock_hz)


def expected(cfg, ch, clock_hz=250_000):
    qm, em = gain_error(cfg.mu, ch)
    qn, en = gain_error(cfg.nu, ch)
    return em, decoy_rate(cfg, qm, em, qn, en, ch.background, clock_hz)
