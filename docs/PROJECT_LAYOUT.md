# Project layout

The runnable folder structure has been restored and organized. Python modules
and Git metadata must remain in their folders. Flattening them breaks imports,
dependency loading and Git commands.

| Location | Purpose |
|---|---|
| `run.py` | Main demonstration, network, ML training and policy-comparison CLI |
| `dashboard.py` | Interactive introductory BB84 dashboard |
| `qkd_sdn/` | Quantum simulation, physics, monitoring, policies, Pareto and security code |
| `sdn/` | Mininet topology, Ryu application, OpenFlow rules and client |
| `experiments/` | Reproducible sweeps, protocol demonstrations and normal reference |
| `tools/` | Results reports, validators and portable project packaging |
| `tests/` | Software checks |
| `notebooks/` | Self-contained BB84 notebook |
| `docs/` | Method, security scope, research notes and migration guide |
| `reports/` | Human-readable reports and professor briefing |
| `results/` | Preserved numerical evidence; see its index first |
| `linux/` | Linux setup, isolated Ryu image and reproduction instructions |
| `environment/` | Historical Windows dependency snapshots |
| `archives/` | Ignored local backups and installers; never needed for a Linux installation |
| `dist/` | Newly built portable ZIP; ignored by Git |
| `.runtime/` | Existing local Windows Python installation; ignored by Git |

Run commands from the project root. Experiments and tools now use module syntax:

```powershell
.\.runtime\python.exe -m experiments.pareto_experiments --out results/pareto-recheck
.\.runtime\python.exe -m tools.report_pareto --out results/pareto-recheck
```

Earlier report snapshots contain commands such as `python pareto_experiments.py`.
Use `python -m experiments.pareto_experiments` in the organized project. The
underlying experiment algorithm and saved evidence were not changed by the move.
The new normal-reference experiment adds evidence in its own results folder.
