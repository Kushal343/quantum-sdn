# Delivered validation record

Delivery date: 6 November 2026. This record concerns the synthetic fixed-configuration monitoring implementation in this folder.

## Executed checks

`python -m unittest discover -s tests -v`: **36 tests passed** on Python 3.12, NumPy 1.26.4, SciPy 1.15.2 and Matplotlib 3.10.1.

The tests include exact enumeration of small-sample confidence-interval coverage and composite-test size; physical probability limits; sampling means; valid count relationships; independent reproducible calibration; artifact inconsistency rejection; strict telemetry validation; configuration immutability; stale/duplicate/gap handling; contextual explanation; local isolation; end-of-window timing; recovery; horizon exhaustion; transient persistence; identical loss/tap observables; paired metric direction; CLI report generation; and observable-only replay.

Initial file-based tests exposed a Windows sandbox temporary-directory restriction. Test temporary files now use checked paths under the project test directory. The complete suite subsequently passed, including subprocess integration tests.

`python scripts/verify_artifacts.py`: **passed for all four delivered result directories**, comprising 2,008 policy-run metric rows. This checked current source hashes, configuration fingerprints, saved calibration hashes and reconstructed calibration intervals, complete scenario/seed/policy rows, expected output files, and reproduction of every non-timing demo decision from telemetry without reading scenario truth.

Generated time-series and comparison PNGs were visually inspected for readable labels, uncertainty bands, event timing, and output-hold shading. No claim is made that the HTML reports were tested in every browser or that the plots represent optical hardware measurements.

## Experiment exposure

| Directory | Experiment | Seeds | Policies | Policy-run rows |
|---|---|---:|---:|---:|
| results/benchmark | Ten scenarios | 1000–1029 | 4 | 1,200 |
| results/benign_audit | Stable and observed classical-power changes | 5000–5099 | 4 | 800 |
| results/demo | Local unexplained optical background | 42 | 4 | 4 |
| results/power_demo | Observed calibrated classical-power increase | 42 | 4 | 4 |

The main study has 500 scenario runs and 2,000 policy evaluations. Demos add eight policy evaluations. Every run has 120 windows and four wavelengths. All policies receive exactly the same telemetry for a given scenario and seed. Run seeds are independent; scenarios sharing a seed/calibration are correlated and are not pooled as independent statistical evidence.

## Observed benign audit

| Scenario, 100 runs each | Fixed-threshold runs with false hold | Contextual pointwise runs with false hold | Uncertainty runs with false hold |
|---|---:|---:|---:|
| Stable | 0/100 | 7/100 | 0/100 |
| Measured classical-power increase | 100/100 | 11/100 | 0/100 |

For the uncertainty policy, each separate 0/100 observation has a two-sided exact 95% interval of **[0, 3.6217%]** for the run-level event probability. The same zero counts and interval apply to raw false alarms in this audit. These are finite simulation observations, not a measured lifetime hardware false-alarm rate. Do not combine the two scenario groups as 200 independent observations; they share run seeds and calibration.

The pointwise policy produced at least one raw false alarm in every run in both benign groups. Its within-window feature correction does not control the probability of any alarm over 120 windows, and it treats uncertain calibration rates as fixed. Persistence prevents many raw alarms from becoming holds, but provides no separately derived run-wise guarantee for this comparator.

The fixed nominal thresholds unnecessarily held channel 3 during the high-power benign scenario. Those thresholds were not optimized at matched operating points. These outcomes support a comparison of the implemented policies under the specified model; they do not establish superiority over all tuned monitoring methods.

## Observed sustained events, main benchmark

| Scenario | Uncertainty events detected | Mean delay among detected runs |
|---|---:|---:|
| Local extra loss | 30/30 | 2.00 s |
| Local extra background | 30/30 | 2.00 s |
| Gradual background drift | 30/30 | 5.03 s |
| Common extra loss | 120/120 channel events | 2.00 s |
| Passive-tap attenuation label | 30/30 | 2.00 s |

These event amplitudes and count exposures were predefined synthetic choices. They do not establish arbitrary weak-event detectability. Common-loss channel events are correlated within a run. The passive-tap result is exactly the local-loss observation law under another evaluator label and adds no evidence of attack attribution. Loss and tap labels generate identical non-timing decisions in the tests.

The pointwise comparator detected gradual drift earlier on average (3.37 s), illustrating a sensitivity/false-alarm trade-off. The default fixed-QBER threshold took about 15.97 s on that drift. The uncertainty policy is deliberately conservative and is not claimed to dominate every policy on delay.

Under explained classical-power changes, the uncertainty policy kept monitoring without output holds. Unsupported power settings and missing reports produced inconclusive states. A one-window transient produced anomaly evidence without satisfying the two-window hold rule. Recovery incurs three passing windows of continued advisory hold, visible in benign held-window counts after real events end.

## Reproduction

```powershell
python -m unittest discover -s tests -v
python -m qkd_monitor demo --scenario local_background --seed 42 --out results/demo
python -m qkd_monitor demo --scenario classical_power --seed 42 --out results/power_demo
python -m qkd_monitor benchmark --seeds 30 --seed 1000 --out results/benchmark
python -m qkd_monitor benchmark --scenarios stable classical_power --seeds 100 --seed 5000 --out results/benign_audit
python scripts/verify_artifacts.py
```

Use the same code, configuration, dependency versions and seed schedule to reproduce non-timing observations and decisions. Timestamps, controller timing and environment metadata vary. Editing source after generating results intentionally causes the provenance checker to flag a mismatch until the relevant studies are regenerated.

## Remaining evidence boundary

No real optical hardware data, finite-key secret-bit output, authenticated live device commands, intensity retuning, ML adaptation or cryptographic attack-identification guarantee is included. The physical coupling coefficients and detector rule are illustrative and documented. The monitoring error bound assumes the calibration/binomial model, supported power contexts, valid reporting and the declared finite horizon. Independent scientific review, device calibration and stronger matched-operating-point studies remain research work, as detailed in RESEARCH_ROADMAP.md.
