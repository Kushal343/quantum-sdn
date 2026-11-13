# Integrated protocol simulation and security accounting

`protocol_demo.py` extends the earlier reduced-block example. It uses Aer state preparation/measurement with independent random basis choices, basis-independent erasure, and explicit intercept-resend when requested. Transmission stops at the first prefix meeting the two basis quotas. Alice and Bob receive only their own private records in separate processes. They exchange bases, detection flags, complementary-basis sample values, a sample error count, a fixed syndrome, independent universal-hash seeds/tags, and a final acknowledgement.

The finite-key calculator is the scoped single-photon calculation described in `FIVE_TASKS_STATUS.md`. Its fixed n, k, tolerance and disclosure cap are agreed before examining test errors. It does not apply to the weak-coherent decoy optical model. A public selection seed selects n raw-basis and k test-basis positions independently of bit values. This fixed-size sampling implementation and stopping rule need independent protocol-to-theorem review; implementation tests cannot establish that correspondence by themselves.

## Authentication construction and budget

The new path replaces HMAC with an explicit one-use polynomial authenticator over p=2^127-1. Messages have a maximum canonical JSON length of 262,144 bytes. Their byte length and padded 15-byte blocks form an injective coefficient vector, placed only at positive polynomial degrees. Each packet uses a fresh uniform field evaluation point and an independent uniform additive pad. A receiver permits one attempt per allocated key and checks session, sender and sequence. No authentication key is reused or recycled.

For distinct messages the difference polynomial, minus any requested tag difference, is nonzero and has degree at most D=17,478. It therefore has at most D roots in the prime field. The one-time pad makes the observed tag independent of the evaluation point. The per-attempt forgery bound is at most D/p; six attempts have union bound **6.164e-34**. See the [polynomial universal-hashing construction](https://www.cs.ucdavis.edu/~rogaway/papers/poly.pdf) for the underlying method. The bound assumes ideal independent uniform secret randomness and the enforced size/attempt limits. It is not a claim that testing empirically measures such tiny probabilities.

Six allocated field-key/pad pairs cost **1,524 stored secret bits**. The run conservatively charges all six pairs, including on an early abort. The QKD secrecy/correctness contribution is 1e-9+1e-12; the authentication bound is added separately. This fixes the unquantified HMAC term in the older demonstration. Authentication key establishment and any later recycling are outside the simulation.

## Leakage ledger

| Public content | Treatment |
|---|---|
| Bases and basis-independent detection flags | Sifting information in the scoped model |
| Random selection and public hash seeds | Independent of bit values; no raw-key disclosure charge |
| Complementary-basis test bits | Parameter-estimation disclosure in the scoped analysis |
| Error count | Conservatively charge ceil(log2(k+1)) bits |
| Fixed sparse syndrome | Charge floor(n/3) bits; no adaptive requests |
| Verification tag | Accounted by theorem verification/extraction penalty |
| Acknowledgement | Charge one bit |
| One-use authentication tags | Independently field-pad masked; secret cost charged separately |

The privacy seed is independent of the verification seed. Bob's decoder never receives Alice's raw bits. Fingerprints used to compare the final outputs are returned only to the trusted test harness, never sent on the simulated public channel or saved to results.

## Example and reproduction

```powershell
.\.runtime\python.exe protocol_demo.py
.\.runtime\python.exe validate_protocol.py
```

With n=k=8192, the example derives 1,676 gross bits and **152 net bits** after authentication cost. The reconciliation cap is 2,745 bits. The first run used 33,400 emitted pulses and 34,512 Aer shots including padding. Sample selection and authentication randomness can change between runs; successful output length remains fixed by the predeclared protocol parameters.

Results are in `results/protocol/summary.json` and `validation.json`. The latter checks normal agreement, tampered-message rejection and strong-interception abort. Source/basis tests, authentication one-use checks, replay rejection, message size caps and budget accounting are also automated.

Validation completed: **48 tests passed**, plus the separate three-case integrated protocol validation and 12 channel trials/tamper rejection for the earlier distributed demonstration.

This is still a simulation: quantum-event randomness is seeded for reproducible experiments, so the files are not a production secret-key generator. Fresh hash seeds and authentication material use system randomness. The assumptions must be mapped and independently reviewed before claiming a complete composable end-to-end proof. In particular, no finite-key decoy-state proof has been implemented. Retuning and correlated-noise results remain the separate optical-model experiments documented in `FIVE_TASKS_STATUS.md`.
