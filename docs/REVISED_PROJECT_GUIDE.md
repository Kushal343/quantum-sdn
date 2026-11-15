# Uncertainty-Aware SDN Control for Adaptive Key Generation in WDM-QKD Networks

## 1. Research question and deliverable

**Research question:** Can a controller that accounts for sampling uncertainty and acts on individual wavelengths improve delivered secure-key volume and reduce unnecessary interruptions compared with fixed-threshold control?

Build a reproducible, classical, event-driven simulation of four quantum wavelengths between Alice and Bob on one fibre, with classical WDM channels contributing wavelength-dependent background counts. Implement a separate controller and device agents. Compare control policies under the same external disturbances, demand, and elapsed time.

The contribution is an operational control policy and its measured trade-offs. Do not claim a new QKD protocol, a new security proof, universal attack identification, or hardware validation.

### Required and optional scope

Required: count-level decoy-state model, finite-key estimator, WDM noise coupling, per-wavelength statistics, direct candidate evaluation, state machine, device-control messages, application key pool, repeated experiments, reproducible results.

Optional after the core passes: ML surrogate, broader wavelength counts, a physically specified attack model, additional routes, a dashboard.

Exclude rerouting and wavelength swapping from the first version: the topology has no alternate route or spare channel. Exclude detector blinding, Trojan-horse attacks, and PNS detection claims unless the corresponding physics, observables, and protocol assumptions are implemented and reviewed.

## 2. Explicit assumptions

1. Four independently encoded and measured quantum wavelengths share the fibre. Each has independent receiver resources in the initial model. Shared detector dead time and saturation are excluded and acknowledged.
2. Classical wavelengths have defined launch powers and schedules. A wavelength-coupling model converts their contribution to receiver background probabilities.
3. Alice and Bob use a single, fully specified three-intensity decoy-state BB84 variant with phase-randomized weak coherent pulses, trusted devices, and authenticated classical communication. Use compatible basis sampling, sifting, and finite-key equations throughout.
4. Controls change only at completed key-block boundaries. A block has one configuration version. Do not pool differently configured blocks unless the chosen proof explicitly supports it.
5. The controller receives measured counts and calibrated device properties. It cannot read simulator event labels, true transmittance, true attack identity, or future disturbances.
6. The model for predicting benign performance may be wrong. An explained observation does not prove the absence of an attacker.
7. The QKD estimator independently decides block eligibility. Operational confidence intervals and ML predictions never authorize key release.
8. Model the classical channel as authenticated without authentication failure in the first version. State whether authentication-key consumption is deducted from application-available keys; report the convention consistently.

## 3. Architecture

```text
External scenario engine (hidden event labels)
                  |
                  v
Fibre/WDM model -> four QKD device agents -> finite-key estimator
                            |                       |
                     measured telemetry      eligible key blocks
                            |                       |
                            v                       v
                 SDN controller             key manager/pool -> demand
                 | detector / state machine
                 | direct candidate evaluator
                 v
             versioned commands -> device agents -> acknowledgements
```

Keep the scenario engine outside the controller. The evaluator can read event labels after a run to measure performance.

## 4. Physical model and count generation

### 4.1 Start with a transparent analytical model

For wavelength i, define total transmittance including detector efficiency:

`eta_i = eta_detector_i * 10^(-(alpha_i * L + insertion_loss_i + extra_loss_i)/10)`.

Use units explicitly: kilometres, dB/km, dB, watts or dBm with explicit conversion, probabilities per gate, emitted pulses/s, and secret bits/s.

Define receiver background probability `Y0_i(t)` from dark counts and optical background. A useful simplified starting form for the optical contribution is `sum_j A[i,j,L] * P_j(t)`, where P is classical launch power and A includes wavelength separation, filtering, propagation direction, and the selected length model. State the units and provenance of A. If coefficients are illustrative, describe the work as a study of a parameterized coexistence model. Do not claim experimentally calibrated Raman propagation.

Convert optical rates to detection probabilities consistently, and combine independent background sources with `1 - product(1-p_source)`. Do not add probabilities blindly at high background levels.

For intensity x, a simple honest-channel gain model is:

`Q_x = 1 - (1-Y0) * exp(-eta*x)`.

For a first analytical implementation, an explicitly approximate error-gain model is:

`T_x = 0.5*Y0 + e_d*(1-exp(-eta*x))`, with `E_x = T_x/Q_x`.

This low-background approximation must be documented. Validate `0 <= T_x <= Q_x <= 1` in every simulated regime. A refined detector model must handle simultaneous signal/background events, double clicks, and receiver assignment consistently rather than clipping invalid equations silently. Do not use an honest-channel formula as a security proof.

### 4.2 Generate observations, not arbitrary QBER values

For each block, allocate emitted pulses across intensity and Alice/Bob basis choices according to the chosen protocol. A count-level multinomial allocation is sufficient; tracking every photon or quantum state is unnecessary for the basic study.

For each compatible category with N emitted pulses:

- Detection count: `D ~ Binomial(N, Q_x)`.
- Error count conditional on detections: `K ~ Binomial(D, E_x)`.
- Observed gain: `D/N`.
- Observed QBER when D > 0: `K/D`.

Never generate errors and detections independently in a way that allows K > D. Handle zero detections and insufficient samples explicitly. Compute reported SKR from extracted secret bits divided by elapsed time, including overhead under the reporting convention.

### 4.3 Three clocks

Specify the pulse clock, telemetry interval, and key-block duration separately. Telemetry can be faster than key production. Only finished eligible blocks add keys to the pool. Configuration updates occur at block boundaries, with modeled command and settling delays.

## 5. Finite-key estimation and key accounting

Implement one published finite-key decoy-state method fully. Match the source's protocol assumptions and notation before coding. Estimate lower single-photon contributions and upper phase-error bounds from observed intensity/basis counts, then calculate the allowable key length with error-correction leakage, verification, privacy amplification, and failure-probability terms.

Use Ma et al. for analytical understanding and asymptotic sanity checks; use a compatible finite-key method such as Lim et al. for the reported finite-block results. Do not assemble unrelated formulas from different protocol variants.

The form `single-photon contribution - leakage - finite-size penalties` is an explanation, not an executable formula. Copy the exact applicable equations into a design note, define every variable, and cross-check an implementation against a published example or independent calculation. Freeze that implementation before policy comparison.

Maintain a documented failure-probability budget across parameter estimation, secrecy, correctness, and the collection of blocks reported. Bound the maximum blocks/trials for a run or use another valid compositional allocation. Operational alarm significance is a separate budget.

For completed block b, the estimator outputs `eligible`, `secret_bits`, `failure_reason`, `security_budget`, and `config_version`. Uncertainty, missing assumptions, or failed bounds do not produce positive keys. Extra operational quarantine can discard otherwise eligible blocks, which is an availability cost.

Maintain:

`pool_next = min(capacity, max(0, pool + eligible_accepted_bits - served_demand - reserved_costs))`.

Track overflow, unmet demand, and reserved authentication costs separately. Maintain per-link key identity and pairing. Pool across the four wavelengths only because all terminate at the same Alice/Bob endpoints and the modeled key manager tracks matching keys correctly.

## 6. Telemetry and SDN interface

Each telemetry record contains wavelength, block ID, configuration version, timestamps, intensity/basis emitted counts, detection counts, error counts, observed QBER/gains, estimator status, secret bits, calibrated hardware parameters, measured classical-channel powers, current state, and sample-sufficiency flags.

Treat link loss and background levels as estimates with uncertainty when inferred from those counts. Do not hand their simulator ground truth to the controller. If an optical monitor is assumed, model what it measures, its accuracy, and its trust assumptions.

Commands:

- `SET_CONFIG(wavelength, config, version, effective_block)`
- `PAUSE(wavelength, reason)`
- `PROBE(wavelength, approved_config, duration)`
- `RESUME(wavelength, version)`

Acknowledgements include acceptance/rejection, actual application time, active version, and failure reason. Bound retries and represent delayed or missing acknowledgements. A late command must not silently affect the wrong block.

An in-process event bus is sufficient initially if commands and telemetry are separate message types with timing. A later local service interface can demonstrate the same contract. Describe it as an emulated SDN control plane. Use ETSI QKD 015 as an architectural reference, not a claim of complete standards conformance or universal device support.

## 7. Statistical monitoring

### 7.1 Conditional baseline

Build baseline expectations from benign calibration data across supported classical powers and configurations. Condition predictions on active configuration, observed classical powers, and calibrated device parameters. A controller-induced intensity change must not automatically look like an attack.

Monitor observed gain, error gain, QBER, and measured key output. Do not assume that these features are statistically independent.

### 7.2 An implementable first detector

Use non-overlapping completed monitoring windows. Obtain predictive count ranges that include measurement and baseline-estimation uncertainty. Wilson intervals can describe QBER uncertainty but do not by themselves define a complete change test. Gain and error-gain checks should compare observed counts to the conditional prediction.

For a bounded first study, predeclare M windows, four wavelengths, and J monitored tests. Allocate a conservative operational false-alarm budget across `M*4*J` valid tests, or use an explicitly justified multiple-testing/sequential method. Account for baseline fitting on separate data. Verify the full-run false-alarm rate empirically on untouched benign runs.

Persistent alarms can require r consecutive qualifying windows. Select r on validation runs, freeze it, and evaluate the resulting policy. Do not claim that this automatically gives a particular theoretical false-alarm rate. A CUSUM variant can be added later, with its complete-run threshold calibrated independently.

### 7.3 Operational categories

- Normal: observations and performance remain acceptable.
- Explained degradation: changed observations fit the measured-power/configuration-conditioned model and other available diagnostics.
- Unexplained anomaly: a persistent mismatch remains after accounting for observed conditions.
- Inconclusive: inadequate samples, missing telemetry, or uncertain model coverage.

No category proves an attacker is absent or present. A common change across wavelengths supports investigating a common cause but does not certify a benign cause.

## 8. Controller state machine

| State | Entry | Action | Exit |
|---|---|---|---|
| INITIALIZING | New session | Calibrate, collect required samples | Sufficient evidence and valid protocol state |
| ACTIVE | Normal operation | Continue and release only eligible accepted blocks | Persistent degradation or mismatch |
| OBSERVING | Inconclusive operational evidence | Gather evidence, avoid speculative reconfiguration | Resolve category or conservative timeout |
| DEGRADED | Explained performance reduction | Evaluate valid candidates | Worthwhile trial or remain unchanged |
| TRIAL | Candidate selected | Apply at next block, measure over predefined blocks | Accept or rollback |
| QUARANTINED | Persistent unexplained anomaly or specified device failure | Stop key release from this wavelength | Scheduled probe |
| PROBING | Quarantined recovery check | Collect diagnostics without application key release | Restore after predefined passing blocks or re-quarantine |

The key estimator's block abort is independent of this state machine. One abort need not permanently quarantine a channel. Define separate persistence rules for protocol aborts, telemetry faults, and operational anomalies.

Priority order: protocol/device validity; unexplained persistent mismatch; inadequate evidence; explained degradation; normal continuation. High QBER and low SKR can occur together and are not mutually exclusive branches.

## 9. Adaptation rule

Represent configuration as `(mu, nu, p_signal, p_weak, p_vacuum, basis_probabilities)`, with a fixed approved vacuum intensity and protocol-specific constraints. Validate probability sums, intensity ordering, hardware ranges, and minimum expected estimation counts. Keep basis probabilities fixed initially to reduce scope.

Start with a small documented grid of valid configurations, including the current setting. Evaluate directly using estimated channel conditions, uncertainty, the chosen finite-key estimator, and the expected observation horizon. Evaluate a range of plausible conditions rather than assuming perfectly known loss/noise.

Use the score:

`predicted delivered secret bits over horizon H - switch/settling losses - operational penalties`.

Use an explicit conservative treatment of prediction uncertainty. Rank by a lower prediction bound or a documented robust scenario score; do not describe an arbitrary safety factor as a formal security guarantee.

Switch only when expected improvement exceeds a predefined margin and the minimum dwell time has elapsed. If no feasible candidate yields a worthwhile benefit, keep the current configuration, collect more evidence, or pause according to the state policy.

Apply at a block boundary, acknowledge the actual version, wait through settling, then run a fixed trial duration. Accept only if the predefined performance and validity criteria pass. Otherwise rollback at the next boundary. Record both trial and rollback costs. Do not repeatedly test until a lucky positive result appears.

Pareto plots may explain QBER/SKR trade-offs, but the actual selection rule must be deterministic and documented. Favor delivered key volume subject to protocol requirements instead of treating low QBER as an independent end goal.

## 10. Main event loop

```text
initialize devices, configurations, key pool, detector and controller
for each scheduled event until fixed experiment end time:
    scenario engine updates hidden channel conditions when scheduled
    devices generate count telemetry under their actual configurations
    estimator processes completed key blocks independently
    key manager admits only eligible blocks allowed by operational policy
    controller ingests telemetry without event labels
    controller updates evidence and per-wavelength state
    if state permits adaptation and completed-block boundary is reached:
        evaluate candidates and switch only if gain criterion passes
    process command acknowledgements, settling and trial outcomes
    consume application demand and record unmet demand
    schedule probe/recovery events for quarantined wavelengths
    append complete structured event log
```

Never rewind elapsed time for a trial. Continue the simulation of healthy wavelengths during quarantine or reconfiguration of another channel.

## 11. Experimental policies

Use the same finite-key estimator, hardware assumptions, demand, control costs, and information restrictions for every policy.

| Policy | Monitoring and action | Purpose |
|---|---|---|
| P0 | Fixed settings, ordinary protocol block acceptance, no adaptive controller | Natural operational reference |
| P1 | Fixed per-wavelength thresholds, fixed settings, defined pause/recovery rules | Practical threshold baseline |
| P2 | Uncertainty-aware monitoring, fixed settings | Isolate monitoring contribution |
| P3 | Uncertainty-aware monitoring plus direct candidate evaluation | Main proposed method |
| P4, optional | Same policy as P3 with ML candidate predictions | Isolate ML speed/accuracy trade-off |
| Pagg, optional | Aggregate-threshold monitoring | Illustrate aggregation limitations |

Compare alarms at matched benign-run false-alarm rates where possible. Freeze thresholds on validation runs. Distinguish statistical monitoring gains from better tuning or access to extra features. An oracle with hidden true conditions is only a labelled upper-reference policy, not a fair deployable baseline.

## 12. Scenarios and expected questions

| Scenario | Construction | Question |
|---|---|---|
| Stable benign operation | Sampling variation only | Does monitoring cause unnecessary interruptions? |
| Classical power increase | Increase measured P_j, affecting multiple quantum wavelengths via A | Can the controller respond to explained WDM degradation? |
| Local additional loss | Change transmittance of one wavelength | Does adaptation help, and when does it fail? |
| Local excess background | Add a receiver background component | Does the controller preserve healthy channels? |
| Gradual drift | Slowly change loss or background | Detection delay versus false alarms |
| Common disturbance | Change a shared physical parameter | Does cross-wavelength context help without assuming the event is benign? |
| Measurement-model mismatch | Use an unmodeled but benign event | Does the controller falsely treat an unknown fault as an identified attack? |
| Indistinguishable loss pair | Label one run fault and one passive tap but give identical observation laws | Demonstrate the limit of attribution |
| Transient disturbance | Short event then recovery | Do dwell time and recovery rules avoid oscillation? |
| Telemetry/control fault | Delay/miss reports or reject commands | Does the control plane handle stale information correctly? |

A passive tap can be modeled as extra attenuation for the attribution-limit experiment. This alone is not an information-leakage model. For an explicit security attack study, specify Eve's action at the photon/device level and verify that the estimator's assumptions apply. Do not manually lower SKR under an attack label.

Train/calibrate on one set of benign regimes. Validate thresholds and tuning on a second set. Evaluate on untouched seeds, regimes, and event traces. Include parameter regions where adaptation is useless or harmful. Do not discard failed or no-key runs.

## 13. Metrics and statistical comparison

Primary metric: application-available or application-delivered secret bits over fixed elapsed time. Report generated, accepted, discarded, delivered, overflow, authentication reservation, and unmet demand separately.

Additional metrics: false quarantines per run or hour; fraction of benign runs with any false quarantine; detection delay with missed detections/censoring stated; time in each state; recovery time; reconfiguration count; key loss due to switching/trials; controller runtime; per-wavelength fairness; finite-key abort rate.

Use paired external scenario traces across policies. Separate random streams for exogenous conditions, device sampling, and policy actions so divergent policies do not accidentally change future disturbances. Repeat across seeds. Start with approximately 30 independent scenario seeds per condition, then add runs where confidence intervals remain too wide for the claim. This is a starting point, not a universal power guarantee.

Compute confidence intervals for paired policy differences at the run level; do not treat every correlated telemetry window as an independent experiment. For very rare false alarms, sufficient benign exposure is necessary. A small run set with zero events does not establish an extremely small probability.

## 14. Optional ML extension

Only begin after P3 works and direct evaluation runtime is measured.

Inputs: observable estimated condition features with uncertainty, configuration, block duration/size, and relevant calibrated parameters. Outputs: candidate key yield/performance or ranking. These are forecasts, never key-security certificates.

Generate training labels offline with the validated evaluator. Keep entire regimes/traces separate between training and testing. Compare simple regression or a tree model before a neural network. Evaluate runtime including feature preparation, selected-configuration regret relative to direct evaluation, realized delivered-key difference, and behavior outside training coverage.

Use direct evaluation or a conservative approved setting outside model coverage. If a five-candidate direct search is already negligible relative to block duration, conclude that ML is unnecessary at this scale. That is a valid finding.

## 15. Suggested repository

```text
configs/                 protocol, devices, coupling, policies, scenarios
src/physics.py           transmittance, gains, background and error model
src/counts.py            category allocation and sampled observations
src/finite_key.py        selected published bound and budgets
src/device_agent.py      configuration versions and command execution
src/telemetry.py         message schemas and validation
src/detector.py          conditional baseline and monitoring tests
src/controller.py        states, priorities, timing and recovery
src/optimizer.py         candidate validity and direct evaluation
src/key_pool.py          pairing, demand, reservations and overflow
src/scenarios.py         hidden external event generation
src/experiment.py        event loop and policies
src/metrics.py           run-level measures and paired comparisons
tests/                   scientific and controller invariants
results/raw/             logs and frozen configurations
results/figures/         generated plots
docs/model.md            equations, units, assumptions and provenance
docs/experiments.md       frozen evaluation protocol
```

Use Python with numerical arrays, scientific statistics/optimization, tables, and plotting. An event queue or an event-simulation library is sufficient. No quantum SDK is required for this count-level model. Record dependency versions and provide one reproducible run command and one figure-generation command.

## 16. Build order and completion gates

| Phase | Work | Completion gate |
|---|---|---|
| 1 | Freeze question, protocol, assumptions and units | Design note reviewed; all simulator-only variables identified |
| 2 | One wavelength, deterministic gains and sampled counts | Correct limiting behavior; counts valid; published-model sanity checks |
| 3 | Finite-key estimator and pool | Independent numerical cross-check; no positive output from invalid blocks |
| 4 | Four wavelengths plus WDM coupling | Classical power changes create documented wavelength-dependent effects |
| 5 | Messages, state machine, commands and delays | Version/delay/rollback/probe behavior verified on deterministic traces |
| 6 | Detector and direct adaptation | Whole-run benign calibration and fixed policy settings |
| 7 | Policy comparison and ablations | Paired repeatable experiments with uncertainty intervals |
| 8 | Optional ML and final write-up | Justified speed/quality result or explicit decision to omit ML |

### Meaningful checks

- Gain decreases with added loss in the stated honest model; zero detections never produce keys.
- Vacuum categories and sparse decoys produce defined estimator outcomes rather than divide-by-zero errors.
- All sampled counts obey physical/category constraints and have reproducible seeds.
- Finite-key calculations match independent reference values and respect the stated budgets.
- Ground-truth scenario labels cannot enter controller inputs.
- Keys are never released from failed estimator blocks or quarantined/probing states.
- Retuning one independent receiver does not change another configuration, while shared WDM disturbances still affect their observations.
- Command timing is honored, partial blocks are handled explicitly, and missing acknowledgements cannot create false version agreement.
- Hysteresis/dwell time prevents unlimited oscillation; probes permit eventual recovery.
- Matched fault/tap observation laws do not yield claimed above-chance attribution from identical priors and observables.

## 17. Six-week planning example

Week 1: scope and model, one-wavelength simulator, equation review.

Week 2: finite-key implementation, independent verification, four wavelengths and key pool.

Week 3: controller messages, states, direct optimizer, timing and recovery.

Week 4: detector calibration, scenarios, fixed baselines and preliminary ablations.

Week 5: repeated frozen experiments, sensitivity studies, optional ML only if justified.

Week 6: regenerate all results, write limitations, prepare demonstration and presentation.

For six members, assign ownership of (1) physical/WDM model, (2) finite-key estimation, (3) statistics, (4) controller/interfaces, (5) optimization/key pool, and (6) experiments/reproducibility. Have the physical-model and finite-key owners cross-review each other. Agree schemas and units before parallel implementation. This is a suggested team division, not a prerequisite.

## 18. Final evidence and presentation

Required figures: example per-wavelength time traces with states/actions; cumulative delivered keys for competing policies; false alarms versus detection delay; effect of disturbance strength; effect of block duration and control cost; monitoring/adaptation ablation. If ML is included, show runtime versus selection regret. Include at least one case with no benefit.

Report sections: precise question; related-work comparison; assumptions; physical and finite-key model; controller algorithm; interfaces/timing; evaluation protocol; results with uncertainty; detection and modeling limits; reproducibility.

Demonstration: run stable operation, introduce an observed classical power increase, show a valid candidate decision and its measured cost/benefit, introduce an unexplained anomaly on one wavelength, show quarantine while others continue, then demonstrate probe-based recovery. Keep labels such as 'attack' in the evaluator view only.

Completion means the model and controller are reproducible, comparisons are fair, outcomes include uncertainty and negative cases, and every claimed improvement corresponds to measured evidence. It does not require the adaptive policy to win in every scenario.

## 19. Source anchors

- Ma et al., Practical Decoy State for Quantum Key Distribution: https://arxiv.org/abs/quant-ph/0503005
- Lim et al., Concise Security Bounds for Practical Decoy-State Quantum Key Distribution: https://arxiv.org/abs/1311.7129
- Wang and Lo, Machine Learning for Optimal Parameter Prediction in Quantum Key Distribution: https://doi.org/10.1103/PhysRevA.100.062334
- ETSI GS QKD 015 V2.1.1, Control Interface for Software Defined Networks: https://www.etsi.org/deliver/etsi_gs/QKD/001_099/015/02.01.01_60/gs_qkd015v020101p.pdf

These anchor the design; they do not replace reading the applicable equations, device assumptions, or interface definitions before implementation.
