# Qiskit BB84 and uncertainty monitoring

Scenario `local_loss`, 30 windows and 4 channels.

Integration optical-qiskit-v1. Backend local StatevectorSampler.
Model Python optical detection model plus Qiskit BB84 Y channel and sifting.

Counts reflect basis-matched BB84 detections per emitted pulse. Python models optical losses and disturbances, and Qiskit executes preparation, Pauli Y channel operations and measurement. Calibration follows the same pipeline using independent random streams.

| Policy | Holds | Restores | False holds | Detected events | Delay in seconds |
|---|---:|---:|---:|---:|---:|
| uncertainty | 1 | 1 | 0 | 1/1 | 2.0 |

Delays describe simulated time at the end of a window. Policies see the same observations and cannot access scenario truth. These are single-seed integration results. The Pauli Y channel is a simplified representation of the optical model's erroneous detections. The experiment counts sifted bits and reports QBER rather than secure key rate.

The full measurement record is in circuit_audit.jsonl. Reconstruct monitor decisions from telemetry.jsonl and calibration.json without reading the truth file.
