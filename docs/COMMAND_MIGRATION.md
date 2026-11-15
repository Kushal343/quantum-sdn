# Commands after organization

All commands below run from the project root using its Python environment.
The main `run.py`, dashboard and SDN module commands remain unchanged.

| Earlier script | Current command |
|---|---|
| `pareto_experiments.py` | `python -m experiments.pareto_experiments` |
| `hybrid_experiments.py` | `python -m experiments.hybrid_experiments` |
| `advanced_experiments.py` | `python -m experiments.advanced_experiments` |
| `evaluate.py` | `python -m experiments.evaluate` |
| `sensitivity.py` | `python -m experiments.sensitivity` |
| `protocol_demo.py` | `python -m experiments.protocol_demo` |
| `distributed_demo.py` | `python -m experiments.distributed_demo` |
| `postprocess_demo.py` | `python -m experiments.postprocess_demo` |
| `decoy_finite_demo.py` | `python -m experiments.decoy_finite_demo` |
| `report_pareto.py` | `python -m tools.report_pareto` |
| `report_hybrid.py` | `python -m tools.report_hybrid` |
| `report_validation.py` | `python -m tools.report_validation` |
| `summarize_sweep.py` | `python -m tools.summarize_sweep` |
| `validate_protocol.py` | `python -m tools.validate_protocol` |
| `validate_distributed.py` | `python -m tools.validate_distributed` |
| `validate_notebook.py` | `python -m tools.validate_notebook` |
| `package_project.py` | `python -m tools.package_project` |

On this Windows machine, replace `python` with `.\.runtime\python.exe`.
On Linux use `.venv-linux/bin/python`. Arguments such as `--out` are unchanged.
The notebook is now `notebooks/bb84_wdm_qiskit.ipynb`.

The matched normal reference is new:

```bash
python -m experiments.normal_comparison --seeds 50
python -m tools.report_normal
```

Preserve earlier results by choosing a new output directory for a rerun.
Security/protocol demonstration validators use their existing fixed results
directories; running them intentionally refreshes those demonstration records.
