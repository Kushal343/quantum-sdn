# Theory experiments and interpretation of the QKD SDN project

Report date: 15 November 2026

This report explains what the project does, how its decisions are made, what the saved experiments show, and how to inspect the evidence. It is written for a reader who has not studied quantum communication. Equations are explained in words; practical instructions appear in the later sections.

The project is a working research simulation of four quantum key distribution channels with software control. Its strongest demonstrated capability is recognizing selected disturbances on one channel and withholding that channel's output while preserving the other channels. It also demonstrates a modest retuning benefit in a specified changing environment. Its main weakness is sensitivity to hidden benign drift. The security calculations and Linux networking components have important scope boundaries described below.

Reading guide: Sections 2 to 6 explain the theory and decisions; Sections 7 to 11 explain the experiments; Sections 13 to 15 show how to open, interpret and reproduce the results. Section 16 discusses the limitations.

## 1 Purpose and main findings

The project asks whether monitoring each wavelength separately, while accounting for uncertainty, can support better operational decisions than fixed thresholds or a single network average. The aim is to preserve useful key-generation capacity without continuing to accept unexplained channel behaviour.

The latest study combined the anomaly-detection branch's independent calibration with the original project's retuning, verification, rollback and targeted isolation. It compared six policies over eighteen scenarios and twenty random seeds per scenario and policy: 2,160 runs in total.

The combined policy isolated the affected channel in all twenty runs for strong interception, weak interception and hidden attenuation. In those local-disturbance cases it did not isolate the three unaffected channels. Weak-interception isolation took 1.15 intervals on average, compared with 1.80 for the previous adaptive policy. Retuning increased mean estimated accepted network output by 2.17% under measured misalignment compared with the same calibrated monitor without retuning.

The improvement is conditional. Hidden correlated drift, which is benign in that experiment, caused permanent isolation in six of twenty combined-policy runs, compared with one of twenty for the previous adaptive policy. This result must accompany any claim of improved monitoring. A stricter or more sensitive monitor can lose availability when its reference model is wrong.

The last completed software suite passed 74 tests. A separate Qiskit Aer smoke run also isolated only the target channel. Ryu and Mininet code, a Linux installation guide and a live packet self-test are supplied. Their live Linux execution was not performed on this Windows machine. The network-monitoring study reports estimated output, not end-to-end distilled secure keys.

## 2 Essential concepts

### Secret keys and quantum key distribution

A secret key is a sequence of bits shared by two parties and used by an encryption system. Quantum key distribution, abbreviated QKD, is a way to establish such a key under specified physical and protocol assumptions. QKD does not itself encrypt an application message. It also needs an authenticated classical channel so that an attacker cannot impersonate a participant during the public exchange.

The sender is conventionally called Alice and the receiver Bob. Eve is the conventional name for an eavesdropper in an attack simulation. These are roles in the program, not actual people or remote computers.

In BB84, Alice randomly chooses a bit and a measurement basis in which to encode it. Bob chooses a basis independently. After public basis comparison, they keep suitable matching-basis observations. This is called sifting. A disclosed test sample helps estimate errors. Error correction, verification and privacy amplification are needed before the remaining data can support a final key.

Measurement disturbance is only part of the security argument. An attacker may sometimes cause no noticeable increase in observed errors, particularly when device imperfections or photon-number effects are relevant. Security therefore requires an applicable analysis and sufficient data; a low error rate alone is insufficient.

### Four wavelengths and the reason for separate monitoring

Wavelength division multiplexing, or WDM, carries several optical channels over shared fibre infrastructure. This project represents four separately encoded quantum channels, labelled lambda_1 to lambda_4. Think of four lanes whose conditions can differ even though they share infrastructure.

A network average can hide a local problem. If three equally weighted channels have a 1% error rate and the fourth has 19%, the average is only 5.5%. A rule that waits for an 11% average would miss the local 19% problem. Actual aggregation uses sample weights, so a channel with fewer observations can be diluted further.

### What the measurements mean

QBER is the quantum bit error rate: errors divided by the relevant disclosed or monitored same-basis bit sample. A value of 0.02 in a CSV means 2%, not 0.02%. The notebook estimates QBER from a public sample. The optical monitoring simulator counts same-basis disagreements directly for its operational study; it is not the full finite-key key-release protocol.

Detection gain is the fraction of emitted pulses that produce a detection. Sifted count is the number retained after basis matching. Estimated key rate is a model-based estimate of potentially extractable bits per second of model time. It differs from both raw detections and a measured production rate of final keys.

## 3 What has been implemented

The project has three related experimental paths. Keeping them distinct prevents a monitoring result from being mistaken for a completed security experiment.

| Path | Implemented work | Main output |
|---|---|---|
| Quantum demonstration | BB84 circuits, intercept-resend, sifting, sampling, four channels, notebook and dashboard | Sampled errors and circuit outcomes |
| Optical monitoring and control | Weak-pulse link model, intensity-resolved counts, six policies, calibration, noise and fault scenarios, retuning and isolation | Decisions and estimated accepted output |
| Security and post-processing demonstrations | Scoped finite-key calculators, reconciliation, verification, privacy amplification and authenticated participant exchanges | Conditional length bounds and accepted demo outputs |

Ryu and Mininet form a fourth integration layer around monitoring decisions. They map a wavelength's operational decision to associated classical packet traffic. They do not turn ordinary Ethernet switches into optical wavelength switches.

The original analytical adaptive controller is retained for comparison. The new uncertainty policy supplies calibrated monitoring with fixed optical settings. The hybrid policy adds the existing retuning loop to that calibrated monitor. Machine learning remains an optional proposal mechanism rather than the basis for accepting a channel or a secret key.

## 4 The optical and quantum simulation model

### Loss background and errors

The optical model computes an effective transmission probability from detector efficiency and total attenuation. In plain terms, longer fibre or additional loss allows fewer useful photons to reach the receiver. The implemented relation is eta = detector efficiency times 10 raised to minus total loss in dB divided by 10. Fibre loss is distance times attenuation per kilometre, plus any additional loss.

Default channels have distances of 20, 22, 24 and 26 km, detector efficiency 0.2 and attenuation 0.2 dB/km. These are illustrative settings. Different distances make baseline detection counts different, so an identical detection count across wavelengths is not expected.

For an intensity x, the signal-click probability is s = 1 - exp(-eta times x). If the background probability is b, the model uses total gain Q = s + (1-s)b. Its conditional error fraction is E = [s times alignment error + 0.5(1-s)b] / Q. Background-only detections are random and therefore contribute errors half the time on average.

This is a simplified receiver rule. It does not reproduce every double-click policy, detector saturation effect or electronic response. The current background is an additive, capped combination of dark counts, an illustrative traffic-dependent Raman term, crosstalk and an FWM term. Small effective probabilities are useful for the study, but these equations are not an experimentally calibrated optical propagation model.

### Signal weak decoy and vacuum settings

Weak coherent pulses can contain zero, one or several photons. Their ideal photon-number distribution is Poisson: P(n) = exp(-mu) times mu to the power n divided by n factorial. Decoy-state methods vary pulse intensity to constrain the single-photon contributions using additional observed statistics. This project models coherent-pulse gain analytically; its circuit simulation does not represent every multiphoton optical state.

The default C3 configuration uses signal intensity mu = 0.6 and weak-decoy intensity nu = 0.12 photons per pulse. Signal, weak-decoy and vacuum probabilities are 0.75, 0.20 and 0.05. Five candidate configurations C1 through C5 vary mu from 0.4 to 0.8 and nu from 0.08 to 0.16; their selection probabilities remain fixed.

Changing these intensities can improve the modeled balance between useful counts and the estimated single-photon contribution. It cannot restore arbitrary physical loss or remove all unwanted light. Retuning is therefore tested for benefit rather than assumed to help every scenario.

### How observations are generated

Emitted pulses are allocated among the three intensities using a multinomial draw. For each class, the number of detections is sampled from a binomial distribution. Basis matching produces sifted observations, and errors are sampled or measured under the specified channel conditions. Count validation requires errors no greater than sifted observations, sifted observations no greater than detections, and detections no greater than emitted pulses.

There are two measurement engines. Qiskit Aer executes BB84 circuits on a classical CPU. The binomial engine samples the exact count law of this project's independent symmetric BB84 model and is much faster for repeated sweeps. The large policy study used the binomial engine. The separate Aer smoke experiment used actual circuit shots. Neither is a physical fibre experiment.

## 5 Noise faults and attack scenarios

The added scenarios distinguish reported changes, hidden changes and missing knowledge. The controller receives counts, its active setting and the reported channel context. It does not receive the attack fraction, hidden attenuation or scenario name. The evaluator uses scenario labels afterwards to interpret decisions.

Dark counts are detector clicks without a useful arriving signal. Raman scattering occurs when strong classical light interacts with the fibre and generates unwanted light at other wavelengths. Four-wave mixing, abbreviated FWM, is a nonlinear interaction that produces additional optical frequencies. Crosstalk is leakage through imperfect filtering. Misalignment means Alice and Bob's preparation and measurement settings do not align as intended. These mechanisms can all worsen observations, but their modeled effect here does not reveal which physical cause actually occurred.

| Scenario name | What changes | What the controller is told |
|---|---|---|
| normal | Sampling fluctuations only | Nominal context |
| loss | Additional 5 dB attenuation on channel 3 | Updated loss |
| noise | Increased classical-traffic background on channel 3 | Updated traffic |
| shared_noise | Increased traffic background on every channel | Updated traffic per channel |
| dark_counts | Increased detector background on channel 3 | Updated dark probability |
| raman | Increased illustrative Raman-like background on channel 3 | Updated traffic and coefficient |
| fwm | Increased FWM-like effective background on channel 3 | Updated effective probability |
| crosstalk | Increased filter leakage on channel 3 | Updated leakage probability |
| misalignment | Alignment error rises from 1.5% to 5% on channel 3 | Updated alignment parameter |
| intercept | Intercept-resend affects 70% of eligible signal-origin detections on channel 3 | No attack label |
| weak_intercept | Interception fraction is 12% on channel 3 | No attack label |
| tap | Hidden 35% transmission reduction on channel 3 | Nominal reported context |
| transient | One interval of hidden attenuation on channel 3 | Nominal reported context |
| burst | One interval of hidden excess background on channel 3 | Nominal reported context |
| correlated | Shared hidden AR1 alignment drift across intervals | Nominal alignment |
| model_mismatch | Persistent hidden alignment error of 5% on channel 3 | Nominal alignment |
| missing | Two unavailable telemetry intervals on channel 3 | Explicit unavailable flag |
| unsupported | Measured traffic outside the finite calibration grid | Reported uncalibrated context |

AR1 means that the next drift partly depends on the previous drift: here the persistence coefficient is 0.85 and innovation standard deviation is 0.004. Parameters change between intervals; trials remain independent within an interval. This is not a general correlated quantum-memory attack model.

Shot or counting variation is inherent in the random counts. Raman, FWM and crosstalk are effective background terms, not individually identifiable optical spectra. Detailed afterpulsing, timing jitter, dead time, detector blinding, Trojan-horse behaviour and electronic noise spectra are not implemented. Loss is a reduction in useful detections, not itself a noise process. A hidden passive attenuator can look identical to a passive tap under this observation model.

## 6 Decision policies and the combined approach

| Policy | Information and action | Purpose in comparison |
|---|---|---|
| fixed | Keep settings; no adaptive response | Uncontrolled operational reference |
| aggregate | Isolate channels if combined sample-weighted QBER exceeds 11% | Show dilution by network averaging |
| per_wavelength | Isolate each channel whose own QBER exceeds 11% | Simple local-threshold reference |
| adaptive | Exact-model residual tests, holds, isolation and retuning | Previous main-project controller |
| uncertainty | Independent calibrated count tests, holds and isolation; fixed optical settings | Separate monitoring from adaptation |
| hybrid | Same calibrated monitor plus candidate trials and rollback | Combined implementation |

The 11% threshold is an illustrative operating cap. It is not a complete finite-key acceptance rule. These policies are operational comparators and do not all have identical statistical false-alarm calibration. Their results therefore do not establish superiority at every matched false-alarm level.

The anomaly branch contributed the stronger treatment of baseline uncertainty, horizon limits and unsupported telemetry. The original project contributed the stronger control loop. The combined design adopts both. It differs from the branch's advisory hold policy by withholding output on the first suspicious interval and keeping permanent isolation latched.

### Independent calibration

Instead of pretending to know the exact true normal rate, the new monitor collects separate benign calibration counts. Calibration covers 160 supported combinations: four wavelengths, eight known contexts for each wavelength and five candidate configurations. Each context uses five million emitted pulses. These are count-model samples, not millions of explicit circuit executions.

For each context it bounds six rates: signal, decoy and vacuum detection gains, and their respective conditional sifted error fractions. Clopper-Pearson intervals express finite-sample uncertainty in those reference rates. Calibration uses a separate random stream from the observations being monitored.

The finite grid matters. If runtime telemetry describes a context outside the grid, the controller reports insufficient knowledge and holds output. It does not silently interpolate or declare the channel benign. Exact, trusted reporting of the context is an assumption; hidden changes test the consequences when that assumption fails.

### Operational significance and uncertainty

Suppose calibration bounds a reference probability between L and U. For an observed count k out of n, the monitor computes p = min[1, 2 times min(BinomialCDF(k; n,L), BinomialSF(k-1; n,U))]. The lower tail checks unexpectedly few events; the upper tail checks unexpectedly many. Using the interval endpoints makes this a conservative test of compatibility with the reference interval.

A small p-value means the observation is difficult to reconcile with that reference model. It is not the probability that Eve is present. A large p-value means the test did not find sufficient evidence of a mismatch; it is not a probability that the channel is safe.

The run-level raw-alarm budget is 0.05, with 0.005 reserved for simultaneous calibration failure. For T intervals, the per-test level is (0.05 - 0.005) / (T times 4 times 6). With T = 18 this is 0.0001041667. A union bound accounts for the finite number of tests without requiring independence among the six features. The individual conditional count laws must still be valid.

This is an operational raw-alarm statement over calibration and runtime randomness in fully benign, supported model conditions. It excludes missing-data holds, unsupported-context holds, operating-cap holds and unmodelled count laws. It is not a 5% cryptographic failure probability or a lifetime guarantee. The controller stops making new inference after its declared horizon.

Wilson intervals also describe uncertainty in measured QBER. The controller uses a three-sigma Wilson upper bound for its operating-cap hold. The 95% Wilson intervals used to summarize repeated-seed success rates are different intervals applied to different data. Neither is a finite-key secrecy proof.

### Decisions and their order

An already isolated channel remains isolated. Otherwise, the controller first checks counts, sample sufficiency, the expected configuration and the observation interval. Malformed, unavailable, sparse or unsupported data lead to a hold and reset the anomaly and recovery streaks. The same occurs when the declared inference horizon is exhausted.

One unexplained interval triggers a temporary hold. Two consecutive unexplained intervals trigger isolation of that wavelength. If no anomaly is found but the upper QBER bound reaches 11%, output is held. A temporary hold is cleared only after three consecutive usable passing intervals. Diagnostic acquisition continues during holds and isolation; accepted output from those periods is zero.

After these checks, the hybrid policy may consider adaptation. It looks for detection gain below 75% of its initial baseline or a QBER lower bound above 2.5%. It selects only a supported, independently calibrated configuration. For elevated QBER, it minimizes predicted error among settings achieving at least 90% of the best feasible predicted rate. Otherwise it maximizes the estimated rate.

The analytical model must then predict sufficient improvement after a settling-cost allowance. The condition compares 7.75 intervals of candidate output with 8 intervals of current output times 1.01, representing a quarter-interval switching loss and a 1% improvement margin. The change takes effect for the next simulated interval. In actual output accounting, a 25% penalty is charged after a retune or rollback.

Two eligible post-change observations form the verification trial. If their average estimated rate is more than 10% below the pre-change measurement, the old configuration is restored. Otherwise the candidate is kept. A four-interval cooldown follows. This trial criterion is a heuristic operational check rather than a formal statistical improvement test, and the fixed eight-interval benefit horizon may extend beyond a short experiment's remaining time.

## 7 Latest experiment design

The primary new comparison used twenty seeds numbered 4100 through 4119. For each seed it generated a separate calibration with seed 9100 through 9119. Each of the eighteen scenarios was run under all six policies, giving 18 times 6 times 20 = 2,160 runs. Each run had eighteen intervals, four wavelengths and 100,000 emitted pulses per wavelength per interval. Disturbances began at zero-based interval 6, the seventh interval.

An interval represents one second of model time at the configured pulse clock. It need not take one second of computer wall time. Each run represents 7.2 million emitted model pulses across all wavelengths. The repeated sweep used count sampling; no hardware sent those pulses.

The study logs permanent isolation, temporary holds, which channel was isolated, isolation delay and estimated accepted output. Output from held or isolated intervals is withheld. A settling penalty is included following optical changes. These estimates come from an asymptotic decoy-rate calculation and are not a count of distilled secure keys.

Seeds are reused to make comparisons more systematic, but changing a configuration can change later random draws. Shared seeds therefore do not guarantee identical physical observations across policies. Statistical intervals are descriptive and were not corrected for searching over many scenarios.

## 8 Results and their meaning

### Local disturbances and the role of wavelength monitoring

The following values count runs in which the target wavelength was permanently isolated, out of twenty runs for each cell.

| Policy | Strong interception | Weak interception | Hidden attenuation |
|---|---|---|---|
| fixed | 0 of 20 | 0 of 20 | 0 of 20 |
| aggregate | 0 of 20 | 0 of 20 | 0 of 20 |
| per_wavelength | 20 of 20 | 0 of 20 | 0 of 20 |
| adaptive | 20 of 20 | 20 of 20 | 20 of 20 |
| uncertainty | 20 of 20 | 20 of 20 | 20 of 20 |
| hybrid | 20 of 20 | 20 of 20 | 20 of 20 |

The local 11% threshold catches the strong error increase but misses weaker disturbances and hidden loss. The calibrated monitor also checks gains and changes relative to the expected operating context, so it can respond before a universal QBER threshold is crossed. The fixed policy is expected to make no isolation decisions; that is its definition rather than a detector failure.

No unaffected wavelength was permanently isolated in any of these three hybrid local-disturbance cases. The result supports selective containment within this model. It does not establish detection of every interception strength or identify the cause of a hidden loss event.

Strong-interception mean isolation delay was one interval for the previous adaptive, uncertainty and hybrid policies. Per-wavelength threshold control isolated at onset in that strong case. Weak-interception delay improved from 1.80 intervals under the previous adaptive policy to 1.15 under the new calibrated policies. Requiring persistence intentionally trades some speed for protection against a single anomalous observation.

### Known noise and normal operation

All six policies had zero permanent isolations in twenty normal runs. The hybrid policy had no holds in those normal runs. Known loss, traffic noise, dark-count increases, Raman-like background, FWM-like background, crosstalk, shared traffic noise and measured misalignment also produced no permanent hybrid isolation in the tested cases.

This result means that their observed counts were compatible with the supplied calibration and operating rules. It does not mean those disturbances caused no loss of performance. A known noise increase can reduce estimated output while remaining statistically explained. Nor does it establish that every real noise condition is supported by the finite calibration grid.

### Retuning benefit

Under measured misalignment, the uncertainty policy with fixed settings delivered a mean of 31,753.6 estimated accepted network bits per run. The hybrid policy delivered 32,442.5, an increase of 688.9 estimated bits or 2.17%. The descriptive paired-bootstrap 95% interval for the mean difference was approximately 400.1 to 975.1 estimated bits across the twenty seeds.

The comparison is useful because both policies share the same calibrated monitor; the main difference is retuning. The gain includes modeled settling costs. It is a network-wide total, so it is diluted by the three channels that were not retuned. It remains a model-specific asymptotic estimate. This study does not show a 2.17% improvement for arbitrary noise, finite-key output or physical hardware.

### Temporary disturbances and missing information

A one-window hidden attenuation event caused a hold but no permanent isolation in all twenty hybrid runs. Output resumed after the required clean recovery intervals. A one-window background burst also caused temporary holds without permanent isolation. These cases demonstrate why the controller has both hold and isolate actions.

Missing telemetry and unsupported contexts caused holds in all twenty corresponding hybrid runs and no permanent isolation. The legacy policies do not check the newly introduced availability flag, so their continued estimates during missing telemetry should not be praised as better availability. They lack the same validity check.

### Hidden benign changes and the failure case

Persistent hidden misalignment caused hybrid isolation in all twenty runs, even though no malicious actor is present in that scenario. It is an unexplained model mismatch. That behaviour may be an appropriate precaution under a conservative operating policy, but it is not evidence that an attack occurred.

Hidden shared correlated drift caused at least one isolation in six of twenty hybrid runs and eleven runs with a temporary hold. The previous adaptive policy isolated in one of twenty. In the hybrid results, six runs also had isolation of a channel other than lambda_3. All wavelengths experience the shared drift, so the column name other_isolated does not mean those other channels were physically unaffected in this scenario.

The calibrated policy is therefore not uniformly better. A realistic baseline for temporal variation, uncertain measurements or overdispersed counts needs further study. Simply expanding the allowed normal range could reduce false alarms while also reducing sensitivity to subtle attacks. Selecting that trade-off requires separate validation and untouched evaluation data.

### How much confidence twenty seeds provide

Twenty successful runs do not prove a 100% success probability. The pointwise 95% Wilson interval for 20 of 20 is approximately 83.9% to 100%. For zero observed failures in twenty runs, the corresponding interval extends from zero to about 16.1%. These are repeated-run empirical intervals, separate from the monitor's operational significance level.

Do not read a blank detection delay as zero. It means no target isolation was observed and there is no delay to average. Delay is averaged only among isolated runs. The isolated-run count must always be read alongside the delay so that missed detections are not hidden by a short average.

## 9 Worked examples from saved traces

These examples use the first saved sweep seed, 4100, with calibration seed 9100. They explain actual stored rows rather than an invented illustration.

### Strong interception on wavelength 3

| Interval | Sifted observations | Errors | QBER | Action |
|---|---|---|---|---|
| 5 | 1494 | 20 | 1.34% | continue |
| 6 | 1434 | 292 | 20.36% | hold |
| 7 | 1428 | 237 | 16.60% | isolate |
| 8 | 1536 | 292 | 19.01% | isolated |

At interval 6 the signal and decoy error fractions were flagged as incompatible with calibration. The controller withheld that channel's estimated output immediately. The next unexplained interval satisfied persistence and latched isolation. Later telemetry still exists because diagnostic acquisition continues; its presence does not mean output was released. Estimated accepted bits for the target are zero from the hold onwards.

Isolation delay is 7 minus onset 6, or one interval. This is a difference between interval indices. The first response was already the hold at interval 6; a delay of one does not mean nothing happened during the onset interval. The source file is results/hybrid/intercept-example.csv.

### One interval of hidden attenuation

For the transient example, wavelength 3 continues at interval 5, holds at interval 6, remains held in recovery at intervals 7 and 8, and continues at interval 9. The third usable passing interval clears the hold. There is no isolate action. This can be checked in results/hybrid/transient-example.csv.

The extra recovery time reduces accepted output compared with immediate resumption. This is an intentional availability cost, not a hidden defect in the output calculation. Permanent isolation would have been a more severe response to a disturbance that had already ended.

### Optical retuning and the settling penalty

In results/hybrid/misalignment-example.csv, interval 6 observes C3 and proposes C1. The row therefore has config C3, next_config C1 and action retune. Interval 7 observes C1 and has action verify. Its estimated rate is 114.37 bits per model second, but accepted output is 85.78 bits because the 25% settling penalty is charged. Interval 8 has action keep after the two-window trial.

Later single-interval estimates can still fluctuate sharply, including reaching zero while the action is continue. Zero estimated rate is not the same as isolation. A keep decision means the specified two-window heuristic passed; it does not guarantee every later interval improves. That is why aggregate repeated-run results are more informative than one favourable row.

## 10 Other completed experiments and ML results

Earlier studies are retained as evidence from earlier versions or different settings. They must not be pooled with the latest study as though they were one experiment.

The earlier controller validation used 100 seeds for each policy and scenario, with sixteen intervals and 100,000 pulses per wavelength per interval. Replacing a Gaussian residual heuristic with exact binomial checks reduced unnecessary holds in benign scenarios. The revised adaptive policy detected strong interception, weak interception and hidden attenuation in 100 of 100 runs each; its normal scenario had one run with a hold and zero false isolation. Those results concern the previous adaptive controller, not the new hybrid policy.

An earlier 360-run advanced study used twenty seeds, forty intervals and one million pulses per channel per interval. In its measured-misalignment case, adaptive retuning increased estimated network output from about 665,078 to 691,996 bits, or 4.05%. The latest 2.17% figure uses shorter runs and fewer pulses with the calibrated-policy comparison. The different percentages are not inconsistent and should not be substituted for one another.

That advanced study also exposed a sensitivity limit: the previous adaptive controller isolated zero of twenty runs at a 3% interception fraction, while tested fractions of 6%, 12%, 30% and 70% were isolated in twenty of twenty runs each. The 3% is the fraction intercepted, not the observed QBER. The latest hybrid study tested 12% weak interception; it has not established a new result at 3%.

### What the ML model learns

The ML component uses two Random Forest regressors with one hundred trees each. They predict QBER and estimated secret fraction from channel parameters and candidate settings. Labels come from the analytical model, not measured hardware or Aer shot labels. Three hundred twenty channel conditions were used for training and eighty unseen conditions for testing, with all five candidates for a condition kept in the same split.

| ML evaluation measure | Saved result | Interpretation |
|---|---|---|
| QBER mean absolute error | 0.003925 | About 0.3925 percentage points on average |
| Secret fraction mean absolute error | 0.0001358 | About 136 estimated bits per million pulses |
| Mean relative candidate regret | 2.70% | Chosen settings averaged 2.70% below the best positive reference rate |

For example, a QBER error of 0.0039 could turn a true 2.0% into a prediction near 2.39%; the result is an average error, not a maximum bound. Candidate regret concerns configuration choice, not attack classification accuracy. An analytical gate checks proposed changes, and calibrated candidates are required in the hybrid policy.

The latest 2,160-run sweep used direct analytical candidate evaluation with ML disabled. It therefore does not demonstrate an end-to-end ML gain. With only five cheap analytical candidates, direct evaluation may be preferable. The train command saves evaluation metrics but not a fitted model for reuse; a run with --ml trains in memory again.

## 11 Security and classical protocol work

### Why matching bits are not enough

Alice and Bob can hold matching bits while an outsider still knows something about them. Finite-key analysis estimates how much uncertainty remains for the outsider after limited observations and public communication. Reconciliation disclosures and security overhead must be subtracted. Privacy amplification compresses eligible data to reduce residual outsider knowledge under the applicable assumptions.

Authentication protects public messages against forgery or alteration; it does not make them secret. The project includes a sparse syndrome reconciler, a normalized min-sum decoder, independent verification, Toeplitz privacy amplification and separate Alice and Bob processes. The parent harness provisions their inputs and compares private fingerprints for validation. This local trusted test harness is not a deployed adversarial network.

### Ideal single photon finite key calculation

The single-photon calculator implements a published BB84 finite-key bound from Tomamichel and colleagues, rather than assuming an arbitrary entropy fraction. It uses a predeclared sample tolerance and a finite-sample phase-error allowance. Its model rejects coherent-pulse inputs; its assumptions cannot be transferred automatically to the decoy monitoring data.

In explanatory notation, the entropy term is n times [q - h2(phase_bound)], where n is retained block length, q is preparation quality and h2 is binary entropy. The phase bound is derived from the declared error tolerance plus the finite-size term in the implemented theorem. The allowable output is the floor of the entropy term minus the declared reconciliation cap and the theorem's logarithmic secrecy/correctness penalty, with abort conditions applied.

In the saved integrated example, n and the test size are both 8,192. There are 45 test errors and a predeclared tolerance of 2%. The finite-size allowance is about 0.07347, making the phase bound about 0.09347. The entropy term is 4,522.29 bits, the reconciliation cap is 2,745 bits and the extraction penalty is 100.66 bits. Their difference permits 1,676 output bits under the model. Matching participant outputs were obtained.

One-use polynomial message authentication consumes 1,524 bits of pre-shared secret material in that example. Net output is therefore 1,676 minus 1,524, or 152 bits. Reporting only the gross output would exaggerate its contribution to the key balance. The saved QKD secrecy and correctness allocations are 1e-9 and 1e-12, plus an authentication bound of about 6.16e-34 under fresh independent one-use key assumptions. The reported total is conditional on the protocol and theorem mapping; independent review is still required.

### Separate finite key decoy estimator

The weak-coherent-pulse path has a separate implementation of Lim and colleagues' finite-key decoy equations. It bounds vacuum and single-photon contributions, single-photon errors and phase errors using basis-resolved intensity counts. It subtracts modeled reconciliation leakage and finite security overhead. It returns zero when bounds are insufficient or an abort condition is met.

Fifty count-level blocks were tested: five pulse counts, five seeds and two disturbance settings. At one billion pulses, the five undisturbed blocks produced length bounds of 871,022; 828,480; 825,134; 894,229; and 858,384 bits. All tested smaller blocks and all strong-interception blocks returned zero under those settings. These are conditional length bounds, not actually decoded and compressed large-block keys.

The complete decoy collection, sampling, reconciliation and privacy-amplification protocol is not connected end to end to this estimator. The fixed emitted-batch demo also differs from the cited protocol's exact collection/stopping rules. Existing optical monitoring records combine bases and cannot simply be fed into the finite-key estimator. The project therefore does not have a completed independently reviewed composable WDM security proof.

## 12 Ryu Mininet and the Windows Linux boundary

Mininet creates a Linux virtual packet network with two Open vSwitch switches and eight hosts. Hosts a1 and b1 represent the application pair associated with wavelength 1, and similarly for the other three pairs. A trunk connects the two switches. VLANs 101 through 104 identify the channel-associated traffic. There is one trunk, with no spare optical wavelength or alternative route modeled.

The Ryu application accepts local authenticated channel/action requests and sends OpenFlow 1.3 messages to the switches. Host-side rules add the appropriate VLAN; trunk-side rules remove it and deliver traffic only to the matching host port. Default unmatched traffic drops. A hold or isolation installs higher-priority drops for the affected channel in both directions. A temporary hold can be released; latched isolation cannot be cleared by an ordinary continue command.

The client waits for barrier acknowledgements from both switches. Errors, disconnects or timeouts invalidate readiness and cause the lab owner to stop and tear down its topology. Barrier acknowledgement means the switch processed preceding messages; it does not prove atomic changes across both switches or replace packet tests. The live self-test separately checks actual ICMP forwarding and cross-channel separation.

VLANs here represent classical traffic associated with a QKD wavelength. Ordinary Ethernet switches do not isolate photons. Optical settings and quantum measurements remain simulated, and diagnostic telemetry continues outside the blocked application VLAN. These distinctions should be stated when demonstrating the project.

Windows can run the simulation, ML, saved-result inspection, unit tests and command dry run. Live Mininet requires Linux networking facilities. The supplied deployment uses an Ubuntu VM with a separate Ryu container, keeping its legacy dependencies apart from Qiskit. Ryu's official repository states that it is no longer maintained. The Linux image and live packet experiment remain to be verified; code availability is not evidence of a passing deployment.

## 13 Where to find results and how to open them

Your project folder is C:\Users\LENOVO\Downloads\qkd-sdn. Existing results can be read without training a model or rerunning an experiment. Start with results\hybrid\FINDINGS.md for the narrative, then summary.csv for comparisons, then a scenario example for the sequence of decisions.

| File or folder | What it contains | What to inspect |
|---|---|---|
| results/hybrid/FINDINGS.md | Latest narrative findings | Strengths, failures and uncertainty |
| results/hybrid/isolation_comparison.png | Isolation comparison chart | Local response and correlated-drift failure |
| results/hybrid/summary.csv | One row per scenario and policy | Twenty-run totals and means |
| results/hybrid/runs.csv | One row per individual run | Variation across seeds |
| results/hybrid/intercept-example.csv | First-seed decisions for all wavelengths | Hold then target isolation |
| results/hybrid/transient-example.csv | First-seed transient decisions | Temporary hold then recovery |
| results/hybrid/misalignment-example.csv | First-seed retuning decisions | config, next_config, trial and penalty |
| results/hybrid/calibration-example.json | First seed's reference counts and bounds | Calibration provenance and supported contexts |
| results/hybrid-aer-smoke/summary.json | Separate circuit-based smoke result | Engine, shots and isolation count |
| results/ml/ml_metrics.json | ML evaluation | Prediction errors and candidate regret |
| results/protocol/summary.json | Integrated single-photon demo | Acceptance, gross/net bits and scope |
| results/decoy-finite/runs.json | Decoy estimator blocks | Conditional length bounds and abort statuses |
| results/sdn/plan.json | Planned OpenFlow commands and states | Dry-run scope; no packet verification |

In File Explorer, open the project folder, then results, then hybrid. Double-click the PNG to view the chart. Open Markdown in VS Code or a text editor; open this report's PDF in a PDF reader. CSV files can be opened in Excel or another spreadsheet viewer. If a CSV appears in a single column, use the viewer's import function with comma as the delimiter.

The existing dashboard is a separate interactive BB84 demonstration. It does not automatically show the saved hybrid-policy sweep. Launching it is useful for understanding channel QBER and aggregate dilution; use the result files above for the calibrated comparison.

### Open and filter results in PowerShell

```powershell
cd C:\Users\LENOVO\Downloads\qkd-sdn
Invoke-Item .\results\hybrid\isolation_comparison.png
Get-Content .\results\hybrid\FINDINGS.md
```

To display only combined-policy summary rows:

```powershell
Import-Csv .\results\hybrid\summary.csv |
  Where-Object policy -eq 'hybrid' |
  Format-Table scenario,runs,isolated_runs,hold_runs,mean_retunes -AutoSize
```

To follow the affected channel through the strong-interception example:

```powershell
Import-Csv .\results\hybrid\intercept-example.csv |
  Where-Object channel -eq 'lambda_3' |
  Format-Table interval,config,next_config,qber,action,category -AutoSize
```

To inspect the ML metrics or protocol accounting:

```powershell
Get-Content .\results\ml\ml_metrics.json
Get-Content .\results\protocol\summary.json
```

The commands read existing files. They do not start Mininet or change any experiment result. The report charts and CSVs contain the same underlying data in different forms, so they should not be counted as independent evidence.

## 14 How to interpret the columns

### Summary table

Each row of summary.csv identifies one scenario and one policy. runs is twenty in this study. isolated_runs counts runs with at least one permanent isolation, not the number of isolated wavelengths. target_isolated counts runs where lambda_3 was isolated. other_isolated counts runs with isolation on any other wavelength.

hold_runs counts runs containing at least one temporary hold. It is not the total number of held intervals. mean_detection_delay is the mean index difference from event onset to target isolation among runs that isolated the target. A blank delay is unavailable, not zero. For a benign scenario, an isolation delay is merely response timing to a benign anomaly, not an attack-detection success.

mean_estimated_bits is the average total accepted asymptotic estimate across the four channels over a run, after holds and modeled settling penalties. It is not a rate, not a measurement in kilobits per second, and not generated secure-key material. mean_retunes is the average number of retune events per run. A value of 1.1 means the total across twenty runs was twenty-two events; no individual run performed a fractional action.

### Individual runs and interval traces

In runs.csv, seed identifies a random trial. any_isolation, target_isolation and other_isolation are Boolean values. estimated_bits is that run's network total. Compare the individual rows when an average hides unusually good or bad trials.

In a scenario trace, interval starts at zero and channel identifies the wavelength. config is the setting used for the measurement that just completed; next_config is the setting requested for the next interval. sample_size is the signal sifted count, errors its disagreements, and qber is errors divided by sample_size.

skr_estimate is a pre-control rate estimate in bits per model second. estimated_released_bits is the interval's accepted estimate after withholding and availability penalties. The historical name released_bits does not mean a secure key was actually released. action records the controller decision; category describes its interpretation, such as NORMAL, UNEXPLAINED_ANOMALY, RECOVERING or INCONCLUSIVE.

qber_low and qber_high are controller uncertainty bounds, here based on the three-sigma Wilson setting. pvalues and flagged_features explain which count tests rejected compatibility. alpha_per_test is the operational test level. config_version tracks the controller's requested version; on a retune row it may already reflect the newly requested configuration even though config records the completed measurement's old setting.

Some CSV cells contain dictionary or list text, such as pvalues. They are audit fields for reading or trusted parsing; they are not additional spreadsheet formulas. Ignore empty flagged_features on an already isolated row as a new diagnosis: the controller has latched the previous decision rather than repeated an attack classification.

### A practical reading sequence

First identify the scenario and whether the event is malicious, known benign, hidden benign, transient or unavailable telemetry. Then check whether action was expected to be a hold, isolation, adaptation or continuation. Compare target_isolated and other_isolated before looking at delay. Finally compare accepted output and retunes, remembering that a policy which misses a disturbance may appear to retain more output.

For example, the hidden-attenuation baseline retains about 34,635 estimated bits, while the hybrid retains about 30,852. That higher baseline total does not prove it is the better policy: the baseline never isolated the unexplained channel. Conversely, during benign correlated drift the hybrid's reduced output is a real availability cost from unnecessary quarantine. The same output metric therefore needs different interpretation in different scenarios.

## 15 Reproducing and demonstrating the experiments

Use new output folders to preserve the original evidence. The project contains a private Windows Python runtime under .runtime. On Linux, use the separately installed .venv-linux/bin/python instead. The commands below assume the project folder is the current directory.

For a fast single-run count-model demonstration:

```powershell
.\.runtime\python.exe run.py network `
  --policy hybrid --engine binomial --scenario intercept `
  --steps 18 --out results/my-intercept
```

For a circuit-based demonstration, replace --engine binomial with --engine aer. Compare all six policies in one scenario with:

```powershell
.\.runtime\python.exe run.py compare `
  --engine binomial --scenario transient --steps 18 `
  --out results/my-comparison
```

For the complete repeated study using the declared runtime and calibration seed schedules:

```powershell
.\.runtime\python.exe hybrid_experiments.py `
  --seeds 20 --steps 18 --pulses 100000 `
  --out results/hybrid-recheck
```

A single network command uses its default calibration seed and is not guaranteed to reproduce the benchmark's first-seed trace. Use the sweep command for its exact seed schedule. Its first-seed examples and run totals are written to the selected folder. report_hybrid.py currently reads results/hybrid specifically; it is not a general viewer for any --out folder and rewrites the narrative/plot in that folder when run.

For a fresh ML evaluation, without replacing the original metrics:

```powershell
.\.runtime\python.exe run.py train `
  --seed 42 --out results/ml-recheck-new
```

For the interactive BB84 dashboard or software checks:

```powershell
.\.runtime\python.exe -m streamlit run dashboard.py --server.address 127.0.0.1
.\.runtime\python.exe -m pytest tests -q
```

The dashboard starts a local web service; stop it with Ctrl+C. To inspect planned OpenFlow commands on Windows, use python -m sdn.plan with the local runtime. That command rewrites results/sdn/plan.json and does not create switches. Do not describe its successful completion as a packet-forwarding test.

The trailing backtick character in a multi-line PowerShell command continues it on the next line. Copy all lines of the command together. Do not add spaces after the backtick.

For live networking, follow linux/README.md inside the Ubuntu VM. Start the Ryu controller first, then run the Mininet self-test in another terminal with the same local token. In the Linux shell, use:

```bash
sudo env QKD_SDN_TOKEN="$QKD_SDN_TOKEN" \
  .venv-linux/bin/python -m sdn.lab \
  --controller ryu --mode selftest --out results/sdn-ryu
```

Successful completion should save a self-test report with actual pair reachability. A separate monitor command with --verify then checks decision-to-packet behaviour throughout an experiment. Restart the lab controller between independent experiments as the guide specifies, because isolation is latched within a session.

## 16 Critique and outstanding work

The defensible contribution is the operational design and its measured trade-offs: separate wavelength monitoring, finite-sample reference uncertainty, explicit holds, targeted quarantine and verified adaptation. It is not a new QKD protocol or a universal attack detector.

The presentation's wavelength-swap and reroute options assume spare wavelengths, alternate paths and optical switching equipment. The implemented topology does not provide those resources. Its actual actions should be demonstrated as simulated intensity changes and classical traffic control associated with each wavelength.

The proposal also needs a precise objective. Minimizing QBER alone can sacrifice rate, while maximizing estimated output alone can reward a policy for ignoring dangerous evidence. A Pareto front does not uniquely choose a configuration. The implemented deterministic selection rule and explicit availability costs make that trade-off reviewable, although application demand and a key pool remain future operational metrics.

Hidden benign changes are the most important monitoring limitation. More realistic noise calibration and measurement uncertainty are needed, together with tests across attack strengths and block sizes. Thresholds or recovery rules should be chosen using validation data and then frozen before evaluation; adjusting them after seeing failures would weaken the evidence.

The quantum security path needs an exact end-to-end decoy protocol connection, actual disclosure accounting for its decoder, matching collection and stopping rules, and independent theorem-to-code review. Software tests cannot replace that review. Likewise, Linux image build, Ryu startup and live Mininet forwarding must pass before network integration is reported as experimentally demonstrated.

No physical deployment is required by the agreed simulation-only scope. A complete and honest simulation project can still make a useful contribution if its assumptions, reproducible failures and claim boundaries are clear.

## 17 Evidence and reading guide

The numerical source of the latest results is results/hybrid/runs.csv. summary.csv and summary.json aggregate those rows. Example CSVs show the first seed for each scenario. The calibration example records the first calibration's counts and intervals. The report does not introduce a new experimental run or combine unlike studies into a single success rate.

Implementation references include qkd_sdn/physics.py, simulation.py, noise.py, monitoring.py, hybrid.py and policies.py; hybrid_experiments.py records the experiment schedule. run.py contains output accounting. sdn/ryu_app.py, ryu_core.py, ryu_client.py, topology.py and lab.py implement the networking path. PROTOCOL_SECURITY.md and DECOY_FINITEKEY.md explain the separate security paths.

For a project presentation, explain the four-channel problem, show why an average can conceal one channel's disturbance, walk through the hold/isolate trace, compare the retuning result, and then show the correlated-drift failure. Finish by distinguishing supplied Linux code from live validation and estimated monitoring output from a reviewed secure-key result. This sequence allows a non-specialist to assess both the contribution and its limits.

## 18 Selected theoretical sources

Ma and colleagues, Practical Decoy State for Quantum Key Distribution, provides the asymptotic decoy-state foundation used by the optical rate estimator. https://arxiv.org/abs/quant-ph/0503005

Tomamichel and colleagues, Tight Finite-Key Analysis for Quantum Cryptography, provides the scoped ideal single-photon finite-key theorem implemented by the project. The correspondence between its assumptions and the complete simulated exchange still requires independent review. https://arxiv.org/abs/1103.4130

Lim and colleagues, Concise Security Bounds for Practical Decoy-State Quantum Key Distribution, provides the separate decoy estimator's finite-size equations. Its existence does not make the monitoring telemetry an eligible input or complete the full protocol. https://arxiv.org/abs/1311.7129

The Mininet walkthrough explains Linux network emulation and remote-controller use. https://mininet.org/walkthrough/

Ryu's official documentation describes OpenFlow 1.3 messages and REST integration; its repository records its maintenance status. https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html and https://github.com/faucetsdn/ryu

The supplied ideation slides and DESIGN_COMPARISON_AND_CRITIQUE.md provide the design context. The conclusions above are grounded in the project's saved experiment files and explicitly scoped model implementations, not an independent security certification.
