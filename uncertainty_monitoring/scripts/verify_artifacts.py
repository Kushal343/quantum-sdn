"""Check delivered provenance, calibration consistency and observable-only replay.

This checks accidental inconsistency, not authenticated provenance against a
malicious actor. It makes no hardware or cryptographic-security assertion.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qkd_monitor.config import Config
from qkd_monitor.calibration import Calibration
from qkd_monitor.monitor import POLICIES,replay
from qkd_monitor.telemetry import Telemetry
from qkd_monitor.io import read_jsonl


def check(directory):
    cfg=Config.load(directory/"config.json")
    manifest=json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    if cfg.fingerprint!=manifest["config_fingerprint"]:
        raise ValueError("Configuration fingerprint mismatch")
    for relative,digest in manifest["source_sha256"].items():
        path=(ROOT/relative).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError(f"Source provenance mismatch: {relative}")
    for relative,digest in manifest["calibration_sha256"].items():
        path=(directory/relative).resolve()
        if not path.is_relative_to(directory) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError(f"Calibration hash mismatch: {relative}")
        Calibration.load(path,cfg)
    with (directory/"run_metrics.csv").open(encoding="utf-8",newline="") as handle:
        metrics=list(csv.DictReader(handle))
    expected=len(manifest["seeds"])*len(manifest["scenarios"])*len(POLICIES)
    if len(metrics)!=expected:
        raise ValueError(f"Metrics cardinality mismatch: expected {expected}, got {len(metrics)}")
    keys={(int(r["seed"]),r["scenario"],r["policy"]) for r in metrics}
    expected_keys={(s,c,p) for s in manifest["seeds"] for c in manifest["scenarios"] for p in POLICIES}
    if keys!=expected_keys:
        raise ValueError("Missing or duplicated scenario/seed/policy rows")
    for file in ("summary.json","paired_comparisons.json","report.html","figures/comparison.png","figures/comparison.pdf"):
        if not (directory/file).is_file():
            raise ValueError(f"Missing artifact: {file}")
    if (directory/"telemetry.jsonl").exists():
        rows=[Telemetry.from_dict(r) for r in read_jsonl(directory/"telemetry.jsonl")]
        calibration=Calibration.load(directory/"calibration"/f'seed_{manifest["seeds"][0]}.json',cfg)
        for policy in POLICIES:
            expected_decisions=replay(cfg,calibration,rows,policy)
            saved=list(read_jsonl(directory/f"decisions_{policy}.jsonl"))
            def normalize(decisions):
                return [{k:v for k,v in r.items() if k!="controller_microseconds"} for r in decisions]
            if normalize(expected_decisions)!=normalize(saved):
                raise ValueError(f"Replay mismatch: {policy}")
    return len(metrics)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories",nargs="*",default=["results/demo","results/power_demo","results/benchmark","results/benign_audit"])
    args=parser.parse_args()
    total=0
    for value in args.directories:
        directory=Path(value).resolve()
        count=check(directory)
        total+=count
        print(f"PASS {directory.name}: {count} policy-run rows; source/calibration consistency and available replay checks")
    print(f"PASS total {total} policy-run rows")


if __name__=="__main__":
    main()
