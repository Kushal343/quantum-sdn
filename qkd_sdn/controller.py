"""Uncertainty-aware research controller with latched isolation and rollback."""
from dataclasses import asdict
from math import sqrt
from scipy.stats import binomtest, binom
from .physics import CANDIDATES, Decoy, expected, gain_error


def wilson(errors, n, z=3.0):
    if not n:
        return 0.0, 1.0
    p = errors/n
    denom = 1+z*z/n
    centre = (p+z*z/(2*n))/denom
    radius = z*sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return max(0.0, centre-radius), min(1.0, centre+radius)


def candidate_scores(ch, clock, predictor=None):
    if predictor is None:
        return [(c, *expected(c, ch, clock)) for c in CANDIDATES]
    return [(c, *predictor.predict(ch, c, clock)) for c in CANDIDATES]


def select_configuration(ch, clock, scenario="low_skr", predictor=None):
    scores = candidate_scores(ch, clock, predictor)
    feasible = [s for s in scores if s[1] <= 0.11 and s[2] > 0]
    if not feasible:
        return None
    if scenario == "high_qber":
        # epsilon constraint: retain >=90% of best predicted SKR, minimise QBER
        best_rate = max(s[2] for s in feasible)
        return min((s for s in feasible if s[2] >= 0.9*best_rate), key=lambda s: s[1])[0]
    return max(feasible, key=lambda s: s[2])[0]


class Controller:
    def __init__(self, policy="adaptive", predictor=None):
        if policy not in ("adaptive", "fixed", "per_wavelength", "aggregate"):
            raise ValueError("Unknown policy")
        self.policy, self.predictor = policy, predictor
        self.states = {i: {"config": Decoy(), "isolated": False, "evidence": 0,
                          "baseline_gain": None, "pending": None, "cooldown": 0}
                       for i in range(4)}

    def decide(self, telemetry):
        total_n = sum(t["records"]["signal"]["sifted"] for t in telemetry)
        aggregate = sum(t["records"]["signal"]["errors"] for t in telemetry)/max(1, total_n)
        decisions = []
        for i, t in enumerate(telemetry):
            state = self.states[i]
            s = t["records"]["signal"]
            lo, hi = wilson(s["errors"], s["sifted"])
            action, reason = "continue", "Within model expectations"
            if state["isolated"]:
                decisions.append(dict(action="isolated", reason="Latched; diagnostic probes only",
                                      qber_low=lo, qber_high=hi))
                continue
            if self.policy in ("aggregate", "per_wavelength"):
                value = aggregate if self.policy == "aggregate" else t["qber"]
                if value > 0.11:
                    state["isolated"] = True
                    action, reason = "isolate", "Fixed 11% demonstration threshold exceeded"
            elif self.policy == "adaptive":
                cfg, ch = t["config"], t["channel"]
                expected_qber, _ = expected(cfg, ch, t["clock_hz"])
                inconsistent = []
                for label, intensity in (("signal", cfg.mu), ("decoy", cfg.nu), ("vacuum", 0)):
                    r = t["records"][label]
                    q, _ = gain_error(intensity, ch)
                    n = r['emitted']
                    clicks = r.get('detections', round(r['gain']*n))
                    if n and binomtest(clicks, n, q).pvalue <= 1e-5:
                        inconsistent.append(label)
                # Four tests/channel/interval. Under the trusted exact model,
                # a union bound over 16 intervals is 16*4*4*1e-5 = .00256.
                unexplained_errors = (s['sifted'] >= 100 and
                    binom.sf(s['errors']-1, s['sifted'], min(.5, expected_qber+.005)) <= 1e-5)
                suspicious = unexplained_errors or bool(inconsistent)
                state["evidence"] = state["evidence"]+1 if suspicious else 0
                if state["baseline_gain"] is None:
                    state["baseline_gain"] = s["gain"]
                if state["evidence"] >= 2:
                    state["isolated"] = True
                    action, reason = "isolate", "Persistent unexplained errors or gain residuals: " + ",".join(inconsistent)
                    state["pending"] = None
                elif suspicious:
                    action, reason = "hold", "Gathering a second interval of evidence; key release withheld"
                elif hi >= 0.11:
                    action, reason = "hold", "Insufficient evidence that QBER is below operating cap"
                elif state["pending"]:
                    pending = state["pending"]
                    pending["rates"].append(t["skr_estimate"])
                    action, reason = "verify", "Collecting post-change measurements"
                    if len(pending["rates"]) >= 2:
                        rate = sum(pending["rates"])/len(pending["rates"])
                        if rate < pending["before"]*0.90:
                            state["config"] = pending["old"]
                            action, reason = "rollback", "Measured rate fell >10%; restore previous configuration"
                        else:
                            action, reason = "keep", "Two-window rate check passed (heuristic tolerance)"
                        state["pending"] = None
                        state["cooldown"] = 4
                elif state["cooldown"]:
                    state["cooldown"] -= 1
                else:
                    low = s["gain"] < 0.75*state["baseline_gain"]
                    high = lo > 0.025
                    if low or high:
                        candidate = select_configuration(ch, t["clock_hz"],
                                     "high_qber" if high else "low_skr", self.predictor)
                        if candidate and candidate != cfg:
                            # Authoritative analytical score gates ML proposals.
                            old_e, old_r = expected(cfg, ch, t["clock_hz"])
                            new_e, new_r = expected(candidate, ch, t["clock_hz"])
                            if new_r > old_r*1.01 and new_e <= 0.11:
                                state["pending"] = {"old": cfg, "before": t["skr_estimate"], "rates": []}
                                state["config"] = candidate
                                action, reason = "retune", "Explained degradation; update valid decoy settings"
                            else:
                                reason = "Explained degradation; no useful candidate improvement"
                        else:
                            reason = "Explained degradation; retain current setting"
            decisions.append(dict(action=action, reason=reason, qber_low=lo, qber_high=hi))
        return decisions

    def snapshot(self):
        return {i: {"config": asdict(s["config"]), "isolated": s["isolated"]}
                for i, s in self.states.items()}
