# Classical postprocessing milestone

The BB84 simulation now has a runnable classical postprocessing path:

1. Random disclosed sample → exact hypergeometric upper bound on the remaining **bit-error** fraction.
2. Session-bound, ordered HMAC-SHA256 transcript messages using an independent simulated pre-shared secret.
3. Six-pass parity/bisection reconciliation, charging each disclosed Alice parity.
4. Independent public-seed 64-bit Toeplitz verification, aborting on mismatch.
5. Toeplitz privacy-amplification demonstration, conditional on an explicitly supplied min-entropy assumption.

The implementation is in `qkd_sdn/postprocessing.py`; `postprocess_demo.py` connects it to Aer BB84. Existing notebook and controller outputs retain their prior meaning.

## Run

```powershell
.\.runtime\python.exe -m experiments.postprocess_demo --out results/postprocessing/default
.\.runtime\python.exe -m experiments.postprocess_demo --assumed-entropy-fraction .8 --out results/postprocessing/assumed-entropy
.\.runtime\python.exe -m experiments.postprocess_demo --eve .8 --out results/postprocessing/intercept
```

The first command deliberately returns no candidate key without an entropy bound. The second explicitly assumes an unproven pre-transcript entropy of 80% of the raw block length, solely to exercise the pipeline. The third tests the QBER abort path. Summaries contain no raw keys, candidate bits, authentication secrets or transcripts.

## Saved demonstration

Full validation: **41 tests passed**. The 80% interception demonstration measured 19.53% sample QBER and aborted before reconciliation or candidate generation.

For 24,000 pulses, seed 42, and 0.5% symmetric channel noise:

- 12,001 sifted bits, including a uniformly disclosed 3,000-bit sample with 15 errors.
- Remaining bit-error fraction upper bound: **1.1221%**, with one-sided failure probability 0.001.
- Reconciliation and verification succeeded; 2,314 Alice parity bits and a 64-bit verification tag were disclosed.
- Default entropy bound zero: no candidate output.
- Assumed entropy 7,200 bits: matching **4,762-bit candidates** after leakage accounting and the extraction margin.

The sample bound is tested by enumerating every possible error population in a small finite population and verifying exact coverage. Tests also check Toeplitz multiplication against an explicit matrix, reconciliation, failure on an unreconciled block, default rejection without entropy, and rejection of modified, reordered, truncated or cross-session transcripts.

## Scope and remaining proof work

The sample inversion bounds errors in a fixed classical block drawn without replacement. It does not infer phase errors, single-photon yields or conditional quantum min-entropy. It must not be applied directly as a finite-key decoy security proof. The distribution used is documented in the [SciPy hypergeometric reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.hypergeom.html).

The candidate-length demonstration subtracts Alice parity disclosure, verification-tag length and `2 log2(1/epsilon_pa)` from the user-supplied entropy assumption. A protocol proof must justify the conditional smooth min-entropy, the full adaptive public transcript leakage, smoothing/failure budgets and abort conditioning. In particular, the current parity count alone is not a proof of the leakage of all adaptive interaction. Quantum-side-information extraction requires the assumptions of the [quantum leftover-hashing result](https://arxiv.org/abs/1002.2436); this implementation does not establish those assumptions. [Finite-key BB84 analysis](https://arxiv.org/abs/1103.4130) is a reference for the remaining protocol-level work, not a certification of this code.

Reconciliation is a local simulation of interactive parity/bisection, not a complete Cascade implementation. The transcript authenticator is computational HMAC, not information-theoretic authentication. It authenticates messages against the simulation's expected complete transcript; it does not implement a distributed receiver or network acknowledgements. A pre-shared authentication secret is assumed rather than established by QKD.

The demo uses deterministic simulation RNG for bit arrays and public hash seeds. It is not a cryptographic key generator. Only the simulated authentication secret/session identifier uses system randomness. A complete operational security claim remains outside this milestone.
