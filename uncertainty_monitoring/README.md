# Uncertainty-aware monitoring with fixed configuration

A self-contained research implementation of stage P2 of the WDM-QKD project. Four quantum wavelengths share a parameterized classical/quantum coexistence model. The monitor uses independent count calibration, exact binomial tail tests, a finite-horizon error budget, and persistent advisory hold/recovery decisions. Quantum intensities and selection probabilities never change.

**Implemented:** count-level simulation, observable telemetry, calibration artifacts, monitoring state machine, baseline comparison, offline replay, repeated experiments, confidence intervals, standalone HTML reports, PNG/PDF plots, source/configuration hashes, and scientific/integration tests.

**Scope:** this is a synthetic monitoring research prototype. No certified secret keys, finite-key distillation engine, real optical device control, or confirmed eavesdropper identification is implemented. Signal detection counts are never presented as secure bits. This stage can be completed and evaluated independently of a future cryptographic key engine.

## Start here

Use Python 3.11 or 3.12 for the pinned dependency environment (delivered run: Python 3.12). From PowerShell:

```powershell
cd 'D:\M.E\Proj\ACN\Basic\uncertainty_monitoring'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m qkd_monitor demo --scenario local_loss --out results/my_demo
```

Open `results/my_demo/report.html` in a browser. It works offline and embeds its figures. If your current Python already has the dependencies, use `python` directly instead of the virtual environment interpreter.

Delivered examples and benchmark are under `results/`. Read `docs/VALIDATION.md` for the actual checks and experiment exposure used in this delivery.

## Reproduce the study

```powershell
python -m qkd_monitor demo --scenario local_background --seed 42 --out results/demo
python -m qkd_monitor demo --scenario classical_power --seed 42 --out results/power_demo
python -m qkd_monitor benchmark --seeds 30 --seed 1000 --out results/benchmark
```

The benchmark runs ten scenarios and four policies on identical telemetry. It repeats calibration independently for each run seed. It stores run-level metrics rather than every decision from every benchmark run; demos store complete traces. Choose a new output folder for a new study. Reusing an output directory replaces files of the same name and may leave older unrelated files; a fresh directory keeps provenance clear.

Optional editable package installation:

```powershell
python -m pip install -e .
qkd-monitor demo --scenario local_loss --out results/installed_demo
```

## Replay measured-count telemetry

```powershell
python -m qkd_monitor replay --telemetry results/demo/telemetry.jsonl --calibration results/demo/calibration/seed_42.json --out results/replay_decisions.jsonl
```

Replay does not read the scenario-truth file. JSONL records must match the documented schema and supply each wavelength's windows consecutively, using explicit unavailable records for gaps. Unsupported contexts are inconclusive. A calibration artifact is bound to the full configuration fingerprint. For hardware data, generate independently validated measured-count calibration with the same schema; do not use the delivered synthetic calibration as a hardware reference.

`python -m qkd_monitor --help` lists commands. A custom configuration goes before the command:

```powershell
python -m qkd_monitor --config configs/default.json demo --scenario stable --out results/custom
```

## Architecture

```text
Scenario engine (hidden labels) -> link/count simulator -> Telemetry JSONL
Independent calibration counts -----------------------> Calibration JSON
                                                           |
Telemetry + Calibration -> Monitor -> decision/advisory log |
                                  -> hold/recovery state <--+

Evaluation alone joins decisions with hidden labels -> metrics and report
```

The fixed-config monitor has no configuration-setting action. Its only actions are `HOLD_OUTPUT`, `RESTORE_OUTPUT`, and `NONE`, issued at window end. Measurements continue during hold so recovery can be assessed. These are local advisories, not hardware acknowledgements or cryptographic release commands.

## Scientific method

- Simulate detection and error counts for signal, weak-decoy, and vacuum pulses. Errors are conditional on detections; all counts respect `errors <= detections <= emitted`.
- Independently calibrate the six per-pulse rates for each wavelength and supported classical-power vector.
- Construct simultaneous Clopper-Pearson calibration intervals using a shared calibration-failure budget.
- At each predeclared window, test all six count rates against their calibration intervals with conservative exact binomial tails.
- Allocate the remaining alarm budget across every wavelength, feature, and window. No feature-independence assumption is needed for the union bound.
- Require persistent unexplained departures before an output-hold advisory; restore after consecutive passing windows.
- Treat unsupported context, missing reports, or exhausted horizon explicitly. Do not silently restart an error budget.

See `docs/METHOD.md` for equations, proof scope, and caveats. The displayed QBER confidence bands are descriptive Wilson intervals, not alarm thresholds or security guarantees.

## Policies and fair interpretation

1. `passive`: collection only, no holds.
2. `fixed_threshold`: fixed 4% signal-QBER threshold or signal gain below 75% of nominal calibrated gain; same persistence/recovery mechanism.
3. `pointwise`: the same contexts and six count features, but plug-in calibration rates and correction within each window only. No complete-run error guarantee is claimed.
4. `uncertainty`: context-conditioned count tests with calibration and repeated-testing budgets.

The fixed thresholds are transparent illustrative engineering defaults. They are **not matched** to the uncertainty policy's false-alarm rate or sensitivity. Results demonstrate these exact policies under the stated model, not superiority over all tuned threshold methods. Passive collection withholding nothing is not evidence of good anomaly detection.

## Scenarios

`stable`, `classical_power`, `local_loss`, `local_background`, `gradual_drift`, `common_loss`, `transient`, `off_grid`, `telemetry_gap`, and `passive_tap`.

The passive-tap case is deliberately observation-equivalent to local loss. This demonstrates an attribution limit. It is not a simulation of Eve's information or a successful key-compromise experiment. The transient is deliberately too short to satisfy two-window persistence. Off-grid powers and telemetry gaps should produce inconclusive decisions, not fabricated attack labels.

## Output files

| File | Meaning |
|---|---|
| `report.html` | Standalone offline visual report |
| `config.json` | Frozen full experiment configuration |
| `manifest.json` | Seeds, versions, source hashes, assumptions, calibration hashes |
| `calibration/seed_*.json` | Independent calibration counts and confidence bounds |
| `run_metrics.csv` | One row per seed/scenario/policy |
| `summary.json` | Aggregated results and run-level confidence intervals |
| `paired_comparisons.json` | Paired uncertainty-minus-fixed differences |
| `telemetry.jsonl` | Demo observations, with no hidden scenario labels |
| `truth_evaluation_only.jsonl` | Demo labels for evaluator use only |
| `decisions_*.jsonl` | Complete demo decisions for each policy |
| `figures/*.png`, `*.pdf` | Reusable plots |

Timing values, timestamps, and platform metadata vary across executions. With the same code, dependencies, configuration, and seeds, telemetry and non-timing decisions are reproducible. No network requests occur during experiments.

## Project map

`physics.py`: link model and count sampling. `calibration.py`: independent training counts and intervals. `statistics.py`: exact tests. `telemetry.py`: validated transport record. `monitor.py`: state machine. `scenarios.py`: external labels. `evaluation.py`: run-level metrics. `report.py`: figures and report. `cli.py`: reproducible commands.

Additional documentation: `docs/METHOD.md`, `docs/TELEMETRY.md`, `docs/EXPERIMENTS.md`, `docs/RESEARCH_ROADMAP.md`, and `docs/VALIDATION.md`.

Check the delivered result artifacts without rerunning the full benchmark:

```powershell
python scripts/verify_artifacts.py
```

This checks source/calibration consistency and demo replay, not authenticated provenance or hardware security.
