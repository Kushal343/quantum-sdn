# BB84 simulation with IBM Qiskit

See [extension interfaces and configuration options](EXTENDING.md) for future integration, controller handoffs and custom measurement adapters.

The connected four-wavelength experiment is available through `monitor.py`. See [the connection guide](CONNECTION.md) for calibration, telemetry definitions, example scenarios and commands.

This experiment models one BB84 sender and receiver. Alice prepares a qubit, Bob measures it, and the simulation keeps the detected outcomes where their bases match. It reports the number of bits left after sifting and the quantum bit error rate (QBER) on those bits.

The circuits run locally with IBM's Qiskit SDK and its `StatevectorSampler`. Installation needs access to the packages on PyPI. Running the experiment uses no IBM account or cloud job. The numbers describe simulated, sifted bits. Secure key processing and the WDM controller are separate project stages.

## Run the experiment

Use Python 3.12 and open PowerShell from the project root.

```powershell
cd bb84_qiskit
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe simulate.py --scenario all --pulses 10000 --seed 42 --output results/my_run.json
```

For a smaller example that isolates loss:

```powershell
.\.venv\Scripts\python.exe simulate.py --scenario loss --pulses 1000 --seed 42
```

The console prints one row per scenario. Use `--output` to save the scenario settings, Qiskit version, counts, and QBER to JSON. The seed makes repeated runs reproducible with the same software and inputs.

## What the circuit does

| Alice's bit | Basis Z | Basis X |
|---|---|---|
| 0 | Prepare the starting state with no gate | Apply H to prepare the plus state |
| 1 | Apply X to prepare the one state | Apply X and then H to prepare the minus state |

Alice chooses a random bit and basis for each pulse. Bob independently chooses Z or X in the standard scenarios. Qiskit measures in Z by default. Applying H immediately before that measurement lets Bob measure in X. When the bases match, an ideal circuit recovers Alice's bit. When the bases differ, each measurement outcome is equally likely in the ideal model.

For example, Alice sends bit 1 in X. The circuit applies X and then H. If Bob also uses X, his H reverses Alice's H and the measurement gives 1. If Bob uses Z, he measures the minus state directly and gets either 0 or 1. This outcome is discarded during sifting because the bases differ.

The simulator groups surviving pulses that use identical circuit settings. It submits one circuit per group with the group's pulse count as its number of shots. Qiskit supplies the measurement outcomes. Python classifies them by basis pair and counts disagreements. Grouping saves work and preserves the aggregate counts, but the output records totals rather than pulse order.

## Scenarios

| Scenario | What changes | Expected behaviour |
|---|---|---|
| `ideal` | Every pulse survives and the qubit arrives intact. | Roughly half the measurements survive sifting. Their QBER is zero. |
| `bit_errors` | A Pauli Y gate is inserted between preparation and measurement with probability 5%. | Y flips the logical bit in both BB84 bases. The sifted QBER is close to 5%, with sampling variation. |
| `loss` | Each pulse has a 50% chance of surviving. Python samples erasures before creating the measurement groups. | Bob receives roughly half the pulses and keeps roughly half of those after sifting. Pure erasure leaves the sifted QBER at zero in this model. |
| `basis_mismatch` | Bob always uses the opposite basis from Alice. | Bob measures every pulse. Sifting discards all outcomes, and QBER appears as N/A because there are zero sifted bits. |

The Y gate is a deliberate circuit disturbance. The loss case represents a missing detection with a classical erasure decision. Neither requires an optical device model. Compare the ideal and loss cases to see how a channel can deliver fewer useful bits even when its error percentage stays the same.

## Read the output

* **Emitted** counts the attempted transmissions. **Detected** counts the surviving pulses for which Qiskit sampled an outcome.
* **Sifted** counts detections with basis pair ZZ or XX. **Errors** counts disagreements between Alice and Bob among those detections.
* **QBER** divides sifted errors by sifted bits. The console displays a percentage and JSON stores a fraction. With zero sifted bits, JSON stores `null`.
* **Basis pairs** show detections, Bob's zero and one outcomes, and disagreements for ZZ, ZX, XZ, and XX. Mismatched disagreements stay outside QBER.
* **Circuit counts** expose the measured outcomes per Alice bit, basis pair, and inserted disturbance so you can audit the totals.

## Verified example run

The saved run used Python 3.12.8, Qiskit 2.6.1, 10,000 attempted pulses per scenario, and seed 42.

| Scenario | Detected | Sifted | Sifted errors | QBER |
|---|---:|---:|---:|---:|
| Ideal | 10,000 | 5,039 | 0 | 0.00% |
| Bit errors | 10,000 | 5,039 | 263 | 5.22% |
| Loss | 5,068 | 2,532 | 0 | 0.00% |
| Basis mismatch | 10,000 | 0 | 0 | N/A |

The saved JSON reproduced exactly on rerun. The checks also reconciled emitted, lost, detected, discarded and sifted counts, and verified that QBER remains undefined when no pulse survives.

## Files added

| File | Purpose |
|---|---|
| `simulate.py` | Builds BB84 circuits, samples outcomes in Qiskit, and calculates sifting statistics. |
| `requirements.txt` | Pins the Qiskit version for the standalone environment. |
| `README.md` | Explains setup, gates, scenarios, and how to interpret the output. |
| `.gitignore` | Keeps the local environment and Python caches out of source control. |
| `results/example_run.json` | Measurement counts and summaries from the verified run above. |

IBM documents the local sampler and how to read measurement counts in its [Qiskit SDK simulation guide](https://quantum.cloud.ibm.com/docs/en/guides/simulate-with-qiskit-sdk-primitives).
