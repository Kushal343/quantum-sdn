"""Observable-only transport schema. Scenario truth is deliberately absent."""
from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class Telemetry:
    schema_version: int
    window: int
    wavelength: int
    config_version: str
    start_seconds: float
    end_seconds: float
    classical_powers_mw: tuple[float, ...]
    emitted: tuple[int, int, int]
    detections: tuple[int, int, int]
    errors: tuple[int, int, int]
    available: bool = True

    def validate(self, cfg):
        if self.schema_version != 1 or self.config_version != cfg.config_version:
            raise ValueError("Unknown schema/configuration version")
        if type(self.window) is not int or self.window < 0 or type(self.wavelength) is not int or not 0 <= self.wavelength < cfg.channels:
            raise ValueError("Invalid window or wavelength")
        if not all(math.isfinite(t) for t in (self.start_seconds, self.end_seconds)) or self.start_seconds < 0 or self.end_seconds <= self.start_seconds:
            raise ValueError("Invalid timestamps")
        if not math.isclose(self.start_seconds, self.window*cfg.window_seconds, abs_tol=1e-8) or not math.isclose(self.end_seconds, (self.window+1)*cfg.window_seconds, abs_tol=1e-8):
            raise ValueError("Timestamps must match the non-overlapping window schedule")
        if type(self.available) is not bool or len(self.classical_powers_mw) != len(cfg.classical_wavelengths_nm) or any(not math.isfinite(p) or p < 0 for p in self.classical_powers_mw):
            raise ValueError("Invalid availability or measured powers")
        if any(len(x) != 3 for x in (self.emitted, self.detections, self.errors)):
            raise ValueError("Three intensity categories are required")
        for n, d, e in zip(self.emitted, self.detections, self.errors):
            if any(type(x) is not int for x in (n, d, e)) or not 0 <= e <= d <= n:
                raise ValueError("Counts require integer 0 <= errors <= detections <= emitted")
        if sum(self.emitted) > cfg.pulses_per_window:
            raise ValueError("Emitted count exceeds configured window capacity")
        if not self.available and any(self.emitted + self.detections + self.errors):
            raise ValueError("Unavailable telemetry cannot carry observed counts")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        for key in ("classical_powers_mw", "emitted", "detections", "errors"):
            data[key] = tuple(data[key])
        return cls(**data)

    @property
    def signal_qber(self):
        return self.errors[0] / self.detections[0] if self.detections[0] else None

    @property
    def signal_gain(self):
        return self.detections[0] / self.emitted[0] if self.emitted[0] else None
