# Combined policy findings

The combined policy is a better structured research controller: it accounts for independent calibration uncertainty, incomplete evidence and recovery, while preserving retuning and targeted isolation. It is not uniformly better on every performance measure. Hidden correlated drift remains a demonstrated failure mode.

This experiment contains 2,160 runs: 20 seeds for every scenario/policy combination, 18 intervals, and 100,000 emitted pulses per wavelength per interval. Six policies and 18 scenarios were compared. Calibration used a separate random stream and 5,000,000 pulses per context. Scenarios begin at interval 6. The table shows isolation runs, not numbers of isolated wavelengths.

| Scenario | Old adaptive: isolation runs | Combined: isolation runs | Combined: isolation of wavelengths other than 3 |
|---|---:|---:|---:|
| normal | 0/20 | 0/20 | 0/20 |
| intercept | 20/20 | 20/20 | 0/20 |
| weak_intercept | 20/20 | 20/20 | 0/20 |
| tap | 20/20 | 20/20 | 0/20 |
| loss | 0/20 | 0/20 | 0/20 |
| raman | 0/20 | 0/20 | 0/20 |
| fwm | 0/20 | 0/20 | 0/20 |
| crosstalk | 0/20 | 0/20 | 0/20 |
| dark_counts | 0/20 | 0/20 | 0/20 |
| misalignment | 0/20 | 0/20 | 0/20 |
| transient | 0/20 | 0/20 | 0/20 |
| burst | 0/20 | 0/20 | 0/20 |
| missing | 0/20 | 0/20 | 0/20 |
| unsupported | 0/20 | 0/20 | 0/20 |
| model_mismatch | 20/20 | 20/20 | 0/20 |
| correlated | 1/20 | 6/20 | 6/20 |

## What improved

- Weak interception was isolated in all 20 runs with both policies. Mean isolation delay fell from 1.80 to 1.15 intervals. The combined controller isolated strong interception and hidden attenuation in all 20 runs each, without isolating the three unaffected wavelengths.
- Known dark-count, Raman-like, FWM-like and crosstalk increases caused no permanent isolation in these runs. Their measured contexts were independently calibrated.
- A one-interval hidden attenuation event caused a temporary hold and then recovery, with no permanent isolation. Missing telemetry and unsupported contexts caused conservative holds instead of unsupported anomaly conclusions.
- Calibration uncertainty and all six count checks per wavelength are included in an explicitly bounded monitoring horizon. The old adaptive baseline assumes exact optical expectations and uses a fixed per-test alarm level.

For measured misalignment, retuning increased mean network-wide estimated accepted bits by **2.17%** relative to the same calibrated monitor with fixed optical settings: 31,753.6 to 32,442.5. The mean paired difference was 688.9 estimated bits; a descriptive paired-bootstrap 95% interval is [400.1, 975.1]. A 25% next-interval settling cost is charged after retuning or rollback. This is an asymptotic model estimate, not distillation of actual secure keys.

## Where it performed worse

The hidden correlated-noise scenario is benign AR(1) misalignment drift shared by all wavelengths. The combined policy permanently isolated at least one wavelength in **6/20 runs**, compared with **1/20** for the old adaptive policy. This is an observed false-quarantine cost under model mismatch, and the method must not be described as robust to arbitrary correlated noise. A shared change is useful diagnostic context, but cannot safely be labelled harmless solely because all wavelengths move together.

Recovery also costs availability: three clean intervals are required after a temporary hold, so transient scenarios deliver fewer estimated bits than immediate resumption. Persistent unknown benign misalignment is isolated in 20/20 runs because it is observationally unexplained; the action does not identify an attacker.

## Uncertainty and limits

With only 20 seeds per case, pointwise 95% Wilson intervals remain broad: 20/20 corresponds to [83.9%, 100.0%], and 0/20 to [0.0%, 16.1%]. These are descriptive intervals and are not adjusted for searching across scenarios.

The run-level operational raw-alarm budget is 5%, including 0.5% for independent calibration. The remaining budget is divided across 18 intervals, four wavelengths and six tests. Its mathematical interpretation requires the calibrated conditional count law and supported contexts to remain valid. It excludes the operating-cap hold rule, missing-data holds, unsupported-context holds and unknown noise laws. It is not a cryptographic security parameter.

All runtime observations in this sweep use the binomial count engine. The model is independent within each interval; the correlated scenario changes its parameter between intervals. This is not a correlated quantum attack model. Calibration contexts assume precisely reported, trusted device/noise parameters on a finite grid. Raman and FWM are illustrative effective-background models, not a propagation solver.

The legacy policies do not check the new available flag, so their continued output in the missing-data scenario is not evidence of superior availability. Every reported bit quantity here is an operational estimate. The existing finite-key estimators and authenticated protocol demonstrations remain separate from this live monitoring path.

Live Ryu/Mininet packet tests are supplied for Linux but were not executed on this Windows machine. Unit tests with fake datapaths verify message construction and failure-state logic; they cannot replace live switch tests.

Raw evidence: `runs.csv`, `summary.csv`, `summary.json`, individual first-seed traces and `calibration-example.json` in this directory. Reproduce with `python -m experiments.hybrid_experiments --seeds 20` and `python -m tools.report_hybrid`.
