# Finite-key decoy analysis and review boundary

Implemented: `qkd_sdn/decoy_finitekey.py` and `decoy_finite_demo.py`.

The estimator implements equations (1)–(5) of [Lim et al., arXiv:1311.7129v1](https://arxiv.org/pdf/1311.7129). It computes finite vacuum/single-photon count bounds separately in X and Z, bounds Z single-photon errors and the X phase-error rate, then subtracts reconciliation disclosure and finite security overhead. It requires three intensity settings, phase-randomized coherent emission, independently randomized settings, basis-independent detection and authenticated classical communication. All X-basis intensity classes contribute to the raw key. The phase threshold is declared before evaluating a block. Degenerate or insufficient bounds return zero rather than an optimistic substitute.

## Correct input mapping

| Input | Meaning | Current source |
|---|---|---|
| `nx` | X-basis raw-block detections at each intensity | New basis-resolved count simulator |
| `nz` | Z-basis test detections at each intensity | New basis-resolved count simulator |
| `mz` | Z-basis test errors at each intensity | New basis-resolved count simulator |
| `leak_ec` | Upper cap on public reconciliation disclosure | Explicit argument; demo uses one-third block plus ack |
| Intensity probabilities | Predeclared source settings | Explicit arguments |
| Secrecy/correctness parameters | QKD failure allocation, excluding authentication | Explicit arguments |

The old `NetworkSimulator.observe()` records cannot be used unchanged: they combine bases and its rate estimator uses signal bits. No conversion from that incomplete telemetry is performed. The new demo samples independent basis choices and optical counts in aggregate. It uses the existing gain/background model; it does not execute Aer shots or implement a quantum multiphoton Fock-state simulator.

## Completed experiments

```powershell
.\.runtime\python.exe decoy_finite_demo.py
.\.runtime\python.exe -m pytest tests/test_decoy_finitekey.py -q
```

`results/decoy-finite/runs.json` contains 50 blocks: five pulse counts, five seeds, and two disturbance settings. At one billion pulses, undisturbed blocks produced bounds of 871,022; 828,480; 825,134; 894,229; and 858,384 bits. All five strong-interception blocks returned zero. Every tested smaller block returned zero under the current settings. The stored statuses distinguish insufficient counts, unavailable phase bounds and phase-threshold aborts.

These are conditional length bounds, not generated keys. The reconciliation cap is modelled; this large-block demo does not execute decoding or privacy amplification. It uses a fixed emitted-pulse batch, whereas the cited protocol specifies detected-block collection and sampling. Consequently, this experiment verifies the estimator numerically but is not itself a complete implementation of the cited protocol's collection/stopping rules.

## Verification

Full project validation after this change: **56 tests passed**.

Eight new tests cover small-block rejection, positive large-block bounds, increasing leakage, tighter secrecy, interception, invalid settings and integer-count constraints. A separate photon-number generator checks estimated vacuum/single-photon lower bounds against latent counts across 30 seeds. The estimator never receives those latent counts. These numerical checks are useful regression evidence, not a replacement for a mathematical security review.

## What is still not complete

1. End-to-end decoy distillation with the exact collection/stopping/sampling rules and actual reconciliation leakage has not been connected to this calculator. The separate-process `protocol_demo.py` remains the ideal single-photon path.
2. The independent security review requested earlier cannot be supplied by the same author. There is no review sign-off, certificate, or claim of production security.
3. The theorem-to-code correspondence, including the single-photon sampling adaptation, requires review by a qualified independent reviewer.

The incomplete decoy **calculation** has now been implemented. It would be inaccurate to mark the entire original optical project as having a completed end-to-end finite-key security proof. This document intentionally records that distinction.
