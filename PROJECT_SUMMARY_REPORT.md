# Project progress summary: QKD–SDN

Latest analysis: the three-intensity finite-key decoy estimator and 50-block
count experiments are implemented. See `DECOY_FINITEKEY.md`. The estimator is
not a completed end-to-end decoy distillation protocol or an independent review.

Latest continuation: **48 tests pass**. The integrated single-photon protocol now
uses explicit Aer bases/sifting, separate Alice/Bob processes, fixed-syndrome
reconciliation and one-use authentication with key-cost accounting. See
`PROTOCOL_SECURITY.md` and `FIVE_TASKS_STATUS.md`. New optical experiments show
a 4.05% estimated retuning gain in one degradation regime, and expose missed
3% interception and false isolation under hidden correlated noise. A complete
reviewed finite-key proof for the original weak-coherent decoy path remains open.

Latest milestone: classical simulation postprocessing is now implemented and validated with **41 passing tests**. See `POSTPROCESSING.md` for finite-sample bit-error bounds, HMAC transcript authentication, parity reconciliation, Toeplitz verification and entropy-conditional candidate generation. A complete finite-key security proof remains outstanding; the default emits no candidate without a supplied entropy bound.

**Report date:** 13 November 2026  
**Current stage:** Local research prototype with executed simulation artifacts

## Follow-up implementation and verification

The project owner confirmed a simulation-only scope with no prescribed detector. The following work was subsequently completed:

- Restored execution using an isolated project-local Python runtime and updated the launcher; recorded installed versions in `requirements-validated.txt`.
- Added the simulated-device interface and connected network execution to it, including latched isolation and rejection of configuration changes after isolation.
- Added regression coverage for two-window keep/rollback, device isolation, and evaluation accounting. **All 24 tests passed**, including a dashboard experiment.
- Re-executed all eight notebook code cells headlessly, preserved the earlier artifacts, and visually checked the regenerated plot.
- Re-ran ML evaluation and reproduced the earlier saved metrics.
- Added and executed optical sensitivity sweeps for five parameter families.
- Added and completed **140 network runs**: seven scenarios × four policies × five seeds, each with 12 intervals and 100,000 pulses per wavelength/interval. Saved full telemetry, run-level metrics, pointwise Wilson intervals and bootstrap throughput intervals.

The adaptive controller detected strong interception, weak interception and hidden loss in 5/5 seeds each, one interval after onset, with no false isolations in this sweep. Per-wavelength thresholding detected strong interception in 5/5 seeds at onset but missed weak interception and hidden loss in all five seeds. Aggregate thresholding missed all three disturbance types. These small-sample results are exploratory: 5/5 corresponds to a pointwise 95% Wilson interval of approximately 56.6%–100%, not a proven 100% detection rate.

See `results/sweeps-initial/RESULTS.md` and `RESEARCH_VALIDATION.md` for the current results and reproduction instructions. The original review below records the earlier state; its runtime/test limitation has now been resolved.

**Still unfinished:** composable finite-key analysis, authenticated classical key processing, statistical calibration of sequential controller thresholds, and a demonstrated retuning advantage. The sensitivity study does not establish empirical optical calibration. Physical deployment is outside the confirmed scope. The work above must not be presented as completion of these remaining security/research requirements.

## 1. Overall progress

The project implements a Qiskit-first demonstration of BB84 quantum key distribution across four logical wavelength channels, supported by a monitoring dashboard. A separate experimental path adds a simplified optical model, decoy-state secret-key-rate estimates, an adaptive simulated controller, baseline policy comparisons, and an optional machine-learning surrogate.

The central demonstrated result is that averaging QBER across wavelengths can conceal a disturbance affecting one channel. Per-wavelength monitoring exposes that disturbance. The current system is a simulation and research platform; it does not produce operational secure keys or control a deployed SDN network.

This report is based on the current source files, notebook execution metadata, saved CSV/JSON results, and README. This folder has no Git repository, so commit history, contributor attribution, and a dated development timeline could not be established.

## 2. Work completed

| Area | Work present in the project | Main files |
|---|---|---|
| BB84 quantum simulation | Random preparation and measurement bases, Qiskit Aer measurement outcomes, basis sifting, explicit intercept-resend, and optional symmetric errors | `qkd_sdn/quantum.py`, `qkd_sdn/bb84.py` |
| Public QBER sampling | Random disclosure of sifted bits, sample-based QBER, uncertainty intervals, and remaining raw-key material | `qkd_sdn/bb84.py` |
| Four-channel WDM demonstration | Independent logical channels labelled 1550.0, 1550.8, 1551.6, and 1552.4 nm; configurable attack onset, fraction, and target; weighted aggregate QBER | `qkd_sdn/bb84.py` |
| Standalone notebook | Self-contained BB84/WDM experiment, interception sweep, saved telemetry, and comparison plot; eight code cells carry execution counts 1–8 | `bb84_wdm_qiskit.ipynb` |
| Optical model | Fibre attenuation, detector efficiency, weak-coherent-pulse gains, dark/background counts, misalignment, and illustrative traffic-dependent Raman/crosstalk contributions | `qkd_sdn/physics.py` |
| Decoy-state estimates | Signal, weak-decoy, and vacuum sampling; asymptotic plug-in estimates of secret key rate (SKR); five candidate intensity configurations | `qkd_sdn/physics.py`, `qkd_sdn/simulation.py` |
| Scenario simulation | Normal operation, measured loss, measured noise, intercept-resend, weak interception, hidden additional loss, and shared noise | `qkd_sdn/simulation.py` |
| Adaptive controller | Model checks, persistent evidence, withholding, latched isolation, candidate retuning, two-window verification, rollback, cooldown, and an illustrative retuning penalty | `qkd_sdn/controller.py`, `run.py` |
| Baseline policies | Fixed settings, aggregate 11% threshold, per-wavelength 11% threshold, and adaptive monitoring | `qkd_sdn/controller.py`, `run.py` |
| Optional ML | Random-forest regression for analytical QBER and secret-fraction predictions, with channel-grouped train/test separation and analytical gating of controller proposals | `qkd_sdn/ml.py` |
| Interactive dashboard | Experiment controls, Aer execution, per-channel and aggregate charts, metrics, telemetry table, and CSV download | `dashboard.py` |
| Execution and packaging | CLI modes for demo/network/train/compare, PowerShell launcher, Python package configuration, dependency ranges and locked versions | `run.py`, `launch.ps1`, `pyproject.toml`, requirements files |
| Automated checks | Tests for quantum behaviour, input validation, reproducibility, physical trends, telemetry separation, and target-only isolation | `tests/` |

The dashboard runs the BB84/WDM demonstration. The optical model and adaptive controller are accessed through the separate command-line network path.

## 3. Results available so far

### A. Notebook: wavelength-specific interception

The saved notebook experiment uses 12 intervals and 12,000 pulses per wavelength per interval. An 80% intercept-resend attack targets `lambda_3` from interval 4, using zero-based indexing.

- Post-onset `lambda_3` sample QBER is **19.03%**, calculated from **2,284 errors in 11,999 disclosed sample bits**.
- The other three channels have zero sampled QBER in the saved idealised experiment.
- Post-onset aggregate QBER ranges from **4.34% to 5.14%**, remaining below the illustrative 11% threshold despite the attacked channel exceeding it.
- The ideal intercept-resend expectation is QBER = intercepted fraction / 4: 20% on the targeted channel and approximately 5% aggregate with equal sample weights.

The saved interception sweep also follows the expected increasing trend:

| Intercepted fraction | Observed sample QBER | Ideal expectation |
|---|---:|---:|
| 0% | 0.00% | 0% |
| 20% | 5.13% | 5% |
| 40% | 10.55% | 10% |
| 60% | 15.54% | 15% |
| 80% | 20.63% | 20% |
| 100% | 26.17% | 25% |

The sweep and monitoring experiment use different samples, so their 80% interception measurements differ. These are finite-sample seeded demonstrations, not detection-probability estimates.

**Artifacts:** `results/notebook/telemetry.csv`, `aggregate.csv`, `ground_truth.csv`, `interception_sweep.csv`, and `wavelength_attack.png`. A companion demo export is available in `results/demo/`.

### B. Optical network and policy comparison

The saved comparison uses the `intercept` scenario, seed 42, 10 intervals, and 100,000 emitted pulses per wavelength per interval. In this path, interception starts at interval 6 and affects 70% of signal-originated detections on the target channel.

| Policy | Isolation events | Retunes | Total estimated released bits |
|---|---:|---:|---:|
| Fixed settings | 0 | 0 | 19,022.66 |
| Aggregate threshold | 0 | 0 | 19,022.66 |
| Per-wavelength threshold | 1 | 0 | 19,022.66 |
| Adaptive | 1 | 0 | 19,022.66 |

Each saved policy run records 142,406 Aer shots, including grouping/padding overhead. The separate adaptive network result records the same summary values.

This experiment demonstrates different isolation behaviour. It does **not** establish a throughput advantage: all four policies have the same saved estimated bit total. Retuning and rollback exist in code, but these saved runs contain no retune events and therefore do not demonstrate their effectiveness.

**Artifacts:** `results/baseline-comparison/` and `results/network-intercept/`.

### C. Machine-learning evaluation

The saved ML evaluation uses 320 training channel conditions and 80 held-out conditions, keeping all candidate configurations for each channel condition in the same split.

| Metric | Saved value |
|---|---:|
| QBER mean absolute error | 0.003925, approximately 0.3925 percentage points |
| Secret-fraction mean absolute error | 0.0001358 |
| Mean relative candidate-selection regret | 2.70% |

The training labels come from analytical equations, not experimental measurements or Qiskit shot-derived training labels. These results assess approximation of the analytical model, not real-world attack detection or security.

**Artifact:** `results/ml/ml_metrics.json`.

## 4. Validation status

The README records **18 passing tests**, successful execution of all eight notebook code cells, visual inspection of its plot, and Streamlit AppTest checks for initial load and a button-triggered Aer run.

Source inspection confirms tests covering ideal agreement and sifting, full/partial interception, combined noise, no-click handling, reproducibility, invalid parameters, channel-specific effects, telemetry/ground-truth separation, loss/noise trends, Wilson intervals, and target-only controller isolation. The notebook currently retains execution counts for all eight code cells.

**Current review limitation:** a fresh test run was attempted using `launch.ps1 -Task test`, but the launcher could not execute the selected `python.exe` (“The file cannot be accessed by the system”). Therefore, the 18-pass result is a previously documented result and was not independently reproduced during this report. Dashboard and notebook execution were not repeated. The target-channel 19.03% figure above was independently recalculated from the saved CSV.

## 5. Boundaries and unfinished work

- **Secure-key processing:** authenticated classical communication, error reconciliation, privacy amplification, and composable finite-key analysis are not implemented. Remaining notebook bits are raw material; SKR outputs are model estimates.
- **Optical fidelity:** wavelength labels represent independent logical channels. Raman/crosstalk coefficients need calibration; detailed four-wave mixing, detector imperfections, electronic noise spectra, and physical multiplexers are absent. Aer does not represent individual multiphoton Fock states here.
- **Attack coverage:** intercept-resend is explicit. Photon-number-splitting and detector attacks are absent. The hidden-loss `tap` scenario cannot uniquely identify malicious tapping.
- **Controller evidence:** confidence thresholds, consecutive-window decisions, and verification tolerances are research heuristics. False-alarm calibration, sequential testing, and repeated-seed detection-delay analysis remain outstanding. The controller assumes trustworthy channel-condition telemetry.
- **SDN integration:** controller actions update in-process simulated state. There is no deployed OpenFlow, Mininet, REST device integration, physical quantum link, or wall-clock real-time monitoring service.
- **ML scope:** predictions approximate an analytical teacher. Physical-data validation and evidence of benefit over direct search across the five candidates remain outstanding.
- **Reproducibility:** the Python runtime referenced by the launcher must be made accessible to reproduce the documented checks in the present environment.

## 6. Recommended next milestones

1. Restore an accessible Python environment and rerun the automated tests, notebook, and dashboard checks.
2. Calibrate optical/noise parameters against published or measured values and document their sources.
3. Run repeated-seed sweeps across all scenarios and policies; report false alarms, missed detections, detection delays, and uncertainty on estimated throughput.
4. Exercise retuning, verification, rollback, and availability penalties explicitly; compare analytical selection with ML proposals.
5. Add finite-key estimation and the classical processing needed for a complete QKD protocol if secure-key generation is a project objective.
6. Define a simulated-device API, then evaluate optional SDN/Mininet integration.

The completed work provides an executable research foundation and saved evidence for wavelength-specific QBER monitoring. Establishing calibrated security and operational SDN behaviour requires the remaining modelling, validation, protocol, and integration work above.
