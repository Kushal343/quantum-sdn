"""Local command-line entry point; also works with the isolated test runtime."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))


def run_network(scenario, steps, seed, pulses, policy="adaptive", predictor=None, engine="aer"):
    from qkd_sdn.simulation import NetworkSimulator, conditions
    from qkd_sdn.controller import Controller
    from qkd_sdn.devices import SimulatedDevice
    sim, control = NetworkSimulator(seed, pulses, engine=engine), Controller(policy, predictor)
    devices = [SimulatedDevice() for _ in range(4)]
    rows = []
    for step in range(steps):
        telemetry = []
        for i in range(4):
            ch, eve, tap = conditions(scenario, step, wavelength=i)
            telemetry.append(sim.observe(ch, devices[i].config, eve, tap))
        decisions = control.decide(telemetry)
        for i, (t, decision) in enumerate(zip(telemetry, decisions)):
            devices[i].apply(control.states[i]["config"], control.states[i]["isolated"])
            blocked = devices[i].isolated or decision["action"] == "hold"
            # A previous interval's retune costs 25% of the following interval.
            previous = next((r for r in reversed(rows) if r["channel"] == f"lambda_{i+1}"), None)
            availability = 0.75 if previous and previous["action"] == "retune" else 1.0
            s = t["records"]["signal"]
            rows.append({"interval": step, "channel": f"lambda_{i+1}",
                         "config": t["config"].name, "next_config": control.states[i]["config"].name,
                         "sample_size": s["sifted"], "errors": s["errors"], "qber": t["qber"],
                         "skr_estimate": t["skr_estimate"],
                         "estimated_released_bits": 0 if blocked else t["skr_estimate"]*t["interval"]*availability,
                         **decision})
    import pandas as pd
    frame = pd.DataFrame(rows)
    return frame, {"scenario": scenario, "policy": policy, "seed": seed, "steps": steps, "engine": engine,
                   "pulses_per_wavelength_interval": pulses, "aer_shots": sim.engine.shots_executed,
                   "estimated_released_bits": float(frame.estimated_released_bits.sum()),
                   "isolation_events": int((frame.action == "isolate").sum()),
                   "retunes": int((frame.action == "retune").sum()),
                   "scope": "asymptotic model estimates, not actual secure keys; simulated controller"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["demo", "network", "train", "compare"], nargs="?", default="demo")
    parser.add_argument("--scenario", default="intercept", choices=["normal", "loss", "noise", "intercept", "weak_intercept", "tap", "shared_noise"])
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--qubits", type=int, default=12000)
    parser.add_argument("--pulses", type=int, default=250000)
    parser.add_argument("--attack-start", type=int, default=4)
    parser.add_argument("--attack-fraction", type=float, default=0.8)
    parser.add_argument("--ml", action="store_true", help="Train analytical surrogate and use it for candidate proposals")
    parser.add_argument("--out", type=Path, default=ROOT/"results"/"demo")
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("--steps must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    if args.mode == "demo":
        from qkd_sdn.bb84 import run_wdm, aggregate_telemetry
        rows, truth = run_wdm(args.steps, args.qubits, args.attack_start, args.attack_fraction, seed=args.seed)
        frame = pd.DataFrame(rows)
        frame.to_csv(args.out/"telemetry.csv", index=False)
        pd.DataFrame(truth).to_csv(args.out/"ground_truth.csv", index=False)
        agg = aggregate_telemetry(frame)
        agg.to_csv(args.out/"aggregate.csv", index=False)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
        for name, group in frame.groupby("channel"):
            axes[0].plot(group.interval, group.qber, "o-", label=name)
        axes[1].plot(agg.interval, agg.qber, "o-", label="Weighted aggregate")
        for ax in axes:
            ax.axhline(0.11, color="red", linestyle="--", label="Illustrative 11% cap")
            ax.axvline(args.attack_start, color="gray", linestyle=":")
            ax.set(xlabel="Interval", ylabel="Sample QBER", ylim=(0, 0.35)); ax.legend(fontsize=8)
        axes[0].set_title("Four independent wavelengths")
        axes[1].set_title("Aggregate can hide a single-channel disturbance")
        fig.tight_layout(); fig.savefig(args.out/"wavelength_attack.png", dpi=160); plt.close(fig)
        print(frame.pivot(index="interval", columns="channel", values="qber").round(4).to_string())
    else:
        predictor = None
        if args.ml or args.mode == "train":
            from qkd_sdn.ml import train
            predictor, metrics = train(args.seed)
            (args.out/"ml_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
            print(json.dumps(metrics, indent=2))
        if args.mode != "train":
            policies = ["fixed", "aggregate", "per_wavelength", "adaptive"] if args.mode == "compare" else ["adaptive"]
            summaries = []
            for policy in policies:
                frame, summary = run_network(args.scenario, args.steps, args.seed, args.pulses, policy, predictor)
                frame.to_csv(args.out/f"{policy}_telemetry.csv", index=False)
                summaries.append(summary)
                print(json.dumps(summary, indent=2))
            (args.out/"summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(f"Saved results: {args.out.resolve()}")


if __name__ == "__main__":
    main()
