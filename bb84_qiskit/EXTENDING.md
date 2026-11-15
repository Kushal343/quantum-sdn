# Extending the connected project

The connected runner now exposes its dependencies explicitly. Changes to measurements, data sources, policies and decision delivery can be made at those boundaries. The existing standalone BB84 command and monitor.py entry point remain available.

## Module responsibilities

| Module | Responsibility |
|---|---|
| simulate.py | BB84 circuit construction and standalone demonstrations |
| bridge.py | Optical counts to Qiskit measurements, basis sifting, matching calibration and runtime conversion |
| integration.py | Dependency contracts, fresh policy state and per-observation decision delivery |
| monitor.py | CLI, experiment orchestration, output files, evaluation and provenance |
| monitor_config.json | Physical and statistical experiment settings |
| uncertainty_monitoring/qkd_monitor | Existing monitoring, telemetry, calibration and statistical implementation |

Keep both sibling project folders together. Imports currently use that workspace layout. Independent distribution as installable packages would require an additional packaging change.

## Change settings from the command line

From bb84_qiskit in PowerShell:

```powershell
.\.venv\Scripts\python.exe monitor.py --scenario local_loss --policies uncertainty --windows 30 --event-start 8 --event-end 20 --out results/flexible_loss
```

Other overrides are --pulses and --calibration-pulses. Unspecified settings come from --config, which defaults to monitor_config.json. The full configuration is validated after overrides and saved with the run. Counts and calibration must continue to use the qiskit-sifted-v1 definition.

## Replace a component from Python

Import Integration and pass it to experiment using the integration keyword. The defaults reproduce the existing pipeline. Callable functions are supplied by trusted Python code rather than loaded dynamically from JSON.

* calibration_source(config, seed) returns a Calibration with count cells covering every configured classical-power context.
* observation_source(config, scenario, seed) returns observable Telemetry records and a matching sequence of evaluator Truth labels. Only the evaluator receives those labels.
* count_adapter(emitted, detected, errors, seed) returns sifted detection counts, sifted error counts and a JSON-serializable audit. The same adapter is used for calibration and runtime. Preserve three pulse categories, count ordering and the emitted-pulse denominator.
* policy_factory(config, calibration, policy_name) creates a fresh object exposing process(observation), which returns a decision dictionary. Include the existing decision fields when using the standard evaluator.
* decision_sink(decision) receives a copy of each decision immediately after processing. It can feed a queue, record events or call a controller adapter. Exceptions propagate so failed delivery is visible.

An example integration that collects advisories:

```python
from pathlib import Path
from monitor import Config, experiment
from integration import Integration

events = []
integration = Integration(name="queued-advisories", decision_sink=events.append)
config = Config.load("monitor_config.json")
experiment(config, "local_loss", 42, Path("results/queued_example"),
           integration=integration, policies=("uncertainty",))
```

Use one selected policy for a sink that performs real actions. Running several policies is an offline comparison. Every policy receives its own processor state and the same observations.

## Live observations and future SDN work

run_policy accepts an iterable, so an adapter can yield observations from a queue or transport as they arrive. Each channel must start at window zero and preserve consecutive window identifiers. Supply explicit unavailable records for gaps. It returns decisions and sends each one to the sink during processing.

The current experiment runner collects a finite synthetic trace and evaluator labels. For live monitoring, call run_policy directly with an independently validated calibration and a trusted observation stream. Large or indefinite streams will need a retention strategy and a statistical horizon design beyond the current finite run.

A Ryu sink can translate HOLD_OUTPUT and RESTORE_OUTPUT into command requests. Command identifiers, acknowledgements, retries and authentication belong in that future transport adapter. Returning from the current sink only confirms local handler completion.

## Alternative Qiskit sampler

sift_counts accepts an optional sampler_factory. A replacement factory must accept seed= and return an object whose run(pubs).result() supports data.meas.get_counts(). Wrap a backend-specific API if needed, then pass a count_adapter using that factory through Integration. Cloud runtimes have their own submission, queueing, authentication and result contracts and require a dedicated adapter.

Set integration name, backend_label and model_description accurately for custom integrations. Regenerate calibration whenever the measurement model changes. A different observable definition requires a new version and corresponding schema validation.

## Output consistency

A nonempty output directory is rejected. A .incomplete marker remains if execution fails partway. Successful runs remove it after all output files are written. Use a fresh directory after a failed run and inspect the error before retrying. This marker is completion evidence, not a concurrent-writer lock. Give concurrent runs distinct output directories.

Manifests record the selected policies, integration identity, backend label, full resolved configuration fingerprint and source hashes including the new modules. Earlier saved studies retain their original hashes and remain historical evidence for that source version.

## Changes and validation

The refactor extracted bridge.py while keeping the old monitor imports available for callers. It added Integration, streaming policy processing, CLI overrides, configurable policy selection, completion markers and extension metadata. It reuses the existing telemetry and statistical contracts.

Run .venv/Scripts/python.exe -m unittest test_connection test_integration -v from this folder. The tests cover count conservation, reproducibility, hold and recovery, compatibility with existing replay, isolation from sink mutation, a custom policy factory and visible delivery failure.
