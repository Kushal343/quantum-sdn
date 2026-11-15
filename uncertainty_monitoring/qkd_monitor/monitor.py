"""Fixed configuration monitor with end-of-window advisory output gating."""
from dataclasses import dataclass
import time
import numpy as np
from scipy.stats import binom
from .statistics import wilson

POLICIES = ("passive", "fixed_threshold", "pointwise", "uncertainty")
FEATURES = ("signal_gain", "weak_gain", "vacuum_gain", "signal_error_gain", "weak_error_gain", "vacuum_error_gain")


@dataclass
class ChannelState:
    last_window: int = -1
    bad_streak: int = 0
    good_streak: int = 0
    held: bool = False


class Monitor:
    def __init__(self, cfg, calibration, policy="uncertainty"):
        if policy not in POLICIES:
            raise ValueError("Unknown policy")
        if cfg.fingerprint != calibration.config_fingerprint:
            raise ValueError("Calibration and monitoring configurations differ")
        self.cfg, self.calibration, self.policy = cfg, calibration, policy
        self.states = [ChannelState() for _ in range(cfg.channels)]

    def process(self, row):
        start = time.perf_counter_ns()
        row.validate(self.cfg)
        state = self.states[row.wavelength]
        if row.window != state.last_window+1:
            raise ValueError("Duplicate, stale or skipped window: emit explicit unavailable records for gaps")
        state.last_window = row.window
        was_held = state.held
        cell = self.calibration.lookup(row.classical_powers_mw,row.wavelength)
        category, reason = "NORMAL", "Within expected measured-count ranges"
        anomalous = False
        pvalues, flagged = [], []
        out_of_budget = row.window >= self.cfg.windows
        insufficient = not row.available or sum(row.emitted) < self.cfg.minimum_pulses or min(row.emitted) == 0
        if out_of_budget:
            category, reason = "OUT_OF_BUDGET", "Predeclared monitoring horizon exhausted; no further inference"
        elif insufficient:
            category, reason = "INCONCLUSIVE", "Unavailable or insufficient emitted observations"
        elif self.policy in ("uncertainty", "pointwise") and cell is None:
            category, reason = "INCONCLUSIVE", "Measured powers outside calibrated contexts"
        elif self.policy in ("uncertainty", "pointwise"):
            n = np.tile(row.emitted,2)
            counts = np.array(row.detections+row.errors)
            if self.policy == "uncertainty":
                lower, upper = cell["lower"], cell["upper"]
                test_level = self.cfg.alpha_test
            else:
                # Same contexts/features, but plug-in rates and per-window budget.
                # No calibration or complete-run error guarantee is claimed here.
                lower = upper = np.array(cell["detections"]+cell["errors"])/np.tile(cell["emitted"],2)
                test_level = self.cfg.alpha_run/self.cfg.tests_per_window
            pvalues = np.minimum(1,2*np.minimum(binom.cdf(counts,n,lower),binom.sf(counts-1,n,upper))).tolist()
            flagged = [feature for feature,p in zip(FEATURES,pvalues) if p <= test_level]
            anomalous = bool(flagged)
            if anomalous:
                category, reason = "UNEXPLAINED_ANOMALY", ", ".join(flagged)
            elif tuple(row.classical_powers_mw) != tuple(self.cfg.nominal_classical_powers_mw):
                category, reason = "EXPLAINED_CHANGE", "Counts fit independent calibration for measured classical powers"
        elif self.policy == "fixed_threshold":
            nominal = self.calibration.lookup(self.cfg.nominal_classical_powers_mw,row.wavelength)
            nominal_gain = nominal["detections"][0]/nominal["emitted"][0]
            if row.signal_qber is not None and row.signal_qber > self.cfg.fixed_qber_threshold:
                flagged.append("signal_qber")
            if row.signal_gain < self.cfg.fixed_gain_fraction*nominal_gain:
                flagged.append("signal_gain")
            anomalous = bool(flagged)
            if anomalous:
                category, reason = "UNEXPLAINED_ANOMALY", ", ".join(flagged)
        else:
            reason = "Passive collection; no operational anomaly inference"

        usable = category not in ("INCONCLUSIVE","OUT_OF_BUDGET")
        action = "NONE"
        if not usable:
            # Missing evidence must not accumulate a recovery or anomaly streak.
            state.bad_streak = state.good_streak = 0
        elif anomalous:
            state.good_streak = 0
            state.bad_streak += 1
            if state.bad_streak >= self.cfg.anomaly_persistence and not state.held:
                state.held, action = True, "HOLD_OUTPUT"
        else:
            state.bad_streak = 0
            state.good_streak += 1
            if state.held and state.good_streak >= self.cfg.recovery_windows:
                state.held, action = False, "RESTORE_OUTPUT"
        operational_state = "QUARANTINED" if state.held else ("OBSERVING" if anomalous or not usable else "ACTIVE")
        lo, hi = wilson(row.errors[0],row.detections[0])
        return {
            "policy": self.policy, "window": row.window, "wavelength": row.wavelength,
            "time_seconds": row.end_seconds, "config_version": row.config_version,
            "category": category, "state": operational_state, "reason": reason,
            "action": action, "anomalous": anomalous, "bad_streak": state.bad_streak,
            "held_during_window": was_held, "held_next_window": state.held,
            "signal_qber": row.signal_qber, "qber_ci_lower": lo, "qber_ci_upper": hi,
            "signal_gain": row.signal_gain, "signal_detections": row.detections[0],
            "available": row.available, "classical_powers_mw": list(row.classical_powers_mw),
            "minimum_pvalue": min(pvalues) if pvalues else None,
            "pvalues": dict(zip(FEATURES,pvalues)), "flagged_features": flagged,
            "alpha_per_test": (self.cfg.alpha_test if self.policy == "uncertainty" else self.cfg.alpha_run/self.cfg.tests_per_window) if self.policy in ("uncertainty","pointwise") else None,
            "controller_microseconds": (time.perf_counter_ns()-start)/1000,
        }


def replay(cfg, calibration, rows, policy):
    monitor = Monitor(cfg,calibration,policy)
    return [monitor.process(row) for row in rows]
