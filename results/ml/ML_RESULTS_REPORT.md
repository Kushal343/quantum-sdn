# ML training results

The project's Random Forest models were trained successfully using seed 42.
They predict the quantum bit error rate and the estimated secret-key fraction for candidate optical settings.

## What was tested

Training used 320 simulated channel conditions, with five candidate settings per condition (1,600 training examples). Testing used 80 separate conditions, also with five settings each (400 test examples). All settings for a condition stayed together in either training or testing, so the test conditions were unseen during training.

The examples come from the project's analytical model, not physical equipment or measured quantum data. Two Random Forest regressors, each with 100 trees, predict the two outputs.

## Findings in plain language

| Measure | Result | Meaning |
|---|---:|---|
| Average absolute error in predicted bit error rate | 0.003925, or 0.3925 percentage points | Predictions differed from the analytical reference by about 0.39 percentage points on average. This is not a worst-case bound. |
| Average absolute error in predicted secret-key fraction | 0.0001358 | This corresponds to about 136 bits per million pulses in the model's estimate, on average. It is not a count of actual generated keys. |
| Average relative loss from choosing a setting using ML | 2.70% | Where the reference model predicted a positive achievable rate, choosing the setting with the highest ML-predicted rate gave an average rate about 2.70% below the best of the five available settings. |

The model can propose settings close to the analytical model's preferred settings on this test set. The 2.70% result measures configuration selection; it is not classification accuracy and does not demonstrate an improvement over the existing analytical controller.

## What this run does not establish

This is one training/test split, not a repeated-seed robustness study. It does not measure attack-detection accuracy, real equipment performance, end-to-end secure-key production, or Mininet packet forwarding. The analytical model is both the source of training labels and the reference used for evaluation. Independent data would be needed to establish accuracy beyond that model.

The training command saves evaluation metrics only. It trains the models in memory and does not save a reusable fitted-model file. The existing network command with `--ml` trains a new model before running its simulation.

## Reproduce

From the project folder in PowerShell:

```powershell
.\.runtime\python.exe run.py train --seed 42 --out results/ml
```

Exact machine-readable results are in `ml_metrics.json` alongside this report.
