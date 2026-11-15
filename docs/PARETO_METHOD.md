# Pareto selection for wavelength level adaptation

The presentation's two objectives are implemented explicitly: lower predicted
signal QBER and higher predicted accepted output. A setting is dominated if
another has no higher QBER and no smaller output, with at least one strict
improvement. Dominated settings are removed. The remaining front contains
trade-offs and needs an additional, declared selection rule.

## Policies

`pareto_front` is an ablation: extract the front, then retain the earlier
selection rule. In high-QBER conditions that rule keeps at least 90% of the
best predicted rate and minimizes QBER; otherwise it maximizes the predicted
rate. This can produce exactly the same decisions as `hybrid`. It does not
demonstrate a new performance gain merely because a Pareto front is logged.

`pareto` uses a delivered-output objective. For each feasible candidate:

```text
H = min(8, number of remaining future intervals)
current setting:  predicted output = rate * H
changed setting:  predicted output = rate * (H - 0.25)
```

Candidates must have positive predicted rate, predicted QBER at most the
illustrative 11% cap, and an independent calibration for the reported context.
The controller constructs the front of QBER versus this output and selects
the greatest output on it. Lower QBER breaks an equal-output tie. It switches
only if predicted output is more than 1% above staying, at least two future
verification intervals remain, and the analytical model approves the change.
ML predictions, when enabled, can propose candidates but cannot replace the
analytical check. The experiments use direct analytical predictions, with ML
disabled.

The original anomaly, hold, recovery, permanent isolation, verification,
rollback and cooldown checks remain in force. Selection runs only after those
validity and anomaly checks permit adaptation. A Pareto result cannot resume
an isolated wavelength.

## Why an output gain is possible

At a reported 3% alignment error in the model, the old high-QBER rule chooses
C3 because it has lower error than C2 while retaining at least 90% of the best
predicted rate. Since C3 is already active, it does not retune. C2 can instead
offer enough additional estimated output to justify its switching cost, with
a small QBER increase. Both choices can lie on the front. The different
operating-point preference creates the possible throughput gain.

Changing source intensity does not physically correct polarization drift.
Predicted rate already includes the model's error-correction and privacy terms,
but remains an asymptotic estimate. The operating cap is not finite-key
security acceptance.

## Audit and complexity

`qkd_sdn/pareto.py` implements the front and selection. The controller logs
`selection_audit` with feasible scores, front membership, chosen configuration,
cost and horizon. `qkd_sdn/hybrid.py` integrates the selection with monitoring.
Both the Windows CLI and Linux Mininet/Ryu lab expose `--policy pareto` and
`--policy pareto_front` through the common policy factory.

There are five discrete candidates. Exact pairwise dominance uses O(K^2)
comparisons; no evolutionary optimizer is needed. Computing a front adds work
to five cheap analytical evaluations, so computational acceleration must not
be assumed. The experiment includes a local selection microbenchmark.

## Reproduce and inspect

```powershell
.\.runtime\python.exe -m experiments.pareto_experiments --out results/pareto-recheck
.\.runtime\python.exe -m tools.report_pareto --out results/pareto-recheck
```

The declared standard cohort uses twenty seeds for each of eighteen scenarios
and three policies, with eighteen intervals and 100,000 pulses per channel.
The separate alignment cohort uses fifty seeds for seven declared alignment
values and four policies, with forty intervals and one million pulses per
channel. These are new evaluation seeds. Calibration randomness is separate
and shared across policies within a seed. Configurations may change later
sampling draws, so common seeds do not guarantee identical observations.

Read [the result report](../results/pareto/PARETO_RESULTS_REPORT.md) and
[candidate predictions](../results/pareto/candidate_objectives.csv). The original
six-policy `hybrid_experiments.py` study keeps its policy list frozen so new
policies do not silently change its historical reproduction command.

The new studies test a selection rule, not a new security proof. Live Ryu,
Mininet and optical-hardware results are not established by these experiments.

## Observed result

The declared grid produced mean estimated network-output gains of 0.62% at
3% reported misalignment, 0.33% at 3.5%, and 0.75% at 4%, compared with the
existing hybrid policy. The other four alignment cases and the eighteen
standard scenarios were unchanged. The front-only ablation was also unchanged.
Fifty seeds were used for each alignment case; the positive differences have
descriptive paired-bootstrap intervals above zero in this model. Individual
runs can lose output after unsuccessful trials and rollback.

The policy accepts a small increase in observed target-channel QBER in exchange
for a larger estimated key-rate term. It does not dominate the old policy in
both objectives. The local selector benchmark increased from about 22 to 48
microseconds per call, so this is an output benefit in selected regimes, not
a computational speedup. The full suite passed 81 tests, and an Aer smoke run
completed one retune without isolation. Neither establishes a physical gain.
