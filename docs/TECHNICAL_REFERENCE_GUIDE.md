# Technical Reference Guide

This guide explains the implementation and experiment terms. Basic Python knowledge is useful; prior quantum or cryptography study is not required.

## Measurement and simulation model

The simulator represents four decoy-BB84 wavelength channels. A `Channel` includes distance, attenuation, detector efficiency, background, traffic, Raman-like noise, crosstalk, misalignment and an effective four-wave-mixing term. The physics model calculates expected click and error probabilities. It is not a detailed optical propagation solver.

`NetworkSimulator.observe()` samples signal, weak-decoy and vacuum pulse counts, detections and sifted errors. The binomial engine samples count distributions directly and does not execute a quantum circuit. Separate Aer smoke runs exercise a circuit-based path. The large repeated studies use the binomial engine.

For each pulse class `x`, the monitor computes:

```text
gain_x = detections_x / emitted_x
error_fraction_x = errors_x / sifted_x
```

Gain uses emitted pulses as its denominator. Error fraction uses sifted detections. `count_features()` validates integer counts and enforces `errors <= sifted <= detections <= emitted`.

## Calibration and anomaly evidence

`calibrate()` creates independent benign reference samples over a finite grid of channel contexts and candidate configurations. It calculates exact Clopper-Pearson intervals for six rates per context: three gains and three error fractions. Calibration error budget is shared across contexts and features.

At run time the monitor calculates binomial tail probabilities against those intervals. The hybrid policy divides its operational alarm budget across the declared run horizon, four wavelengths and six features. This depends on the supported count model remaining valid. It is an operational false-alarm design, not a cryptographic secrecy parameter or lifetime guarantee.

Malformed, sparse, missing, stale or unsupported telemetry causes a hold and resets the evidence streak. An upper Wilson interval reaching the illustrative 11% operating cap also causes a hold. That cap is a demonstration setting, not a universal QKD security threshold.

## Policies

| Policy | Behaviour | Comparison role |
|---|---|---|
| `fixed` | Keep the initial setting | No-adaptation baseline |
| `aggregate` | Threshold the network average | Shows how averages can hide local problems |
| `per_wavelength` | Apply a fixed threshold to each wavelength | Local threshold baseline |
| `adaptive` | Earlier statistical monitoring and retuning | Legacy baseline |
| `uncertainty` | Calibrated monitor without optical retuning | Monitoring ablation |
| `hybrid` | Calibrated monitoring plus analytical retuning | Main combined-policy baseline |
| `pareto_front` | Form a Pareto front but keep the old selection rule | Front-extraction ablation |
| `pareto` | Form the front, then select by delivered output after cost | New operating-point rule |

The hybrid order is: validate telemetry; compare six statistics with calibration; hold on incomplete or unexplained data; isolate after two consecutive unexplained intervals; require three clean intervals to recover from a temporary hold; then consider adaptation. Isolation remains latched for the run. It means quarantine, not attack attribution.

## Pareto selection and feedback

Five discrete candidate intensity settings `C1` to `C5` are evaluated on predicted QBER and asymptotic estimated output. Candidate A is dominated if another has no higher QBER and no lower output, with at least one strict improvement. The remaining candidates form the Pareto front.

The delivered-output selector considers up to eight remaining intervals. It charges a changed setting 0.25 interval of settling time, requires over 1% predicted improvement, and needs at least two intervals for verification. Two observations evaluate a candidate. If measured rate falls below 90% of the pre-change estimate, the controller rolls back and waits four intervals before trying again. These are operational heuristics.

Changing source intensity cannot correct polarization, phase or timing misalignment. Physical recalibration is not simulated.

## Machine learning

`qkd_sdn/ml.py` trains Random Forest regressors on analytical model outputs for the five candidate settings. The reported split uses 320 training channel conditions and 80 held-out conditions. All candidates for one condition stay in the same split.

Reported mean absolute errors are about 0.3925 percentage points for QBER and 0.0001358 in secret fraction. Mean candidate regret is 2.70%. These labels come from an analytical teacher, not hardware data. The model is evaluated against the same teacher, not attack labels. The controller accepts an optional predictor, while analytical calculations still approve a change. The repeated Pareto studies use `ml=False`; a matched integrated ML-plus-Pareto benefit has not been shown.

## Noise and attack models

| Scenario | Modelled effect | Limitation |
|---|---|---|
| `normal` | No injected change | Healthy baseline |
| `loss`, `tap` | Extra loss or reduced detection efficiency | Does not prove malicious tapping |
| `noise`, `dark_counts`, `raman`, `fwm`, `crosstalk` | Increase simplified background | Raman/FWM are effective terms, not propagation models |
| `misalignment` | Higher error probability | Modelled alignment change |
| `intercept`, `weak_intercept` | Add intercept-resend error fraction to signal detections | Not photon-number splitting |
| `burst`, `transient` | One-window background burst or attenuation | Tests temporary anomaly and recovery |
| `correlated` | Shared AR(1) misalignment drift over intervals | Tests temporal correlation and model mismatch |
| `model_mismatch`, `unsupported`, `missing` | Reported context wrong, outside grid or absent | Tests robustness and holds |

There is no explicit photon-number-splitting (PNS) scenario yet. A PNS model must sample photon number from each weak coherent pulse's Poisson distribution and let Eve exploit multiphoton pulses while preserving the appropriate decoy-class counts. A simple loss or added-error model is not PNS. The separate finite-key decoy estimator does not change that.

## Experiment vocabulary

| Term | Meaning here |
|---|---|
| Run | One complete simulated case with scenario, policy, seed and intervals |
| Seed | Initial value for a pseudo-random generator; repeating it helps reproduce samples |
| Matched seeds | Policies use corresponding seeds/settings to reduce some sampling noise; later random draws can still diverge when decisions change settings |
| Scenario | Declared condition, such as healthy, loss or misalignment |
| Policy | Controller rule being evaluated |
| Interval/window | One measurement and decision round |
| Pulse budget | Emitted pulses per wavelength per interval; four channels at 1M each means 4M per network interval |
| Mean | Average over run-level observations in a group |
| Confidence interval | Range describing sampling uncertainty under a method; it does not include all model errors |
| Bootstrap | Resampling run-level paired differences to describe uncertainty in their mean |
| Hold | Temporarily withhold estimated output while collecting evidence or recovering |
| Isolation | Quarantine a wavelength from output/forwarding for the run |
| False isolation | Isolation in a scenario designated benign; result depends on those modeled benign conditions |
| Retune | Change a candidate source/decoy setting |
| Rollback | Restore the prior setting after verification rejects the new one |
| Throughput estimate | Asymptotic model output; not final secure keys |

## Benchmark results

The original combined-policy study has 2,160 runs. The Pareto follow-up has 2,480 runs: 1,080 standard-scenario runs and 1,400 alignment-grid runs. A matched healthy reference adds 200. The separate single-channel/WDM study adds 1,000. These cohorts use different seed ranges and sometimes different link assumptions, so do not combine raw totals.

The matched normal/alignment comparison uses 50 seeds, 40 intervals and 1M pulses per wavelength per interval. Healthy mean output is 816,210 estimated bits/run. Pareto versus hybrid gains 0.622% at 3%, 0.332% at 3.5% and 0.748% at 4% reported misalignment. At other grid values it has no change. At 3%, mean target QBER rises from 3.0783% to 3.0939%. At 4%, Pareto remains 11.90% below healthy output.

The single-channel comparison uses an equal 160M total pulse budget. Healthy output is 774,360 for fixed single-channel and 772,215 for fixed WDM. Under local 4% misalignment it is 322,739 for single-channel, 660,628 for fixed WDM and 675,179 for Pareto WDM. Under shared 4% misalignment, Pareto WDM is 19.04% above fixed WDM. Hardware limits and WDM insertion loss are omitted.

The Pareto selector microbenchmark was about 22 microseconds/call for the old selector and 48 microseconds/call for Pareto. Pareto adds computation; it is not a speedup.

## Reproduction and files

Run from the project root. Use `.\.runtime\python.exe` on this Windows machine or `.venv-linux/bin/python` on Linux:

```bash
python -m experiments.pareto_experiments --suite alignment --out results/pareto-recheck
python -m tools.report_pareto --out results/pareto-recheck
python -m experiments.normal_comparison --seeds 50 --pareto-results results/pareto-recheck --out results/normal-recheck
python -m experiments.single_channel_comparison --seeds 50 --out results/single-channel-recheck
python -m experiments.decoy_finite_demo
```

`runs.csv` contains individual runs. `summary.csv` groups means. JSON files contain metadata and uncertainty summaries. Example traces show per-interval decisions. Use fresh output folders to preserve existing evidence.

## Limits

Operational throughput uses an asymptotic estimator. The separate finite-key decoy estimator is not connected to basis-resolved monitoring and complete decoy reconciliation/privacy amplification. A full end-to-end security proof and independent review are absent. Noise models are simplified; model mismatch can cause false isolation. The 11% cap is illustrative. Mininet/Ryu code awaits live Linux validation. OpenFlow blocks associated classical VLAN traffic, not photons. Alternate-path rerouting and spare-wavelength switching shown in a presentation diagram are not implemented.
