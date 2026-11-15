# Pareto selection experiment and interpretation

Pareto selection is now implemented in the project as two explicit policies. `pareto_front` removes dominated candidates and applies the previous 90%-rate/error trade-off rule. `pareto` chooses the largest predicted delivered output on a Pareto front after switching cost, subject to the same illustrative QBER cap and existing isolation checks.

The method follows the presentation idea of comparing error and key-rate objectives, but specifies a unique operating-point rule. A front is a set of alternatives: by itself it cannot tell the controller which point to use. Better throughput may require accepting a slightly higher error rate within the operating constraints.

Observed outcome: the delivered-output policy improved the mean in **3 of seven** declared alignment cases, with network-wide gains from **0.33% to 0.75%** in those cases. The other four alignment cases were unchanged. The greatest absolute mean difference in the original eighteen standard scenarios was 0.0 estimated bits: those results were unchanged. Front extraction while keeping the previous rule produced no throughput improvement.

## How the algorithm works

1. Predict QBER and asymptotic key rate for each independently calibrated C1–C5 configuration.
2. Keep positive-rate candidates with predicted QBER no greater than 11%. That cap is an operating rule, not a security proof.
3. Compute output over H future intervals. Staying in the current setting gives rate × H. Switching gives rate × (H − 0.25), charging the modeled settling loss. H is at most eight and cannot exceed the run’s remaining intervals.
4. Remove a setting if another has both no higher predicted QBER and no smaller predicted delivered output, with a strict improvement in at least one objective.
5. Choose the front point with highest delivered output; use lower QBER and then deterministic configuration ordering to break ties. Switch only if predicted delivered output improves by more than 1%, at least two trial intervals remain, and the analytical check agrees.
6. Apply the existing two-window verification, rollback and cooldown. Anomalies, invalid telemetry and latched isolation are handled before selection. Pareto cannot resume a quarantined wavelength.

The audit in `selection_audit` records all feasible candidate scores, front membership, the chosen setting, horizon and cost. The current setting receives no switching charge. The `pareto_front` ablation deliberately retains the old selection and horizon rules so that front pruning can be tested separately.

## Experiment design

Total: **2,480 runs**. Two separately reported cohorts were predeclared in `pareto_experiments.py`:

- Standard scenarios: 20 fresh seeds per case and policy, 18 scenarios, three policies (`hybrid`, `pareto_front`, `pareto`), 18 intervals, 100,000 pulses per wavelength per interval.
- Measured alignment grid: 50 fresh seeds per case and policy, seven declared alignment-error values (2%, 2.5%, 3%, 3.5%, 4%, 4.5%, 5%), four policies (also `uncertainty`), 40 intervals, 1,000,000 pulses per wavelength per interval.
- Disturbances start at interval 6 and affect wavelength 3 in the alignment grid. Calibration includes every tested configuration/context and uses separate seeds. Runtime labels are not given to the controller.
- All policies share the same per-cohort monitoring budget, observations model, candidate grid and output-accounting convention. ML is disabled; the measurement engine is binomial, not Aer.
- The alignment cohort deliberately tests conditions between the previous study’s nominal and 5% alignment values. This is expanded validation, not a rerun of the exact previous 2,160-run study. Results from the cohorts must not be pooled into an unqualified improvement percentage.

## Measured output comparisons

The table reports average estimated accepted bits across all four wavelengths over an entire 40-interval run. Percent changes compare `pareto` with the existing `hybrid`, which already retunes.

| Reported alignment error | Existing hybrid | Pareto front with old rule | Pareto delivered-output rule | Change versus hybrid |
|---|---:|---:|---:|---:|
| 2% | 790,934.6 | 790,934.6 | 790,934.6 | +0.000% |
| 2.5% | 767,337.9 | 767,337.9 | 767,337.9 | +0.000% |
| 3% | 744,928.1 | 744,928.1 | 749,562.3 | +0.622% |
| 3.5% | 731,381.6 | 731,381.6 | 733,807.7 | +0.332% |
| 4% | 713,770.2 | 713,770.2 | 719,106.6 | +0.748% |
| 4.5% | 705,251.0 | 705,251.0 | 705,251.0 | +0.000% |
| 5% | 692,238.1 | 692,238.1 | 692,238.1 | +0.000% |

The front-only comparison is important: if its result equals hybrid, front extraction itself did not create a throughput gain. Any difference with the delivered-output policy also includes its explicit throughput preference and remaining-horizon switching guard. It must not be attributed to the dominance operation alone.

## Uncertainty and the error trade-off

| Alignment error | Mean paired difference in estimated bits | Descriptive bootstrap 95% interval | Seeds better / same / worse | Mean target QBER hybrid → Pareto |
|---|---:|---|---|---|
| 2% | +0.0 | [+0.0, +0.0] | 0 / 50 / 0 | 2.0810% → 2.0810% |
| 2.5% | +0.0 | [+0.0, +0.0] | 0 / 50 / 0 | 2.5792% → 2.5792% |
| 3% | +4,634.1 | [+3,875.0, +5,400.1] | 46 / 0 / 4 | 3.0783% → 3.0939% |
| 3.5% | +2,426.1 | [+1,580.9, +3,307.5] | 42 / 0 / 8 | 3.5907% → 3.6135% |
| 4% | +5,336.4 | [+4,289.8, +6,406.8] | 47 / 0 / 3 | 4.0868% → 4.1116% |
| 4.5% | +0.0 | [+0.0, +0.0] | 0 / 50 / 0 | 4.6191% → 4.6191% |
| 5% | +0.0 | [+0.0, +0.0] | 0 / 50 / 0 | 5.1104% → 5.1104% |

Target QBER is the observed, count-weighted error fraction over unblocked target-channel intervals after onset, averaged across seeds. It is diagnostic, not a security bound. The bootstrap resamples seed-level paired differences; its intervals are descriptive, not corrected for multiple scenarios. Shared seeds do not guarantee identical draws after different configurations are selected.

A positive mean with an interval crossing zero is inconclusive for a positive average gain in this experiment. An interval above zero supports a gain within the sampled model and conditions. It does not predict physical hardware performance or demonstrate a finite-key throughput gain.

## Standard scenarios and isolation

| Scenario | Hybrid isolation runs | Pareto isolation runs | Hybrid / Pareto hold runs | Hybrid / Pareto mean target isolation delay |
|---|---:|---:|---|---|
| burst | 0/20 | 0/20 | 20 / 20 | N/A / N/A |
| correlated | 2/20 | 2/20 | 9 / 9 | 11.00 / 11.00 |
| crosstalk | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| dark_counts | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| fwm | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| intercept | 20/20 | 20/20 | 20 / 20 | 1.00 / 1.00 |
| loss | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| misalignment | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| missing | 0/20 | 0/20 | 20 / 20 | N/A / N/A |
| model_mismatch | 20/20 | 20/20 | 20 / 20 | 1.00 / 1.00 |
| noise | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| normal | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| raman | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| shared_noise | 0/20 | 0/20 | 0 / 0 | N/A / N/A |
| tap | 20/20 | 20/20 | 20 / 20 | 1.00 / 1.00 |
| transient | 0/20 | 0/20 | 20 / 20 | N/A / N/A |
| unsupported | 0/20 | 0/20 | 20 / 20 | N/A / N/A |
| weak_intercept | 20/20 | 20/20 | 20 / 20 | 1.05 / 1.05 |

The isolation rules are unchanged, but different optical settings can change later statistical observations. The saved results, rather than an assumption, determine whether decisions match. A delay for benign model mismatch is anomaly-response timing, not attack identification. Correlated hidden drift is still a benign false-quarantine test. Pareto tuning does not solve that monitoring limitation.

## Computational efficiency

The local selector microbenchmark measured a median of **21.90 microseconds** for the existing selector and **47.73 microseconds** for the delivered-output Pareto selector. Each includes analytical scoring of five candidates; the Pareto version also constructs its audit. Calibration, full controller bookkeeping, Ryu and network latency are excluded.
These are seven batches of 1,000 calls on this machine and can vary with scheduling and hardware. With only five candidates, pairwise front extraction is O(K²) and adds work. Do not claim that this implementation accelerates the controller. Its purpose is a visible operating trade-off and cost-aware selection.

## How to see and interpret the results

- Open `results/pareto/summary.csv` to compare policies at each alignment value. Check the cohort (`suite`) before comparing rows.
- Open `results/pareto/paired_comparisons.json` for uncertainty intervals and how many seeds improved or worsened.
- Open `results/pareto/candidate_objectives.csv` for predicted candidate errors, rates, delivered output and front membership.
- Open `results/pareto/alignment_0.030-pareto-example.csv` and its `hybrid` counterpart. Follow wavelength 3 at intervals 6 onward; compare `config`, `next_config`, `action` and `selection_audit`.
- `pareto_front.png` explains one declared operating point. `output_comparison.png` shows repeated-run estimated output changes, not secret-key generation.
- Reproduce with `.\.runtime\python.exe -m experiments.pareto_experiments --out results/pareto-recheck`, then `.\.runtime\python.exe -m tools.report_pareto --out results/pareto-recheck`. Existing results are preserved by using a new output folder.

In the first saved 3% alignment seed, the Pareto controller proposes C2 at interval 6, verifies at 7 and rolls back at 8. The noisy two-window test fails even though the analytical model predicts an improvement. This example is deliberately retained: a front prediction is not a guarantee of improvement in every run, and the existing trial rule can reject a beneficial model prediction or incur repeated switching costs.

For a standard scenario, run `.\.runtime\python.exe run.py network --policy pareto --engine binomial --scenario misalignment --steps 40 --pulses 1000000 --out results/pareto-demo`. That named scenario uses 5% alignment; the separate grid script covers the intermediate values. The same `--policy pareto` choice is available in the Linux Mininet/Ryu monitor. Live Linux validation remains pending.

## Limits of the claim

The policy chooses among five illustrative decoy intensity settings. It does not correct the physical polarization/phase drift or perform optical rerouting. The error constraint and anomaly tests do not replace finite-key security analysis. The output metric uses the existing asymptotic rate estimator; no final secure keys are generated by these experiments. Raman/FWM and detector physics remain simplified. Positive results here justify testing the operating-point rule further, not promising a physical improvement of the same size.
