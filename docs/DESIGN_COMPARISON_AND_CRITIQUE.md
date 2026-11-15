# Comparing the two approaches and reviewing the project idea

## Recommendation in plain language

Use the anomaly-detection branch's **calibrated statistical monitoring** to decide whether observations are unusual. Use the original project's **retuning, verification, rollback and wavelength-specific isolation** to decide what action to take. Connect those decisions to **Ryu and Mininet on Linux**. This combination is implemented as the `hybrid` policy; `uncertainty` uses the same monitor with optical retuning disabled.

This is a more complete operational design, but it is not a universal winner. Its stronger sensitivity can also quarantine benign, unmodelled changes. The new experiments expose that trade-off rather than proving that the combined controller is always better.

The research question should be: **Can calibrated monitoring and selective control preserve useful key-generation capacity while limiting unnecessary interruptions?** The present evidence supports further study of that question. It does not establish a new QKD security proof or reliable identification of every attack.

## What was compared

The local starting point was `main` at commit `7b22968`. The remote [Anomoly-detection branch](https://github.com/Kushal343/quantum-sdn/tree/72ca35a7115de875c88ce31be9fc00aac1593ccc) was inspected at commit `72ca35a7115de875c88ce31be9fc00aac1593ccc`, including its monitor, calibration, statistical tests, Qiskit bridge and revised design guide. Its proposed roadmap was distinguished from implemented code. Your 26-slide ideation presentation was reviewed, including the SDN and ML workflow images on slides 14–18. The original presentation was used as a source and has not been rewritten.

| Aspect | Original main project | Anomaly-detection branch | Decision implemented here |
|---|---|---|---|
| Reference for normal observations | Exact analytical expectations treated as known | Independent count calibration with confidence intervals | Use independent calibration in the new policies |
| Statistical features | Three gain tests and a signal-error test | Three gains and three error gains; Qiskit bridge adapts observations after sifting | Monitor three detection gains and three conditional sifted error fractions, with the correct denominator for each |
| Alarm accounting | Fixed per-test significance | Separate calibration and complete-run budgets | Allocate a declared finite-horizon operational budget |
| Unsupported context or incomplete data | Limited explicit checks | Explicit inconclusive status | Hold output without claiming an anomaly or accumulating an isolation streak |
| First suspicious observation | Immediate hold | Observe first, hold after persistence | Immediate temporary hold, then isolate after two consecutive unexplained windows |
| Recovery | Permanent isolation latched; temporary hold can end immediately | Three passing windows can restore advisory output | Three clean windows clear temporary holds; isolation stays latched |
| Optical adaptation | Candidate selection, two-window trial, rollback, cooldown | Fixed settings in implemented monitor | Keep adaptation for calibrated candidates and include a settling-cost hurdle |
| ML | Optional analytical Random Forest surrogate | Optional future optimization in the design guide | Retain as an optional proposer; analytical benefit check remains authoritative |
| SDN | OVS management commands and Mininet topology | No live switch implementation | Add Ryu OpenFlow 1.3 control and retain OVS as an explicit comparison backend |
| Security | Separate finite-key/protocol demonstrations with stated scope | Monitoring prototype, separate future security layer | Keep security calculations separate from operational anomaly decisions |

The six-policy comparison is an ablation study: `fixed`, `aggregate`, `per_wavelength`, `adaptive`, `uncertainty`, and `hybrid`. In particular, comparing `uncertainty` with `hybrid` isolates the contribution of retuning, because they share the same calibrated monitor. The old aggregate/per-wavelength policies use the illustrative 11% cap; their missed low-level disturbances do not by themselves demonstrate a fair comparison at matched false-alarm rates.

## Implemented decisions about each wavelength

Each completed interval is assessed independently for each of the four wavelengths. A signal, decoy or vacuum gain is a detection count divided by emitted pulses. An error fraction uses errors divided by sifted detections; it must not use emitted pulses or all detector clicks as its denominator.

Calibration samples come from an independent benign simulation stream. For each supported device/noise context and candidate configuration, exact Clopper–Pearson intervals describe the uncertainty in six reference rates. At runtime a conservative two-tail binomial test checks whether counts are compatible with any rate in the appropriate reference interval. Dependence among the six tests does not invalidate a union bound, but their individual count laws must remain valid.

The default operational run budget is 0.05, with 0.005 reserved for calibration failure. The remainder is divided across the declared number of intervals, four wavelengths and six tests. All supported candidate configurations are covered by the simultaneous calibration budget. Changing configuration therefore does not silently reuse an incompatible baseline. This finite-horizon statement is conditional on the assumed supported, stable count laws; it is not a lifetime alarm guarantee or a secrecy parameter.

| Observation | Response | Why |
|---|---|---|
| Counts fit calibration, sufficient data, acceptable error uncertainty | Continue | No operational reason to pause |
| One unexplained interval | Hold this wavelength's output | Collect evidence without continuing to accept its estimated output |
| Two consecutive unexplained intervals | Isolate this wavelength | Persistent mismatch warrants quarantine; it does not identify its cause |
| Missing, malformed, sparse, stale or unsupported telemetry | Hold; reset evidence streaks | Missing knowledge cannot establish safety, recovery or an attack |
| Upper QBER confidence bound reaches 11% | Hold | Illustrative operating-cap rule, separate from anomaly significance |
| Temporary hold followed by three usable passing intervals | Resume | Recovery hysteresis avoids immediate oscillation |
| Already isolated | Remain isolated, retain diagnostic acquisition | A continue command cannot bypass quarantine |
| Explained degradation with a worthwhile calibrated candidate | Retune next interval, then verify | Adapt only when an analytical benefit survives the modeled settling cost |
| Two eligible post-change observations show average estimated rate falling by more than 10% | Roll back | Avoid retaining a harmful change |
| Declared horizon exhausted | Hold; report OUT_OF_BUDGET | No unsupported continuation of the statistical claim |

Retuning changes only one wavelength's simulated intensity configuration. It requires more than 1% predicted improvement after charging a 25% interval settling loss over an eight-interval evaluation horizon. Candidate selection retains the existing error/rate trade-off: for elevated errors, minimize predicted QBER among settings giving at least 90% of the best feasible rate. The current model is cheap to evaluate directly, so ML is optional. A four-interval cooldown follows a completed trial.

The controller acts after observing an interval. Estimated output from that completed monitoring block can be withheld before acceptance; switch updates affect subsequent packet forwarding. Diagnostics continue outside the blocked application VLAN. A real device would need an authenticated management channel and an explicit protocol-block boundary before applying optical settings. The current simulator's interval boundary is an operational approximation to that interface.

## Noise and degradation included

| Type | Plain-language explanation | Representation and limit |
|---|---|---|
| Counting/shot fluctuations | Random variation because only a finite number of pulses is observed | Binomial and multinomial sampling; not a detector-electronics model |
| Dark counts | Detector clicks without a useful arriving signal | Background probability; a dedicated measured-increase scenario is added |
| Raman scattering | Strong classical light creates unwanted photons that enter a quantum receiver | Traffic times an illustrative coefficient; dedicated known-context scenario, not a calibrated Raman spectrum |
| Four-wave mixing (FWM) | Nonlinear interaction of optical channels generates other frequencies | A separate effective-background probability and scenario; no phase matching, dispersion or pump-power propagation solver |
| Crosstalk/filter leakage | Light from another channel leaks through imperfect filtering | Separate background probability and measured-context scenario |
| Polarization/phase misalignment | Sender and receiver settings cease to align well | Symmetric bit-error parameter; measured and hidden variants |
| Short noise bursts | A brief sudden increase in unwanted counts | One-window hidden background increase |
| Correlated drift | A disturbance persists over time and can affect several wavelengths | Shared AR(1) misalignment parameter between intervals; trials remain independent within each interval |
| Optical attenuation/loss | Fewer useful photons reach the detector | Measured additional dB loss, hidden attenuation and transient attenuation scenarios; loss is not itself noise |
| Telemetry/model faults | The controller lacks a trustworthy description of current conditions | Missing-record flag, unsupported context, and hidden parameter mismatch scenarios |

Raman, FWM and crosstalk matter in optical coexistence studies, but their importance depends on powers, wavelengths, filters, fibre and receiver design. [Bahrani, Razavi and Salehi's wavelength-assignment study](https://www.nature.com/articles/s41598-018-21418-6) motivates the coexistence problem. Its physical parameters and performance results have not been copied into this simulator as if they were calibrated measurements.

Afterpulsing, detector dead time/saturation, timing jitter, source fluctuations, amplifier spontaneous-emission spectra and detailed electronic noise are not individually implemented. Merely giving background different labels cannot demonstrate that the controller can identify the physical source. A next physical-model study should specify a real receiver and optical power/wavelength grid, then use those data to replace the illustrative coefficients.

## Experimental findings and criticism of the implementation

See [the reproducible findings report](../results/hybrid/FINDINGS.md), [all summary rows](../results/hybrid/summary.csv), and [individual outcomes](../results/hybrid/runs.csv).

Across 20 seeds per case, strong interception, weak interception and hidden attenuation were isolated in all 20 cases by the combined policy. No other wavelength was isolated in those local-disturbance cases. Known noise changes and the one-window transient did not cause permanent isolation. Weak-interception mean isolation delay improved from 1.80 intervals for the previous adaptive policy to 1.15 for the combined policy.

However, hidden correlated drift caused false quarantine in 6/20 combined-policy runs versus 1/20 with the previous adaptive policy. The finite-grid monitor is sensitive to unmodelled benign behaviour. It must not be advertised as generally resistant to correlated noise. Adding a wider benign calibration envelope could reduce false alarms but would also make subtle attacks harder to detect; that trade-off needs independent validation data and a frozen test protocol.

Measured misalignment produced a modest retuning benefit relative to the same monitor without retuning; the findings report quantifies the result and uncertainty. Adaptation could not recover every loss/noise case, which is physically plausible: changing pulse intensity cannot undo arbitrary attenuation or remove optical background. The three-clean-window recovery rule also deliberately sacrifices availability after a transient.

Twenty seeds are exploratory evidence. A 20/20 observed success has a pointwise 95% Wilson lower bound of about 83.9%; 0/20 observed failures has an upper bound of about 16.1%. Stronger empirical claims need more untouched seeds and variation in attack strength, observation size, measurement uncertainty and device parameters. These runs use one model family, not external experimental data.

## Critique of the presentation and research claim

1. **Slides 2–3 simplify the security argument too far.** A measurement does not always create an observable error, and security is not preserved merely because states may change. QKD security requires a specified protocol, device assumptions, parameter estimation, authenticated public communication and privacy amplification. The detector and controller cannot replace those requirements.

2. **Slides 5–6 list attacks that are not all simulated.** Intercept-resend is explicit. Hidden attenuation is an attribution-limit example, not a full PNS information-leakage model. Detector blinding, timing attacks and Trojan-horse attacks need their own device physics and observables before detection claims are justified. Decoy statistics constrain photon-number contributions; they are not a universal attack classifier.

3. **Slide 8's 80% key-rate loss is not a universal fibre-bend rule.** Keep that figure only if accompanied by a defined example or a source. Loss can reduce output without a large QBER rise, but its numerical impact depends on operating conditions and finite-size effects.

4. **Slide 14 assumes spare resources.** Its wavelength-swap and whole-fibre-reroute branches require spare wavelengths, alternate optical paths and suitable optical equipment. The implemented two-switch topology has one trunk. Its supported actions are continue, targeted hold/isolation, and simulated intensity retuning. Ethernet VLAN blocking demonstrates the control mapping; it cannot directly switch photon wavelengths.

5. **Slide 15's low-SKR/high-QBER branches can overlap.** A channel can have high errors and low rate simultaneously. Use ordered validity, anomaly, uncertainty and adaptation checks, as implemented, rather than treating those situations as exclusive classes. Shared degradation should trigger investigation, not automatic trust.

6. **Slides 16–18 contain illustrative numbers, not measured findings.** Label candidate tables and before/after rates as conceptual examples unless reproduced by an experiment. The implemented C1–C5 grid differs from the slide examples. Compare final settings and outcomes using the saved experiment logs.

7. **Slide 17's uncertainty example needs correction.** For 520 errors in 10,000 independent Bernoulli observations, a descriptive 95% Wilson interval is approximately 4.78%–5.65%, not a generic plus/minus 1.5 percentage points. The relevant QBER denominator must be disclosed same-basis sample bits. A monitoring interval does not by itself determine whether noise is legitimate or whether a key is secure.

8. **Slides 16 and 18 need a reproducible selection rule.** A Pareto front contains several non-dominated choices; it does not uniquely choose C4. Specify the constraint and objective. This implementation uses a deterministic error/rate rule and an analytical improvement check with a settling-cost allowance.

9. **ML needs a reason to exist.** Training a Random Forest to approximate a cheap analytical model may add error and training cost. The earlier 2.70% mean candidate-selection regret shows that ML can choose a worse setting. Retain it as an ablation or future acceleration tool for expensive calibrated models, and measure prediction error, selection regret, latency and end-to-end benefit separately. It does not learn new physical truth from its own teacher.

10. **The main scientific limitation is attribution.** An unreported benign attenuator and a passive tap can produce the same monitoring law. An isolated wavelength should be labelled unexplained or unavailable. Calling every isolation an attack detection would overstate the result.

11. **The security/output claim must stay scoped.** The integrated monitoring path reports asymptotic estimated accepted bits. It does not run the full finite-key decoy distillation pipeline for every wavelength and block. Existing finite-key modules and separate-process authentication demonstrations are valuable components, but their existence does not establish a reviewed end-to-end composable WDM system.

12. **Availability needs an application-level measure.** A future comparison should include key demand, a matched-key pool, authentication consumption, command delays and unmet demand. Then decide whether a conservative hold protects the application enough to justify lost output. Current estimated-bit totals do not establish that the application can meet a real workload.

The cited [2026 adversarial-learning paper](https://arxiv.org/abs/2603.03502) uses additional hardware-oriented observables and a different adaptive attack framework. Its reported numerical results are not a benchmark result for this project. The [advantage-distillation paper](https://www.nature.com/articles/s41598-026-52452-4) studies a post-processing change; this project's controller has not implemented advantage distillation. Those distinctions should be stated during the presentation.

## Linux SDN architecture and remaining validation

The requested Ryu application sends real OpenFlow 1.3 messages to the two OVS switches. A local token-authenticated API accepts channel/action requests, checks expected switch connections and waits for barrier acknowledgements. Invalid actions cannot become arbitrary shell commands. Per-wavelength VLAN matches constrain blocking; isolated state cannot be cleared by ordinary continuation. Errors invalidate readiness and stop the topology owner, which tears down the lab.

Updates are not atomic across the two switches. This is a dedicated local experiment, with no production TLS deployment or persistent state store. A Ryu process restart starts a new session and must not be treated as an authorized production quarantine reset. Reconnect within the same process replays recorded restrictive state when explicitly reinitialized. Controller failure and process restart require separate operational procedures in a deployed system.

[Ryu's own repository](https://github.com/faucetsdn/ryu) states that it is not maintained. It is used here because it was requested, inside a separate pinned-source controller container. The simulation remains usable on Windows; live Mininet runs in Linux. [The Linux guide](../linux/README.md) provides setup and packet-validation commands, and the included workflow is ready to test them in GitHub Actions after upload. This Windows machine did not build that Linux image or run live Mininet, so a working Linux deployment is a required remaining verification, not an achieved result.

For a defensible project submission, present this work as a **simulation study of calibrated wavelength-level monitoring and operational control, with a supplied Ryu/Mininet integration awaiting live Linux validation**. Report the correlated-noise failure alongside the successful local-isolation cases.
