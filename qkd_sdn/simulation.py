from dataclasses import replace
import numpy as np
from .physics import Channel, Decoy, gain_error, decoy_rate
from .quantum import BB84Engine

SCENARIOS = {
    "normal": "No injected disturbance",
    "loss": "Measured +5 dB loss on lambda-3",
    "noise": "Measured classical-traffic/background increase on lambda-3",
    "intercept": "Intercept-resend on 70% of lambda-3 detections",
    "weak_intercept": "Intercept-resend on 12% of lambda-3 detections",
    "tap": "Unreported 35% transmission reduction on lambda-3 (not uniquely an attack)",
    "shared_noise": "Measured common classical-traffic increase",
}


def conditions(scenario, step, onset=6, wavelength=2):
    ch = Channel(distance_km=20 + wavelength * 2)
    active = step >= onset
    intercept, tap = 0.0, 0.0
    if active and (wavelength == 2 or scenario == "shared_noise"):
        if scenario == "loss":
            ch = replace(ch, extra_loss_db=5)
        elif scenario in ("noise", "shared_noise"):
            ch = replace(ch, traffic=8)
        elif scenario == "intercept":
            intercept = 0.70
        elif scenario == "weak_intercept":
            intercept = 0.12
        elif scenario == "tap":
            tap = 0.35
    return ch, intercept, tap


class NetworkSimulator:
    def __init__(self, seed=7, pulses=250_000, interval=1.0, engine="aer"):
        if pulses < 1000 or interval <= 0:
            raise ValueError("Require at least 1000 pulses and positive interval")
        self.rng = np.random.default_rng(seed)
        if engine not in ('aer', 'binomial'):
            raise ValueError('Unknown measurement engine')
        self.engine = BB84Engine(seed+1) if engine == 'aer' else BinomialEngine(seed+1)
        self.pulses, self.interval = int(pulses), float(interval)

    def observe(self, ch, cfg=Decoy(), intercept=0.0, tap=0.0):
        if not 0 <= tap < 1:
            raise ValueError("Tap fraction must be in [0, 1)")
        # Loss acts on photons independently; detected coherent-state gain is
        # 1-exp(-eta*intensity), with background on otherwise empty gates.
        actual = replace(ch, detector_efficiency=ch.detector_efficiency*(1-tap))
        emitted = self.rng.multinomial(self.pulses,
                  [cfg.p_signal, cfg.p_decoy, 1-cfg.p_signal-cfg.p_decoy])
        records = {}
        for label, intensity, n in zip(("signal", "decoy", "vacuum"),
                                      (cfg.mu, cfg.nu, 0.0), emitted):
            gain, err = gain_error(intensity, actual)
            detected = self.rng.binomial(int(n), gain)
            # All outcomes, including background and vacuum, go through Aer.
            # Conditional optical error is represented as a BB84-symmetric Y
            # channel. Eve applies only to signal-originated detections.
            signal_gain = 1-np.exp(-actual.eta*intensity)
            eve_share = intercept * signal_gain/gain if gain else 0
            r = self.engine.measure(int(detected), err, eve_share)
            records[label] = dict(r, emitted=int(n), gain=detected/int(n) if n else 0,
                                 qber=r["errors"]/r["sifted"] if r["sifted"] else 0.5)
        s, d, v = (records[k] for k in ("signal", "decoy", "vacuum"))
        skr = decoy_rate(cfg, s["gain"], s["qber"], d["gain"], d["qber"],
                         v["gain"], self.pulses/self.interval)
        # This object is the only controller input. No attack labels, hidden
        # loss, intercept fraction or scenario identifiers are exposed here.
        return {"records": records, "qber": s["qber"], "skr_estimate": skr,
                "channel": ch, "config": cfg, "interval": self.interval,
                "clock_hz": self.pulses/self.interval}


class BinomialEngine:
    """Exact count distribution of the current independent symmetric BB84 model.

    Intended for statistical sweeps; does not execute quantum circuits. This
    reduction does not apply to correlated noise or general attacks.
    """
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.shots_executed = 0

    def measure(self, detections, error_probability, intercept_fraction=0):
        if detections < 0 or not 0 <= error_probability <= .5 or not 0 <= intercept_fraction <= 1:
            raise ValueError('Invalid BB84 sampling parameters')
        sifted = int(self.rng.binomial(detections, .5))
        error = error_probability + intercept_fraction/4*(1-2*error_probability)
        return dict(sifted=sifted, errors=int(self.rng.binomial(sifted, error)), detections=detections)
