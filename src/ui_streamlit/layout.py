# page layout & sidebar controls (mirrors views.py)

# src/ui_streamlit/layout.py
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_plotly_events2 import plotly_events

from src.ui_streamlit.plot_st import signal_figure, overlay_figure
from src.ui_streamlit.events import handle_click_insert_remove_min, handle_click_toggle_remove_by_max
from src.segment import resample_periods
from src.metrics import metrics_for_periods, aggregate_metrics

def sidebar_controls(state):
    st.header("Data")
    raw_up = st.file_uploader("Raw (CSV/XLSX)", type=["csv", "xlsx"], key="raw_file")
    amb_up = st.file_uploader("Ambient (optional)", type=["csv", "xlsx"], key="amb_file")

    col_a, col_b = st.columns(2)
    with col_a:
        state["ambient"]["offset_ms"] = st.number_input("Ambient offset (ms)", value=float(state["ambient"]["offset_ms"]), step=1.0)
    with col_b:
        state["ambient"]["scale"] = st.number_input("Ambient scale", value=float(state["ambient"]["scale"]), step=0.1, format="%.2f")

    st.header("Filtering")
    state["smoothing"] = st.slider("S (0=raw...5=heavy)", min_value=0, max_value=5, value=int(state["smoothing"]))

    st.header("Detection")
    pac = st.text_input("Pacing hint (Hz, optional)", value=str(state["pacing_hint_hz"] or ""))
    try:
        state["pacing_hint_hz"] = float(pac) if pac.strip() else None
    except ValueError:
        st.warning("Pacing hint must be a number (Hz). Ignored.")

    st.header("Click mode")
    mode = st.radio("On canvas click:", ["Insert/Remove MIN", "Remove by MAX"], horizontal=True)
    state["click_mode"] = "min" if mode == "Insert/Remove MIN" else "remove_by_max"

    return raw_up, amb_up

def tabs_main(state, t_work, y_work):
    tab_signal, tab_overlay, tab_metrics = st.tabs(["Signal & Edit", "Overlay", "Metrics"])

    # Signal & Edit
    with tab_signal:
        st.subheader("Signal (click to edit)")
        fig = signal_figure(t_work, y_work, state["peaks_max"], state["peaks_min"], period_bounds=state.get("period_bounds", []))
        clicks = plotly_events(fig, click_event=True, select_event=False, hover_event=False,
                               override_width="100%", override_height=340)

        if clicks:
            x_clicked = float(clicks[0]["x"])
            if state["click_mode"] == "min":
                ok, msg = handle_click_insert_remove_min(st.session_state, x_clicked)
            else:
                ok, msg = handle_click_toggle_remove_by_max(st.session_state, x_clicked)
            st.toast(msg, icon="✅" if ok else "⚠️")

    # Overlay
    with tab_overlay:
        st.subheader("Overlay of retained periods")
        periods = state["periods_filt"]
        if not periods:
            st.info("No periods to show. Detect and curate periods first.")
        else:
            X, tau = resample_periods(periods, n_points=200)
            st.plotly_chart(overlay_figure(tau, X), use_container_width=True)

    # Metrics
    with tab_metrics:
        st.subheader("Metrics")
        r, f = state["periods_raw"], state["periods_filt"]
        col1, col2 = st.columns(2)
        if r:
            with col1:
                st.markdown("**Per-period (Raw)**")
                st.dataframe(pd.DataFrame(metrics_for_periods(r)), use_container_width=True)
        if f:
            with col2:
                st.markdown("**Per-period (Filtered)**")
                st.dataframe(pd.DataFrame(metrics_for_periods(f)), use_container_width=True)

        # Aggregates (optional)
        if r or f:
            agg_rows = []
            if r: agg_rows.append({"pipeline": "raw", **aggregate_metrics(metrics_for_periods(r))})
            if f: agg_rows.append({"pipeline": "filtered", **aggregate_metrics(metrics_for_periods(f))})
            if agg_rows:
                st.divider()
                st.markdown("**Aggregates**")
                st.dataframe(pd.DataFrame(agg_rows), use_container_width=True)
