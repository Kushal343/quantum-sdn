"""Run a local BB84 prepare, measure, and sift experiment in Qiskit."""

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from random import Random

from qiskit import QuantumCircuit, __version__ as qiskit_version
from qiskit.primitives import StatevectorSampler


@dataclass(frozen=True)
class Scenario:
    survival: float = 1.0
    flip_probability: float = 0.0
    force_basis_mismatch: bool = False


SCENARIOS = {
    "ideal": Scenario(),
    "bit_errors": Scenario(flip_probability=0.05),
    "loss": Scenario(survival=0.5),
    "basis_mismatch": Scenario(force_basis_mismatch=True),
}


def measurement_circuit(bit, alice_basis, bob_basis, flip):
    circuit = QuantumCircuit(1)
    if bit == 1:
        circuit.x(0)
    if alice_basis == "X":
        circuit.h(0)
    if flip:
        # Y swaps the two logical bit values in either BB84 basis.
        circuit.y(0)
    if bob_basis == "X":
        circuit.h(0)
    circuit.measure_all()
    return circuit


def simulate(name, pulses, seed):
    scenario = SCENARIOS[name]
    rng = Random(seed)
    groups = Counter()
    for _ in range(pulses):
        bit = rng.randrange(2)
        alice_basis = rng.choice(("Z", "X"))
        random_bob_basis = rng.choice(("Z", "X"))
        survives = rng.random() < scenario.survival
        flip = rng.random() < scenario.flip_probability
        bob_basis = random_bob_basis
        if scenario.force_basis_mismatch:
            bob_basis = {"Z": "X", "X": "Z"}[alice_basis]
        if survives:
            groups[bit, alice_basis, bob_basis, flip] += 1

    settings = sorted(groups)
    pubs = [(measurement_circuit(*setting), None, groups[setting]) for setting in settings]
    results = StatevectorSampler(seed=seed).run(pubs).result() if pubs else ()

    basis_pairs = {
        a + b: {"detections": 0, "bob_zero": 0, "bob_one": 0, "disagreements": 0}
        for a in ("Z", "X") for b in ("Z", "X")
    }
    circuit_counts = []
    for (bit, alice_basis, bob_basis, flip), result in zip(settings, results, strict=True):
        counts = result.data.meas.get_counts()
        zero, one = counts.get("0", 0), counts.get("1", 0)
        pair = basis_pairs[alice_basis + bob_basis]
        pair["detections"] += zero + one
        pair["bob_zero"] += zero
        pair["bob_one"] += one
        pair["disagreements"] += one if bit == 0 else zero
        circuit_counts.append({
            "alice_bit": bit,
            "alice_basis": alice_basis,
            "bob_basis": bob_basis,
            "pauli_y_applied": flip,
            "counts": counts,
        })

    detected = sum(groups.values())
    sifted = sum(basis_pairs[pair]["detections"] for pair in ("ZZ", "XX"))
    errors = sum(basis_pairs[pair]["disagreements"] for pair in ("ZZ", "XX"))
    return {
        "scenario": name,
        "backend": "local Qiskit StatevectorSampler",
        "qiskit_version": qiskit_version,
        "seed": seed,
        "settings": vars(scenario),
        "emitted": pulses,
        "detected": detected,
        "lost": pulses - detected,
        "detection_gain": detected / pulses,
        "discarded_basis_mismatch": detected - sifted,
        "sifted": sifted,
        "sifted_errors": errors,
        "qber": errors / sifted if sifted else None,
        "basis_pairs": basis_pairs,
        "circuit_counts": circuit_counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all", *SCENARIOS), default="all")
    parser.add_argument("--pulses", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.pulses < 1 or args.seed < 0:
        parser.error("pulses must be positive and seed must be nonnegative")

    names = SCENARIOS if args.scenario == "all" else (args.scenario,)
    runs = [simulate(name, args.pulses, args.seed) for name in names]
    print(f"Qiskit {qiskit_version} | local StatevectorSampler | seed {args.seed}")
    print(f"{'Scenario':<17} {'Emitted':>8} {'Detected':>9} {'Sifted':>8} {'Errors':>8} {'QBER':>8}")
    for row in runs:
        qber = "N/A" if row["qber"] is None else f"{row['qber']:.2%}"
        print(f"{row['scenario']:<17} {row['emitted']:>8} {row['detected']:>9} "
              f"{row['sifted']:>8} {row['sifted_errors']:>8} {qber:>8}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(runs, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
