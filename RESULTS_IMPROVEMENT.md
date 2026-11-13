# Controller and evaluation improvement

The original five-seed results were expanded in two stages: 2,800 runs with the original controller (seeds 1000–1099), then 2,800 runs with the revised controller on fresh seeds (2000–2099). Both use 16 intervals and 100,000 pulses/channel/interval. These are independent cohorts, not paired causal estimates.

## Actual controller change

Replaced Gaussian gain residual checks with exact two-sided binomial tests, including sparse vacuum counts. Replaced the unexplained-QBER heuristic with a one-sided binomial tail test against expected QBER plus the existing 0.005 tolerance. Per-test significance is 0.00001. The two-consecutive-interval isolation rule remains. Wilson intervals still serve the separate operating-cap hold check.

Under the exact trusted independent channel model, four tests per channel over four channels and 16 intervals have a union-bound suspicion probability of at most 0.00256. This statement excludes the separate Wilson operating-cap rule, model mismatch, and runs of arbitrary duration. It is not a QKD security guarantee.

## Observed changes

| Adaptive metric | Original controller, 100 seeds | Revised controller, 100 fresh seeds |
|---|---:|---:|
| Normal runs with false hold | 24/100 | 1/100 |
| Measured-loss runs with false hold | 27/100 | 0/100 |
| Measured-noise runs with false hold | 20/100 | 0/100 |
| Shared-noise runs with false hold | 12/100 | 0/100 |
| Measured-loss runs with false isolation | 1/100 | 0/100 |
| Strong interception detected | 100/100 | 100/100 |
| Weak interception detected | 100/100 | 100/100 |
| Hidden loss detected | 100/100 | 100/100 |
| Mean weak-interception isolation delay | 1.02 intervals | 1.42 intervals |
| Mean weak-interception first protective response | 0.00 intervals | 0.06 intervals |

The stricter tests reduced false responses while preserving detection in these experiments, at the cost of slower weak-interception isolation. Mean normal estimated throughput was 32,909.8 bits versus 32,915.8 for fixed settings in the revised cohort, an approximately 0.018% difference. No throughput advantage from retuning is claimed.

For each 100/100 detection result the pointwise 95% Wilson interval is 96.3%–100%, compared with 56.6%–100% for the original 5/5 result. Zero observed false isolations in 100 runs still has an upper Wilson bound of approximately 3.7%; it does not establish a zero false-alarm probability.

## Evidence and reproduction

All 31 tests passed, including Aer checks at four noise/interception combinations, sparse-vacuum regression tests and the dashboard test. Large sweeps use a separately labelled binomial count sampler that reproduces the current independent symmetric BB84 count distribution. They do not execute Aer shots and cannot cover correlations or arbitrary attacks. Earlier Aer results remain preserved.

Full revised tables: `results/validation-exact-100/REPORT.md`; full bounds: `summary.json`; run outcomes: `runs.csv`; interval telemetry: individual CSVs. The original-controller expanded results remain in `results/validation-100/`.

```powershell
.\.runtime\python.exe evaluate.py --seeds 100 --seed-start 2000 --steps 16 --pulses 100000 --engine binomial --out results/reproduction-exact
```

Use `--engine aer` to execute circuits instead. Reproducing the original controller requires its earlier implementation; the current source contains the revised tests. Neither cohort was used to tune parameters after its results were examined. The first cohort revealed the sparse-count weakness and informed the change before the second cohort ran.

Detection is intentionally not assigned to normal, measured loss or measured noise: those are benign-condition tests. Their useful metrics are false responses and estimated throughput. Fixed and threshold policies are baselines; their inability to detect subtle disturbances is a result, not a missing value to alter. The default C3 setting is already the best candidate under the tested conditions, so artificial retunes would not improve this model.
