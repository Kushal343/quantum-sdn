"""CLI for calibration, synthetic experiments, and observable-only replay."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
from . import __version__
from .config import Config
from .calibration import Calibration, calibrate
from .scenarios import SCENARIOS, simulate
from .monitor import POLICIES, replay
from .telemetry import Telemetry
from .io import write_json,write_jsonl,read_jsonl
from .evaluation import run_metrics,summarize,paired_comparisons,write_csv
from .report import build_report,trace_figure

ROOT = Path(__file__).resolve().parents[1]


def manifest(cfg,kind,seeds):
    source_hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT/"qkd_monitor").glob("*.py"))}
    return {"schema_version":1,"kind":kind,"created_utc":datetime.now(timezone.utc).isoformat(),
            "seeds":seeds,"package_version":__version__,"python":sys.version,"platform":platform.platform(),
            "dependencies":{name:importlib.metadata.version(name) for name in ("numpy","scipy","matplotlib")},
            "config_fingerprint":cfg.fingerprint,"source_sha256":source_hashes,
            "security_claim":"No certified key generation or attack attribution; count monitoring only",
            "run_false_alarm_bound":cfg.alpha_run,"bound_scope":"One uncertainty-policy horizon, under documented calibration/count model assumptions"}


def experiment(args,cfg):
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    (out/"figures").mkdir(exist_ok=True);(out/"calibration").mkdir(exist_ok=True)
    seeds=list(range(args.seed,args.seed+args.seeds)) if args.command=="benchmark" else [args.seed]
    if not seeds or min(seeds)<0:
        raise ValueError("Require positive seed count and nonnegative seed")
    scenarios=args.scenarios if args.command=="benchmark" else [args.scenario]
    info=manifest(cfg,args.command,seeds)
    write_json(out/"config.json",cfg.to_dict())
    records=[]; representative=None
    for seed in seeds:
        calibration=calibrate(cfg,seed)
        calibration.save(out/"calibration"/f"seed_{seed}.json")
        for scenario in scenarios:
            rows,truth=simulate(cfg,scenario,seed)
            for policy in POLICIES:
                decisions=replay(cfg,calibration,rows,policy)
                records.append(run_metrics(cfg,scenario,seed,policy,decisions,truth))
                if seed==seeds[0] and scenario==scenarios[0] and policy=="uncertainty":
                    representative=(decisions,truth)
                if args.command=="demo":
                    write_jsonl(out/f"decisions_{policy}.jsonl",decisions)
            if args.command=="demo":
                write_jsonl(out/"telemetry.jsonl",[row.to_dict() for row in rows])
                write_jsonl(out/"truth_evaluation_only.jsonl",[asdict(row) for row in truth])
        print(f"Completed seed {seed}: {len(scenarios)} scenario(s), {len(POLICIES)} policies",flush=True)
    summary=summarize(records)
    write_csv(out/"run_metrics.csv",records);write_json(out/"summary.json",summary)
    write_json(out/"paired_comparisons.json",paired_comparisons(records))
    trace_path=None
    if representative:
        trace_path=out/"figures"/"representative_trace.png"
        trace_figure(cfg,*representative,trace_path)
    info["scenarios"]=scenarios
    info["calibration_sha256"]={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/"calibration").glob("*.json"))}
    write_json(out/"manifest.json",info)
    build_report(out,cfg,summary,info,trace_path)
    print(f"Report: {(out/'report.html').resolve()}")


def main(argv=None):
    parser=argparse.ArgumentParser(description="Fixed-configuration WDM-QKD count monitoring (no key certification)")
    parser.add_argument("--config",default=str(ROOT/"configs"/"default.json"))
    sub=parser.add_subparsers(dest="command",required=True)
    demo=sub.add_parser("demo",help="Single trace with raw telemetry and policy logs")
    demo.add_argument("--scenario",choices=SCENARIOS,default="local_background")
    demo.add_argument("--seed",type=int,default=42);demo.add_argument("--out",default="results/demo")
    bench=sub.add_parser("benchmark",help="Repeated paired synthetic experiments")
    bench.add_argument("--scenarios",nargs="+",choices=SCENARIOS,default=list(SCENARIOS))
    bench.add_argument("--seed",type=int,default=1000);bench.add_argument("--seeds",type=int,default=30)
    bench.add_argument("--out",default="results/benchmark")
    cal=sub.add_parser("calibrate",help="Generate independent synthetic calibration artifact")
    cal.add_argument("--seed",type=int,default=42);cal.add_argument("--out",required=True)
    rep=sub.add_parser("replay",help="Process JSONL observations without scenario truth")
    rep.add_argument("--telemetry",required=True);rep.add_argument("--calibration",required=True)
    rep.add_argument("--policy",choices=POLICIES,default="uncertainty");rep.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    try:
        cfg=Config.load(args.config)
        if args.command in ("demo","benchmark"):
            experiment(args,cfg)
        elif args.command=="calibrate":
            Path(args.out).parent.mkdir(parents=True,exist_ok=True)
            calibrate(cfg,args.seed).save(args.out)
            print(f"Calibration: {Path(args.out).resolve()}")
        else:
            calibration=Calibration.load(args.calibration,cfg)
            rows=[Telemetry.from_dict(data) for data in read_jsonl(args.telemetry)]
            if not rows:
                raise ValueError("No telemetry records supplied")
            decisions=replay(cfg,calibration,rows,args.policy)
            Path(args.out).parent.mkdir(parents=True,exist_ok=True)
            write_jsonl(args.out,decisions)
            print(f"Decisions: {Path(args.out).resolve()}")
    except (ValueError,TypeError,KeyError,OSError) as exc:
        parser.exit(2,f"Error: {exc}\n")


if __name__=="__main__":
    main()
