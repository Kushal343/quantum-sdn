# Dependency records

`requirements-windows-original.txt` and `requirements-windows-validated.txt`
are historical dependency snapshots from this Windows project. They were
renamed from the earlier root-level lock/validated files during organization.
They do not specify a portable Linux environment.

Use the root `requirements.txt` to install the simulation dependencies, then
record the actual Linux environment:

```bash
.venv-linux/bin/python -m pip freeze > environment/linux-installed.txt
.venv-linux/bin/python --version
```

Ryu has a separate image and requirements under `../linux/`. Follow that
folder's guide rather than installing Ryu into the simulation environment.
