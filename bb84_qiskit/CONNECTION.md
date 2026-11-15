# Qiskit BB84 connected to uncertainty monitoring

## The connected workflow

The new `monitor.py` entry point joins the existing projects. It runs four logical wavelengths, produces BB84 measurement outcomes with IBM Qiskit, then passes observations to the existing four monitoring policies.

```text
Optical scenario and fixed signal weak vacuum settings
    -> Python samples detections and disturbance counts
    -> Random Alice bits and Alice and Bob basis assignments
    -> Qiskit prepares qubits and applies selected Pauli Y disturbances
    -> Qiskit samples Bob's measurement outcomes
    -> Keep detections with matching bases
    -> Telemetry record for each wavelength and time window
    -> Existing passive fixed threshold pointwise uncertainty policies
    -> Hold and recovery decisions and evaluation metrics
```

The scenario labels stay in a separate evaluator file. The monitor receives observable counts, configuration identifiers and measured classical powers.

## Run it

From PowerShell in this folder:

```powershell
.\.venv\Scripts\python.exe monitor.py --scenario local_background --seed 42 --out results/my_connected_run
```

Choose a fresh output directory for each run. The command rejects a nonempty directory to keep calibration and traces from different runs from being mixed.

Use the same command with `stable`, `local_loss`, `classical_power`, or any of the ten optical scenarios. A complete list is available through `monitor.py --help`. Configuration defaults are in `monitor_config.json`.

Run the connection checks:

```powershell
.\.venv\Scripts\python.exe -m unittest test_connection -v
```

## What happens to one observation

The original optical simulator allocates emitted pulses among signal, weak and vacuum categories and generates detection and error counts from its probability model. Suppose one category contains 10,000 emissions, 500 detections and 20 erroneous detections.

The adapter assigns a random Alice bit and independent Alice and Bob bases to those 500 detections. It assigns the 20 disturbances to circuits containing a Pauli Y gate. That gate swaps the logical bit in both BB84 bases. Qiskit executes every populated setting using its detection count as the shot count.

The adapter then retains the ZZ and XX outcomes. Approximately 250 of the 500 detections survive, with approximately 10 errors. An actual seed can produce different integer totals. The monitor receives 10,000 emitted pulses, the actual sifted detection count, and the actual matching-basis error count.

The ZX and XZ outcomes are measured and included in the audit. They are discarded from the monitoring denominator and error count. Including their random disagreements would incorrectly push the reported BB84 QBER towards 25% even in an otherwise ideal channel.

## Count definitions and calibration

The connected experiment has its own `qiskit-sifted-v1` configuration version. Its gain is **basis-matched detections divided by all emitted pulses in that intensity category**. Its error gain is matching-basis disagreements divided by the same emitted count. QBER divides the matching-basis disagreements by matching-basis detections.

The original monitoring experiment counts pre-sifting detections. For the connection, all nine supported power contexts receive fresh calibration that follows the same optical and Qiskit sifting pipeline as the runtime observations. The adapter reconstructs the exact calibration intervals using the existing statistical helper.

Calibration uses a separate random stream from runtime observations. All four policies replay exactly the same runtime trace and share the same calibration. The existing configuration fingerprint and calibration loader validate the resulting artifact.

The bridge keeps the monitor's finite-horizon operational alarm budget and persistence rules. Their interpretation still depends on the assumed binomial count model and supported power contexts. Observed performance from a single seed is an integration check.

## Choices made for this connection

* Four quantum channels and the existing signal, weak and vacuum intensities are retained.
* The default run uses 40 one-second windows with a disturbance from 12 seconds until 26 seconds. Each channel attempts 200,000 pulses per window.
* Independent calibration uses 2,000,000 pulses per channel and classical-power context. Shorter counts than the original large benchmark keep local circuit execution practical.
* Python supplies the optical probabilities, random erasures, disturbance counts and basis assignments. Qiskit supplies the measured qubit outcomes.
* Pauli Y provides a deliberately simplified basis-symmetric error channel. This interface re-expresses the optical model's erroneous detections as circuit disturbances. It does not independently verify that optical error model.
* The intensity labels and photon losses belong to the classical optical model. A single qubit per detected event represents BB84 logical state behaviour. A full optical multiphoton state is outside this circuit representation.
* The saved outcomes count sifted bits. Secure-key post-processing and SKR estimation remain separate work.
* The original standalone BB84 command and original monitoring source files keep their existing behaviour.

## Files and their roles

| File | Role |
|---|---|
| `monitor.py` | Adapts optical counts to Qiskit circuits, builds calibration, runs the four monitor policies and saves evaluation outputs. |
| `monitor_config.json` | Frozen defaults for the connected count definition and shorter demonstration horizon. |
| `test_connection.py` | Checks count conservation, basis sifting, deterministic replay, empty counts, and hold/recovery integration. |
| `CONNECTION.md` | Explains the interface and examples. |
| `simulate.py` | Existing BB84 circuit builder reused by the adapter. |

Each output directory includes `REPORT.md`, calibration, observable telemetry, decisions per policy, summary metrics, paired comparisons and a provenance manifest. Both calibration and runtime circuit audits contain the actual Qiskit measurement counts. The truth file is reserved for evaluation.

## Replaying without Qiskit

Once the counts have been saved, the existing monitoring environment can replay them directly. Run from the `uncertainty_monitoring` folder so its package is importable:

```powershell
cd ..\uncertainty_monitoring
.\.venv\Scripts\python.exe -m qkd_monitor --config ../bb84_qiskit/results/my_connected_run/config.json replay --telemetry ../bb84_qiskit/results/my_connected_run/telemetry.jsonl --calibration ../bb84_qiskit/results/my_connected_run/calibration.json --out ../bb84_qiskit/results/my_connected_run/replayed.jsonl
```

The monitor can reconstruct its decisions from those files without reading the hidden truth or circuit audit.

## Verified connected examples

The delivered examples used seed 42 and the default connected configuration. All three connection regression checks passed. An additional replay through the original monitoring CLI reproduced every classification, action, streak and output-gate state. The two environments use different SciPy versions, so a few stored p-values differ at floating-point rounding precision.

| Example directory under results | Observed uncertainty-policy behaviour |
|---|---|
| `connected_stable` | Zero holds across the 40-window run. |
| `connected_background` | One hold on channel 3 after two simulated seconds of extra background, followed by one restoration. |
| `connected_local_loss` | One hold on channel 3 after two simulated seconds of extra loss, followed by one restoration. |
| `connected_classical_power` | Zero holds for the calibrated power increase. The fixed-threshold comparator issued one false hold. |

The local disturbances start at 12 seconds. The monitor issues its hold at 14 seconds. They end at 26 seconds, and the monitor issues restoration at 29 seconds after three passing observations. Other channels continue. Every output directory includes its full Qiskit circuit audit and a short report.

The 40-window examples validate the connection. Their results should be kept separate from the earlier 120-window optical-only benchmark because the exposure, calibration size and count definitions differ.
