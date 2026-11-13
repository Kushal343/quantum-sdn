"""Qiskit adaptation of the supplied bb84_simulation.ipynb.

Keeps explicit bit arrays and a revealed random test sample. No error correction
or privacy amplification: remaining arrays are raw key material, not secure keys.
Wavelengths are independently encoded logical modes, not extra entangled qubits.
"""
from dataclasses import dataclass
import numpy as np
from .quantum import BB84Engine
from .controller import wilson


def bb84(n_qubits=2000, eve_fraction=0.0, channel_noise=0.0,
         sample_fraction=0.25, qber_threshold=0.11, seed=42,
         detection_probability=1.0):
    if not isinstance(n_qubits, (int, np.integer)) or n_qubits < 0:
        raise ValueError("n_qubits must be a nonnegative integer")
    if not 0 <= eve_fraction <= 1 or not 0 <= channel_noise <= 0.5:
        raise ValueError("Invalid Eve fraction or channel noise")
    if not 0 < sample_fraction <= 1 or not 0 <= detection_probability <= 1:
        raise ValueError("Invalid sample fraction or detection probability")
    if not 0 <= qber_threshold <= 0.5:
        raise ValueError("Invalid QBER threshold")
    rng = np.random.default_rng(seed)
    alice_bits = rng.integers(0, 2, n_qubits)
    alice_bases = rng.integers(0, 2, n_qubits)
    bob_bases = rng.integers(0, 2, n_qubits)
    intercepted = rng.random(n_qubits) < eve_fraction
    eve_bases = rng.integers(0, 2, n_qubits)
    # Basis-independent erasure; discarded pulses never become bit zero.
    detected = rng.random(n_qubits) < detection_probability
    bob_bits = np.full(n_qubits, -1, dtype=int)
    engine = BB84Engine(seed)
    circuits, groups = [], []
    for bit in (0, 1):
        for a in (0, 1):
            for b in (0, 1):
                for eve in (None, 0, 1):
                    selection = detected & (alice_bits == bit) & (alice_bases == a) & (bob_bases == b)
                    selection &= (~intercepted if eve is None else intercepted & (eve_bases == eve))
                    indices = np.flatnonzero(selection)
                    if len(indices):
                        circuits.append(engine.circuit(bit, a, b, channel_noise, eve))
                        groups.append(indices)
    shots_executed = 0
    if circuits:
        shots = max(map(len, groups))
        result = engine.backend.run(circuits, shots=shots, memory=True,
                    seed_simulator=int(rng.integers(1, 2**31-1))).result()
        shots_executed = shots*len(circuits)
        for i, indices in enumerate(groups):
            # Qiskit prints high-index classical bits first; Bob is the last
            # measured classical bit, so his outcome is the leftmost character.
            bob_bits[indices] = [int(x.replace(" ", "")[0])
                                for x in result.get_memory(i)[:len(indices)]]
    keep = detected & (alice_bases == bob_bases)
    alice_sifted, bob_sifted = alice_bits[keep], bob_bits[keep]
    n_sifted = len(alice_sifted)
    n_sample = min(n_sifted, max(1, int(sample_fraction*n_sifted))) if n_sifted else 0
    sample_idx = rng.choice(n_sifted, n_sample, replace=False)
    errors = int(np.count_nonzero(alice_sifted[sample_idx] != bob_sifted[sample_idx]))
    qber = errors/n_sample if n_sample else None
    mask = np.ones(n_sifted, dtype=bool)
    mask[sample_idx] = False
    alice_key, bob_key = alice_sifted[mask], bob_sifted[mask]
    aborted = qber is None or qber > qber_threshold
    return {
        "n_sent": n_qubits, "n_detected": int(detected.sum()), "n_sifted": n_sifted,
        "n_sample": n_sample, "sample_errors": errors, "qber": qber,
        "qber_ci": wilson(errors, n_sample, z=1.96), "aborted": aborted,
        "status": "insufficient_data" if qber is None else "abort" if aborted else "below_demo_threshold",
        "alice_key": alice_key, "bob_key": bob_key,
        "keys_match": bool(n_sifted and np.array_equal(alice_key, bob_key)),
        "key_error_rate": float(np.mean(alice_key != bob_key)) if len(alice_key) else None,
        "sifted_errors": int(np.count_nonzero(alice_sifted != bob_sifted)),
        "aer_shots": shots_executed,
    }


@dataclass(frozen=True)
class Wavelength:
    id: str
    wavelength_nm: float
    detection_probability: float = 1.0
    channel_noise: float = 0.0


WAVELENGTHS = tuple(Wavelength(f"lambda_{i+1}", 1550.0+0.8*i) for i in range(4))


def run_wdm(intervals=12, n_qubits=12_000, attack_start=4, attack_fraction=0.8,
            target="lambda_3", seed=42, channels=WAVELENGTHS):
    """Independent channel/session RNG streams; attack labels are evaluator-only.

    This is logical WDM, without an optical mux, Raman or crosstalk simulation.
    Telemetry contains only publicly sampled error counts; full sifted errors
    are excluded. No remaining key arrays are written to experiment logs.
    """
    if intervals <= 0 or attack_start < 0 or not 0 <= attack_fraction <= 1:
        raise ValueError("Invalid experiment settings")
    ids = [c.id for c in channels]
    if not channels or len(set(ids)) != len(ids) or target not in ids:
        raise ValueError("Need unique channels and a valid attack target")
    streams = np.random.SeedSequence(seed).spawn(intervals*len(channels))
    telemetry, truth = [], []
    for step in range(intervals):
        for index, ch in enumerate(channels):
            fraction = attack_fraction if step >= attack_start and ch.id == target else 0
            session_seed = int(streams[step*len(channels)+index].generate_state(1)[0])
            r = bb84(n_qubits=n_qubits, eve_fraction=fraction, channel_noise=ch.channel_noise,
                     seed=session_seed, detection_probability=ch.detection_probability)
            lo, hi = r["qber_ci"]
            telemetry.append({"interval": step, "channel": ch.id, "wavelength_nm": ch.wavelength_nm,
                              **{k: r[k] for k in ("n_sent", "n_detected", "n_sifted", "n_sample",
                                                  "sample_errors", "qber", "aborted", "status", "aer_shots")},
                              "qber_low": lo, "qber_high": hi})
            truth.append({"interval": step, "channel": ch.id, "eve_fraction": fraction,
                          "expected_qber": ch.channel_noise + fraction/4*(1-2*ch.channel_noise)})
    return telemetry, truth


def aggregate_telemetry(frame):
    import pandas as pd
    result = frame.groupby("interval")[["sample_errors", "n_sample"]].sum()
    result["qber"] = result.sample_errors/result.n_sample.replace(0, float("nan"))
    return result.reset_index()
