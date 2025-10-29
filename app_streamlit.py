import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events2 import plotly_events
import numpy as np
import pandas as pd
import io
import json
import matplotlib.pyplot as plt  # For generating PNG exports in-memory
from pathlib import Path

# Local imports
from src.io import load_signal, subtract_ambient
from src.filters import FilterEngine
from src.detect import find_peaks_adaptive, snap_to_local_extremum, insert_peak, remove_peak, enforce_alternation
from src.segment import build_period_indices, slice_periods, resample_periods, normalize_periods, average_period
from src.metrics import metrics_for_periods, aggregate_metrics
from src.ui.plot import draw_periods_overlay


class SignalPlotStreamlit:
    def __init__(self, on_click_peak=None):
        self.on_click_peak = on_click_peak
        self.t = None
        self.y_raw = None
        self.y_filt = None
        self.peaks_min = np.array([], dtype=int)
        self.peaks_max = np.array([], dtype=int)
        self._edit_enabled = False
        self._removed_spans = []
        self._period_bounds = []
        self._periods_removed = set()
        self._filt_legend_label = "Filtered"
        self.base_label = "Raw"

    def set_data(self, t, y_base, y_filt=None):
        self.t = t
        self.y_raw = y_base
        self.y_filt = y_filt

    def set_filter_label(self, text):
        self._filt_legend_label = text

    def set_peaks(self, peaks_min, peaks_max):
        self.peaks_min = np.asarray(peaks_min, dtype=int)
        self.peaks_max = np.asarray(peaks_max, dtype=int)

    def enable_edit(self, enabled):
        self._edit_enabled = bool(enabled)

    def set_removed_spans(self, spans):
        self._removed_spans = list(spans or [])

    def set_period_boundaries(self, boundaries, removed=set()):
        self._period_bounds = list(boundaries or [])
        self._periods_removed = set(removed or set())

    def _draw_extrema_arrows(self, fig, t, y, idxs_up, idxs_dn):
        if len(y) == 0:
            return
        yspan = max(1e-9, np.nanmax(y) - np.nanmin(y))
        h = 0.12 * yspan
        for i in idxs_up:
            fig.add_annotation(
                x=t[i], y=y[i] + h * 0.5,
                ax=t[i], ay=y[i] - h * 0.5,
                arrowhead=1, arrowsize=1.5, arrowwidth=1.2, arrowcolor='darkorange'
                )
        for i in idxs_dn:
            fig.add_annotation(
                x=t[i], y=y[i] - h * 0.5,
                ax=t[i], ay=y[i] + h * 0.5,
                arrowhead=1, arrowsize=1.5, arrowwidth=1.2, arrowcolor='darkblue'
                )

    def render(self):
        fig = go.Figure()
        if self.t is None or self.y_raw is None:
            fig.update_layout(title="Load a signal to begin")
            return fig, None

        y_for_peaks = self.y_filt if self.y_filt is not None else self.y_raw

        # Raw line
        fig.add_trace(go.Scatter(
            x=self.t, y=self.y_raw, 
            mode='lines', name=self.base_label, 
            line=dict(width=1, color='blue'), 
            opacity=0.7
            ))

        # Filtered line
        if self.y_filt is not None:
            fig.add_trace(go.Scatter(
                x=self.t, y=self.y_filt, 
                mode='lines', name=self._filt_legend_label, 
                line=dict(width=1.2)
                ))

        # Min peaks
        if self.peaks_min.size > 0:
            fig.add_trace(go.Scatter(
                x=self.t[self.peaks_min], y=y_for_peaks[self.peaks_min],
                mode='markers', name='min', 
                marker=dict(symbol='triangle-down', size=8, color='blue')
                ))

        # Max peaks
        if self.peaks_max.size > 0:
            fig.add_trace(go.Scatter(
                x=self.t[self.peaks_max], y=y_for_peaks[self.peaks_max],
                mode='markers', name='max', 
                marker=dict(symbol='triangle-up', size=8, color='orange')
                ))

        # Collect all plotted y values for range calculation
        all_y = np.concatenate([self.y_raw[~np.isnan(self.y_raw)]])
        if self.y_filt is not None:
            all_y = np.concatenate([all_y, self.y_filt[~np.isnan(self.y_filt)]])
        if self.peaks_min.size > 0:
            all_y = np.concatenate([all_y, y_for_peaks[self.peaks_min]])
        if self.peaks_max.size > 0:
            all_y = np.concatenate([all_y, y_for_peaks[self.peaks_max]])
        
        if len(all_y) > 0:
            min_y = np.nanmin(all_y)
            max_y = np.nanmax(all_y)
            yspan_data = max_y - min_y if max_y - min_y > 0 else 1
            fig.update_yaxes(range=[min_y - 0.1 * yspan_data, max_y + 0.1 * yspan_data])

        # Extrema arrows
        self._draw_extrema_arrows(fig, self.t, y_for_peaks, self.peaks_max, self.peaks_min)

        # Removed spans
        for t0, t1 in self._removed_spans:
            fig.add_vrect(x0=t0, x1=t1, fillcolor='red', opacity=0.15, line_width=0)

        # Period boundaries
        for t0, t1, k in self._period_bounds:
            color = 'red' if k in self._periods_removed else 'black' # black->yellow
            fig.add_vline(x=t0, line=dict(color=color, dash='dash', width=0.8), opacity=0.5)
            fig.add_vline(x=t1, line=dict(color=color, dash='dash', width=0.8), opacity=0.5)
            # Label
            tx = 0.5 * (t0 + t1)
            fig.add_annotation(
                x=tx, y=0.95, 
                yref='paper', text=str(k), showarrow=False,
                font=dict(size=9, color=color), bgcolor='white', 
                opacity=0.6
                )

        fig.update_layout(xaxis_title='Time (s)', yaxis_title='Signal (a.u.)', showlegend=True, legend=dict(x=1, y=1))
        fig.update_xaxes(showgrid=True, gridcolor='lightgray', gridwidth=0.5)
        fig.update_yaxes(showgrid=True, gridcolor='lightgray', gridwidth=0.5)

        # For interactivity, use plotly_events to capture clicks
        if self._edit_enabled:
            selected_points = plotly_events(fig, click_event=True, hover_event=False, select_event=False)
            return fig, selected_points
        else:
            st.plotly_chart(fig)
            return fig, None


def draw_periods_overlay_streamlit(tau, Xn, mean, std, labels=None, labeled_max=12):
    fig = go.Figure()
    if Xn is None or Xn.shape[0] == 0:
        fig.update_layout(title="No periods available")
        return fig

    n = Xn.shape[0]
    for i in range(n):
        lbl = None
        if labels and i < len(labels):
            lbl = labels[i] if i < labeled_max else None
        else:
            lbl = f"Period {i+1}" if i < labeled_max else None
        fig.add_trace(go.Scatter(x=tau, y=Xn[i], mode='lines', name=lbl, opacity=0.35, line=dict(width=1)))

    fig.add_trace(go.Scatter(x=tau, y=mean, mode='lines', name='Mean', line=dict(width=1.8)))

    if std is not None and np.all(np.isfinite(std)):
        fig.add_trace(go.Scatter(
            x=tau, y=mean + std, 
            mode='lines', line=dict(width=0), 
            showlegend=False, fill=None
            ))
        fig.add_trace(go.Scatter(
            x=tau, y=mean - std, 
            mode='lines', line=dict(width=0), 
            fill='tonexty', fillcolor='rgba(0,100,80,0.15)', 
            showlegend=False
            ))

    fig.update_layout(
        xaxis_title="Normalized time τ", yaxis_title="Normalized amplitude", 
        showlegend=True, 
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font_size=9
                    ))
    return fig

@st.cache_data(show_spinner=False)
def load_user_guide() -> str:
    """Return the Markdown of docs/User-Guide.md, with robust path fallback."""
    candidates = [
        Path("docs/User-Guide.md"),
        Path(__file__).resolve().parent / "docs" / "User-Guide.md",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return "# User Guide not found\nPlease ensure `docs/User-Guide.md` is included in the deployment."

# Main Streamlit App
def main():
    st.set_page_config(page_title="KAI - Calcium Imaging Analyzer", layout="wide")
    st.title("KAI - Calcium Imaging Analyzer")

    guide_md = load_user_guide()

    # Session state for persisting data
    if 't_raw' not in st.session_state:
        st.session_state.t_raw = None
    if 'y_raw' not in st.session_state:
        st.session_state.y_raw = None
    if 't_amb' not in st.session_state:
        st.session_state.t_amb = None
    if 'y_amb' not in st.session_state:
        st.session_state.y_amb = None
    if 'y_corr' not in st.session_state:
        st.session_state.y_corr = None
    if 'meta_amb' not in st.session_state:
        st.session_state.meta_amb = {}
    if 'filter_engine' not in st.session_state:
        st.session_state.filter_engine = FilterEngine(0)
    if 'y_filt' not in st.session_state:
        st.session_state.y_filt = None
    if 'peaks_min' not in st.session_state:
        st.session_state.peaks_min = np.array([], dtype=int)
    if 'peaks_max' not in st.session_state:
        st.session_state.peaks_max = np.array([], dtype=int)
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'seg_info' not in st.session_state:
        st.session_state.seg_info = None
    if 'periods' not in st.session_state:
        st.session_state.periods = []
    if 'periods_raw' not in st.session_state:
        st.session_state.periods_raw = []
    if 'period_original_indices' not in st.session_state:
        st.session_state.period_original_indices = []
    if 'removed_periods' not in st.session_state:
        st.session_state.removed_periods = set()
    if 'metrics_agg_raw' not in st.session_state:
        st.session_state.metrics_agg_raw = {}
    if 'metrics_agg_filt' not in st.session_state:
        st.session_state.metrics_agg_filt = {}
    if 'pacing_hz_manual' not in st.session_state:
        st.session_state.pacing_hz_manual = None
    if 'status' not in st.session_state:
        st.session_state.status = "Ready."
    if 'offset_ms' not in st.session_state:
        st.session_state.offset_ms = 0.0
    if 'scale' not in st.session_state:
        st.session_state.scale = 1.0    

    # Sidebar
    with st.sidebar:
        st.header("Session")

        # Help box
        st.info(
            "Need help with the workflow? "
            "Open the **User Guide** tab for a step-by-step walkthrough, or download it to read offline."
            )
        st.download_button(
            label="⬇️ Download User-Guide.md",
            data=guide_md.encode("utf-8"),
            file_name="User-Guide.md",
            mime="text/markdown",
            use_container_width=True,
            )

        raw_file = st.file_uploader("Load Raw...", type=['csv', 'xlsx', 'xls'])
        if raw_file:
            t, y, info = load_signal(raw_file)
            st.session_state.t_raw = t
            st.session_state.y_raw = y
            st.session_state.filter_engine.clear_cache()
            st.session_state.status = f"Loaded raw: {raw_file.name} ({info.n_rows} rows)"
            refresh_signal()

        amb_file = st.file_uploader("Load Ambient (optional)...", type=['csv', 'xlsx', 'xls'])
        if amb_file:
            t, y, info = load_signal(amb_file)
            st.session_state.t_amb = t
            st.session_state.y_amb = y
            st.session_state.filter_engine.clear_cache()
            st.session_state.status = f"Loaded ambient: {amb_file.name} ({info.n_rows} rows)"
            apply_offset_scale(st.session_state.offset_ms, st.session_state.scale)

        st.header("Ambient alignment")
        offset_ms = st.number_input("Offset (ms):", value=st.session_state.offset_ms)
        scale = st.number_input("Scale:", value=st.session_state.scale)
        if st.button("Apply"):
            apply_offset_scale(offset_ms, scale)

        st.header("Pacing (manual)")
        pace_hz = st.number_input("Hz:", value=1.0)
        if st.button("Use"):
            on_set_pacing(pace_hz)

        st.text(st.session_state.get('pace_status', "Current: auto"))

        st.header("Smoothing")
        smoothing_level = st.slider("S = ", min_value=0, max_value=5, value=st.session_state.filter_engine.smoothing_level, step=1)
        if smoothing_level != st.session_state.filter_engine.smoothing_level:
            on_smooth_changed(smoothing_level)

        st.text("0 = raw - 5 = heavy")

        if st.button("Detect Peaks"):
            detect_peaks()

        edit_mode = st.checkbox("Edit Mode", value=st.session_state.edit_mode)
        if edit_mode != st.session_state.edit_mode:
            toggle_edit()

        if st.button("Export XLSX/CSV"):
            export_all()

        st.text(st.session_state.status)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Signal", "Periods", "Overlay", "Metrics", "User Guide"])

    with tab1:
        if raw_file is None:
            st.text("Load raw first")
        sig_plot = SignalPlotStreamlit(on_click_peak=on_click_peak)
        base_y = st.session_state.y_corr if st.session_state.y_corr is not None else st.session_state.y_raw
        sig_plot.base_label = "Ambient-corrected" if st.session_state.y_corr is not None else "Raw"
        sig_plot.set_data(st.session_state.t_raw, base_y, st.session_state.y_filt)
        sig_plot.set_filter_label(f"Filtered (S={st.session_state.filter_engine.smoothing_level})")
        sig_plot.set_peaks(st.session_state.peaks_min, st.session_state.peaks_max)
        sig_plot.enable_edit(st.session_state.edit_mode)

        # Set spans and boundaries (from state)
        if st.session_state.seg_info:
            spans = calculate_removed_spans()
            sig_plot.set_removed_spans(spans)
            bounds = [
                (
                    st.session_state.t_raw[i], 
                    st.session_state.t_raw[j-1] if j < len(st.session_state.t_raw) else st.session_state.t_raw[-1], k
                    ) for k, (i, j) in enumerate(st.session_state.seg_info.indices, 1)
                    ] 
            sig_plot.set_period_boundaries(bounds, st.session_state.removed_periods)
        _, selected_points = sig_plot.render()
        if selected_points:
            for point in selected_points:
                if 'x' in point:
                    on_click_peak(point['x'])

    with tab2:
        render_periods_tab()

    with tab3:
        update_overlay_plot()

    with tab4:
        render_metrics_tab()

    with tab5:
    # Fully rendered guide in-app
        with st.expander("Show / hide full User Guide", expanded=True):
            st.markdown(guide_md)

        st.download_button(
            label="⬇️ Download User-Guide.md",
            data=guide_md.encode("utf-8"),
            file_name="User-Guide.md",
            mime="text/markdown",
            )
        

# Helpers
def calculate_removed_spans():
    spans = []
    if st.session_state.seg_info and st.session_state.seg_info.indices:
        i0 = st.session_state.seg_info.indices[0][0]
        spans.append((st.session_state.t_raw[0], st.session_state.t_raw[i0]))
        jlast = st.session_state.seg_info.indices[-1][1]
        spans.append((st.session_state.t_raw[jlast], st.session_state.t_raw[-1]))
        for k in st.session_state.removed_periods:
            if 0 < k <= len(st.session_state.seg_info.indices):
                i, j = st.session_state.seg_info.indices[k-1]
                spans.append((st.session_state.t_raw[i], st.session_state.t_raw[j]))
    return spans

def apply_offset_scale(offset_ms, scale):
    st.session_state['offset_ms'] = offset_ms
    st.session_state['scale'] = scale
    if st.session_state.t_raw is None or st.session_state.y_raw is None or st.session_state.t_amb is None or st.session_state.y_amb is None:
        st.session_state.status = "Load raw and ambient first"
        return
    y_corr, meta = subtract_ambient(
        st.session_state.t_raw, st.session_state.y_raw, 
        st.session_state.t_amb, st.session_state.y_amb, 
        offset_ms=offset_ms, scale=scale
        )
    st.session_state.y_corr = y_corr
    st.session_state.meta_amb = meta
    st.session_state.status = f"Ambient subtracted (offset={meta['offset_ms']} ms, scale={meta['scale']})"
    refresh_signal()

def on_set_pacing(hz):
    st.session_state.pacing_hz_manual = hz if hz > 0 else None
    msg = f"Current: {hz:.3g} Hz" if hz else "Current: auto"
    st.session_state['pace_status'] = msg
    refresh_signal(live=False)

def _pacing_hint():
    return st.session_state.pacing_hz_manual

def _current_signal():
    return (st.session_state.t_raw, st.session_state.y_corr if st.session_state.y_corr is not None else st.session_state.y_raw)

def refresh_signal(live=False):
    if st.session_state.t_raw is None or st.session_state.y_raw is None:
        return
    t, y = _current_signal()
    S = st.session_state.filter_engine.smoothing_level
    if S == 0:
        st.session_state.y_filt = None
    else:
        st.session_state.y_filt = st.session_state.filter_engine.apply(t, y, pacing_freq_hz=_pacing_hint())
    if not live:
        st.session_state.status = f"Updated view (S={S})"

def on_smooth_changed(S):
    st.session_state.filter_engine.set_level(S)
    refresh_signal(live=True)

def detect_peaks():
    if st.session_state.t_raw is None or st.session_state.y_raw is None:
        st.session_state.status = "Load raw first"
        return
    t, y_base = _current_signal()
    y_for_det = st.session_state.y_filt if st.session_state.y_filt is not None else y_base
    det = find_peaks_adaptive(t, y_for_det, fp_hint=_pacing_hint(), prefer="max")
    st.session_state.peaks_min = det.peaks_min
    st.session_state.peaks_max = det.peaks_max
    st.session_state.status = f"Detected peaks (min={len(st.session_state.peaks_min)}, max={len(st.session_state.peaks_max)})"
    recompute_periods()
    compute_metrics_aggregates()

def toggle_edit():
    st.session_state.edit_mode = not st.session_state.edit_mode
    st.session_state.status = f"Edit mode: {'ON' if st.session_state.edit_mode else 'OFF'}"

def on_click_peak(x_click):
    if st.session_state.t_raw is None or st.session_state.y_raw is None:
        return
    t, y_base = _current_signal()
    y_for_edit = st.session_state.y_filt if st.session_state.y_filt is not None else y_base
    try:
        idx, kind = snap_to_local_extremum(t, y_for_edit, x_click, radius_ms=60.0)
    except Exception:
        return
    if kind == "max":
        if st.session_state.seg_info and st.session_state.seg_info.indices:
            for k, (i, j) in enumerate(st.session_state.seg_info.indices, start=1):
                if i <= idx < j:
                    if k in st.session_state.removed_periods:
                        st.session_state.removed_periods.remove(k)
                        st.session_state.status = f"Restored period {k}"
                    else:
                        st.session_state.removed_periods.add(k)
                        st.session_state.status = f"Removed period {k}"
                    break
    else:
        if idx in st.session_state.peaks_min:
            st.session_state.peaks_min = remove_peak(st.session_state.peaks_min, idx, tol=1)
        else:
            st.session_state.peaks_min = insert_peak(st.session_state.peaks_min, idx)
    st.session_state.peaks_min, st.session_state.peaks_max = enforce_alternation(st.session_state.peaks_min, st.session_state.peaks_max, anchor="min")
    recompute_periods()
    compute_metrics_aggregates()

def recompute_periods():
    if st.session_state.t_raw is None or st.session_state.y_raw is None:
        return
    
    t, y_base = _current_signal()
    y_det = st.session_state.y_filt if st.session_state.y_filt is not None else y_base
    st.session_state.seg_info = build_period_indices(t, st.session_state.peaks_min, st.session_state.peaks_max, strategy="min2min")
    if not st.session_state.seg_info or not st.session_state.seg_info.indices:
        st.session_state.periods = []
        st.session_state.periods_raw = []
        st.session_state.period_original_indices = []
        #render_periods_tab()
        #update_overlay_plot()
        return
    
    removed = st.session_state.removed_periods
    kept_indices = [ij for k, ij in enumerate(st.session_state.seg_info.indices, start=1) if k not in removed]
    st.session_state.period_original_indices = [k for k, ij in enumerate(st.session_state.seg_info.indices, start=1) if k not in removed]

    if not kept_indices:
        st.session_state.periods = []
        st.session_state.periods_raw = []
        render_periods_tab()
        update_overlay_plot()
        return
    
    st.session_state.periods = slice_periods(t, y_det, kept_indices)
    st.session_state.periods_raw = slice_periods(t, y_base, kept_indices)
    render_periods_tab()
    update_overlay_plot()

def render_periods_tab():
    if not st.session_state.periods:
        st.text("No periods yet. Detect peaks first.")
        return
    
    lines = []
    for orig_k, (t_seg, y_seg) in zip(st.session_state.period_original_indices, st.session_state.periods):
        dur = t_seg[-1] - t_seg[0]
        lines.append(f"Period {orig_k:02d}: N={len(t_seg)}  duration={dur:.3f}s")
    st.text("\n".join(lines))

def update_overlay_plot():
    if not st.session_state.periods or len(st.session_state.periods) == 0:
        st.text("No periods yet. Detect peaks first.")
        return
    
    try:
        res = resample_periods(st.session_state.periods, n_points=200)
        X, tau = res if isinstance(res, tuple) else (res, np.linspace(0.0, 1.0, res.shape[1]))
        labels = [f"Period {k}" for k in st.session_state.period_original_indices]
        if not labels:
            st.text("All periods removed - nothing to display")
            return
        
        Xn = normalize_periods(X, mode="baseline")
        mu, sd = average_period(Xn)
        fig = draw_periods_overlay_streamlit(tau, Xn, mu, sd, labels=labels, labeled_max=12)
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Overlay error: {e}")

def compute_metrics_aggregates():
    if not st.session_state.periods:
        st.session_state.metrics_agg_raw = {}
        st.session_state.metrics_agg_filt = {}
        #render_metrics_tab()
        return
    
    per_f = metrics_for_periods(st.session_state.periods) or []
    per_r = metrics_for_periods(st.session_state.periods_raw) or []
    agg_f = aggregate_metrics(per_f) if per_f else {}
    agg_r = aggregate_metrics(per_r) if per_r else {}
    st.session_state.metrics_agg_raw = agg_r
    st.session_state.metrics_agg_filt = agg_f
    render_metrics_tab()

def render_metrics_tab():
    if not st.session_state.metrics_agg_raw and not st.session_state.metrics_agg_filt:
        st.text("No periods yet. Detect peaks first.")
        return
    
    # Similar to _render_metrics_tab_from_aggs
    norm_r = normalize_agg(st.session_state.metrics_agg_raw)
    norm_f = normalize_agg(st.session_state.metrics_agg_filt)
    bases = sorted(set(norm_r.keys()) | set(norm_f.keys()))
    if not bases:
        return
    
    priority = ["APD20","APD50","APD90","rise_10_90","decay_90_10",
                "time_to_peak","upstroke_angle_deg","downstroke_angle_deg",
                "auc_above_baseline","duration_s","amp_mean","amp_std","amp_peak","amp_min","amp_range","slope_max","slope_min"]
    order = [b for b in priority if b in bases] + [b for b in bases if b not in priority]
    data = []

    for base in order:
        rmu, rsd = norm_r.get(base, (np.nan, np.nan))
        fmu, fsd = norm_f.get(base, (np.nan, np.nan))
        if all(np.isnan(v) for v in (rmu, rsd, fmu, fsd)):
            continue

        data.append({
            "Metric": base,
            "Raw mean": f"{rmu:.4g}" if not np.isnan(rmu) else "—",
            "Raw std": f"{rsd:.4g}" if not np.isnan(rsd) else "—",
            "Filt mean": f"{fmu:.4g}" if not np.isnan(fmu) else "—",
            "Filt std": f"{fsd:.4g}" if not np.isnan(fsd) else "—",
            })
    df = pd.DataFrame(data)
    st.table(df)

def normalize_agg(agg):
    out = {}
    for k, v in agg.items():
        if isinstance(v, dict):
            mean = v.get("mean", np.nan)
            std = v.get("std", np.nan)
            out[k] = (mean, std)
        else:
            if k.endswith("_mean"):
                base = k[:-5]
                mean = v
                cur = out.get(base, (np.nan, np.nan))
                out[base] = (mean, cur[1])
            elif k.endswith("_std"):
                base = k[:-4]
                std = v
                cur = out.get(base, (np.nan, np.nan))
                out[base] = (cur[0], std)
    return out

def export_all():
    if st.session_state.t_raw is None or st.session_state.y_raw is None or not st.session_state.periods:
        st.info("Nothing to export yet.")
        return
    
    # Generate in-memory Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        params = {
            "smoothing_level": st.session_state.filter_engine.smoothing_level,
            "ambient_offset_ms": st.session_state.meta_amb.get("offset_ms"),
            "ambient_scale": st.session_state.meta_amb.get("scale"),
            "n_periods": len(st.session_state.periods),
            }
        pd.DataFrame([params]).to_excel(writer, sheet_name="Parameters", index=False)
        durs = [float(t_seg[-1] - t_seg[0]) for (t_seg, _y) in st.session_state.periods]
        pd.DataFrame({"period": list(range(1, len(durs)+1)), "duration_s": durs}).to_excel(writer, sheet_name="Periods", index=False)
        pd.DataFrame(metrics_for_periods(st.session_state.periods_raw)).to_excel(writer, sheet_name="Metrics_Period_Raw", index=False)
        pd.DataFrame(metrics_for_periods(st.session_state.periods)).to_excel(writer, sheet_name="Metrics_Period_Filt", index=False)
        pd.DataFrame([st.session_state.metrics_agg_raw]).to_excel(writer, sheet_name="Metrics_Aggregated_Raw", index=False)
        pd.DataFrame([st.session_state.metrics_agg_filt]).to_excel(writer, sheet_name="Metrics_Aggregated_Filt", index=False)
        res = resample_periods(st.session_state.periods, n_points=200)
        X, tau = res if isinstance(res, tuple) else (res, np.linspace(0.0, 1.0, X.shape[1]))
        Xn = normalize_periods(X, mode="baseline")
        mu, sd = average_period(Xn)
        df_res = pd.DataFrame({"tau": tau})
        for i in range(Xn.shape[0]):
            df_res[f"period_{i+1}"] = Xn[i]
        df_res["mean"] = mu
        df_res["std"] = sd
        df_res.to_excel(writer, sheet_name="Resampled_Periods", index=False)
    output.seek(0)
    st.download_button("Download XLSX", output, file_name="output.xlsx")

    # Figures as PNG
    # Signal PNG
    fig1 = plt.figure(figsize=(8,3))
    t, y_base = _current_signal()
    plt.plot(t, y_base, label="Raw" if st.session_state.y_corr is None else "Ambient-corrected", lw=1.0, alpha=0.7)
    if st.session_state.y_filt is not None:
        plt.plot(t, st.session_state.y_filt, label=f"Filtered (S={st.session_state.filter_engine.smoothing_level})", lw=1.2)
    plt.legend(bbox_to_anchor=(1.0, 1.35), loc="upper right")
    plt.xlabel("Time (s)"); plt.ylabel("Signal"); plt.tight_layout()
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png", dpi=160)
    buf1.seek(0)
    st.download_button("Download signal.png", buf1, file_name="signal.png")
    plt.close(fig1)

    # Overlay PNG
    if st.session_state.periods:
        res = resample_periods(st.session_state.periods, n_points=200)
        X, tau = res if isinstance(res, tuple) else (res, np.linspace(0.0, 1.0, X.shape[1]))
        labels = [f"Period {k}" for k in st.session_state.period_original_indices]
        if labels:
            Xn = normalize_periods(X, mode="baseline")
            mu, sd = average_period(Xn)
            fig2 = plt.Figure(figsize=(5,4))
            ax2 = fig2.add_subplot(111)
            # Use original draw_periods_overlay (from plot.py) since it's Matplotlib
            draw_periods_overlay(ax2, tau, Xn, mu, sd, labels=labels, labeled_max=12)
            buf2 = io.BytesIO()
            fig2.savefig(buf2, format="png", dpi=160)
            buf2.seek(0)
            st.download_button("Download periods_overlay.png", buf2, file_name="periods_overlay.png")
            plt.close(fig2)

    # Session JSON
    session = {
        "smoothing_level": st.session_state.filter_engine.smoothing_level,
        "peaks_min": st.session_state.peaks_min.tolist(),
        "peaks_max": st.session_state.peaks_max.tolist(),
        "removed_periods": list(st.session_state.removed_periods),
        "meta_ambient": st.session_state.meta_amb,
        "n_periods": len(st.session_state.periods),
    }
    json_buf = io.BytesIO(json.dumps(session, indent=2).encode())
    st.download_button("Download session.json", json_buf, file_name="session.json")
    st.session_state.status = "Exported files available for download."

if __name__ == "__main__":
    main()