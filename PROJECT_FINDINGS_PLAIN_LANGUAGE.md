# Project Findings Report
## Monitoring and improving a simulated quantum communication network

**Report date:** 13 November 2026  
**Audience:** Readers without a background in quantum technology  
**Project stage:** Working research simulation; further security validation is required

**SDN update:** The project now also includes code for a Mininet virtual network
with two software switches and four separate traffic channels. Its controller
can translate the quantum monitor's stop/pause decisions into OpenFlow traffic
rules. The software suite now has 61 passing tests. Actual packet forwarding
still needs to be verified on Linux; it has not been demonstrated on this
Windows machine. Instructions and the live test are in `sdn/README.md`.

---

## 1. What this project is about

When two people communicate privately, they often use a secret digital key to protect their messages. A key is a sequence of zeros and ones used by an encryption system. Both people need the correct key, and an outsider should not be able to discover it.

This project studies a method called **quantum key distribution**, or **QKD**. QKD is a way of establishing shared keys using quantum signals. It does not itself encrypt the message. Under suitable conditions, attempts to measure these signals can introduce disturbances that the communicating parties can detect.

The project combines this idea with software that monitors several communication channels, identifies unusual behaviour, and decides whether to continue, temporarily withhold output, stop using a channel, or adjust its settings.

Everything described in this report was tested in **computer simulations**. No real optical fibre link, quantum transmitter, or physical network was deployed. This lets us investigate the ideas and discover weaknesses before considering practical deployment.

### A simple picture of the system

Imagine one road with four lanes. Each lane carries traffic, but a problem may affect only one lane. Looking at the average condition of the whole road could hide that local problem.

Our simulated network has four channels. They represent different wavelengths, or colours of light, that could share an optical fibre. The software monitors each channel individually as well as the combined network. The road analogy explains the monitoring idea; the simulation does not reproduce every physical detail of a real fibre.

**The main question is:** can the software recognise disturbances, avoid unnecessary interruptions, and adjust the network in ways that improve useful output?

## 2. The most important results

| Result | Meaning for a nontechnical reader |
|---|---|
| Individual-channel monitoring revealed a disturbance hidden by the network average. | A healthy-looking overall average does not mean every channel is healthy. |
| The revised controller produced fewer unnecessary pauses. | Better statistical checks helped the software distinguish random fluctuations from suspicious behaviour. |
| Adaptive monitoring detected disturbances that simple threshold rules missed. | Comparing observations with expected channel behaviour can reveal problems that a single fixed limit cannot. |
| Changing settings improved estimated output by 4.05% in one tested condition. | Adjustment can be worthwhile when operating conditions change enough to make another setting better. |
| Very weak interception and unreported fluctuating noise exposed weaknesses. | The system still has detection limits and can mistake environmental changes for suspicious activity. |
| The project now simulates key correction, verification and authenticated messages. | It checks more of the communication process than the original signal-monitoring demonstration. |
| Finite-key calculations sometimes returned no usable length. | A small quantity of data may not provide enough evidence to justify extracting a key under the selected security assumptions. |

These results are useful research evidence. They do not establish that the system detects every possible attack or is ready to protect real communications.

## 3. Findings explained in detail

### Finding 1: an average can hide a serious local problem

One experiment introduced interception on the third of the four channels. The monitor compared a publicly checked sample of the sender's and receiver's bits.

The percentage of disagreements is called the **quantum bit error rate**, usually shortened to **QBER**. For example, a 5% error rate means about five disagreements in every hundred checked bits.

The disturbed channel had a sampled error rate of **19.03%** after the disturbance began. However, the combined error rate across all four channels stayed between approximately **4.34% and 5.14%**. The other channels diluted the disturbed channel's contribution to the average.

The demonstration used an illustrative 11% limit. The disturbed channel exceeded it, while the network average did not. This limit is a demonstration setting, not a universal security rule for every system.

**What we learned:** monitoring each channel separately is essential. A decision based only on the overall average can miss a concentrated disturbance.

### Finding 2: the first controller paused too often, and we improved it

A protective system should respond to real problems without constantly interrupting normal operation. The earlier controller sometimes treated ordinary random variations as suspicious, particularly when only a small number of events had been observed.

We replaced its approximate statistical checks with checks that better match the actual count data. This mattered especially for rare background detections, where an approximation can be misleading.

| Operating condition | Earlier controller: runs with an unnecessary pause | Revised controller: runs with an unnecessary pause |
|---|---:|---:|
| Normal operation | 24 out of 100 | 1 out of 100 |
| Known additional signal loss | 27 out of 100 | 0 out of 100 |
| Known additional noise | 20 out of 100 | 0 out of 100 |
| Known noise affecting all channels | 12 out of 100 | 0 out of 100 |

These comparisons use two different sets of random trials under the same stated conditions. They are not measurements from the exact same individual runs.

A **pause**, called a hold in the software, temporarily withholds estimated key output while more evidence is collected. **Isolation** is stronger: the software stops releasing output from the affected channel. The revised validation observed no false isolations in any of the four benign conditions above, with 100 runs per condition.

**What we learned:** the revised controller reduced unnecessary interruptions in the tested conditions. Observing no false isolation in these tests does not prove that false isolation can never occur.

### Finding 3: adaptive monitoring detects more than a fixed error limit

We compared four approaches:

- **Fixed operation:** keep the settings and take no protective isolation action.
- **Network-average threshold:** respond when the combined error rate exceeds a limit.
- **Individual-channel threshold:** apply the limit to each channel separately.
- **Adaptive monitoring:** compare each channel with its expected behaviour and gather evidence before isolating it.

In the expanded validation, adaptive monitoring detected strong interception, weaker interception, and hidden additional loss in **all 100 trials for each disturbance**. The individual-channel threshold detected strong interception but missed the weaker interception and hidden loss. The network-average threshold missed all three in these particular experiments.

“Hidden loss” means that fewer signals arrived than the monitor's information predicted. Detecting that disagreement does **not** prove that an attacker caused it. An unreported equipment or channel change could also be responsible.

The revised adaptive controller deliberately waited for repeated evidence before isolation. For weaker interception, its average isolation delay increased from **1.02 to 1.42 monitoring intervals**. Its first protective response was much earlier: an average of **0.06 intervals** after onset in the revised tests. These intervals are simulation steps, not measured real-world response times.

**What we learned:** better protection involves a trade-off. Requiring stronger evidence reduces false alarms but may delay a final isolation decision.

### Finding 4: adjusting settings can improve output—but only when it helps the channel

Earlier experiments showed no useful setting changes because the starting configuration was already the best available option for those conditions. Forcing a change would not have demonstrated an improvement.

We therefore tested a different operating condition: a modelled alignment-related error increased from 1.5% to 5%. This changed which of the available configurations performed best.

Across 20 trials, the adaptive controller changed settings once per run. Its mean estimated network output increased from about **665,078 bits to 691,996 bits**, a gain of **4.05%**. This calculation included the modelled cost of changing settings: a 25% reduction in availability during the following interval.

These quantities are estimated key-production output from the optical model. They are not counts of independently certified secure key bits.

**What we learned:** adjustment can deliver a net benefit when conditions make another setting more suitable. The 4.05% result belongs to this tested operating condition; it is not a promised improvement for every network.

### Finding 5: harder tests revealed important limitations

We broadened the evaluation to include weaker attacks, inaccurate channel information, and noise that persists across successive intervals instead of changing independently each time.

Two results deserve particular attention:

1. When interception affected only **3% of the eligible signal detections**, adaptive monitoring failed to isolate the target in **all 20 trials**. This percentage describes the interception strength, not the observed error rate.
2. When the actual noise fluctuated over time but those changes were hidden from the monitor, it incorrectly isolated the channel in **8 of 20 trials**.

At the tested 6%, 12%, 30% and 70% interception strengths, it detected the disturbance in all 20 trials for each strength. Separate tests with a 20% difference between the actual and reported alignment-error parameter produced no false isolations, showing that the effect depends on the type and size of the mismatch.

**What we learned:** the monitor depends on the accuracy of its channel information. It is good at recognising some unexplained disturbances, but recognising a disturbance is not the same as identifying its cause. More work is needed on subtle attacks and changing environmental conditions.

## 4. Improvements beyond monitoring

The original project mainly demonstrated signal generation, error measurement and monitoring decisions. It now includes more of the steps needed to turn imperfect shared data into a potential key.

### Correcting and checking the shared data

The sender and receiver are called **Alice** and **Bob** in the simulation. These are conventional names for the two communicating parties.

Alice and Bob now run in separate computer processes. They exchange carefully structured information that lets Bob correct some disagreements without receiving Alice's complete raw bit sequence. They then compare short verification values to check whether the corrected results agree. A failed check causes the protocol to reject the result.

### Protecting the public messages

Some messages must be exchanged openly—for example, instructions needed to compare or correct data. **Authentication** helps the recipient detect whether a message was changed or replayed. It protects the identity and integrity of the message; it does not make the public message secret.

The newer simulation uses one-use authentication material and accounts for its secret-key cost. Tests cover ordinary agreement, altered messages, replay attempts, and aborting when strong interception is present.

### Accounting for the real cost of producing a key

One integrated example produced **1,676 matching output bits**. However, it charged **1,524 bits of pre-shared secret material** to authenticate the exchange. The resulting net balance was only **152 bits**.

This does not mean the system sent only 152 physical signals. It means that, after counting the secret material consumed for authentication, the example added 152 bits to the simulated secret-key balance under its model assumptions.

**What we learned:** reporting only the final output length can exaggerate the benefit. Authentication and other processing costs must also be counted. Matching outputs alone do not establish secrecy from an outsider.

## 5. Why the amount of collected data matters

An error estimate from a small sample is uncertain. Checking ten items tells us less about a large population than checking thousands of items. The same principle matters when deciding whether quantum communication data can support a key.

The project now includes **finite-key calculations**. “Finite” simply means that the calculation recognises that only a limited amount of data was collected. It reduces the permitted key length to account for uncertainty and public information revealed during processing.

Two related paths must be distinguished:

| Path | What it currently demonstrates |
|---|---|
| Ideal single-photon protocol | An integrated simulation with signal measurements, separate participants, correction, verification, authentication and a scoped finite-key calculation. |
| Weak-light-pulse, or decoy-state, model | A separate finite-key estimator using counts grouped by measurement setting and light intensity. Complete key distillation is not yet connected to it. |

The second path is relevant because a weak light pulse can sometimes contain more than one photon. Varying pulse intensity provides additional statistics for the analysis. The two paths have different assumptions, so the security calculation from one cannot simply be reused for the other.

In the decoy-state experiments, all tested smaller pulse batches returned **zero permitted key length** under the chosen settings. Undisturbed batches of one billion pulses produced calculated bounds of approximately **825,000–894,000 bits** across five trials. Strong-interception batches of the same size returned zero.

These are calculated length bounds. The large-block experiment did not actually correct and compress those bit strings into final keys. A positive calculation is conditional on its protocol assumptions and successful subsequent processing.

**What we learned:** collecting some matching bits is not enough. There must also be enough statistical evidence, and enough output left after accounting for disclosure and security costs.

## 6. How much confidence should we place in the findings?

The project was evaluated through repeated simulations with different random outcomes. Major completed studies include:

- An initial 140-run comparison of four monitoring policies across seven conditions.
- Two larger 2,800-run studies used to investigate and then validate the controller improvement.
- A 360-run study of retuning, different interception strengths, inaccurate channel information and persistent noise.
- Fifty finite-key decoy count experiments.
- An automated software suite with **56 passing tests** at the latest completed validation.

Some experiments execute quantum circuits using **Qiskit Aer**, a quantum-circuit simulator running on an ordinary computer. Larger statistical studies use a faster mathematical count sampler checked against Aer for the modelled conditions. They are explicitly labelled; they are not all circuit executions or physical experiments.

A random trial is a fresh simulated outcome, not a separate real-world installation. Likewise, a passing software test confirms a particular expected behaviour, not the complete security of the system.

Even **100 successes in 100 trials** do not prove a 100% detection rate. The reported statistical interval for those results extends down to about **96.3%** under the trial assumptions. A smaller result of 20 successes in 20 trials has a much wider lower bound, about **83.9%**. These figures explain why repeated testing matters and why perfect-looking tables should be interpreted carefully.

## 7. What is complete and what remains unfinished?

| Area | Current status |
|---|---|
| Four-channel quantum communication demonstration | Implemented and tested in simulation |
| Dashboard and experiment controls | Implemented and tested |
| Adaptive monitoring and improved statistical checks | Implemented; strengths and failures measured |
| Retuning experiments | A useful gain demonstrated in one changing-condition scenario |
| Separate sender/receiver processes and authenticated messages | Implemented in local simulation |
| Correction, verification and key-compression demonstrations | Implemented, with explicit assumptions and abort conditions |
| Finite-key single-photon calculation | Implemented; the exact match between protocol and theorem still requires independent review |
| Finite-key decoy estimator | Implemented and tested numerically |
| Complete decoy-state key distillation connected to that estimator | **Not yet complete** |
| Independent security review | **Not yet completed** |
| Real hardware deployment | Outside the agreed simulation-only scope |

The remaining priorities are to connect the decoy calculation to the complete matching protocol, review the security assumptions independently, improve handling of changing noise, and investigate weaker attacks. A stronger research claim requires both successful experiments and a justified explanation of why the chosen security analysis applies to the implemented protocol.

## 8. Overall assessment

The project now provides a working environment for studying how software can monitor and manage a simulated quantum communication network. Its clearest contribution is showing why channel-by-channel monitoring matters, then improving the controller so that it makes fewer unnecessary interruptions. It also demonstrates that adjustment can improve estimated output in a suitable operating regime.

Equally important, the broader tests have identified weaknesses rather than hiding them: very weak interception can be missed, persistent unreported noise can trigger false isolation, and small data blocks may not justify a positive key length.

**The appropriate description today is a substantially developed and tested research simulation. It is not yet a fully reviewed system ready to secure real communications.**

---

## Evidence behind this report

The explanations above are self-contained. The following project records allow a technical reviewer to check the underlying details:

| Evidence | Project record |
|---|---|
| Channel-level and aggregate error rates | `results/notebook/telemetry.csv` and `aggregate.csv` |
| Earlier and revised controller evaluations | `results/validation-100/` and `results/validation-exact-100/` |
| Retuning, attack-strength and noise studies | `results/advanced/runs.csv` and `summary.json` |
| Integrated protocol output and rejection tests | `results/protocol/summary.json` and `validation.json` |
| Finite-key decoy experiments | `results/decoy-finite/runs.json` |
| Security assumptions and outstanding work | `PROTOCOL_SECURITY.md` and `DECOY_FINITEKEY.md` |

This report summarises the existing project evidence. It does not introduce a new experiment or an independent security certification.
