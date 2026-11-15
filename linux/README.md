# Reproducing the project on Linux

Use an Ubuntu 24.04 Linux VM for the live Mininet/Ryu lab. Allocate at least
2 CPU cores and 4 GB RAM; larger Aer runs benefit from more memory. Native
Windows runs the simulation and unit tests. The commands below run **inside
Linux**, from the organized project root. No change to Windows virtualization
or reboot is made by these scripts.

## 1. Transfer the current project

Use the freshly built `dist/qkd-sdn-linux-project.zip`: it contains local changes
that may not yet be on GitHub. Copy it to the VM's `~/Downloads` folder, then:

```bash
sudo apt-get update
sudo apt-get install -y unzip python3-venv python3-pip git
mkdir -p ~/qkd-lab
unzip ~/Downloads/qkd-sdn-linux-project.zip -d ~/qkd-lab
cd ~/qkd-lab/qkd-sdn
```

Extract into a new directory if that destination already contains a project.
The bundle excludes `.git`, the Windows `.runtime`, caches and local archives.
After the new files have been committed and pushed, cloning the repository is
another option:

```bash
git clone https://github.com/Kushal343/quantum-sdn.git
cd quantum-sdn
```

## 2. Reproduce simulation results first

This step does not require Mininet or Docker. Python 3.11 or newer is required;
Ubuntu 24.04 provides the intended Python 3.12 host environment.

```bash
python3 -m venv --system-site-packages .venv-linux
.venv-linux/bin/python -m pip install -r requirements.txt
.venv-linux/bin/python -m pytest tests -q
.venv-linux/bin/python -m pip freeze > environment/linux-installed.txt
.venv-linux/bin/python --version
```

The current Windows check passes 81 tests. Record the Linux output separately;
no Linux test pass is claimed by the Windows result. Requirements use bounded
version ranges, so preserve `linux-installed.txt` when archiving a new run.
The snapshots under `environment/requirements-windows-*.txt` describe Windows;
they are not Linux lock files.

Run a quick simulation:

```bash
.venv-linux/bin/python run.py network --policy pareto --engine binomial \
  --scenario intercept --steps 18 --pulses 100000 \
  --out results/linux-intercept
```

Inspect `results/linux-intercept/summary.json` and `pareto_telemetry.csv`.
In the CSV, follow `channel`, `interval`, `qber`, `action`, `reason`, `config`
and `next_config`. A hold blocks estimated output temporarily; isolation
permanently blocks that channel for the run. Output bits are asymptotic model
estimates, not distilled secure keys.

To run circuit observations, replace `--engine binomial` with `--engine aer`.
The binomial engine samples the independent symmetric model's count law; it
does not execute circuits. For the introductory dashboard:

```bash
.venv-linux/bin/python -m streamlit run dashboard.py
```

## 3. Reproduce the reported studies

Use fresh output directories. These are full repeated-seed sweeps, not quick
demonstrations. Runtime depends on the machine.

```bash
# Original combined-policy study: 2,160 runs.
.venv-linux/bin/python -m experiments.hybrid_experiments --seeds 20 --out results/hybrid-recheck
.venv-linux/bin/python -m tools.report_hybrid --out results/hybrid-recheck

# Pareto follow-up: 2,480 runs, including 50 seeds per alignment/policy case.
.venv-linux/bin/python -m experiments.pareto_experiments --out results/pareto-recheck
.venv-linux/bin/python -m tools.report_pareto --out results/pareto-recheck

# Healthy reference: 200 runs matched to the alignment cohort above.
.venv-linux/bin/python -m experiments.normal_comparison --seeds 50 \
  --pareto-results results/pareto-recheck --out results/normal-recheck
.venv-linux/bin/python -m tools.report_normal --out results/normal-recheck \
  --pareto-results results/pareto-recheck --brief reports/PROFESSOR_BRIEF_RECHECK.md
```

Start interpretation with the generated `PROFESSOR_BRIEF_RECHECK.md`,
`normal-recheck/comparison.csv`, `normal_vs_degradation.png`, and the Pareto
report. `runs.csv` contains seed-level outcomes; `summary.csv` contains means.
Compare the same scenario, pulse budget, duration and seed cohort. Expect the
same qualitative findings; different dependency versions or numerical backends
can affect exact floating-point results, and the timing benchmark is specific
to the machine. ML is disabled in this Pareto study.

The notebook is `notebooks/bb84_wdm_qiskit.ipynb`. Earlier standalone script
commands have moved to `python -m experiments.NAME` and `python -m tools.NAME`;
see `docs/COMMAND_MIGRATION.md`.

## 4. Install the live SDN lab

Run only in the dedicated Ubuntu lab VM. This installs Mininet/Open vSwitch
and Docker, starts their services, installs host Python requirements and builds
the Ryu image. It requires network access and sudo.

```bash
bash linux/setup.sh
```

The host environment uses `--system-site-packages` so it can import Ubuntu's
Mininet package. Ryu uses a separate Python 3.10 container; the host's Qiskit
environment remains separate. This workflow targets Linux host networking,
not Docker Desktop on native Windows.

## 5. Terminal 1: start Ryu

From the project root:

```bash
export QKD_SDN_TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
# Copy this value to terminal 2; never commit it or put it in a report.
printf '%s\n' "$QKD_SDN_TOKEN"
sudo docker run --rm --name qkd-ryu --network host \
  -e QKD_SDN_TOKEN="$QKD_SDN_TOKEN" qkd-ryu:local
```

Ryu listens on loopback: OpenFlow TCP 6653 and decision API TCP 8080. The bearer
token authenticates local API calls. This is a local lab boundary, not a
distributed production authentication protocol or an ETSI QKD 015 implementation.

## 6. Terminal 2: verify forwarding and isolation

From the same project root:

```bash
export QKD_SDN_TOKEN='paste-the-same-token-from-terminal-1'
sudo env QKD_SDN_TOKEN="$QKD_SDN_TOKEN" .venv-linux/bin/python -m sdn.lab \
  --controller ryu --mode selftest --out results/sdn-ryu
```

The self-test checks ICMP forwarding for all four pairs, rejects cross-wavelength
traffic, holds pair 3, restores a temporary hold and verifies that permanent
isolation cannot be cleared by a continue command. It writes `selftest.json`.
A failed check aborts and tears down the topology.

Restart Ryu after the self-test: Ctrl+C in terminal 1, then repeat its Docker
command using the same token. This clears the deliberately latched self-test
isolation before the next independent experiment. Then in terminal 2:

```bash
sudo env QKD_SDN_TOKEN="$QKD_SDN_TOKEN" .venv-linux/bin/python -m sdn.lab \
  --controller ryu --mode monitor --policy pareto --scenario intercept \
  --steps 18 --verify --out results/sdn-ryu-intercept
```

Repeat with `--scenario normal`, `raman`, `fwm`, `crosstalk`, `misalignment`,
`transient`, `model_mismatch` or `correlated`. Restart Ryu between independent
experiments. `--verify` compares actual pair reachability with acknowledged
forwarding state after every decision. OpenFlow barriers acknowledge processing
on both switches; they do not make an update atomic across switches. ICMP checks
separately establish packet forwarding. Archive each new output directory.

## What the switches represent

```text
a1--port1                        port1--b1  VLAN 101 / lambda_1
a2--port2--qkds1--port10--qkds2--port2--b2  VLAN 102 / lambda_2
a3--port3                        port3--b3  VLAN 103 / lambda_3
a4--port4                        port4--b4  VLAN 104 / lambda_4
                 Ryu OpenFlow 1.3
                         ^
                 local decision API
                         ^
              calibrated QKD controller
```

VLANs carry classical application traffic associated with each simulated QKD
wavelength. Ordinary Ethernet switches cannot block optical photons. Diagnostic
telemetry remains available outside the blocked application VLAN so the monitor
can assess recovery. The topology has one trunk and no alternate route; optical
switching, wavelength reassignment and rerouting are not demonstrated.

## Troubleshooting and validation status

- `ModuleNotFoundError: mininet`: run the setup script and use its
  `.venv-linux/bin/python`, created with `--system-site-packages`.
- Controller/API connection refused: check terminal 1 and the Docker build/logs.
  Token rejection: use exactly the same token in both terminals.
- Existing `qkds1/qkds2` bridges: the launcher refuses to overwrite another lab.
  After an interrupted experiment, inspect the VM before using `sudo mn -c`;
  it cleans other Mininet experiments too. Run one lab at a time.
- A new experiment starts isolated: restart Ryu between independent runs.
- Older script paths fail: use `docs/COMMAND_MIGRATION.md`.

Ryu's official repository states it is not currently maintained. The requested
Ryu controller is isolated at a fixed official source revision with pinned
direct dependencies; build-time imports check compatibility. The base image
and some transitive dependencies are not pinned by digest/version, so this is
not a fully locked environment. Preserve the built image and dependency lists
for archival replication.

Windows tests cover protocol logic, generated OpenFlow messages and failure
handling. Docker build/startup and live Linux packet tests remain unexecuted on
this Windows machine. The GitHub Actions workflow is provided but must be pushed
and run before claiming a passing Linux integration result.

Official references: [Mininet walkthrough](https://mininet.org/walkthrough/),
[Ryu REST integration](https://book.ryu-sdn.org/en/html/rest_api.html),
[OpenFlow 1.3 API](https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html),
[Ryu project status](https://github.com/faucetsdn/ryu).
