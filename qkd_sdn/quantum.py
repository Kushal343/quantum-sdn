"""All detected BB84 measurement outcomes are sampled by Qiskit Aer.

Equivalent independent preparations are grouped into circuits to avoid building
one circuit per pulse. Each circuit shot still represents one detected pulse.
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import pauli_error


class BB84Engine:
    def __init__(self, seed=7):
        self.rng = np.random.default_rng(seed)
        self.backend = AerSimulator(method="stabilizer", max_parallel_threads=1)
        self.shots_executed = 0

    @staticmethod
    def circuit(bit, alice_basis, bob_basis, error_probability=0, eve_basis=None):
        qc = QuantumCircuit(1, 2 if eve_basis is not None else 1)
        if bit:
            qc.x(0)
        if alice_basis:
            qc.h(0)
        if eve_basis is not None:
            if eve_basis:
                qc.h(0)
            qc.measure(0, 0)  # collapse, then resend the measured state
            if eve_basis:
                qc.h(0)
        if error_probability:
            # A Y error flips the measurement outcome in both BB84 bases.
            qc.append(pauli_error([("Y", error_probability),
                                   ("I", 1-error_probability)]).to_instruction(), [0])
        if bob_basis:
            qc.h(0)
        qc.measure(0, qc.num_clbits - 1)
        return qc

    def measure(self, detections, error_probability, intercept_fraction=0.0):
        if detections < 0 or not 0 <= error_probability <= 0.5 or not 0 <= intercept_fraction <= 1:
            raise ValueError("Invalid BB84 sampling parameters")
        if not detections:
            return {"sifted": 0, "errors": 0, "detections": 0}
        circuits, groups = [], []
        # Random bit, Alice basis, Bob basis, Eve participation and Eve basis.
        specs, weights = [], []
        for bit in (0, 1):
            for a in (0, 1):
                for b in (0, 1):
                    specs.append((bit, a, b, None))
                    weights.append((1-intercept_fraction)/8)
                    for eve in (0, 1):
                        specs.append((bit, a, b, eve))
                        weights.append(intercept_fraction/16)
        counts = self.rng.multinomial(int(detections), weights)
        for spec, count in zip(specs, counts):
            if count:
                bit, a, b, eve = spec
                circuits.append(self.circuit(bit, a, b, error_probability, eve))
                groups.append((bit, a, b, int(count)))
        # Aer has a single shots count per job. Unused padding shots are ignored.
        shots = max(g[3] for g in groups)
        result = self.backend.run(circuits, shots=shots, memory=True,
                  seed_simulator=int(self.rng.integers(1, 2**31-1))).result()
        self.shots_executed += shots * len(circuits)
        sifted = errors = 0
        for i, (bit, a, b, count) in enumerate(groups):
            if a == b:
                outcomes = result.get_memory(i)[:count]
                sifted += count
                errors += sum(int(outcome.replace(" ", "")[0]) != bit for outcome in outcomes)
        return {"sifted": sifted, "errors": errors, "detections": int(detections)}
