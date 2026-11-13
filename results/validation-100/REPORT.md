# Expanded validation

100 new seeds (1000–1099) per scenario and policy; 16 intervals; 100,000 pulses per channel/interval.
2,800 runs use the binomial count sampler, not Aer circuits. This sampler reproduces the count distribution of the current independent symmetric BB84 model. Four parameter combinations were checked against Aer and the theoretical distribution. The original 140 Aer runs remain separate.

The controller and its thresholds were not tuned on these validation seeds.

## Disturbance response

| Scenario | Policy | Isolated | 95% Wilson interval | First hold/isolate delay | Isolation delay |
|---|---|---:|---:|---:|---:|
| intercept | adaptive | 100/100 | 96.3%–100.0% | 0.00 | 1.00 |
| intercept | aggregate | 0/100 | 0.0%–3.7% | No response | No response |
| intercept | fixed | 0/100 | 0.0%–3.7% | No response | No response |
| intercept | per_wavelength | 100/100 | 96.3%–100.0% | 0.00 | 0.00 |
| tap | adaptive | 100/100 | 96.3%–100.0% | 0.00 | 1.00 |
| tap | aggregate | 0/100 | 0.0%–3.7% | No response | No response |
| tap | fixed | 0/100 | 0.0%–3.7% | No response | No response |
| tap | per_wavelength | 0/100 | 0.0%–3.7% | No response | No response |
| weak_intercept | adaptive | 100/100 | 96.3%–100.0% | 0.00 | 1.02 |
| weak_intercept | aggregate | 0/100 | 0.0%–3.7% | No response | No response |
| weak_intercept | fixed | 0/100 | 0.0%–3.7% | No response | No response |
| weak_intercept | per_wavelength | 0/100 | 0.0%–3.7% | No response | No response |

Delays are in simulated intervals and conditional on a response. Misses remain visible in the isolation count. A hold withholds estimated key release; it is not an isolation. Tap is hidden loss, not attribution of an attacker.

## Benign operation

| Scenario | Policy | Runs with isolation | Runs with hold | Mean estimated released bits |
|---|---|---:|---:|---:|
| loss | adaptive | 1/100 | 27/100 | 29,412.1 |
| loss | aggregate | 0/100 | 0/100 | 29,577.0 |
| loss | fixed | 0/100 | 0/100 | 29,577.0 |
| loss | per_wavelength | 0/100 | 0/100 | 29,577.0 |
| noise | adaptive | 0/100 | 20/100 | 30,580.0 |
| noise | aggregate | 0/100 | 0/100 | 30,697.6 |
| noise | fixed | 0/100 | 0/100 | 30,697.6 |
| noise | per_wavelength | 0/100 | 0/100 | 30,697.6 |
| normal | adaptive | 0/100 | 24/100 | 32,836.6 |
| normal | aggregate | 0/100 | 0/100 | 33,000.0 |
| normal | fixed | 0/100 | 0/100 | 33,000.0 |
| normal | per_wavelength | 0/100 | 0/100 | 33,000.0 |
| shared_noise | adaptive | 0/100 | 12/100 | 23,917.7 |
| shared_noise | aggregate | 0/100 | 0/100 | 23,974.6 |
| shared_noise | fixed | 0/100 | 0/100 | 23,974.6 |
| shared_noise | per_wavelength | 0/100 | 0/100 | 23,974.6 |

The false-isolation definition concerns disturbance discrimination, not whether a cap-triggered protective action is justified. All uncertainty bounds and throughput bootstrap intervals are retained in summary.json. Intervals are pointwise; there is no simultaneous or sequential security guarantee.

## Interpretation

The default C3 configuration is already the best of the five candidates under the tested normal/noise conditions. A retune count of zero does not establish a controller failure or benefit. Wider operating conditions and additional useful control actions are needed to demonstrate adaptation gains.

These are simulation estimates. They do not establish finite-key security or produce usable secure keys.
