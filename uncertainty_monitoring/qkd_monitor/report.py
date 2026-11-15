"""Standalone offline HTML report and publication-exportable PNG/PDF figures."""
import base64
import html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {"passive":"#738399","fixed_threshold":"#ce7040","pointwise":"#8060ad","uncertainty":"#147d83"}


def _save(fig,path):
    fig.savefig(path,dpi=160,bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"),bbox_inches="tight")
    plt.close(fig)


def trace_figure(cfg,decisions,truth,path):
    fig,axes = plt.subplots(cfg.channels,2,figsize=(12,2.6*cfg.channels),sharex=True,squeeze=False)
    for channel in range(cfg.channels):
        rows = [d for d in decisions if d["wavelength"]==channel]
        x = np.array([d["time_seconds"] for d in rows])
        qber = np.array([np.nan if d["signal_qber"] is None else d["signal_qber"]*100 for d in rows])
        lower = np.array([np.nan if d["qber_ci_lower"] is None else d["qber_ci_lower"]*100 for d in rows])
        upper = np.array([np.nan if d["qber_ci_upper"] is None else d["qber_ci_upper"]*100 for d in rows])
        axes[channel,0].plot(x,qber,color=COLORS["uncertainty"],lw=1.2)
        axes[channel,0].fill_between(x,lower,upper,alpha=.18,color=COLORS["uncertainty"])
        axes[channel,0].set_ylabel(f"Channel {channel+1}\nQBER (%)")
        gain = [np.nan if d["signal_gain"] is None else d["signal_gain"] for d in rows]
        axes[channel,1].plot(x,gain,color="#354a68",lw=1.2)
        axes[channel,1].set_ylabel("Signal gain")
        for axis in axes[channel]:
            ymin,ymax=axis.get_ylim()
            for d in rows:
                if d["held_during_window"]:
                    axis.axvspan(d["time_seconds"]-cfg.window_seconds,d["time_seconds"],color="#cd5b50",alpha=.16,lw=0)
                elif d["category"]=="INCONCLUSIVE":
                    axis.axvspan(d["time_seconds"]-cfg.window_seconds,d["time_seconds"],color="#d3a43b",alpha=.2,lw=0)
            axis.axvline(cfg.event_start*cfg.window_seconds,color="#888",ls="--",lw=.7)
            axis.axvline(cfg.event_end*cfg.window_seconds,color="#888",ls="--",lw=.7)
            axis.grid(alpha=.15); axis.spines[["top","right"]].set_visible(False)
    axes[0,0].set_title("Observed signal QBER with descriptive 95% Wilson intervals")
    axes[0,1].set_title("Observed signal detection probability")
    axes[-1,0].set_xlabel("Elapsed seconds"); axes[-1,1].set_xlabel("Elapsed seconds")
    fig.suptitle("Fixed configuration | uncertainty-aware monitor\nRed: output-hold advisory active; amber: inconclusive",fontsize=13)
    fig.tight_layout(rect=(0,0,1,.95)); _save(fig,path)


def comparison_figure(summary,path):
    scenarios = sorted(set(r["scenario"] for r in summary))
    fig,axes=plt.subplots(2,1,figsize=(max(10,len(scenarios)*1.1),9),sharex=True)
    for j,policy in enumerate(("passive","fixed_threshold","pointwise","uncertainty")):
        rows = {r["scenario"]:r for r in summary if r["policy"]==policy}
        x=np.arange(len(scenarios))+(j-1.5)*.20
        for axis,metric in zip(axes,("benign_windows_held","signal_detection_fraction_while_held")):
            means=[rows[s][metric]["mean"] for s in scenarios]
            errors=[max(0,(rows[s][metric]["upper"] or rows[s][metric]["mean"])-rows[s][metric]["mean"]) for s in scenarios]
            axis.bar(x,means,.19,yerr=errors,label=policy,color=COLORS[policy],capsize=2)
            axis.spines[["top","right"]].set_visible(False);axis.grid(axis="y",alpha=.15)
    axes[0].set_ylabel("Benign channel-windows held\nIncludes recovery overhead")
    axes[1].set_ylabel("Fraction of observed signal detections\noccurring during advisory hold")
    axes[0].legend(frameon=False,ncol=4)
    axes[1].set_xticks(np.arange(len(scenarios)),[s.replace("_","\n") for s in scenarios],fontsize=9)
    fig.suptitle("Matched telemetry across policies | run-level mean and 95% t intervals\nDetection counts are not secret keys",fontsize=13)
    fig.tight_layout(rect=(0,0,1,.93)); _save(fig,path)


def _image(path):
    return '<img alt="Experiment figure" src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'">'


def build_report(out,cfg,summary,manifest,trace_path=None):
    rows=[]
    for r in summary:
        delay=r["delay_among_detected_runs"]["mean"]
        detection = "N/A" if r["event_detection_fraction"] is None else f'{r["event_detection_fraction"]:.1%} ({r["detected_events"]}/{r["eligible_events"]})'
        rows.append("<tr>"+"".join(f"<td>{html.escape(str(v))}</td>" for v in (
            r["scenario"],r["policy"],r["runs"],
            f'{r["false_hold_run_fraction"]:.1%} [{r["false_hold_run_ci"][0]:.1%}, {r["false_hold_run_ci"][1]:.1%}]',
            f'{r["false_raw_alarm_run_fraction"]:.1%}',
            detection, "N/A" if delay is None else f"{delay:.2f}",
            f'{r["benign_windows_held"]["mean"]:.2f}',f'{r["inconclusive_windows"]["mean"]:.2f}'
        ))+"</tr>")
    figure=out/"figures"/"comparison.png"
    comparison_figure(summary,figure)
    trace_html = "" if trace_path is None else "<h2>Representative trace</h2>"+_image(trace_path)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WDM-QKD monitoring experiment</title><style>
body{font:16px/1.6 system-ui,sans-serif;color:#203044;background:#f3f6f8;margin:0}main{max-width:1250px;margin:auto;padding:48px 26px}h1{font-size:36px;line-height:1.2;max-width:900px}h2{margin-top:38px}p{max-width:950px}.eyebrow{color:#147d83;font-weight:700;letter-spacing:.1em}.scope{border-left:4px solid #147d83;padding:12px 20px;background:white}.metrics{display:flex;gap:36px;flex-wrap:wrap;padding:20px 0}.metrics strong{display:block;font-size:26px}img{width:100%;background:white;margin:15px 0}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;background:white}th,td{padding:10px;text-align:left;border-bottom:1px solid #dce3e8}th{background:#203044;color:white}code{overflow-wrap:anywhere}footer{margin-top:40px;color:#617080}a{color:#147d83}</style><main>
<div class="eyebrow">REPRODUCIBLE RESEARCH PROTOTYPE · STAGE P2</div>
<h1>Uncertainty-aware monitoring with fixed QKD configuration</h1>
<p class="scope">Synthetic count telemetry. Decisions are advisory output holds, not confirmed attacks. No finite-key security engine or certified secret-key output is included. Every policy sees identical observations; configuration is unchanged throughout.</p>
'''
    page+=f'<div class="metrics"><div><strong>{cfg.channels}</strong>Quantum wavelengths</div><div><strong>{cfg.windows}</strong>Windows per run</div><div><strong>{cfg.alpha_run:.1%}</strong>Conditional model-based run alarm budget</div><div><strong>{cfg.alpha_test:.3g}</strong>Per-feature test level</div></div>'
    page+='<h2>Interpretation</h2><p>The uncertainty policy tests detection gain and error gain for all three intensities against independently calibrated binomial rate intervals. Calibration uncertainty and all predeclared tests share the run budget. The bound requires stationary independent count trials within each supported context and correct telemetry. It is not a cryptographic security probability.</p>'
    page+='<p>Fixed thresholds are transparent engineering defaults, not a baseline matched for false-alarm rate or sensitivity. The pointwise ablation uses the same contexts and six count features, with plug-in calibration rates and per-window correction. It has no claimed whole-run error guarantee. Zero holds can also mean missed events: inspect detection and latency together. Benign windows held include recovery after genuine events. Event-detection percentages apply only to sustained unexplained physical shifts; off-grid powers and missing reports require inconclusive handling. Delays exclude missed events, which remain in the event denominator. Channel events within a run are correlated; no binomial confidence interval is claimed for pooled channel-event detection.</p>'
    page+='<h2>Policy comparison</h2>'+_image(figure)
    page+='<h2>Run summary</h2><p>False-hold fractions show exact 95% intervals across independent run seeds. A small experiment with zero events does not establish a rare-event rate.</p><div class="table"><table><thead><tr>'+''.join(f'<th>{x}</th>' for x in ('Scenario','Policy','Runs','Runs with false hold [95% CI]','Runs with raw false alarm','Sustained events detected','Delay when detected (s)','Benign windows held','Inconclusive windows'))+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
    page+=trace_html
    page+='<h2>Limits and reproducibility</h2><p>WDM coupling coefficients are illustrative, not measured hardware data. Power contexts are discrete and measured without error in this stage. Shared-detector effects, real device commands, finite-key distillation, authenticated transport, and attack attribution are outside this implementation. Telemetry continues during advisory hold for recovery assessment.</p>'
    page+=f'<p>Configuration SHA-256: <code>{cfg.fingerprint}</code><br>Experiment: {html.escape(manifest["kind"])}. Seeds: {html.escape(str(manifest["seeds"]))}. Package version: {html.escape(manifest["package_version"])}.</p>'
    page+='<p>Inspect manifest.json, config.json, summary.json, paired_comparisons.json and run_metrics.csv alongside this report. Representative decision and truth logs, when included, are separate files. All plots also have PDF exports.</p><footer>Generated locally from recorded experiment outputs. No external assets or network requests.</footer></main></html>'
    (out/"report.html").write_text(page,encoding="utf-8")
