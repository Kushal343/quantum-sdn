# Moving from this stage to a larger research programme

This implementation makes the fixed-configuration monitoring hypothesis testable. Funding scale does not make synthetic effects equivalent to experimentally validated performance.

## Current deliverable

Observable count schema, reproducible synthetic data, exact interval-based monitoring, finite-horizon statistical accounting, advisory hold/recovery, baseline experiments and reporting. No quantum configuration changes occur.

## Before claiming experimental QKD security

Integrate a separately validated, compatible, basis-resolved finite-key engine and independently check its security/correctness budget and parameter estimation. Security acceptance must remain outside the statistical monitoring classifier. A finite-key reference is Lim et al., https://arxiv.org/abs/1311.7129. This implementation deliberately reports no secret-key numbers without that integration.

## Before claiming device applicability

Acquire labelled benign telemetry and independent calibration from representative devices. Record detector dead time, afterpulsing, saturation, filtering, pulse/intensity stability, power-monitor uncertainty, clock synchronization and covariance. Replace illustrative coupling coefficients with measured or independently validated propagation models. Quantify model error and overdispersion; the present binomial null is not automatically valid under correlated detector noise.

Extend supported power contexts using a justified interval model or an independently validated regression with uncertainty. Do not silently interpolate and retain the finite-grid coverage claim. Add an indefinitely valid sequential monitor only after deriving its error guarantees.

## Before research-performance claims

Use separate calibration, validation/tuning and held-out test traces. Compare well-tuned threshold methods, count-based methods using the same features, and sequential alternatives at matched false-alarm operating points. Study block sizes, pulse rates, loss, background, event amplitude and persistence. Include non-improvement, sensitivity, and identifiability results. Use more benign exposure for rare-event claims.

## Before a control-plane deployment

Add authenticated message transport, configuration/device capability discovery, bounded delays, clock alignment, replay protection, audited calibration provenance and command acknowledgement semantics. Verify control safety and key-release gating independently. The current HOLD_OUTPUT and RESTORE_OUTPUT fields are offline recommendations, not physical control commands.

## Next project stages

1. Integrate real independently calibrated telemetry without changing monitoring logic.
2. Add the validated finite-key/key-management layer and measure delivered key volume.
3. Add direct candidate adaptation at block boundaries with actual switching costs.
4. Add an ML surrogate only if direct evaluation runtime justifies it.

External review should examine the count model, statistical argument, protocol security assumptions, hardware calibration, and experimental comparisons as distinct evidence streams. This is a research-development roadmap, not a claim that those reviews have occurred.
