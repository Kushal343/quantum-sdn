# Reproducible evaluation

Scope confirmed by the project owner: simulation only, with no prescribed detector specifications. Physical SDN deployment is not an outstanding deliverable for this scope. Optical coefficients remain explicitly illustrative rather than fitted to an unspecified detector.

The project-local `.runtime/python.exe` is supported by `launch.ps1`. It leaves the system Python and PATH unchanged. The downloaded runtime is not part of source distribution.

Run tests:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch.ps1 -Task test
```

Run repeated-seed evaluation across all seven scenarios and four policies:

```powershell
.\.runtime\python.exe -m experiments.evaluate --seeds 20 --steps 16 --pulses 100000 --out results/sweeps
```

Each run writes its interval telemetry. `runs.csv` is checkpointed after every completed run. `summary.json` contains run-level false-isolation probabilities, disturbance-detection probabilities, pointwise Wilson intervals, missed-run counts, conditional detection delay, and bootstrap intervals for mean estimated bits. The statistical unit is a complete seeded run. Use more seeds for research conclusions; a small smoke sweep verifies execution only.

False isolation is defined relative to the injected scenario: any isolation in normal/measured-loss/measured-noise scenarios, or isolation of an unaffected channel or before onset in an unexplained-disturbance scenario. This measures disturbance discrimination, not a proof that an operating-cap isolation is unjustified. Hidden-loss detection cannot establish malicious attribution. Detection delay excludes misses, which must always be reported alongside it.

The device boundary is defined in `qkd_sdn/devices.py`. Network simulation now observes the device configuration and applies controller commands through a simulated device. Isolation is latched and configuration changes after isolation are rejected. A physical adapter would need acknowledgement, timeout, identity, authentication, failure recovery and hardware validation; the present interface is local only.

Tests explicitly exercise two-window keep/rollback decisions, latched device state, and evaluation accounting. They do not establish that the controller thresholds or verification windows are statistically calibrated.

`sensitivity.py` exports one-factor analytical sweeps for distance, efficiency, dark counts, traffic and misalignment to `results/sensitivity/analytical.csv`. These are sensitivity tests, not empirical calibration. `validate_notebook.py` runs all notebook code cells headlessly and preserves the original results. `requirements-validated.txt` records the current installed environment.

Current verification: all 24 tests passed, including Streamlit AppTest, in 11.12 seconds. On this Windows sandbox the Streamlit test required execution outside the sandbox because asyncio's local socket creation stalled. All eight notebook code cells also completed via sequential Python execution with an Agg rendering backend. The ML rerun reproduced the saved metrics exactly.

Completed experiment: `results/sweeps-initial/` contains 140 runs (7 scenarios × 4 policies × 5 seeds), 12 intervals each, with 100,000 pulses per wavelength/interval. Read `RESULTS.md` for the comparison and `summary.json` for uncertainty. Adaptive detection was 5/5 for each unexplained-disturbance scenario, at one interval after onset. No false isolation occurred in this sweep. Five successes have a pointwise Wilson 95% interval of approximately 56.6%–100%; this is not a validated detection guarantee.

Remaining security research requirements include composable finite-key analysis with matching protocol assumptions and authenticated classical processing. These require more than adding numerical penalties to the existing asymptotic rate. Existing results must continue to be described as estimates, not usable secure keys. Neither the sensitivity study nor the new tests establish a security proof or statistical calibration of the controller's thresholds.
