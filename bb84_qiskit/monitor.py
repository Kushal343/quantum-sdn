"""Connect Qiskit BB84 basis-sifted observations to the existing monitor."""

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "uncertainty_monitoring"))

from qkd_monitor.calibration import Calibration
from qkd_monitor.config import Config
from qkd_monitor.evaluation import paired_comparisons, run_metrics, summarize, write_csv
from qkd_monitor.io import write_json, write_jsonl
from qkd_monitor.monitor import POLICIES, replay
from qkd_monitor.scenarios import SCENARIOS
try:
    from .bridge import sift_counts, qiskit_calibration, qiskit_trace
    from .integration import Integration, run_policy
except ImportError:
    from bridge import sift_counts, qiskit_calibration, qiskit_trace
    from integration import Integration, run_policy


def experiment(cfg, scenario, seed, output, *, integration=None, policies=POLICIES):
    integration = integration or Integration()
    if not policies or len(set(policies)) != len(policies):
        raise ValueError("Select at least one unique policy")
    if any(policy not in integration.policy_names for policy in policies):
        raise ValueError("Selected policy is unavailable in this integration")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose an empty output directory to keep run provenance clear")
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "config.json", cfg.to_dict())
    incomplete = output / ".incomplete"
    incomplete.write_text("Run is in progress or failed before completion.\n", encoding="utf-8")
    calibration, calibration_audit = qiskit_calibration(
        cfg, seed, integration.count_adapter, integration.calibration_source)
    calibration.save(output / "calibration.json")
    # Validate that the regular monitoring loader accepts the bridge artifact.
    calibration = Calibration.load(output / "calibration.json", cfg)
    observations, truth, audit = qiskit_trace(
        cfg, scenario, seed, integration.count_adapter, integration.observation_source)
    write_jsonl(output / "telemetry.jsonl", [r.to_dict() for r in observations])
    write_jsonl(output / "circuit_audit.jsonl", audit)
    write_jsonl(output / "calibration_circuit_audit.jsonl", calibration_audit)
    write_jsonl(output / "truth_evaluation_only.jsonl", [asdict(r) for r in truth])
    metrics = []
    for policy in policies:
        decisions = run_policy(cfg, calibration, observations, policy,
                               integration.policy_factory, integration.decision_sink)
        write_jsonl(output / f"decisions_{policy}.jsonl", decisions)
        metric = run_metrics(cfg, scenario, seed, policy, decisions, truth)
        metrics.append(metric)
        print(f"{policy}: holds={metric['hold_actions']}, "
              f"restores={metric['restore_actions']}, "
              f"false holds={metric['false_hold_actions']}, "
              f"delay={metric['mean_detection_delay_seconds']}")
    write_csv(output / "run_metrics.csv", metrics)
    write_json(output / "summary.json", summarize(metrics))
    write_json(output / "paired_comparisons.json", paired_comparisons(metrics))
    source_files = list((ROOT / "uncertainty_monitoring" / "qkd_monitor").glob("*.py"))
    source_files += list(Path(__file__).parent.glob("*.py"))
    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in source_files}
    write_json(output / "manifest.json", {
        "schema_version": 1, "scenario": scenario, "seed": seed,
        "model": integration.model_description,
        "count_definition": "emitted pulses; basis-matched detections and errors",
        "backend": integration.backend_label, "config_fingerprint": cfg.fingerprint,
        "integration": integration.name, "policies": list(policies),
        "versions": {p: importlib.metadata.version(p) for p in ("qiskit", "numpy", "scipy")},
        "source_sha256": source_hashes,
    })
    write_report(output, cfg, scenario, metrics, integration)
    incomplete.unlink()
    return metrics


def write_report(output, cfg, scenario, metrics, integration):
    lines = [
        "# Qiskit BB84 and uncertainty monitoring",
        "",
        f"Scenario `{scenario}`, {cfg.windows} windows and {cfg.channels} channels.",
        "",
        f"Integration {integration.name}. Backend {integration.backend_label}.",
        f"Model {integration.model_description}.",
        "",
        "Counts reflect basis-matched BB84 detections per emitted pulse. Python "
        "models optical losses and disturbances, and Qiskit executes preparation, "
        "Pauli Y channel operations and measurement. Calibration follows the same "
        "pipeline using independent random streams.",
        "",
        "| Policy | Holds | Restores | False holds | Detected events | Delay in seconds |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in metrics:
        lines.append(f"| {r['policy']} | {r['hold_actions']} | {r['restore_actions']} | "
                     f"{r['false_hold_actions']} | {r['detected_events']}/"
                     f"{r['eligible_events']} | {r['mean_detection_delay_seconds']} |")
    lines += [
        "",
        "Delays describe simulated time at the end of a window. Policies see the "
        "same observations and cannot access scenario truth. These are "
        "single-seed integration results. The Pauli Y channel is a simplified "
        "representation of the optical model's erroneous detections. The "
        "experiment counts sifted bits and reports QBER rather than secure key rate.",
        "",
        "The full measurement record is in circuit_audit.jsonl. Reconstruct "
        "monitor decisions from telemetry.jsonl and calibration.json without "
        "reading the truth file.",
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="local_background")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--config", type=Path,
                        default=Path(__file__).with_name("monitor_config.json"))
    parser.add_argument("--out", type=Path, default=Path("results/connected_demo"))
    parser.add_argument("--policies", nargs="+", choices=POLICIES, default=list(POLICIES))
    parser.add_argument("--windows", type=int)
    parser.add_argument("--pulses", type=int)
    parser.add_argument("--calibration-pulses", type=int)
    parser.add_argument("--event-start", type=int)
    parser.add_argument("--event-end", type=int)
    args = parser.parse_args()
    try:
        cfg = Config.load(args.config)
        overrides = {
            "windows": args.windows, "pulses_per_window": args.pulses,
            "calibration_pulses_per_context": args.calibration_pulses,
            "event_start": args.event_start, "event_end": args.event_end,
        }
        cfg = replace(cfg, **{key: value for key, value in overrides.items() if value is not None})
        cfg.validate()
        if args.seed < 0:
            raise ValueError("Seed must be nonnegative")
        if cfg.config_version != "qiskit-sifted-v1":
            raise ValueError("The bridge requires the qiskit-sifted-v1 count contract")
        experiment(cfg, args.scenario, args.seed, args.out, policies=args.policies)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
