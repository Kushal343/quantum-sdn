# Mininet and OpenFlow SDN lab

This folder provides two OpenFlow 1.3 backends for the same two-switch, four-pair Mininet topology. **Ryu is now the default**: follow [the Linux deployment guide](../linux/README.md) to run its controller and local decision API. `ryu_app.py` handles OpenFlow sessions, `ryu_core.py` builds VLAN/isolation rules, and `ryu_client.py` carries acknowledged QKD decisions. The earlier `ovs-ofctl` backend remains available with `--controller ovs`; the commands below describe that backend.

```text
 a1 -- port 1                    port 1 -- b1    channel 1 / VLAN 101
 a2 -- port 2                    port 2 -- b2    channel 2 / VLAN 102
 a3 -- port 3 -- qkds1 == qkds2 -- port 3 -- b3 channel 3 / VLAN 103
 a4 -- port 4                    port 4 -- b4    channel 4 / VLAN 104
                    trunk port 10
```

The VLAN identifies classical traffic associated with a logical wavelength. **Ethernet packets are not quantum photons.** Mininet emulates the classical network; QKD measurements and wavelength physics remain simulated. This integration demonstrates QKD-informed traffic control, not physical optical switching.

## Files

| File | Purpose |
|---|---|
| `topology.py` | Builds eight Linux network-namespace hosts and two OpenFlow switches |
| `openflow.py` | Central flow-rule controller, VLAN forwarding, holds and latched isolation |
| `lab.py` | Owns network lifecycle, live packet self-test, interactive CLI and QKD monitoring loop |
| `plan.py` | Windows-compatible dry run that records commands without executing them |

Default rules permit only the matching host pairs. Each switch adds a channel VLAN at the host-facing ingress and removes it at the far endpoint. Unmatched traffic and host-injected VLAN frames drop. Channel-specific high-priority rules block both directions during a hold or isolation. Releasing a temporary hold removes only its block rules. Isolation stays latched for the lab lifetime.

`retune`, `verify`, `keep`, and `rollback` do not silently become network reroutes: they continue to control the simulated optical configuration. This topology provides one trunk, with no alternate route. New OpenFlow forwarding and blocking are the SDN actions implemented here.

## Windows status

Implementation validation completed: **61 project tests passed**, including five new OpenFlow-controller tests. The dry-run interception experiment ended with channels 1, 2 and 4 active and channel 3 isolated. No live-switch success is inferred from those tests.

This PC has no installed WSL environment, Mininet, or Open vSwitch. Live network tests therefore **have not been run here**. The Python controller tests and a QKD-to-OpenFlow dry run pass. They validate generated rules and state handling; they do not validate Linux packet forwarding.

Run the dry run from the project root in PowerShell:

```powershell
.\.runtime\python.exe -m sdn.plan
```

It writes `results/sdn/plan.json`, explicitly marked as a dry run. It currently plans isolation of channel 3 only after simulated interception. No real switch is contacted.

## Linux setup

Use a dedicated Ubuntu VM or Linux machine with Mininet and OVS support. WSL2 may require additional kernel/module configuration; the presence of WSL alone does not guarantee Mininet support. The [Mininet walkthrough](https://mininet.org/walkthrough/) describes the native Linux/VM environment. Switch commands follow the [Open vSwitch OpenFlow administration manual](https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.html).

Copy or clone the project into Linux. In its project root, run:

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch python3-venv iputils-ping
sudo service openvswitch-switch start

# System site packages exposes the distribution's Mininet Python module.
/usr/bin/python3 -m venv --system-site-packages .venv-sdn
.venv-sdn/bin/python -m pip install -r requirements.txt
```

No physical network interfaces are attached. Live execution requires root to create namespaces and virtual links. The runner refuses to replace existing experiment bridges. Run only one lab at a time.

## 1. Verify actual switching first

```bash
sudo .venv-sdn/bin/python -m sdn.lab --controller ovs --mode selftest
```

The self-test verifies:

1. All four intended host pairs can exchange ping packets.
2. A cross-channel pair cannot communicate, even with explicit endpoint routes/neighbours.
3. Holding channel 3 blocks its packets while leaving channels 1, 2 and 4 reachable.
4. Releasing the hold restores communication.
5. Isolation blocks channel 3 and remains latched after a continue request.

Failures raise an error. Success saves measurements and flow tables in `results/sdn/selftest.json`. The network is torn down on normal exit, exceptions and Ctrl+C.

## 2. Run QKD-controlled OpenFlow isolation

```bash
sudo .venv-sdn/bin/python -m sdn.lab --controller ovs --mode monitor --scenario intercept --steps 12 --verify
```

At each interval, the existing `qkd_sdn.controller.Controller` reads simulated telemetry. Its hold/isolation decisions are applied to the OVS switches, then all host pairs are probed with actual ICMP packets. `--verify` requires measured reachability to agree with the intended forwarding state. Results and flow tables are saved in `results/sdn/monitor.json`.

The default count engine is fast and labelled `binomial`. Use `--engine aer` for Qiskit circuit measurements. Detection is not guaranteed on every seed. A QKD monitoring interval is not a real-time service deadline; ping probes, simulator execution, and command overhead add wall-clock delay.

## 3. Inspect the network interactively

```bash
sudo .venv-sdn/bin/python -m sdn.lab --controller ovs --mode cli
```

Inside the Mininet prompt:

```text
net
a1 ping -c 3 10.1.0.2
a3 ping -c 3 10.3.0.2
sh ovs-ofctl -O OpenFlow13 dump-flows qkds1
sh ovs-ofctl -O OpenFlow13 dump-flows qkds2
exit
```

`pingall` is not expected to succeed: different channel subnets are intentionally isolated.

## Failure handling and limitations

Switch commands use argument arrays, timeouts and checked return codes. Software state is updated only after both switches acknowledge successful modifications. OVS commands internally wait on OpenFlow barriers; updates are **not atomic across switches**. If a command fails, the runner aborts and tears down the lab instead of reporting successful isolation. Packets already in flight are not revoked. Flow tables remain installed if the controller process alone stops, until topology cleanup removes the bridges.

The link is a 100 Mbit/s, 2 ms emulated trunk. Host pairs use `10.i.0.1/24` and `10.i.0.2/24` for channel i. These are lab settings, not calibrated optical measurements. There is no external TCP OpenFlow controller listener, REST service, network deployment, or claim that Mininet validates quantum security. A future remote controller adapter can replace the `ovs-ofctl` transport without changing the QKD decision logic.
