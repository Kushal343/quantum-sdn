# Qiskit-first SDN/WDM-QKD research prototype

Finite-key decoy count estimation is now available via `decoy_finite_demo.py`.
See [DECOY_FINITEKEY.md](DECOY_FINITEKEY.md) for input requirements, experiments,
and the remaining end-to-end protocol and independent-review boundaries.

The integrated Aer/basis-sifting and separate-process protocol now has
one-use authentication with an explicit failure bound and secret-key cost.
See [PROTOCOL_SECURITY.md](PROTOCOL_SECURITY.md) for its scope and leakage ledger.

The latest five-task milestone is documented in
[FIVE_TASKS_STATUS.md](FIVE_TASKS_STATUS.md): a scoped single-photon finite-key
calculator, fixed-syndrome disclosure accounting, separate Alice/Bob processes,
measured retuning gains, and robustness experiments including observed failures.

The next classical-processing milestone is implemented in
[POSTPROCESSING.md](POSTPROCESSING.md): exact finite-sample bit-error bounds,
authenticated simulated transcripts, parity reconciliation, verification and
conditional privacy-amplification demonstrations. Run `postprocess_demo.py`;
the default releases no candidate without an explicit entropy assumption.

## Validation extension

The latest controller improvement and 100-seed comparisons are documented in
[RESULTS_IMPROVEMENT.md](RESULTS_IMPROVEMENT.md). Exact binomial anomaly tests
replace the earlier Gaussian residual heuristic. The large sweeps use an explicitly
labelled count sampler; the Aer path remains the default.

The project now includes a local `.runtime` Python installation, an explicit
simulated-device interface, repeated-seed scenario evaluation (`evaluate.py`),
optical sensitivity sweeps (`sensitivity.py`), and headless notebook verification
(`validate_notebook.py`). See [RESEARCH_VALIDATION.md](RESEARCH_VALIDATION.md)
for commands, statistical definitions, current verification, and remaining limits.
The confirmed project scope is simulation only.

Start with **bb84_wdm_qiskit.ipynb**, the executed, self-contained adaptation of
your supplied `bb84_simulation.ipynb`. The source notebook in Downloads was not
modified. The adaptation preserves random bits/bases, Eve's intercept-resend,
Bob's measurements, basis sifting and public random-sample QBER estimation.
Quantum outcomes now come from actual Qiskit Aer shots.

## Run the notebook

Open `bb84_wdm_qiskit.ipynb` in Jupyter, VS Code notebooks or Google Colab.
In that notebook's environment, install:

```python
%pip install qiskit qiskit-aer numpy pandas matplotlib
```

Restart the kernel and Run All. It includes its own function definitions, so it
does not need the companion project package. Colab is optional; no IBM account,
cloud backend, credentials or paid service is required for local Aer execution.

Edit `ATTACK_START`, `ATTACK_FRACTION` and `TARGET` in section 5 to change the
attack schedule. Default: 12 monitoring intervals, 12,000 pulses per channel per
interval, Eve intercepts 80% on lambda_3 from interval 4 (zero-based indexing).
Four illustrative wavelength labels: 1550.0, 1550.8, 1551.6 and 1552.4 nm.

The executed example gave 19.03% sampled QBER on lambda_3 after onset and zero
on the other channels. This is one idealised seeded run, not a detection-rate
claim. Theory is 20% on lambda_3 and approximately 5% aggregate at equal sample
weights. CSVs and the comparison plot are in `results/notebook/`.

## Run the Python project

On this workspace a private Python 3.12 runtime and packages have been placed
under `../../work/runtime/`; the launcher detects it. It does not change your
system Python or PATH. From a PowerShell terminal in this project folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch.ps1 -Task demo
powershell -ExecutionPolicy Bypass -File .\launch.ps1 -Task dashboard
powershell -ExecutionPolicy Bypass -File .\launch.ps1 -Task test
```

`ExecutionPolicy Bypass` applies to that process only; it does not change the
machine's policy. The dashboard listens on localhost. Stop it with Ctrl+C.

On another computer, install Python 3.11+ and create an environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py demo
.\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.address 127.0.0.1
```

`requirements-lock.txt` records the exact tested Windows/Python 3.12 environment;
`requirements.txt` gives broader compatibility ranges. The private runtime is
not included in the project ZIP. The notebook alone needs only the five packages
listed above; the full project includes scikit-learn, SciPy, pytest and Streamlit.

## Implemented components

| File | Purpose |
|---|---|
| `qkd_sdn/quantum.py` | BB84 preparation, Eve's mid-circuit measurement/resend, Bob's measurement |
| `qkd_sdn/bb84.py` | Adapted session API, random public sampling, four logical wavelengths |
| `qkd_sdn/physics.py` | Simplified coherent-pulse gains, background model, asymptotic weak+vacuum decoy estimates |
| `qkd_sdn/simulation.py` | Optical sampling plus Aer outcomes for all detected signal/decoy/vacuum events |
| `qkd_sdn/controller.py` | Model residual checks, uncertainty, persistent evidence, retune/isolate/rollback |
| `qkd_sdn/ml.py` | Optional regression surrogate for analytical QBER/SKR estimates |
| `run.py` | Notebook-style demo, optical network run, baselines and ML evaluation |
| `dashboard.py` | Interactive four-wavelength intercept-resend demonstration |

The notebook/dashboard are the first BB84/WDM demonstration. The optical model
and adaptive controller are a separate experimental path, accessible via:

```powershell
python run.py network --scenario intercept --steps 12 --out results/network
python run.py network --scenario loss --steps 12 --ml --out results/loss
python run.py compare --scenario intercept --steps 12 --out results/comparison
python run.py train --out results/ml
```

Scenarios: `normal`, `loss`, `noise`, `intercept`, `weak_intercept`, `tap`,
`shared_noise`. The optical-path scenario onset is interval 6. In that path,
`--pulses` sets emitted pulses per wavelength/interval; interval duration is 1 s
of model time. Baseline policies: fixed settings, aggregate 11% threshold,
per-wavelength 11% threshold and adaptive monitoring. A single-seed comparison
is a smoke experiment, not a statistically established research result.

## Modelling and security boundaries

- Wavelengths are independent logical channels on a shared conceptual fibre.
  Qiskit does not infer wavelength-dependent physics from a numeric label.
  The notebook has optional basis-independent erasure and symmetric bit errors.
- The optical path adds transmission/detection efficiency, weak-coherent pulse
  gains, vacuum background and illustrative traffic-dependent Raman/crosstalk
  terms. Coefficients need literature-based calibration. Detailed FWM, detector
  imperfections, electronic noise spectra and real optical multiplexers are not
  implemented. Poisson emission is integrated analytically through coherent-state
  gain; individual multiphoton Fock states are not represented in Aer.
- Intercept-resend is an explicit circuit operation. PNS and detector attacks are
  not implemented. The `tap` scenario is hidden additional loss, which is not
  uniquely distinguishable from unmeasured benign loss.
- Wavelength telemetry excludes Eve's participation and scenario labels. The
  evaluator's truth table is stored separately. Model-based detection assumes
  trustworthy, sufficiently accurate channel-condition telemetry.
- Remaining bits in the notebook are raw key material, not final secure keys.
  There is no authenticated classical exchange, reconciliation or privacy
  amplification. `aborted=False` means only below the demo error threshold.
- The optical path uses asymptotic plug-in decoy bounds. Its SKR is an estimate
  and can fluctuate strongly for sparse decoy/vacuum counts. Monitoring intervals
  do not create a composable finite-key proof. Never use outputs as actual keys.
- The adaptive controller uses 3-sigma Wilson intervals, 4-sigma gain residuals,
  two consecutive suspicious intervals, and a heuristic two-window verification
  and rollback rule. These are initial research settings, not calibrated security
  guarantees. Family-wise/sequential false-alarm control is future work.
- Isolation is latched. Diagnostic probes continue, but their estimated key bits
  are not released. A held interval is also withheld. Retuning charges a fixed
  illustrative 25% next-interval availability penalty.
- ML labels come from analytical equations, not Aer training shots or physical
  measurements. Held-out channel conditions keep all their candidate settings
  together. Analytical scoring gates proposed changes; ML is not a security
  authority. Direct optimisation here exhaustively searches the five candidates,
  rather than a continuous global parameter space.
- Controller commands currently update in-process simulated devices. There is
  no deployed OpenFlow/Mininet/REST integration or real SDN monitoring platform.
- The SDK runtime performs simulated measurements on a classical CPU. No quantum
  hardware, network transport, wall-clock realtime service or paid platform is
  involved.

## Validation

18 tests passed: ideal key agreement, basis-sifting fraction, full/partial
interception versus f/4, combined noise, no-click handling, repeatability,
channel-specific attack effects, telemetry/ground-truth separation, physical
trends and target-only controller isolation. All eight notebook code cells ran
successfully; its plot was visually inspected. Streamlit's AppTest verified
initial load and a button-triggered Aer run.

The next research milestones are calibrated optical parameters, finite-key
estimation, repeated-seed sweeps, false-alarm/detection-delay analysis, robust
retune verification and an explicit device API before optional Mininet work.

## References

- Qiskit AerSimulator: https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html
- Qiskit Aer noise: https://qiskit.github.io/qiskit-aer/apidocs/aer_noise
- Ma et al., Practical Decoy State for Quantum Key Distribution, PRA 72, 012326:
  https://arxiv.org/abs/quant-ph/0503005

The supplied notebook is the starting reference. No licence is asserted over
your original code; add your team's chosen licence before redistribution.
#   q u a n t u m - s d n  
 #   q u a n t u m - s d n  
 