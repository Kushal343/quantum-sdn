"""Optical-to-BB84 measurement adapter shared by calibration and runtime."""
from copy import deepcopy
from dataclasses import replace
import numpy as np
from qiskit.primitives import StatevectorSampler
try:
    from .simulate import measurement_circuit
except ImportError:
    from simulate import measurement_circuit

from qkd_monitor.calibration import calibrate
from qkd_monitor.scenarios import simulate as optical_simulation
from qkd_monitor.statistics import clopper_pearson

def sift_counts(emitted, detected, errors, seed, sampler_factory=StatevectorSampler):
    """Sample basis assignments, execute circuits, and audit all detections.

    The optical simulator supplies detections and disturbance counts. Those
    counts determine whether the transmitted qubit gets a Pauli Y operation.
    Qiskit supplies Bob's measurement outcomes. Gains are sifted detections
    per emitted pulse, so mismatched bases are excluded from monitor errors.
    """
    rng = np.random.default_rng(seed)
    settings, pubs = [], []
    for category in range(3):
        for flip, total in ((False, detected[category] - errors[category]),
                            (True, errors[category])):
            groups = rng.multinomial(total, [0.125] * 8)
            for index, shots in enumerate(groups):
                if shots == 0:
                    continue
                bit = index // 4
                alice_basis = ("Z", "X")[(index // 2) % 2]
                bob_basis = ("Z", "X")[index % 2]
                settings.append((category, bit, alice_basis, bob_basis, flip))
                pubs.append((measurement_circuit(bit, alice_basis, bob_basis, flip),
                             None, int(shots)))
    sampler_seed = int(rng.integers(0, 2**32))
    results = sampler_factory(seed=sampler_seed).run(pubs).result() if pubs else ()
    sifted, sifted_errors = [0] * 3, [0] * 3
    basis_counts = [{pair: {"detections": 0, "disagreements": 0}
                     for pair in ("ZZ", "ZX", "XZ", "XX")} for _ in range(3)]
    circuit_results = []
    for setting, result in zip(settings, results, strict=True):
        category, bit, alice_basis, bob_basis, flip = setting
        counts = result.data.meas.get_counts()
        total = sum(counts.values())
        disagreements = counts.get(str(1 - bit), 0)
        pair = basis_counts[category][alice_basis + bob_basis]
        pair["detections"] += total
        pair["disagreements"] += disagreements
        if alice_basis == bob_basis:
            sifted[category] += total
            sifted_errors[category] += disagreements
        circuit_results.append({
            "category": category, "alice_bit": bit, "alice_basis": alice_basis,
            "bob_basis": bob_basis, "pauli_y_applied": flip, "counts": counts,
        })
    audit = {
        "emitted": list(emitted), "optical_detections": list(detected),
        "optical_disturbance_counts": list(errors),
        "sifted_detections": sifted, "sifted_errors": sifted_errors,
        "basis_counts": basis_counts, "sampler_seed": sampler_seed,
        "circuit_results": circuit_results,
    }
    return tuple(sifted), tuple(sifted_errors), audit


def qiskit_calibration(cfg, seed, count_adapter=sift_counts, calibration_source=calibrate):
    calibration = deepcopy(calibration_source(cfg, seed))
    audit_rows = []
    for context_index, channels in enumerate(calibration.cells.values()):
        for wavelength in range(cfg.channels):
            cell = channels[str(wavelength)]
            random_seed = np.random.SeedSequence([seed, 404, context_index, wavelength])
            detections, errors, audit = count_adapter(
                cell["emitted"], cell["detections"], cell["errors"], random_seed)
            cell["detections"], cell["errors"] = detections, errors
            lower, upper = [], []
            for counts in (detections, errors):
                for count, total in zip(counts, cell["emitted"]):
                    lo, hi = clopper_pearson(count, total, calibration.interval_alpha)
                    lower.append(lo)
                    upper.append(hi)
            cell["lower"], cell["upper"] = lower, upper
            audit_rows.append({"context_index": context_index, "wavelength": wavelength,
                               **audit})
    return calibration, audit_rows


def qiskit_trace(cfg, scenario, seed, count_adapter=sift_counts, observation_source=optical_simulation):
    optical_rows, truth = observation_source(cfg, scenario, seed)
    observations, audit_rows = [], []
    for row in optical_rows:
        random_seed = np.random.SeedSequence([seed, 303, row.window, row.wavelength])
        detected, errors, audit = count_adapter(row.emitted, row.detections, row.errors,
                                             random_seed)
        observation = replace(row, detections=detected, errors=errors)
        observation.validate(cfg)
        observations.append(observation)
        audit_rows.append({"window": row.window, "wavelength": row.wavelength, **audit})
    return observations, truth, audit_rows
