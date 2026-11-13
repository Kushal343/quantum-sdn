# Five-task simulation milestone

Follow-up: `protocol_demo.py` now integrates explicit Aer basis preparation/sifting
and one-use polynomial authentication. See `PROTOCOL_SECURITY.md` for the updated
authentication budget, six-message ledger and net key accounting. The reduced
HMAC demonstration described below is preserved as an earlier comparison.

## 1. Finite-key calculation

`qkd_sdn/finitekey.py` implements equation (2) of [Tomamichel et al., arXiv:1103.4130v2](https://arxiv.org/pdf/1103.4130). It computes a finite-size entropy term and output length using fixed block sizes, a predeclared error tolerance, reconciliation cap, secrecy and correctness parameters. The complementary-basis sample must pass the tolerance test. Ideal preparation quality is q=1. The supported model requires single-photon qubits, basis-independent detection, memoryless measurement and an authenticated classical channel. Coherent-pulse inputs are rejected. This is a theorem implementation for that model, not a new proof or a proof for the existing decoy-state optical simulation.

The distributed demonstration generates reduced post-sifting independent symmetric bit blocks. It does not simulate the full theorem's basis-selection/sifting exchange. The original pooled-basis `bb84()` outputs are deliberately not passed into this calculation. Establishing and reviewing an end-to-end protocol-to-theorem correspondence, particularly for the decoy path, remains outstanding.

## 2. Disclosure and failure accounting

The new reconciler sends exactly `floor(n/3)` syndrome bits, using a fixed public sparse graph. Bob sends one acknowledgement bit. Both are included in the reconciliation cap. Public verification and privacy seeds are independently generated and do not depend on the raw key. Verification-tag leakage and extraction overhead are covered by the theorem's logarithmic penalty; they are not subtracted twice. The sample disclosure is the complementary-basis parameter-estimation data handled by the theorem. No raw key or test-harness key fingerprint is sent over the public channel.

The default QKD budget is epsilon_secrecy=1e-9 plus epsilon_correctness=1e-12. The calculator reports their sum, 1.001e-9. **This excludes authentication failure.** Authentication uses computational HMAC-SHA256; no numerical information-theoretic authentication probability is claimed. Deriving a complete composable total including authentication would require a matching authentication construction and its key-consumption accounting. The existing adaptive parity demonstration is not certified by this fixed-syndrome ledger.

## 3. Reconciliation and participant separation

`qkd_sdn/reconciliation.py` implements a sparse parity-check syndrome and normalized min-sum decoder. The decoder receives Bob's bits and Alice's syndrome, never Alice's raw key. `distributed_demo.py` runs Alice and Bob in separate Python processes connected by local pipes. Packets bind session, sender and sequence under HMAC. Receivers reject tampering/replay; waits are bounded. Independent Toeplitz verification gates acceptance, and each process derives its own output.

The first saved run has n=k=8192, 55 sample errors, a 2731-bit reconciliation cap, a 40-bit verification tag and **1690 matching output bits**. No assumed entropy fraction is used. This remains a reduced simulation under the listed assumptions. The parent test harness provisions private inputs and shared setup, and compares private fingerprints; that trusted harness is not Eve or a network endpoint. The local pipe is a transport simulation, not a deployed network service.

## 4. Useful retuning

`advanced_experiments.py` changes reported channel misalignment from 1.5% to 5% at interval 6. This changes which candidate configuration is beneficial. Across 20 seeds and 40 intervals, adaptive control retuned once per run, with no isolation events. Mean estimated network bits increased from 665,078 to 691,996 (**4.05%**), including the 25% next-interval switching penalty. The seed-level mean difference is 26,917 bits; a 5,000-resample bootstrap interval is approximately [25,459, 28,289]. Shared seeds do not guarantee identical draws after configuration changes. This is one modelled operating regime, not a universal gain or finite-key throughput claim.

## 5. Broader validation

The study contains 360 runs: nine conditions, 20 seeds, fixed/adaptive policies, 40 intervals, one million emitted pulses per channel/interval. It uses the labelled binomial count engine, not Aer.

| Condition | Adaptive result |
|---|---|
| 3% intercept-resend | 0/20 detected |
| 6%, 12%, 30%, 70% interception | 20/20 detected at each strength; mean delay 1 interval |
| Actual misalignment 20% lower/higher than reported | 0/20 false isolations for each bias |
| Hidden AR(1) interval noise, persistence 0.85 and innovation std 0.004 | 8/20 false isolations |

The correlated-noise experiment varies the channel error parameter across intervals. It is not an arbitrary within-pulse quantum-memory attack model. Failure under hidden drift demonstrates that the controller cannot reliably attribute an unexplained disturbance to Eve. These findings are retained rather than filtered out. Each 20/20 detection result has a pointwise Wilson lower 95% bound of only about 83.9%.

## Reproduce and inspect

```powershell
.\.runtime\python.exe distributed_demo.py
.\.runtime\python.exe validate_distributed.py
.\.runtime\python.exe advanced_experiments.py
.\.runtime\python.exe -m pytest tests -q
```

Artifacts: `results/distributed/summary.json`, `results/distributed/validation.json`, `results/advanced/runs.csv`, `results/advanced/summary.json`. Unit/dashboard validation: **44 tests passed**. Security-sensitive changes still need independent review. This milestone advances all five tasks; it does not complete a composable proof for the original optical decoy project.
