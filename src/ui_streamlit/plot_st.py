# Plotly figure builders (mirrors plot.py)

# src/ui_streamlit/plot.py
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go

def signal_figure(t, y, peaks_max=None, peaks_min=None, period_bounds=None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=y, mode="lines", name="signal"))
    if peaks_max is not None and len(peaks_max) > 0:
        fig.add_trace(go.Scatter(
            x=t[peaks_max], y=y[peaks_max], mode="markers",
            marker_symbol="triangle-up", marker_size=8, name="max"))
    if peaks_min is not None and len(peaks_min) > 0:
        fig.add_trace(go.Scatter(
            x=t[peaks_min], y=y[peaks_min], mode="markers",
            marker_symbol="triangle-down", marker_size=8, name="min"))
    
    # dashed separators + labels
    if period_bounds:
        for b in period_bounds:
            color = "red" if b["removed"] else "black"
            # left/right dashed lines
            fig.add_vline(x=b["t0"], line=dict(color=color, width=1, dash="dash"))
            fig.add_vline(x=b["t1"], line=dict(color=color, width=1, dash="dash"))
            # label at the top center of the period
            tx = 0.5 * (b["t0"] + b["t1"])
            fig.add_annotation(
                x=tx, y=max(y) if len(y) else 0, text=str(b["k"]),
                showarrow=False, yshift=18, font=dict(color=color, size=10),
                bgcolor="white", opacity=0.7
            )
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Time (s)", yaxis_title="Signal (a.u.)",
        hovermode="x unified",
        )
    return fig

def overlay_figure(tau, X) -> go.Figure:
    fig = go.Figure()
    if X.ndim == 2 and X.size > 0:
        # X is (n_periods, n_points)
        n_periods = X.shape[0]
        for i in range(n_periods):
            fig.add_trace(go.Scatter(x=tau, y=X[i, :], mode="lines", opacity=0.3, showlegend=False))
        fig.add_trace(go.Scatter(x=tau, y=np.nanmean(X, axis=0), mode="lines", name="mean"))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Normalized time (τ)", yaxis_title="Signal (a.u.)",
        hovermode=False,
        )
    return fig
