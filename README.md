# QKD wavelength monitoring and SDN control

A simulation of four QKD wavelengths, calibrated anomaly monitoring, selective
holds/isolation and parameter retuning. It includes Pareto policy comparisons,
scoped security/protocol demonstrations and a Linux Mininet/Ryu lab.

Start with the [professor briefing](reports/PROFESSOR_BRIEF.md),
[results index](results/README.md) and [Linux reproduction guide](linux/README.md).
The [folder guide](docs/PROJECT_LAYOUT.md) explains the organized layout;
[command migration](docs/COMMAND_MIGRATION.md) maps earlier script commands.

## Measured results

The following matched comparison uses 50 seeds, 40 intervals and 1,000,000 pulses
per wavelength per interval. Values are mean estimated accepted network bits
per run, not physically distilled secure keys.

| Condition | Hybrid | Pareto | Gain over hybrid |
|---|---:|---:|---:|
| Healthy nominal 1.5% misalignment | 816,210 | 816,210 | 0.00% |
| 3% reported misalignment | 744,928 | 749,562 | +0.62% |
| 3.5% reported misalignment | 731,382 | 733,808 | +0.33% |
| 4% reported misalignment | 713,770 | 719,107 | +0.75% |

Healthy operation needed no holds, retunes or isolation. The improvements under
degradation are partial recovery: at 4%, Pareto still falls 11.90% below healthy
output. Other alignment cases and the standard scenario cohort showed no
Pareto output gain. Hidden benign correlated drift can cause false isolation.
Read the [briefing](reports/PROFESSOR_BRIEF.md) for the failure results and scope.

## Windows quick start

Run these commands from this project directory. The existing local Python is
kept in `.runtime/`; Linux uses a separate environment.

```powershell
.\.runtime\python.exe run.py network --policy pareto --engine binomial --scenario intercept --out results/windows-demo
.\.runtime\python.exe -m streamlit run dashboard.py
.\.runtime\python.exe -m pytest tests -q
```

The demonstration writes `results/windows-demo/pareto_telemetry.csv`. For an
OpenFlow plan without Mininet, run `python -m sdn.plan` with the same Python.
Live Mininet/Ryu requires the [Linux lab](linux/README.md).

## Reproduce the comparisons

On Windows use `.\.runtime\python.exe` in place of `python`; on Linux use
`.venv-linux/bin/python`. Use fresh output directories to preserve the evidence.

```bash
python -m experiments.hybrid_experiments --seeds 20 --out results/hybrid-recheck
python -m tools.report_hybrid --out results/hybrid-recheck
python -m experiments.pareto_experiments --out results/pareto-recheck
python -m tools.report_pareto --out results/pareto-recheck
python -m experiments.normal_comparison --seeds 50 --pareto-results results/pareto-recheck --out results/normal-recheck
python -m tools.report_normal --out results/normal-recheck --pareto-results results/pareto-recheck --brief reports/PROFESSOR_BRIEF_RECHECK.md
```

The existing results can be read without rerunning them. The Pareto cohort has
2,480 runs and the new matched normal reference has 200 runs. The large sweeps
use the binomial observation engine; separate Aer runs check circuit integration.
ML is a separate optional component and was disabled in this Pareto comparison.

For a controlled comparison with standalone fixed single-channel QKD, including
equal total pulse budgets, read
[the single-channel comparison](results/single-channel-comparison/REPORT.md).
Reproduce with `python -m experiments.single_channel_comparison --seeds 50`,
then `python -m tools.report_single_channel`. This uses new seeds and uniform
24 km links; its fixed baseline differs from the earlier hybrid comparator.

## Where things live

| Folder | Contents |
|---|---|
| `qkd_sdn/` | Simulation, monitoring, decision policies, Pareto and security code |
| `sdn/`, `linux/` | OpenFlow/Mininet/Ryu implementation and Linux setup |
| `experiments/`, `tools/` | Reproducible studies, reporting and validation commands |
| `tests/`, `notebooks/` | Software checks and the BB84 notebook |
| `docs/`, `reports/` | Technical explanations and readable reports |
| `results/` | Numerical evidence, plots and per-study reports |
| `environment/` | Historical Windows dependency snapshots |
| `archives/`, `dist/` | Local recovery backups and portable ZIP; ignored by Git |

The [complete PDF](reports/QKD_SDN_Complete_Report.pdf) and
[Word report](reports/QKD_SDN_Complete_Report.docx) are earlier snapshots. Use the
new briefing for the matched normal/Pareto comparison and the migration guide
for commands in older reports. Keep the folder structure: Python imports and
Git metadata depend on it.

## Scope and portability

This is simulation evidence. Ordinary OpenFlow switches block classical VLAN
traffic representing a wavelength; they do not block optical photons. The
monitor's output estimate is not an end-to-end composable finite-key proof.
Published-bound implementations and protocol demonstrations have their own
assumptions, described under `docs/`. Live Linux forwarding remains to be
verified on a Linux host; Windows unit tests do not establish it.

Build a portable source/results ZIP with `python -m tools.package_project`.
It excludes Windows runtimes, Git metadata, caches, secrets and local archives.
Copy the resulting `dist/qkd-sdn-linux-project.zip` to Linux and follow the guide.
