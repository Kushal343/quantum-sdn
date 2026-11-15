# QKD Wavelength Monitoring: Beginner's Guide

This guide is for classmates with little background in quantum computing, cryptography or machine learning. It explains the project, what its results mean and how to run the examples.

## What does the project do?

The project simulates Alice sending weak light pulses to Bob over an optical link. Four wavelengths share the simulated link. A software controller watches each wavelength separately and decides whether to continue, temporarily hold output, isolate a channel or test a different pulse setting.

The project studies network operation around QKD. It does not transmit real photons or create certified secure keys.

## Basic ideas

**Quantum key distribution (QKD)** is a way for two parties to establish matching random bits using quantum signals and public discussion. The bits can later be used by a separate encryption system. QKD itself does not encrypt messages.

**BB84** is a QKD protocol. Alice and Bob choose measurement bases, compare those choices publicly, keep positions where they match and reveal a sample to estimate errors. If the observations fail the protocol checks, they reject the data.

**QBER** is the fraction of checked bits that disagree. Misalignment, noise or an attack can raise it. QBER alone does not say which cause occurred.

**Secure key rate (SKR)** refers to final secret bits after security processing. Our operational experiments instead report an asymptotic model estimate of accepted bits. They do not report final keys actually distilled by Alice and Bob.

**Wavelength-division multiplexing (WDM)** sends several colours of light over one fibre. We simulate four channels. **Software-defined networking (SDN)** lets software control forwarding rules in network switches. Our OpenFlow rules can block classical traffic associated with a wavelength. An Ethernet switch cannot block photons.

## Why are there signal, decoy and vacuum pulses?

Practical weak laser pulses may contain different numbers of photons. The transmitter randomly sends three intensity classes:

| Pulse class | Purpose |
|---|---|
| Signal | Main intensity used in the key-rate estimate |
| Weak decoy | Helps estimate photon-number contributions |
| Vacuum | Helps estimate background detections |

The monitor records detection and error statistics for each class. The separate finite-key decoy estimator is not yet connected to the live monitor and a complete decoy key-generation pipeline.

## What does the controller do?

For each wavelength it checks six statistics: detection fraction and error fraction for signal, decoy and vacuum pulses. It compares these counts with independently simulated calibration data.

- If the counts fit calibration, it continues.
- One unexplained interval causes a temporary hold while more evidence is gathered.
- Two consecutive unexplained intervals can isolate that wavelength.
- Missing or unsupported data also causes a hold.
- After a temporary hold, three passing intervals are required before resuming.
- For a supported degradation, the controller may test a new decoy setting, measure again and roll back if the observed result is poor.

A hold pauses output while evidence is collected. Isolation quarantines the channel for the run. Neither proves that an attacker is present.

## What does Pareto mean here?

The controller scores five allowed settings on two goals: lower predicted error and higher estimated output. A setting is removed if another is at least as good on both goals and strictly better on one. The remaining candidates form the Pareto front. Because they trade error against output, an extra rule must select one.

The `pareto` policy chooses by estimated output over a short horizon, charges a 25% interval switching cost and requires over 1% predicted gain before trying a setting. It then verifies the change and can roll back. These settings change modelled pulse intensities. They do not repair physical polarization or phase alignment.

## Benchmark results

The matched normal/alignment study used 50 seeds, 40 intervals and 1 million pulses per wavelength per interval. Values are mean estimated accepted bits per run.

| Modelled condition | Existing hybrid policy | Pareto policy | Change |
|---|---:|---:|---:|
| Healthy, nominal 1.5% misalignment | 816,210 | 816,210 | 0.00% |
| 3% reported misalignment | 744,928 | 749,562 | +0.62% |
| 3.5% | 731,382 | 733,808 | +0.33% |
| 4% | 713,770 | 719,107 | +0.75% |

At 4%, Pareto remains 11.90% below healthy output: that is partial recovery. Under healthy conditions none of the compared policies held, retuned or isolated in 50 runs per policy.

A separate comparison used an equal budget of 160 million pulses per run and 50 seeds. Under healthy conditions fixed single-channel output averaged 774,360 estimated bits and fixed four-channel WDM averaged 772,215. With a local 4% disturbance, fixed single-channel output was 322,739, fixed WDM was 660,628 and Pareto WDM was 675,179. Pareto added 2.20% over fixed WDM. Three unaffected channels explain much of WDM's advantage in this local case. When the 4% disturbance affected every channel, Pareto was 19.04% above fixed WDM.

The single-channel result uses a reconstructed fixed C3 model, not recovered historical code. Equal pulse budget assumes one channel can run four times faster. Detector limits, WDM insertion loss and hardware costs are omitted.

An earlier 20-seed study reduced mean weak-interception isolation delay from 1.80 to 1.15 intervals. However, benign correlated drift falsely isolated a channel in 6/20 hybrid runs. Include both findings when presenting the project.

## What is implemented and what remains?

Implemented: four-channel simulation, per-channel signal/decoy/vacuum monitoring, calibrated uncertainty checks, several policies, holds, isolation, retuning with verification and rollback, Pareto selection, optional ML, finite-key demonstration code, and Mininet/Ryu integration code.

Still unfinished: the main Pareto study disabled ML, so integrated ML-plus-Pareto benefit is not demonstrated. The existing interception scenario is not a photon-number-splitting (PNS) attack. An explicit PNS model and decoy-statistic evaluation remain to be done. Complete decoy finite-key processing is not connected to the monitor. Live Mininet/Ryu packet validation has not been run on Linux. Spare-wavelength swapping and alternate-path rerouting from one presentation diagram are not implemented.

## Reproduce on Windows

Open PowerShell in `C:\Users\LENOVO\Downloads\qkd-sdn`:

```powershell
.\.runtime\python.exe -m pytest tests -q
.\.runtime\python.exe run.py network --policy pareto --engine binomial --scenario intercept --out results/friendly-demo
.\.runtime\python.exe -m experiments.pareto_experiments --suite alignment --out results/pareto-recheck
.\.runtime\python.exe -m tools.report_pareto --out results/pareto-recheck
```

The first command runs software tests, the second a short example, and the third the alignment sweep: 50 seeds x 7 alignment settings x 4 policies. Read `results/pareto-recheck/PARETO_RESULTS_REPORT.md`. For Linux Mininet/Ryu instructions, see `../linux/README.md`.

## A short explanation for classmates

“We simulated four QKD wavelengths and built a controller that checks each one separately using signal, decoy and vacuum counts. It can continue, pause output, quarantine an unexplained channel or test a new pulse setting. Pareto selection gave small estimated output gains under three alignment disturbances, with no gain in healthy conditions. These are model estimates, not proof of secure-key gains. Benign correlated noise can still cause false isolation. The integrated ML test and explicit PNS test remain unfinished.”
