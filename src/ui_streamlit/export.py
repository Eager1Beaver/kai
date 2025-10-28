# Excel bundle/CSV/figs

# src/ui_streamlit/export.py
from __future__ import annotations
from io import BytesIO
from typing import Dict, Tuple, Optional, List

import numpy as np
import pandas as pd

from src.segment import resample_periods
from src.metrics import metrics_for_periods, aggregate_metrics


def _safe_agg(state) -> pd.DataFrame:
    """Aggregate metrics for raw/filtered if available."""
    rows = []
    if state.get("periods_raw"):
        m = metrics_for_periods(state["periods_raw"])
        rows.append({"pipeline": "raw", **aggregate_metrics(m)})
    if state.get("periods_filt"):
        m = metrics_for_periods(state["periods_filt"])
        rows.append({"pipeline": "filtered", **aggregate_metrics(m)})
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def build_excel_bundle(
    state: dict,
    include_resampled: bool = True,
    ) -> bytes:
    """
    Build an in-memory XLSX using current state.
    Sheets:
      - Parameters
      - Periods
      - Metrics_Period_Raw (if any)
      - Metrics_Period_Filt (if any)
      - Aggregates (if any)
      - Resampled_Periods (optional)
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # 1) Parameters / session snapshot
        params = {
            "smoothing_level": int(state.get("smoothing", 0)),
            "pacing_hint_hz": state.get("pacing_hint_hz") or "",
            "ambient_offset_ms": (state.get("ambient") or {}).get("offset_ms", 0.0),
            "ambient_scale": (state.get("ambient") or {}).get("scale", 1.0),
            "n_periods_filtered": len(state.get("periods_filt") or []),
            "n_periods_raw": len(state.get("periods_raw") or []),
            "n_removed_by_max": len(state.get("removed_max_idxs") or []),
            }
        pd.DataFrame([params]).to_excel(writer, sheet_name="Parameters", index=False)

        # 2) Period durations (filtered)
        durs = []
        for (t_seg, _y) in (state.get("periods_filt") or []):
            durs.append(float(t_seg[-1] - t_seg[0]) if len(t_seg) else np.nan)
        if durs:
            pd.DataFrame(
                {"period": np.arange(1, len(durs) + 1), "duration_s": durs}
            ).to_excel(writer, sheet_name="Periods", index=False)

        # 3) Metrics per-period
        if state.get("periods_raw"):
            df_r = pd.DataFrame(metrics_for_periods(state["periods_raw"]))
            df_r.to_excel(writer, sheet_name="Metrics_Period_Raw", index=False)
        if state.get("periods_filt"):
            df_f = pd.DataFrame(metrics_for_periods(state["periods_filt"]))
            df_f.to_excel(writer, sheet_name="Metrics_Period_Filt", index=False)

        # 4) Aggregates
        df_agg = _safe_agg(state)
        if not df_agg.empty:
            df_agg.to_excel(writer, sheet_name="Aggregates", index=False)

        # 5) Resampled periods (overlay matrix)
        if include_resampled and state.get("periods_filt"):
            X, tau = resample_periods(state["periods_filt"], n_points=200)
            df = pd.DataFrame({"tau": tau})
            for i in range(X.shape[0]):     # loop periods
                df[f"p{i+1}"] = X[i, :]
            df.to_excel(writer, sheet_name="Resampled_Periods", index=False)

    output.seek(0)
    return output.read()


def save_plotly_figure(fig, path: str) -> None:
    """
    Save a Plotly figure to PNG (requires kaleido).
    """
    fig.write_image(path)  # e.g., "overlay.png"
