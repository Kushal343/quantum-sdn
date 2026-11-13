# Initial repeated-seed results

Five seeds per scenario/policy, 12 intervals, 100,000 pulses per wavelength/interval.
This is exploratory evidence. Pointwise 95% Wilson intervals remain wide with five seeds.

| Scenario | Policy | Detected | Mean delay (detected only) | Runs with false isolation |
|---|---|---:|---:|---:|
| intercept | adaptive | 5/5 | 1.0 | 0/5 |
| intercept | aggregate | 0/5 | N/A | 0/5 |
| intercept | fixed | 0/5 | N/A | 0/5 |
| intercept | per_wavelength | 5/5 | 0.0 | 0/5 |
| loss | adaptive | N/A | N/A | 0/5 |
| loss | aggregate | N/A | N/A | 0/5 |
| loss | fixed | N/A | N/A | 0/5 |
| loss | per_wavelength | N/A | N/A | 0/5 |
| noise | adaptive | N/A | N/A | 0/5 |
| noise | aggregate | N/A | N/A | 0/5 |
| noise | fixed | N/A | N/A | 0/5 |
| noise | per_wavelength | N/A | N/A | 0/5 |
| normal | adaptive | N/A | N/A | 0/5 |
| normal | aggregate | N/A | N/A | 0/5 |
| normal | fixed | N/A | N/A | 0/5 |
| normal | per_wavelength | N/A | N/A | 0/5 |
| shared_noise | adaptive | N/A | N/A | 0/5 |
| shared_noise | aggregate | N/A | N/A | 0/5 |
| shared_noise | fixed | N/A | N/A | 0/5 |
| shared_noise | per_wavelength | N/A | N/A | 0/5 |
| tap | adaptive | 5/5 | 1.0 | 0/5 |
| tap | aggregate | 0/5 | N/A | 0/5 |
| tap | fixed | 0/5 | N/A | 0/5 |
| tap | per_wavelength | 0/5 | N/A | 0/5 |
| weak_intercept | adaptive | 5/5 | 1.0 | 0/5 |
| weak_intercept | aggregate | 0/5 | N/A | 0/5 |
| weak_intercept | fixed | 0/5 | N/A | 0/5 |
| weak_intercept | per_wavelength | 0/5 | N/A | 0/5 |

Full uncertainty bounds and estimated throughput are in `summary.json`; individual outcomes are in `runs.csv`.
Tap means hidden loss. A detection is not attribution of malicious behaviour.
No actual secure keys are generated. These tests do not validate a composable finite-key proof.
