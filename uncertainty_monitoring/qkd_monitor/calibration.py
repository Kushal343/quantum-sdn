"""Independent count calibration for a finite, explicitly supported power grid."""
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import hashlib
import json
import numpy as np
from .physics import sample_counts
from .statistics import clopper_pearson


def context_key(powers):
    return json.dumps(list(powers), separators=(",", ":"))


@dataclass
class Calibration:
    config_fingerprint: str
    seed: int
    interval_alpha: float
    cells: dict

    def lookup(self, powers, wavelength):
        # Numeric tuple matching avoids treating JSON 1 and 1.0 differently.
        requested = tuple(powers)
        for key, channels in self.cells.items():
            if tuple(json.loads(key)) == requested:
                return channels[str(wavelength)]
        return None

    def to_dict(self):
        return {"schema_version": 1, "config_fingerprint": self.config_fingerprint,
                "seed": self.seed, "interval_alpha": self.interval_alpha, "cells": self.cells}

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, allow_nan=False), encoding="utf-8")

    @classmethod
    def load(cls, path, cfg):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if set(data) != {"schema_version", "config_fingerprint", "seed", "interval_alpha", "cells"} or data["schema_version"] != 1 or data["config_fingerprint"] != cfg.fingerprint:
            raise ValueError("Calibration schema or experiment configuration does not match")
        obj = cls(data["config_fingerprint"], data["seed"], data["interval_alpha"], data["cells"])
        contexts = list(product(cfg.classical_power_grid_mw, repeat=len(cfg.classical_wavelengths_nm)))
        expected_alpha = cfg.calibration_failure_budget/(len(contexts)*cfg.tests_per_window)
        if not np.isclose(obj.interval_alpha, expected_alpha, rtol=1e-12, atol=0) or len(obj.cells) != len(contexts):
            raise ValueError("Invalid calibration confidence budget")
        for powers in contexts:
            for wavelength in range(cfg.channels):
                cell = obj.lookup(powers, wavelength)
                if cell is None:
                    raise ValueError("Calibration is incomplete")
                n, d, e = cell["emitted"], cell["detections"], cell["errors"]
                if any(len(x) != 3 for x in (n,d,e)) or sum(n) != cfg.calibration_pulses_per_context:
                    raise ValueError("Invalid calibration counts")
                lower, upper = [], []
                for counts in (d,e):
                    for k, total in zip(counts,n):
                        if type(k) is not int or type(total) is not int:
                            raise ValueError("Calibration counts must be integers")
                        lo, hi = clopper_pearson(k,total,obj.interval_alpha)
                        lower.append(lo); upper.append(hi)
                if any(not 0 <= err <= det <= total for total,det,err in zip(n,d,e)) or not np.allclose(lower,cell["lower"],rtol=1e-12,atol=0) or not np.allclose(upper,cell["upper"],rtol=1e-12,atol=0):
                    raise ValueError("Calibration bounds/counts are inconsistent")
        return obj


def calibrate(cfg, seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("Calibration seed must be a nonnegative integer")
    rng = np.random.default_rng(np.random.SeedSequence([seed, 101]))
    contexts = list(product(cfg.classical_power_grid_mw, repeat=len(cfg.classical_wavelengths_nm)))
    alpha = cfg.calibration_failure_budget/(len(contexts)*cfg.tests_per_window)
    cells = {}
    for powers in contexts:
        channels = {}
        for wavelength in range(cfg.channels):
            n, d, e = sample_counts(cfg, wavelength, powers, cfg.calibration_pulses_per_context, rng)
            lower, upper = [], []
            for counts in (d,e):
                for k, total in zip(counts,n):
                    lo, hi = clopper_pearson(k,total,alpha)
                    lower.append(lo); upper.append(hi)
            channels[str(wavelength)] = {"emitted": n, "detections": d, "errors": e,
                                        "lower": lower, "upper": upper}
        cells[context_key(powers)] = channels
    return Calibration(cfg.fingerprint, seed, alpha, cells)
