# streamlit_app.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import streamlit as st

# Core
from src.io import load_signal, subtract_ambient
from src.filters import FilterEngine
from src.detect import find_peaks_adaptive
from src.segment import build_period_indices, slice_periods, resample_periods

# Streamlit UI layer
from src.ui_streamlit.layout import sidebar_controls, tabs_main
from src.ui_streamlit.export import build_excel_bundle, build_csv_mirrors, save_plotly_figure
from src.ui_streamlit.plot_st import overlay_figure

st.set_page_config(page_title="KAI — Calcium Imaging Analyzer", layout="wide")


# Session-state utilities
def ensure_state_defaults():
    ss = st.session_state
    ss.setdefault("_tmpdir", Path("./.st_tmp"))
    ss["_tmpdir"].mkdir(parents=True, exist_ok=True)

    # Raw / Ambient
    ss.setdefault("t_raw", None)
    ss.setdefault("y_raw", None)
    ss.setdefault("t_amb", None)
    ss.setdefault("y_amb", None)
    ss.setdefault("ambient", {"offset_ms": 0.0, "scale": 1.0})

    # Params
    ss.setdefault("smoothing", 0)           # 0..5
    ss.setdefault("pacing_hint_hz", 1)   # Optional float

    # Detection / Editing
    ss.setdefault("peaks_max", np.array([], dtype=int))
    ss.setdefault("peaks_min", np.array([], dtype=int))
    ss.setdefault("removed_max_idxs", set())  # raw max indices to exclude

    # Segmentation results
    ss.setdefault("idx_periods", [])        # kept intervals [(i0, i1), ...]
    ss.setdefault("periods_raw", [])        # list of (t_seg, y_seg)
    ss.setdefault("periods_filt", [])       # list of (t_seg, y_seg)

    # Filter engine (kept in memory to reuse config)
    ss.setdefault("filter_engine", FilterEngine(smoothing_level=int(ss["smoothing"])))


def _persist_upload(uploaded) -> Optional[str]:
    """Write UploadedFile to a deterministic path inside .st_tmp and return that path."""
    if uploaded is None:
        return None
    name = Path(uploaded.name).name.replace(" ", "_")
    p = st.session_state["_tmpdir"] / f"upload_{name}"
    with open(p, "wb") as f:
        f.write(uploaded.getbuffer())
    return str(p)


def current_working_signal() -> Tuple[np.ndarray, np.ndarray]:
    """Return (t, y_filtered) after optional ambient subtraction + smoothing."""
    t = st.session_state["t_raw"]
    y = st.session_state["y_raw"]
    if t is None or y is None:
        return np.array([]), np.array([])

    y_work = y.copy()
    if st.session_state["t_amb"] is not None and st.session_state["y_amb"] is not None:
        off_ms = st.session_state["ambient"]["offset_ms"]
        scale = st.session_state["ambient"]["scale"]
        y_work, _meta = subtract_ambient(
            t, y_work, st.session_state["t_amb"], st.session_state["y_amb"],
            offset_ms=off_ms, scale=scale
        )

    S = int(st.session_state["smoothing"])
    fe: FilterEngine = st.session_state["filter_engine"]
    fe.smoothing_level = S
    y_f = fe.apply(t, y_work, pacing_freq_hz=st.session_state["pacing_hint_hz"])
    # Cache for click handlers
    st.session_state["t_work"] = t
    st.session_state["y_work"] = y_f
    return t, y_f


def recompute_periods_and_metrics():
    """Rebuild segmentation from minima/maxima; drop removed periods; slice raw & filtered."""
    t = st.session_state["t_raw"]
    y = st.session_state["y_raw"]
    if t is None or y is None or len(t) == 0:
        st.session_state["idx_periods"] = []
        st.session_state["periods_raw"] = []
        st.session_state["periods_filt"] = []
        return

    # 1) Full segmentation (min→min) from detected extrema
    seg = build_period_indices(
        t,
        st.session_state["peaks_min"],
        st.session_state["peaks_max"],
        strategy="min2min",
    )
    # In case build_period_indices returns a dataclass (SegmentationInfo), use .indices
    idx_periods_full = getattr(seg, "indices", seg)

    # 2) Drop periods whose local max belongs to removed_max_idxs
    kept, bounds, removed_period_numbers = [], [], set()
    # number periods 1..K in full segmentation
    for k, (a, b) in enumerate(idx_periods_full, start=1):
        win = np.arange(a, b, dtype=int)  # end is exclusive in segment.py
        if win.size == 0:
            continue
        local_max = win[np.argmax(st.session_state["y_raw"][win])]
        is_removed = (local_max in st.session_state["removed_max_idxs"])
        if is_removed:
            removed_period_numbers.add(k)
        else:
            kept.append((a, b))
        # keep a time-version for drawing
        bounds.append({
            "k": k,
            "t0": float(t[a]),
            "t1": float(t[b-1] if b-1 < len(t) else t[-1]),
            "removed": bool(is_removed),
        })

    st.session_state["idx_periods"] = kept
    st.session_state["period_bounds"] = bounds
    st.session_state["removed_period_numbers"] = removed_period_numbers

    # 3) Slice raw & filtered with the kept intervals
    st.session_state["periods_raw"] = slice_periods(t, y, kept)
    t_f, y_f = current_working_signal()
    st.session_state["periods_filt"] = slice_periods(t_f, y_f, kept)


# Page
def main():
    ensure_state_defaults()

    st.title("KAI — Calcium Imaging Analyzer")
    st.caption("Load → Smooth → Detect → Curate → Overlay → Metrics → Export")

    # Sidebar controls (uploads, params, click mode selection in tabs_main)
    raw_up, amb_up = sidebar_controls(st.session_state)

    # Actions row
    colA, colB, colC = st.columns([1, 1, 2])
    with colA:
        if st.button("Detect peaks / recompute", width='stretch'): # use_container_width=True
            # Load files if (re)uploaded now
            raw_path = _persist_upload(raw_up) if raw_up is not None else None
            amb_path = _persist_upload(amb_up) if amb_up is not None else None

            if raw_path is not None:
                t_raw, y_raw, _info = load_signal(raw_path)
                st.session_state["t_raw"] = t_raw
                st.session_state["y_raw"] = y_raw

            if amb_path is not None:
                t_amb, y_amb, _ainfo = load_signal(amb_path)
                st.session_state["t_amb"] = t_amb
                st.session_state["y_amb"] = y_amb
            elif amb_up is None:
                # Explicitly clear ambient if user removed it
                st.session_state["t_amb"] = None
                st.session_state["y_amb"] = None

            # Run detection on the filtered working signal
            t_w, y_w = current_working_signal()
            if t_w.size == 0:
                st.error("Please upload a raw signal first.")
            else:
                res = find_peaks_adaptive(t_w, y_w, fp_hint=st.session_state["pacing_hint_hz"])
                st.session_state["peaks_max"] = res.peaks_max
                st.session_state["peaks_min"] = res.peaks_min
                st.session_state["removed_max_idxs"] = set()   # reset removals
                recompute_periods_and_metrics()
                st.success(f"Detected {len(st.session_state['periods_filt'])} periods.")

    # Working signal for plotting
    t_work, y_work = current_working_signal()

    # Track edits made by plot clicks (compare before/after arrays & sets)
    pre_state_signature = (
        tuple(st.session_state["peaks_min"].tolist()),
        tuple(st.session_state["peaks_max"].tolist()),
        tuple(sorted(st.session_state["removed_max_idxs"])),
    )

    # Tabs (Signal & Edit [clickable], Overlay, Metrics)
    tabs_main(st.session_state, t_work, y_work)

    post_state_signature = (
        tuple(st.session_state["peaks_min"].tolist()),
        tuple(st.session_state["peaks_max"].tolist()),
        tuple(sorted(st.session_state["removed_max_idxs"])),
    )
    if post_state_signature != pre_state_signature:
        # Recompute only if the user actually changed something via clicks
        recompute_periods_and_metrics()

    st.divider()

    # Export section
    col1, col2 = st.columns([1, 1])
    with col1:
        xlsx = build_excel_bundle(st.session_state, include_resampled=True)
        st.download_button(
            "Download Excel bundle",
            data=xlsx,
            file_name="KAI_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
            )

    with col2:
        # Optional: export overlay PNG using kaleido (if we have periods)
        periods = st.session_state.get("periods_filt") or []
        if periods:
            X, tau = resample_periods(periods, n_points=200)
            fig_overlay = overlay_figure(tau, X)
            # Save to temp path and expose as download
            png_path = st.session_state["_tmpdir"] / "overlay.png"
            save_plotly_figure(fig_overlay, str(png_path))
            with open(png_path, "rb") as f:
                st.download_button(
                    "Download overlay.png",
                    data=f.read(),
                    file_name="overlay.png",
                    mime="image/png",
                    width='stretch',
                    )

    st.caption("Tip: use S=1-2 for research; strong smoothing is for diagnostics only.")


if __name__ == "__main__":
    main()
