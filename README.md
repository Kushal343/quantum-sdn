# Quantum SDN monitoring and Qiskit BB84

This branch contains the fixed-configuration WDM-QKD monitoring research prototype and its connected local Qiskit BB84 experiment.

## Start here

- [Connected Qiskit experiment](bb84_qiskit/CONNECTION.md)
- [Qiskit setup and BB84 explanation](bb84_qiskit/README.md)
- [Monitoring setup, experiments and results](uncertainty_monitoring/README.md)
- [Extension interfaces for future integration](bb84_qiskit/EXTENDING.md)
- [Monitoring methodology](uncertainty_monitoring/docs/METHOD.md)
- [Recorded validation](uncertainty_monitoring/docs/VALIDATION.md)

Keep bb84_qiskit and uncertainty_monitoring together. The connected runner imports the sibling monitoring package.

## Run the connected experiment

Use Python 3.12. In PowerShell from the repository root:

```powershell
cd bb84_qiskit
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe monitor.py --scenario local_background --seed 42 --out results/my_run
.\.venv\Scripts\python.exe -m unittest test_connection test_integration -v
```

Use a fresh output directory for each run. The runner saves calibration, circuit audits, telemetry, decisions, metrics and a Markdown report. Saved example runs are under bb84_qiskit/results. Historical manifests retain source hashes for the code versions that produced them.

The local Qiskit StatevectorSampler executes BB84 qubit preparation and measurement. Python models optical detections and disturbances. Results describe sifted bits and operational monitoring. SKR estimation, live SDN commands and IBM cloud hardware execution are future work.

The two projects use separate virtual environments because their recorded experiments use different dependency versions. No virtual environments are committed.
