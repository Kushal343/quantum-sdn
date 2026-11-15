# Model, statistical method, and claim boundaries

## Fixed configuration

Default signal/weak/vacuum intensities are `(0.5, 0.1, 0)` photons/pulse and probabilities `(0.8, 0.15, 0.05)`. Every record carries `fixed-v1`. There is no optimizer, ML model, wavelength reassignment, or retuning action in this stage.

The monitored counts are pre-sifting intensity-category detections and errors. The simulator does not execute the complete basis-resolved BB84 protocol, error correction, privacy amplification, or finite-key security proof. It models a weak-coherent-pulse link's intensity-resolved monitoring observables. A future security engine must use its own complete compatible protocol data and proof.

## Physical probability model

For channel i, loss L_i is fibre attenuation plus insertion and scenario loss, in dB. Total efficiency is `eta_i = detector_efficiency * 10^(-L_i/10)`.

The optical background mean per gate is `b_i = sum_j A_ij P_j + b_extra_i`, with P in mW and A in per-gate mean detections per mW. Dark-count probability is d, so the probability of any background hit is `Y0_i = 1 - (1-d) exp(-b_i)`.

For intensity x define `s_x = 1-exp(-eta_i*x)`. Detection gain is `Q_x = Y0_i + (1-Y0_i)*s_x`. Error gain is `T_x = 0.5*Y0_i + e_d*(1-Y0_i)*s_x`.

This is an explicit simplified receiver rule: if background hits, assign a random bit, including signal/background coincidence. Otherwise an arriving signal has error probability e_d. It yields `0 <= T_x <= Q_x <= 1` and vacuum error fraction 1/2 when background is present. It is not a universal detector model; double-click treatment and saturation in a particular device may differ.

For N emitted pulses in one intensity category, generate `D ~ Binomial(N,Q_x)`, followed by `K|D ~ Binomial(D,T_x/Q_x)`. Marginally `K ~ Binomial(N,T_x)`. Random pulse allocation across intensity categories is multinomial. Conditioning on allocated N makes binomial inference valid. QBER is K/D when D>0; D=0 produces a missing QBER, while detection gain is still informative.

The default coupling matrix is illustrative. It makes wavelength-specific coexistence effects explicit, but does not implement a calibrated Raman spectrum, four-wave-mixing propagation, traffic-bit-rate noise law, shared-detector saturation, or optical hardware. Classical launch powers are observed exactly and take values from a discrete grid. General power uncertainty, interpolation, and model discrepancy are outside the bound below.

## Calibration

For each supported classical-power vector c, wavelength i, and feature f, independently collect calibration counts k_cf out of n_cf trials. Features are three detection gains and three error gains, all per emitted pulse. Obtain a Clopper-Pearson interval `[L_cf,U_cf]` using per-cell error `delta_cal/M_cal`.

Here M_cal counts every context, wavelength, and feature. A union bound gives simultaneous coverage at least `1-delta_cal`. Calibration windows must represent the same stable conditional count laws as future benign windows. Synthetic calibration uses a random stream separate from runtime observations. Each benchmark seed gets a fresh calibration, allowing run-wise uncertainty assessment that includes calibration randomness.

Changing the experiment fingerprint invalidates the saved calibration. Loading checks counts and recomputes intervals. This catches accidental artifact inconsistency, not malicious substitution of a complete internally consistent calibration. Operational deployment would need authenticated calibration provenance.

## Composite-null binomial test

For an observed count k out of n, the benign hypothesis is `p in [L,U]`. Define:

`p_interval = min(1, 2 * min(BinomCDF(k;n,L), BinomSF(k-1;n,U)))`.

For any true p inside that interval, binomial monotonicity makes the lower-tail test at L and upper-tail test at U conservative. Each tail has rejection probability at most a/2 when `p_interval <= a`, hence total rejection probability at most a. Count discreteness can make it more conservative.

The code uses SciPy's survival function for the upper tail to avoid subtracting a tiny tail probability from one. Sparse counts, zero detections, and vacuum observations require no Gaussian approximation.

## Complete-run alarm budget

Predeclare T windows, C wavelengths and F=6 tests per channel-window. With total budget alpha_run and calibration budget delta_cal, set:

`alpha_test = (alpha_run - delta_cal)/(T*C*F)`.

Conditional on simultaneous calibration coverage, union-bounding all test rejections gives at most `alpha_run-delta_cal`. Including calibration failure gives an unconditional probability of at least one raw false alarm in a fully benign, supported-context run of at most alpha_run. A hold requires r consecutive raw alarms, so a false hold is a subset of this event and has no larger probability.

This result does not require independence among the six features, among wavelengths, or among window-level test decisions, provided each conditional count test remains valid under the assumed benign law. The simulation assumes independent pulse trials within windows. Burst noise, afterpulsing, drift within a stratum, selective reporting, and incorrect measured powers may invalidate that law.

The default values are alpha_run=0.05, delta_cal=0.005, T=120, C=4, F=6, yielding alpha_test=0.000015625. The horizon is the absolute configured window index, not a resettable counter. Beyond it, the policy returns OUT_OF_BUDGET and makes no new inference. Do not concatenate these horizons and claim a 5% lifetime bound.

The probability statement is over calibration and runtime observations. It is not a guarantee conditional on one unusually poor fixed calibration, nor a cryptographic secrecy/correctness parameter. Results under alternatives do not certify the absence of an adversary. A future indefinite-horizon monitor could replace this conservative allocation with a correctly derived confidence-sequence/e-process design.

## Categories and persistence

- NORMAL: no rate test rejects at nominal measured powers.
- EXPLAINED_CHANGE: no test rejects at supported non-nominal powers.
- UNEXPLAINED_ANOMALY: at least one rate test rejects. A streak of two triggers HOLD_OUTPUT.
- INCONCLUSIVE: missing/insufficient counts or unsupported power context. Both streaks reset; a prior hold remains held.
- OUT_OF_BUDGET: predeclared horizon exhausted. No new evidence accumulates.

Three consecutive passing windows restore held output. Telemetry acquisition remains on throughout the advisory hold. This emulates diagnostic monitoring, not a physical optical shutoff. Decisions occur at window end; a HOLD_OUTPUT advisory affects the following window. Consequently detection delay includes a full observation window and persistence.

Wilson QBER intervals in plots are only descriptive 95% intervals. They are neither multiplicity-corrected alert regions nor key-security criteria.

## References

- NIST exact binomial confidence limits: https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm
- SciPy binomial distribution, CDF and survival function: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html
- Ma et al., practical decoy-state foundation: https://arxiv.org/abs/quant-ph/0503005
- Lim et al., separate finite-key security layer for future integration: https://arxiv.org/abs/1311.7129

The interval-composite test and finite-horizon union-bound argument above describe this implementation. They do not claim a newly published statistical technique or a new QKD security proof.
