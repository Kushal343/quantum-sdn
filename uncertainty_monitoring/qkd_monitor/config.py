"""Strict, hashable experiment configuration; JSON is the public format."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import math


@dataclass(frozen=True)
class Config:
    schema_version: int
    wavelengths_nm: tuple[float, ...]
    classical_wavelengths_nm: tuple[float, ...]
    intensities: tuple[float, ...]
    intensity_probabilities: tuple[float, ...]
    config_version: str
    fibre_length_km: float
    attenuation_db_per_km: float
    insertion_loss_db: float
    detector_efficiency: float
    dark_probability_per_gate: float
    misalignment_error: float
    background_coupling_per_mw: tuple[tuple[float, ...], ...]
    classical_power_grid_mw: tuple[float, ...]
    nominal_classical_powers_mw: tuple[float, ...]
    pulses_per_window: int
    window_seconds: float
    windows: int
    calibration_pulses_per_context: int
    alpha_run: float
    calibration_failure_budget: float
    anomaly_persistence: int
    recovery_windows: int
    minimum_pulses: int
    fixed_qber_threshold: float
    fixed_gain_fraction: float
    event_start: int
    event_end: int

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        for key in ("wavelengths_nm", "classical_wavelengths_nm", "intensities",
                    "intensity_probabilities", "classical_power_grid_mw",
                    "nominal_classical_powers_mw"):
            data[key] = tuple(data[key])
        data["background_coupling_per_mw"] = tuple(tuple(x) for x in data["background_coupling_per_mw"])
        obj = cls(**data)
        obj.validate()
        return obj

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def validate(self):
        def finite_tree(value):
            if isinstance(value, (tuple, list)):
                return all(finite_tree(v) for v in value)
            if isinstance(value, dict):
                return all(finite_tree(v) for v in value.values())
            return not isinstance(value, (int, float)) or (not isinstance(value, bool) and math.isfinite(value))
        if not finite_tree(asdict(self)):
            raise ValueError("All numeric settings must be finite numbers, not booleans")
        if self.schema_version != 1 or not self.config_version:
            raise ValueError("Unsupported schema or empty configuration version")
        if not self.wavelengths_nm or len(set(self.wavelengths_nm)) != len(self.wavelengths_nm):
            raise ValueError("Quantum wavelengths must be unique and nonempty")
        if len(self.intensities) != 3 or not self.intensities[0] > self.intensities[1] > self.intensities[2] == 0:
            raise ValueError("Require signal > weak > vacuum=0")
        if len(self.intensity_probabilities) != 3 or any(p <= 0 for p in self.intensity_probabilities) or not math.isclose(sum(self.intensity_probabilities), 1):
            raise ValueError("Three positive intensity probabilities must sum to one")
        if not 0 < self.detector_efficiency <= 1 or not 0 <= self.misalignment_error <= 0.5 or not 0 <= self.dark_probability_per_gate < 1:
            raise ValueError("Invalid detector parameters")
        if any(v < 0 for v in (self.fibre_length_km, self.attenuation_db_per_km, self.insertion_loss_db)):
            raise ValueError("Loss parameters must be nonnegative")
        if len(self.background_coupling_per_mw) != self.channels or any(len(row) != len(self.classical_wavelengths_nm) or any(v < 0 for v in row) for row in self.background_coupling_per_mw):
            raise ValueError("Coupling matrix must be nonnegative [quantum, classical]")
        if not self.classical_wavelengths_nm or not self.classical_power_grid_mw or any(x < 0 for x in self.classical_power_grid_mw) or len(set(self.classical_power_grid_mw)) != len(self.classical_power_grid_mw):
            raise ValueError("Invalid classical powers/wavelengths")
        if len(self.nominal_classical_powers_mw) != len(self.classical_wavelengths_nm) or any(x not in self.classical_power_grid_mw for x in self.nominal_classical_powers_mw):
            raise ValueError("Nominal powers must belong to calibration grid")
        for name in ("pulses_per_window", "windows", "calibration_pulses_per_context", "anomaly_persistence", "recovery_windows", "minimum_pulses"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.window_seconds <= 0 or self.pulses_per_window < self.minimum_pulses:
            raise ValueError("Invalid monitoring window")
        if not 0 < self.calibration_failure_budget < self.alpha_run < 1:
            raise ValueError("Require 0 < calibration budget < run alpha < 1")
        if not 0 < self.fixed_qber_threshold < 0.5 or not 0 < self.fixed_gain_fraction < 1:
            raise ValueError("Invalid fixed thresholds")
        if type(self.event_start) is not int or type(self.event_end) is not int or not 0 < self.event_start < self.event_end < self.windows:
            raise ValueError("Event bounds must be inside monitoring horizon")

    @property
    def channels(self):
        return len(self.wavelengths_nm)

    @property
    def tests_per_window(self):
        return self.channels * 2 * len(self.intensities)

    @property
    def alpha_test(self):
        return (self.alpha_run - self.calibration_failure_budget) / (self.windows * self.tests_per_window)

    def to_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()
