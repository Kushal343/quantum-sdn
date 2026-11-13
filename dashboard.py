import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import streamlit as st
from qkd_sdn.bb84 import run_wdm, aggregate_telemetry

st.set_page_config(page_title="WDM QKD Monitor", page_icon="🔬", layout="wide")
st.title("Four-wavelength BB84 monitor")
st.caption("Local Qiskit Aer simulation · independently encoded wavelength modes")
st.info("This demonstration estimates sampled QBER. Remaining raw bits are not secure keys. Optical WDM physics and SKR are separate model components.")
with st.sidebar:
    st.header("Experiment")
    steps = st.slider("Monitoring intervals", 4, 24, 12)
    onset = st.slider("Attack begins at interval", 0, steps-1, min(4, steps-1))
    fraction = st.slider("Fraction intercepted", 0.0, 1.0, 0.8, 0.05)
    target = st.selectbox("Target wavelength", [f"lambda_{i}" for i in range(1, 5)], index=2)
    qubits = st.select_slider("Pulses per wavelength/interval", [2000, 6000, 12000, 24000], value=12000)
    seed = st.number_input("Random seed", min_value=0, value=42, step=1)
    run = st.button("Run Qiskit experiment", type="primary")
    st.caption("Simulated intervals are not wall-clock seconds. Threshold: illustrative 11%.")

if run:
    with st.spinner("Executing BB84 circuits in Aer…"):
        rows, truth = run_wdm(steps, qubits, onset, fraction, target, int(seed))
        st.session_state["experiment"] = (pd.DataFrame(rows), pd.DataFrame(truth), onset)

if "experiment" in st.session_state:
    frame, truth, actual_onset = st.session_state["experiment"]
    agg = aggregate_telemetry(frame)
    cols = st.columns(3)
    cols[0].metric("Aer shots, including padding", f"{frame.aer_shots.sum():,}")
    cols[1].metric("Revealed sample bits", f"{frame.n_sample.sum():,}")
    cols[2].metric("Largest channel QBER", f"{frame.qber.max():.1%}")
    left, right = st.columns(2)
    left.subheader("Per wavelength")
    left.line_chart(frame.pivot(index="interval", columns="channel", values="qber"))
    right.subheader("Weighted aggregate")
    right.line_chart(agg.set_index("interval")[["qber"]].assign(demo_threshold=0.11))
    st.caption(f"Last executed experiment: attack begins at interval {actual_onset}. QBER is computed from disclosed samples, not evaluator-only full sifted keys.")
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Download telemetry CSV", frame.to_csv(index=False), "telemetry.csv", "text/csv")
    with st.expander("Evaluator-only attack schedule"):
        st.caption("Kept separate from controller telemetry.")
        st.dataframe(truth, hide_index=True)
else:
    st.write("Choose an experiment and click **Run Qiskit experiment**.")
