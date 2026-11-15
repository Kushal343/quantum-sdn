"""Independent calibration and finite-horizon operational anomaly tests.

Adapted from the Anomoly-detection branch's composite-null count approach.
This is an availability monitor, separate from cryptographic block acceptance.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from scipy.stats import beta, binom

LABELS = ('signal', 'decoy', 'vacuum')


def context_key(channel, config):
    return json.dumps([asdict(channel), asdict(config)], sort_keys=True)


def count_features(telemetry):
    result = []
    for label in LABELS:
        r = telemetry['records'][label]
        n, d, s, e = (r[k] for k in ('emitted', 'detections', 'sifted', 'errors'))
        if any(type(x) is not int for x in (n, d, s, e)) or not 0 <= e <= s <= d <= n:
            raise ValueError('Invalid integer count telemetry')
        result.append((label + '_gain', d, n))
        result.append((label + '_qber', e, s))
    return result


def exact_interval(k, n, alpha):
    if not n:
        return 0.0, 1.0
    return (0.0 if k == 0 else float(beta.ppf(alpha/2, k, n-k+1)),
            1.0 if k == n else float(beta.isf(alpha/2, k+1, n-k)))


def interval_pvalue(k, n, lower, upper):
    if n == 0:
        return 1.0
    return min(1.0, 2*min(float(binom.cdf(k, n, lower)),
                            float(binom.sf(k-1, n, upper))))


@dataclass
class Calibration:
    cells: dict
    calibration_budget: float
    seed: int
    pulses_per_context: int

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.cells, sort_keys=True).encode()).hexdigest()

    def save(self, path):
        Path(path).write_text(json.dumps(dict(schema=1, fingerprint=self.fingerprint,
            calibration_budget=self.calibration_budget, seed=self.seed,
            pulses_per_context=self.pulses_per_context, cells=self.cells), indent=2), encoding='utf-8')

    def assess(self, telemetry, alpha):
        features = count_features(telemetry)
        cell = self.cells.get(context_key(telemetry['channel'], telemetry['config']))
        if cell is None:
            return None
        return {name: interval_pvalue(k, n, *cell[name]['interval']) for name, k, n in features}


def calibrate(contexts, seed=701, pulses=5_000_000, budget=.005):
    """Fresh benign samples, separate from runtime observations; finite grid only."""
    from .simulation import NetworkSimulator
    if type(pulses) is not int or pulses < 1000 or not 0 < budget < 1:
        raise ValueError('Invalid calibration settings')
    unique = {context_key(ch, cfg): (ch, cfg) for ch, cfg in contexts}
    if not unique:
        raise ValueError('Calibration contexts cannot be empty')
    alpha = budget/(len(unique)*6)
    simulator = NetworkSimulator(seed, pulses, engine='binomial')
    cells = {}
    for key, (ch, cfg) in unique.items():
        t = simulator.observe(ch, cfg)
        cells[key] = {name: dict(count=k, trials=n, interval=exact_interval(k, n, alpha))
                      for name, k, n in count_features(t)}
    return Calibration(cells, budget, seed, pulses)
