# Normal operation comparison and professor briefing

The project demonstrates operational monitoring and parameter control in a simulated four-wavelength QKD system. The main contribution is the decision process and its measured trade-offs, rather than a new quantum protocol or a hardware performance claim.

## Normal operation and degradation

A new matched healthy reference uses 50 seeds, 40 intervals, 1,000,000 pulses per wavelength per interval and the same calibration contexts and runtime/calibration seeds as the existing Pareto alignment grid. This adds 200 normal-reference runs. The referenced Pareto comparison contains 2,480 runs; they are kept as separate evidence files. The inference horizon and pulse budget are the same within this normal/alignment comparison.

Healthy operation has nominal misalignment of 1.5%. `uncertainty`, `hybrid`, `pareto_front` and `pareto` all produced **816,210.3 estimated accepted network bits per run**, with zero retunes, holds or isolations in all 50 runs per policy. Pareto provided **0% improvement** in healthy operation. This is a useful result: unnecessary reconfiguration would incur cost without improving an already suitable setting.

| Reported misalignment parameter | Hybrid estimated bits/run | Pareto estimated bits/run | Pareto gain over hybrid | Pareto deficit from healthy operation |
|---|---:|---:|---:|---:|
| Healthy nominal 1.5% | 816,210.3 | 816,210.3 | 0.00% | 0.00% |
| 2% | 790,934.6 | 790,934.6 | +0.000% | 3.10% |
| 2.5% | 767,337.9 | 767,337.9 | +0.000% | 5.99% |
| 3% | 744,928.1 | 749,562.3 | +0.622% | 8.17% |
| 3.5% | 731,381.6 | 733,807.7 | +0.332% | 10.10% |
| 4% | 713,770.2 | 719,106.6 | +0.748% | 11.90% |
| 4.5% | 705,251.0 | 705,251.0 | +0.000% | 13.59% |
| 5% | 692,238.1 | 692,238.1 | +0.000% | 15.19% |

These percentages answer different questions. Gain over hybrid measures the extra output from the new selection rule under the same disturbance. Deficit from healthy operation measures how much degradation remains. A positive Pareto gain does not mean the physical disturbance has disappeared or normal performance has been restored.

The alignment value is a model parameter, not exactly the measured QBER. At 3% reported misalignment, mean observed target QBER rose from about 3.0783% under hybrid to 3.0939% under Pareto. The new policy trades that small error increase for higher estimated output. These means include only usable target-channel intervals after onset.

## What was contributed theoretically

1. A conditional monitoring method for each wavelength, using independent benign calibration rather than treating normal probabilities as perfectly known. Six detection/error checks are made for each wavelength and setting.
2. Exact count intervals and composite-null binomial tests with an explicit finite-horizon operational alarm budget. This handles sparse observations and accounts for calibration uncertainty under the declared count model.
3. An ordered decision policy: telemetry validity, anomaly evidence, uncertainty holds, persistent quarantine, recovery, then optional adaptation. A low network-average QBER cannot override a local anomaly.
4. Explicit Pareto nondominance between predicted QBER and output, followed by a deterministic operating-point rule that charges settling cost and respects remaining verification time. A front alone does not select an operating point.
5. Separate implementations of published finite-key bounds and classical-protocol demonstrations. These are existing-theorem implementations under stated assumptions, not a new composable security proof for the full monitoring project.

## What was demonstrated experimentally

- The original combined-policy study comprised 2,160 simulation runs. Both old adaptive and hybrid isolated tested strong/weak interception and hidden attenuation in 20/20 runs each. Hybrid reduced mean weak-interception isolation delay from 1.80 to 1.15 intervals, without isolating unaffected wavelengths in those cases.
- The archived follow-up Pareto study comprised 2,480 runs: 1,080 standard-scenario runs and 1,400 alignment-grid runs. It used new evaluation seeds. The normal reference supplied to this report comprises 200 runs.
- Pareto delivered-output selection improved network-wide estimated output over hybrid by 0.62%, 0.33% and 0.75% at reported 3%, 3.5% and 4% misalignment. Fifty seeds were used per alignment/policy case. Descriptive paired-bootstrap intervals for the three mean differences were above zero; other grid cases showed no change.
- Extracting the Pareto front while retaining the old rule produced no improvement. The gain comes from the declared operating-point preference and cost/horizon treatment, not from dominance pruning alone.
- The original eighteen standard scenarios showed no output change after adding Pareto selection. Its attack-detection logic was not improved by the optimizer.
- Separate Aer runs checked circuit-based integration. The larger repeated studies used the binomial count engine for the independent symmetric model. They did not transmit physical photons.
- The reorganized software passes 81 tests. Linux Ryu/Mininet code is supplied; image startup and live packet tests still need Linux execution. A passing software test is not a physical security validation.

## The failure result that must be presented

In the earlier hybrid study, hidden benign correlated drift caused unnecessary permanent isolation in 6/20 hybrid runs versus 1/20 previous-adaptive runs. The later Pareto standard cohort used different seeds and had 2/20 false-isolation runs for both hybrid and Pareto. These numbers must not be interpreted as Pareto reducing the earlier 6/20 rate: the seed cohorts differ, and Pareto made no change within its own matched comparison.
The system recognizes a mismatch with its model. It cannot reliably attribute that mismatch to an attacker. Correlated noise, inaccurate context information and physical detector effects remain important limitations.

## A short explanation to give the professor

We built a simulation of four independently monitored QKD wavelengths and compared operational control policies under shared experimental conditions. Our controller uses calibrated count uncertainty to decide whether to continue, temporarily hold, isolate or retune one wavelength. We made the Pareto selection rule explicit and included switching and verification costs. Under healthy conditions it made no unnecessary changes. Under three tested alignment conditions it improved estimated accepted output by roughly 0.3% to 0.75% over the existing adaptive controller, while preserving its anomaly checks. The result is partial recovery, with a small error-rate trade-off. Hidden benign drift can still cause false isolation. We have not established physical gains or an independently reviewed end-to-end WDM security proof.

## What not to claim

Do not call 20/20 observed successes a guaranteed 100% detection rate. Do not describe asymptotic estimated bits as actually generated secure keys. Do not credit ML for the Pareto study: ML was disabled. Do not call the 11% operating cap a complete security acceptance rule. Do not describe VLAN blocking as optical photon isolation. Do not claim that decoy intensity retuning repairs polarization drift or creates an alternate optical route.

## How to show the evidence

1. Show `normal-comparison/comparison.csv` and `normal_vs_degradation.png`: normal operation first, then degradation and partial recovery.
2. Show `pareto/pareto_front.png`: explain why two points can both be nondominated and why a selection rule is needed.
3. Show the held/isolated target trace in `hybrid/intercept-example.csv`: only wavelength 3 is stopped in the demonstrated local case.
4. Show the correlated-drift failure before stating the final scope. Explain that actual finite-key security and live optical control are separate validation tasks.

## Reproduce on Linux

Run from the organized project root with its Linux Python environment:

```bash
.venv-linux/bin/python -m experiments.pareto_experiments --out results/pareto-recheck
.venv-linux/bin/python -m tools.report_pareto --out results/pareto-recheck
.venv-linux/bin/python -m experiments.normal_comparison --seeds 50 \
  --pareto-results results/pareto-recheck --out results/normal-recheck
.venv-linux/bin/python -m tools.report_normal --out results/normal-recheck \
  --pareto-results results/pareto-recheck --brief reports/PROFESSOR_BRIEF_RECHECK.md
```

For installation and live Ryu/Mininet commands, read `linux/README.md`. The existing results can be opened without rerunning anything. The matched normal script reads the saved alignment cohort and writes its own files; it does not modify the earlier experiment.
