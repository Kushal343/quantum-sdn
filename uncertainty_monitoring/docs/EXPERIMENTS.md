# Evaluation protocol

## Fixed external conditions and random streams

Default runs contain 120 one-second windows, 2 million emitted pulses per channel-window, four quantum channels, and two classical channels. Calibration uses 40 million pulses per context/channel. Powers use a 3x3 grid. Disturbances normally occupy windows 35 through 84 inclusive. A transient occupies only window 35; missing reports occupy 35 through 37.

Calibration uses SeedSequence([seed,101]). Each simulated channel-window uses SeedSequence([seed,202,window,wavelength]). All policies replay exactly the same telemetry. Controller state cannot alter the physical observations in this fixed-configuration advisory study. Each repeated seed uses independently regenerated calibration. This makes paired comparisons well defined and includes calibration randomness in run-level sampling.

Defaults were chosen to exercise different branches and produce visible count effects, not fitted to measurements from an optical testbed. Calibration exposure corresponds to 20 nominal monitoring windows per context at the configured pulse rate; all nine contexts require 180 seconds if measured sequentially with four receivers concurrently. Actual hardware calibration would require settling/stability checks beyond this synthetic exposure.

## Policies

Passive collection provides a no-operational-hold reference. Fixed threshold uses a 4% QBER cutoff or 25% nominal signal-gain drop. Uncertainty uses all calibrated detection/error gains with the declared whole-run budget. The pointwise ablation uses the same power contexts and six count features as uncertainty, but plug-in calibration rates and a within-window test level of alpha_run/(C*6). It isolates the combined contribution of calibration intervals and whole-run multiplicity handling from additional contextual features. No whole-run guarantee is claimed for pointwise. All active policies use the same two-window alarm persistence and three-window recovery.

These thresholds are exploratory engineering choices and are not falsely described as matched operating points. Before a research publication, sweep fixed thresholds on separate validation scenarios and compare detection/false-alarm frontiers on held-out test scenarios. Do not tune on the delivered benchmark then call that same benchmark untouched test evidence.

## Scenario interpretation

Stable and measured classical-power scenarios are fully benign, supported contexts. Sustained unexplained shift scenarios are local loss, local background, gradual drift, common loss and the observation-equivalent passive-tap label. Detection is an operational unexplained-shift event, not attack identification.

The known classical-power increase should normally be explained by context calibration. The fixed nominal threshold can unnecessarily hold in this situation. The local-loss and passive-tap cases generate byte-identical observable telemetry for a given seed; the different evaluator labels cannot be recovered by this monitor.

Off-grid measurements require INCONCLUSIVE, while the telemetry-gap case checks state reset. These are not scored as sustained physical anomaly misses. The one-window transient tests persistence and may create raw anomaly evidence without quarantine. Unknown benign physical changes can also trigger quarantine, exposing the difference between model mismatch and attack attribution.

## Metrics

False hold action: a new HOLD_OUTPUT advisory issued in a benign-labelled window. A held window after a real event has ended is recovery overhead, not a new false action. `benign_channel_windows_held` includes this overhead explicitly.

`false_raw_alarm_run_fraction` and `false_hold_run_fraction` are proportions of independent seeds with at least one respective event in benign-labelled windows. Summary confidence intervals use exact binomial Clopper-Pearson limits across run seeds. The model-based bound applies to wholly benign supported runs, not arbitrary event-subselected portions as a separate new statistical theorem.

Sustained-event detection counts target channels held during their event interval. Detection delay is decision end time minus onset time. Misses remain in the denominator. `delay_among_detected_runs` averages channel delays within a run and then summarizes detected runs; it is conditional and must be read with the miss count. No confidence interval from treating simultaneous channel events as independent trials is claimed.

`signal_detection_fraction_while_held` is the fraction of signal detections occurring while the advisory hold was already active. These detections still occur diagnostically. This is a potential availability cost proxy, not secret bits discarded or delivered and not QKD security loss.

Paired differences are uncertainty minus fixed_threshold and uncertainty minus pointwise, grouped by scenario and seed, with run-level 95% t intervals for the mean difference. Sparse count distributions and small exposure limit normal-based mean intervals; inspect raw metrics. Exact run-event intervals are supplied separately. Timing uses wall-clock instrumentation and varies with load; the benchmark is not a hardware throughput certification.

## Completion evidence

Read the delivered VALIDATION document for test and run results. Files preserve configuration, source hashes, calibration hashes, dependencies, seeds, raw demo observations and decisions. Re-run all policies after changing code or parameters. Never present illustration numbers as measured hardware results.
