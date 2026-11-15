"""Run-level evaluation. Only this layer may join observations with scenario truth."""
from collections import defaultdict
import csv
import math
from pathlib import Path
import numpy as np
from scipy.stats import t
from .statistics import clopper_pearson


DETECTION_SCENARIOS = {"local_loss","local_background","gradual_drift","common_loss","passive_tap"}


def run_metrics(cfg,scenario,seed,policy,decisions,truth):
    if len(decisions) != len(truth):
        raise ValueError("Decision/truth length mismatch")
    event_channels = defaultdict(list)
    false_holds = false_raw = benign_held = target_held = inconclusive = 0
    withheld_counts = raw_targets = 0
    for decision,label in zip(decisions,truth):
        if (decision["window"],decision["wavelength"]) != (label.window,label.wavelength):
            raise ValueError("Decision/truth ordering mismatch")
        if label.target:
            event_channels[label.wavelength].append((decision,label))
            target_held += int(decision["held_during_window"])
            raw_targets += int(decision["anomalous"])
        else:
            false_holds += int(decision["action"] == "HOLD_OUTPUT")
            false_raw += int(decision["anomalous"])
            benign_held += int(decision["held_during_window"])
        inconclusive += int(decision["category"] in ("INCONCLUSIVE","OUT_OF_BUDGET"))
        withheld_counts += decision["signal_detections"]*int(decision["held_during_window"])
    delays, missed = [], 0
    eligible_events = len(event_channels) if scenario in DETECTION_SCENARIOS else 0
    if eligible_events:
        for events in event_channels.values():
            hits = [d["window"] for d,label in events if d["action"] == "HOLD_OUTPUT"]
            if hits:
                # Onset is a window start, decision occurs at a window end.
                delays.append((min(hits)+1-events[0][1].onset)*cfg.window_seconds)
            else:
                missed += 1
    observed = sum(d["signal_detections"] for d in decisions)
    return {
        "scenario":scenario,"seed":seed,"policy":policy,
        "false_hold_actions":false_holds,"any_false_hold":int(false_holds>0),
        "false_raw_alarm_windows":false_raw,"any_false_raw_alarm":int(false_raw>0),
        "benign_channel_windows_held":benign_held,"target_channel_windows_held":target_held,
        "inconclusive_channel_windows":inconclusive,"target_raw_alarm_windows":raw_targets,
        "eligible_events":eligible_events,"detected_events":len(delays),"missed_events":missed,
        "mean_detection_delay_seconds":float(np.mean(delays)) if delays else None,
        "hold_actions":sum(d["action"]=="HOLD_OUTPUT" for d in decisions),
        "restore_actions":sum(d["action"]=="RESTORE_OUTPUT" for d in decisions),
        "signal_detections":observed,"signal_detections_while_held":withheld_counts,
        "signal_detection_fraction_while_held":withheld_counts/observed if observed else 0.0,
        "mean_controller_microseconds":float(np.mean([d["controller_microseconds"] for d in decisions])),
        "p95_controller_microseconds":float(np.quantile([d["controller_microseconds"] for d in decisions],0.95)),
    }


def mean_interval(values):
    values = [float(x) for x in values if x is not None]
    if not values:
        return {"n":0,"mean":None,"lower":None,"upper":None}
    mean = float(np.mean(values))
    if len(values) < 2:
        return {"n":len(values),"mean":mean,"lower":None,"upper":None}
    half = float(t.ppf(.975,len(values)-1)*np.std(values,ddof=1)/math.sqrt(len(values)))
    return {"n":len(values),"mean":mean,"lower":mean-half,"upper":mean+half}


def summarize(records):
    groups = defaultdict(list)
    for row in records:
        groups[(row["scenario"],row["policy"])].append(row)
    summary = []
    for (scenario,policy),rows in sorted(groups.items()):
        hits = sum(row["any_false_hold"] for row in rows)
        ci = clopper_pearson(hits,len(rows))
        alarms = sum(row["any_false_raw_alarm"] for row in rows)
        alarm_ci = clopper_pearson(alarms,len(rows))
        events = sum(row["eligible_events"] for row in rows)
        summary.append({
            "scenario":scenario,"policy":policy,"runs":len(rows),
            "false_hold_run_fraction":hits/len(rows),"false_hold_run_ci":ci,
            "false_raw_alarm_run_fraction":alarms/len(rows),"false_raw_alarm_run_ci":alarm_ci,
            "detected_events":sum(row["detected_events"] for row in rows),"eligible_events":events,
            "event_detection_fraction":sum(row["detected_events"] for row in rows)/events if events else None,
            "benign_windows_held":mean_interval([r["benign_channel_windows_held"] for r in rows]),
            "signal_detection_fraction_while_held":mean_interval([r["signal_detection_fraction_while_held"] for r in rows]),
            "delay_among_detected_runs":mean_interval([r["mean_detection_delay_seconds"] for r in rows]),
            "inconclusive_windows":mean_interval([r["inconclusive_channel_windows"] for r in rows]),
            "controller_microseconds":mean_interval([r["mean_controller_microseconds"] for r in rows]),
        })
    return summary


def paired_comparisons(records):
    groups = defaultdict(dict)
    for row in records:
        groups[(row["scenario"],row["seed"])][row["policy"]] = row
    differences = defaultdict(list)
    for (scenario,seed), policies in groups.items():
        if "uncertainty" not in policies:
            continue
        for reference in ("fixed_threshold","pointwise"):
            if reference not in policies:
                continue
            for metric in ("false_hold_actions","false_raw_alarm_windows","benign_channel_windows_held","signal_detection_fraction_while_held"):
                if metric in policies["uncertainty"] and metric in policies[reference]:
                    differences[(scenario,reference,metric)].append(policies["uncertainty"][metric]-policies[reference][metric])
    return [{"scenario":scenario,"reference":reference,"metric":metric,"difference":f"uncertainty minus {reference}",**mean_interval(values)} for (scenario,reference,metric),values in sorted(differences.items())]


def write_csv(path,records):
    if not records:
        return
    with Path(path).open("w",newline="",encoding="utf-8") as handle:
        writer = csv.DictWriter(handle,fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
