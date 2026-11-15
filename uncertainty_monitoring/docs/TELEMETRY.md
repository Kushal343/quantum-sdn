# Telemetry and decisions

Each JSONL line is one completed non-overlapping window from one wavelength. Quantum wavelength indices are zero-based; plots label channels starting from one. Each wavelength must start at window zero and supply every subsequent window once. Interleaving channels is allowed. Emit explicit unavailable records for gaps rather than skipping indices.

| Field | Type / units |
|---|---|
| schema_version | Integer 1 |
| window | Nonnegative integer |
| wavelength | Integer channel index |
| config_version | Exactly the configured fixed version |
| start_seconds, end_seconds | Finite seconds matching window schedule |
| classical_powers_mw | Nonnegative measured powers in configured channel order |
| emitted | Three integer counts: signal, weak, vacuum |
| detections | Three integer counts, no greater than emitted |
| errors | Three integer counts, no greater than detections |
| available | Boolean; false requires all counts zero |

No scenario, attack flag, true loss, hidden background, or event-target label belongs in this schema. Unknown fields fail parsing. Data transport and provenance are assumed trusted in this offline stage; no authentication or tamper-proof claims are made.

Small example (valid counts, not a calibrated experiment):

```json
{"schema_version":1,"window":0,"wavelength":0,"config_version":"fixed-v1","start_seconds":0.0,"end_seconds":1.0,"classical_powers_mw":[1.0,1.0],"emitted":[1600000,300000,100000],"detections":[40000,1600,24],"errors":[800,50,12],"available":true}
```

Decision logs include classification, state, reason, six exact p-values, flagged features, alpha per test, signal QBER and descriptive interval, signal gain, and streaks. `held_during_window` records the prior advisory state; `held_next_window` records the state after processing this window. Actions are local recommendations only. There is no mutation of a quantum configuration and no security-release API.

Malformed input, duplicate/stale records, skipped indices, changed configuration version, and impossible counts cause an explicit CLI error. A missing report must instead be represented by an unavailable row with valid timestamps. Numerical zero is a real observation and is not treated as missing telemetry.

The replay command binds observations to a validated calibration artifact and does not need a truth file. Demos supply a complete replay example. Replay stores decisions without manufacturing experimental truth or evaluation metrics.
