from __future__ import annotations
import os, json, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math


# Ensure TkAgg backend for interactive use
import matplotlib
matplotlib.use("TkAgg")

from src.filters import FilterEngine
from src.io import load_signal, subtract_ambient
from src.detect import find_peaks_adaptive, snap_to_local_extremum, insert_peak, remove_peak, enforce_alternation
from src.segment import build_period_indices, slice_periods, resample_periods, normalize_periods, average_period
from src.metrics import metrics_for_periods, aggregate_metrics

from .plot import SignalPlot, draw_periods_overlay
from .views import Sidebar, Tabs

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KAI - Calcium Signal Analyzer")
        self.geometry("1100x700")
        self._build_styles()

        # State
        self.t_raw = None
        self.y_raw = None
        self.t_amb = None
        self.y_amb = None
        self.y_corr = None
        self.meta_amb = {}
        self.filter_engine = FilterEngine(0)
        self.y_filt = None
        self.peaks_min = np.array([], dtype=int)
        self.peaks_max = np.array([], dtype=int)
        self.edit_mode = False
        self.seg_info = None
        self.periods = []
        self.X = None
        self.tau = None
        self.metrics_period = []
        self.metrics_agg = {}

        self.pacing_hz_manual = None

        # Layout
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.sidebar = Sidebar(self,
            on_load_raw=self.load_raw,
            on_load_ambient=self.load_ambient,
            on_detect=self.detect_peaks,
            on_export=self.export_all,
            on_toggle_edit=self.toggle_edit,
            on_apply_offset_scale=self.apply_offset_scale,
            on_smooth_changed=self.on_smooth_changed,
            on_set_pacing=self.on_set_pacing,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.tabs = Tabs(self)
        self.tabs.grid(row=0, column=1, sticky="nsew")
        # Signal tab -> SignalPlot
        self.sig_plot = SignalPlot(self.tabs.signal_frame, on_click_peak=self.on_click_peak)
        self.sig_plot.get_widget().pack(fill="both", expand=True)

        # Periods tab
        self.periods_text = tk.Text(self.tabs.periods_frame, height=6)
        self.periods_text.pack(fill="both", expand=True)

        # Metrics tab
        self.metrics_tree = ttk.Treeview(
            self.tabs.metrics_frame, 
            columns=("metric","raw_mean","raw_std","filt_mean","filt_std"), 
            show="headings", height=12
            )
        for col,title,w in [
        ("metric","Metric",240),
        ("raw_mean","Raw mean",110),
        ("raw_std","Raw std",110),
        ("filt_mean","Filt mean",110),
        ("filt_std","Filt std",110)]:
            self.metrics_tree.heading(col, text=title)
            self.metrics_tree.column(col, width=w, anchor="center" if col!="metric" else "w")

        '''self.metrics_tree.heading("metric", text="Metric")
        self.metrics_tree.heading("mean", text="Mean")
        self.metrics_tree.heading("std", text="Std")
        self.metrics_tree.column("metric", width=240, anchor="w")
        self.metrics_tree.column("mean", width=120, anchor="center")
        self.metrics_tree.column("std", width=120, anchor="center")'''
        self.metrics_tree.pack(fill="both", expand=True, padx=6, pady=6)
    

    # ---------- UI Style ----------
    def _build_styles(self):
        style = ttk.Style(self)
        style.configure("Heading.TLabel", font=("TkDefaultFont", 10, "bold"))

    # ---------- File IO ----------
    def load_raw(self):
        path = filedialog.askopenfilename(title="Select raw CSV/XLSX", filetypes=[("CSV","*.csv"), ("Excel","*.xlsx *.xls"), ("All","*.*")])
        if not path:
            return
        t, y, info = load_signal(path)
        self.t_raw, self.y_raw = t, y
        self.sidebar.status.config(text=f"Loaded raw: {os.path.basename(path)} ({info.n_rows} rows)")
        self.refresh_signal()

    def load_ambient(self):
        path = filedialog.askopenfilename(title="Select ambient CSV/XLSX", filetypes=[("CSV","*.csv"), ("Excel","*.xlsx *.xls"), ("All","*.*")])
        if not path:
            return
        t, y, info = load_signal(path)
        self.t_amb, self.y_amb = t, y
        self.sidebar.status.config(text=f"Loaded ambient: {os.path.basename(path)} ({info.n_rows} rows)")
        self.apply_offset_scale(self.sidebar.offset_var.get(), self.sidebar.scale_var.get())

    def on_set_pacing(self, hz: float):
        self.pacing_hz_manual = float(hz) if hz and hz > 0 else None
        msg = f"Current: {self.pacing_hz_manual:.3g} Hz" if self.pacing_hz_manual else "Current: auto"
        try:
            self.sidebar.pace_status.config(text=msg)
        except Exception:
            pass
        self.refresh_signal(live=False)

    def _pacing_hint(self):
        return self.pacing_hz_manual    

    # ---------- Processing ----------
    def apply_offset_scale(self, offset_ms: float, scale: float):
        if self.t_raw is None or self.y_raw is None or self.t_amb is None or self.y_amb is None:
            self.sidebar.status.config(text="Load raw and ambient first")
            return
        y_corr, meta = subtract_ambient(self.t_raw, self.y_raw, self.t_amb, self.y_amb, offset_ms=float(offset_ms), scale=float(scale))
        self.y_corr, self.meta_amb = y_corr, meta
        self.sidebar.status.config(text=f"Ambient subtracted (offset={meta['offset_ms']} ms, scale={meta['scale']})")
        self.refresh_signal()

    def on_smooth_changed(self, S: int):
        self.filter_engine.set_level(int(S))
        self.refresh_signal(live=True)    

    def _current_signal(self):
        # Prefer ambient-corrected if available
        return (self.t_raw, self.y_corr if self.y_corr is not None else self.y_raw)

    def refresh_signal(self, live: bool = False):
        if self.t_raw is None or self.y_raw is None:
            return
        t, y = self._current_signal()
        if t is None or y is None: return
        S = self.filter_engine.smoothing_level
        if S == 0:
            self.y_filt = None
        else:
            self.y_filt = self.filter_engine.apply(t, y, pacing_freq_hz=self._pacing_hint())
            #self.y_filt = self.filter_engine.apply(t, y, pacing_freq_hz=None)
        self.sig_plot.set_filter_label(f"Filtered (S={S})")    
        self.sig_plot.set_data(t, y, self.y_filt)
        # keep peaks visual if any
        self.sig_plot.set_peaks(self.peaks_min, self.peaks_max)
        if not live:
            self.sidebar.status.config(text=f"Updated view (S={S})")

    def detect_peaks(self):
        if self.t_raw is None or self.y_raw is None:
            self.sidebar.status.config(text="Load raw first")
            return
        t, y_base = self._current_signal()
        y_for_det = self.y_filt if (self.y_filt is not None) else y_base
        #det = find_peaks_adaptive(t, y, fp_hint=None, prefer="max")
        det = find_peaks_adaptive(t, y_for_det, fp_hint=self._pacing_hint(), prefer="max")
        self.peaks_min, self.peaks_max = det.peaks_min, det.peaks_max
        self.sig_plot.set_peaks(self.peaks_min, self.peaks_max)
        self.sidebar.status.config(text=f"Detected peaks (min={len(self.peaks_min)}, max={len(self.peaks_max)})")
        self._recompute_periods_and_metrics()

    def toggle_edit(self):
        self.edit_mode = not self.edit_mode
        self.sig_plot.enable_edit(self.edit_mode)
        self.sidebar.status.config(text=f"Edit mode: {'ON' if self.edit_mode else 'OFF'}")

    def on_click_peak(self, x_click: float):
        """Snap click to nearest extremum and toggle it (add/remove) in the appropriate set."""
        if self.t_raw is None or self.y_raw is None: return
        t, _y_base = self._current_signal()
        y_for_edit = self.y_filt if (self.y_filt is not None) else (_y_base)
        try:
            idx, kind = snap_to_local_extremum(t, y_for_edit, x_click, radius_ms=60.0)
        except Exception:
            return
        if kind == "min":
            # toggle
            if idx in self.peaks_min:
                self.peaks_min = remove_peak(self.peaks_min, idx, tol=1)
            else:
                self.peaks_min = insert_peak(self.peaks_min, idx)
        else:
            if idx in self.peaks_max:
                self.peaks_max = remove_peak(self.peaks_max, idx, tol=1)
            else:
                self.peaks_max = insert_peak(self.peaks_max, idx)
        self.peaks_min, self.peaks_max = enforce_alternation(self.peaks_min, self.peaks_max)
        self.sig_plot.set_peaks(self.peaks_min, self.peaks_max)
        self._recompute_periods_and_metrics()

    # ---------- Periods & Metrics ----------
    def _recompute_periods_and_metrics(self):
        if self.t_raw is None or self.y_raw is None:
            return
        # Build periods from the analysis signal (filtered if available) for visuals
        t, y_base = self._current_signal()
        y_det = self.y_filt if (self.y_filt is not None) else y_base
        self.seg_info = build_period_indices(t, self.peaks_min, self.peaks_max, strategy="min2min")
        self.periods = slice_periods(t, y_det, self.seg_info.indices)

        if not self.seg_info or not self.seg_info.indices:
            self.periods = []
            self.metrics_agg = {}
            self._render_metrics_tab()
            self._update_overlay_plot()
            return

        # Also slice RAW (ambient-corrected/raw) periods on the same indices
        periods_raw = slice_periods(t, y_base, self.seg_info.indices)

        if not self.periods or len(self.periods) == 0:
            self.metrics_agg = {}
            self._render_metrics_tab(); self._update_overlay_plot()
            return
    
        # Metrics
        per_f = metrics_for_periods(self.periods) or []
        per_r = metrics_for_periods(periods_raw) or []
        agg_f = aggregate_metrics(per_f) if per_f else {}
        agg_r = aggregate_metrics(per_r) if per_r else {}
        self._render_metrics_tab_from_aggs(agg_r, agg_f)

        # Merge both into a flat dict for rendering/export
        #self.metrics_period = {"filtered": per_f, "raw": per_r}
        keys = sorted(set(k.split("_")[0] for k in list(agg_f.keys())+list(agg_r.keys())))
        self.metrics_agg = {}
        for base in keys:
            self.metrics_agg[f"{base}_raw_mean"]  = agg_r.get(f"{base}_mean",  float("nan"))
            self.metrics_agg[f"{base}_raw_std"]   = agg_r.get(f"{base}_std",   float("nan"))
            self.metrics_agg[f"{base}_filt_mean"] = agg_f.get(f"{base}_mean",  float("nan"))
            self.metrics_agg[f"{base}_filt_std"]  = agg_f.get(f"{base}_std",   float("nan"))
        self._render_metrics_tab()

        # Build spans for visual "to be removed" preview (edges + future selections)
        spans = []
        if self.seg_info and self.seg_info.indices:
            # left appendix
            i0, _ = self.seg_info.indices[0]
            spans.append((self.t_raw[0], self.t_raw[i0]))
            # right appendix
            _, jlast = self.seg_info.indices[-1]
            spans.append((self.t_raw[jlast], self.t_raw[-1]))
            # TODO: add user-selected deletions here (period index -> (i,j))
        self.sig_plot.set_removed_spans(spans)
        # For quick preview in the Periods tab, print a short summary
        self._render_periods_tab()
        # Compute metrics
        self.metrics_period = metrics_for_periods(self.periods)
        self.metrics_agg = aggregate_metrics(self.metrics_period)
        self._render_metrics_tab()

        # Build period boundaries for drawing (using indices from seg_info)
        bounds = []
        for p_idx, (i, j) in enumerate(self.seg_info.indices, start=1):
            bounds.append((self.t_raw[i], self.t_raw[j], p_idx))
        self.sig_plot.set_period_boundaries(bounds, removed=getattr(self, "removed_periods", set()))

        self._update_overlay_plot()

        # TODO: deprecate this func in favor of separate calls
        self.recompute_periods()
        self.compute_metrics_aggregates()


    def _render_periods_tab(self):
        self.periods_text.delete("1.0", "end")
        if not self.periods:
            self.periods_text.insert("end", "No periods yet. Detect peaks first.")
            return
        lines = []
        for k, (t_seg, y_seg) in enumerate(self.periods, start=1):
            dur = t_seg[-1] - t_seg[0]
            lines.append(f"Period {k:02d}: N={len(t_seg)}  duration={dur:.3f}s")
        self.periods_text.insert("end", "\n".join(lines))


    def _update_overlay_plot(self):
        if not hasattr(self, "tabs") or not hasattr(self.tabs, "overlay_ax"): return

        ax = self.tabs.overlay_ax
        canvas = self.tabs.overlay_canvas
        ax.clear()

         
        # If we have no periods computed yet, show a helpful title
        if not getattr(self, "periods", None) or len(self.periods) == 0:
            ax.set_title("No periods yet — detect extrema first.")
            canvas.draw_idle()
            return

        # Resample current analysis signal periods (filtered if available)
        res = resample_periods(self.periods, n_points=200)
        try:
            X, tau = res
        except Exception:
            X = res
            tau = np.linspace(0.0, 1.0, X.shape[1])

        if X is None or len(X) == 0:
            ax.set_title("No periods to display")
            canvas.draw_idle()
            return

        kept_rows, labels = self._kept_row_indices_and_labels()
        if not kept_rows:
            ax.set_title("All periods removed — nothing to display")
            canvas.draw_idle()
            return

        # Select kept rows (by original order) so numbering matches Signal tab
        X_kept = X[kept_rows, :]

        # Normalize and average
        Xn = normalize_periods(X_kept, mode="baseline")
        mu, sd = average_period(Xn)

        # Draw overlay
        draw_periods_overlay(ax, tau, Xn, mu, sd, labels=labels, labeled_max=12)

        canvas.draw_idle()

    
        # Fail-safe: show error on the canvas to aid debugging (optional)
        #ax.clear()
        #ax.text(0.02, 0.95, f"Overlay error:\n{e}", transform=ax.transAxes,
        #        va="top", ha="left", fontsize=9, color="crimson")
        #canvas.draw_idle()
    

    def _kept_row_indices_and_labels(self):
        """
        Returns:
        kept_rows: list[int]     -- 0-based row indices into self.periods / resampled matrix
        labels:    list[str]     -- e.g., ["Period 1", "Period 3", ...] using original numbering
        Uses self.seg_info.indices order (1..N). Skips self.removed_periods if present.
        """
        kept_rows, labels = [], []
        if not getattr(self, "seg_info", None) or not self.seg_info.indices:
            return kept_rows, labels

        removed = getattr(self, "removed_periods", set())  # {1-based indices}
        for row_idx_0, (_ij) in enumerate(self.seg_info.indices):
            k = row_idx_0 + 1  # 1-based label, consistent with Signal tab
            if k in removed:
                continue
            kept_rows.append(row_idx_0)
            labels.append(f"Period {k}")
        return kept_rows, labels


    def _render_metrics_tab(self):
        # Clear
        for row in self.metrics_tree.get_children(): self.metrics_tree.delete(row)
        if not self.metrics_agg: return
        # Only render metrics that have at least one non-NaN value
        bases = sorted(set(k.rsplit("_", 2)[0] for k in self.metrics_agg.keys()))
        for base in bases:
            row = (
                base,
                self.metrics_agg.get(f"{base}_raw_mean", float("nan")),
                self.metrics_agg.get(f"{base}_raw_std", float("nan")),
                self.metrics_agg.get(f"{base}_filt_mean", float("nan")),
                self.metrics_agg.get(f"{base}_filt_std", float("nan")),
            )
            if all((isinstance(v, float) and (v != v)) for v in row[1:]):  # all NaN
                continue
            self.metrics_tree.insert("", "end", values=(row[0], *(f"{v:.6g}" for v in row[1:])))
        
        # Deprecate this func
        agg_r = getattr(self, "metrics_agg_raw", {})
        agg_f = getattr(self, "metrics_agg_filt", {})
        self._render_metrics_tab_from_aggs(agg_r, agg_f)
    
    
    
    ##################
    # NEW, separate function, just periods
    def recompute_periods(self):
        """
        Build kept periods for the analysis signal (filtered if available) and for the raw baseline,
        using the current segmentation indices and removed_periods set. Also updates the Overlay tab.
        Produces: self.periods        (list of (t_i, y_i) or as your segment.py returns inside slice_periods)
                self.periods_raw    (same indices, raw baseline)
        """
        # need segmentation indices
        if not getattr(self, "seg_info", None) or not self.seg_info.indices:
            self.periods = []
            self.periods_raw = []
            self._update_overlay_plot()
            return

        # choose series
        t, y_base = self._current_signal()
        y_det = self.y_filt if (self.y_filt is not None) else y_base

        # keep-by-index respecting removed_periods (1-based)
        removed = getattr(self, "removed_periods", set())
        kept_indices = [ij for k, ij in enumerate(self.seg_info.indices, start=1) if k not in removed]
        if not kept_indices:
            self.periods = []
            self.periods_raw = []
            self._update_overlay_plot()
            return

        # slice on SAME indices for both series
        self.periods = slice_periods(t, y_det, kept_indices)
        self.periods_raw = slice_periods(t, y_base, kept_indices)

        # refresh overlay (uses self.periods)
        self._update_overlay_plot()
        #

    # app.py
    def compute_metrics_aggregates(self):
        """
        Use metrics.py to compute per-period metrics for filtered and raw,
        aggregate them, store, and render the Metrics tab.
        Requires self.periods and self.periods_raw built by recompute_periods().
        Produces: self.metrics_agg_raw, self.metrics_agg_filt
        """
        # if no periods, clear table
        if not getattr(self, "periods", None):
            self.metrics_agg_raw = {}
            self.metrics_agg_filt = {}
            self._render_metrics_tab_from_aggs(self.metrics_agg_raw, self.metrics_agg_filt)
            return

        # Use your already-imported metrics.py API

        per_f = metrics_for_periods(self.periods) or []
        per_r = metrics_for_periods(self.periods_raw) or []
        agg_f = aggregate_metrics(per_f) if per_f else {}
        agg_r = aggregate_metrics(per_r) if per_r else {}

        self.metrics_agg_raw = agg_r
        self.metrics_agg_filt = agg_f

        self._render_metrics_tab_from_aggs(agg_r, agg_f)
        #

    #
    def _clear_metrics_table(self):
        if hasattr(self, "metrics_tree"):
            for row in self.metrics_tree.get_children():
                self.metrics_tree.delete(row)

    def _normalize_agg(self, agg):
        """
        Accepts either:
        A) {'APD90_mean': x, 'APD90_std': y, 'rise_10_90_mean': ...}
        B) {'APD90': {'mean': x, 'std': y}, 'rise_10_90': {'mean':...,'std':...}}
        Returns: dict base -> (mean, std)
        """
        if not agg:
            return {}
        out = {}
        for k, v in agg.items():
            if isinstance(v, dict):
                mean = v.get("mean", float("nan"))
                std  = v.get("std", float("nan"))
                out[k] = (mean, std)
            else:
                if k.endswith("_mean"):
                    base = k[:-5]
                    mean = v
                    cur = out.get(base, (float("nan"), float("nan")))
                    out[base] = (mean, cur[1])
                elif k.endswith("_std"):
                    base = k[:-4]
                    std = v
                    cur = out.get(base, (float("nan"), float("nan")))
                    out[base] = (cur[0], std)
                # ignore other keys if any
        return out

    def _render_metrics_tab_from_aggs(self, agg_raw, agg_filt):
        """
        agg_raw / agg_filt: whatever your metrics.py returns; we normalize them
        and fill the table with columns: Metric | Raw mean | Raw std | Filt mean | Filt std
        """
        self._clear_metrics_table()
        if not hasattr(self, "metrics_tree"):
            return

        norm_r = self._normalize_agg(agg_raw)
        norm_f = self._normalize_agg(agg_filt)
        bases = sorted(set(norm_r.keys()) | set(norm_f.keys()))
        if not bases:
            return

        # optional ordering: put common electrophys metrics first
        priority = ["APD20","APD50","APD90","rise_10_90","decay_90_10",
                    "time_to_peak","upstroke_angle_deg","downstroke_angle_deg",
                    "auc_above_baseline","duration_s","amp_mean","amp_std","amp_peak","amp_min","amp_range","slope_max","slope_min"]
        order = [b for b in priority if b in bases] + [b for b in bases if b not in priority]

        def fmt(x):
            if x is None or (isinstance(x, float) and math.isnan(x)):
                return "—"
            return f"{x:.4g}"

        for base in order:
            rmu, rsd = norm_r.get(base, (float("nan"), float("nan")))
            fmu, fsd = norm_f.get(base, (float("nan"), float("nan")))
            # if literally everything is NaN, skip
            if all(isinstance(v, float) and math.isnan(v) for v in (rmu, rsd, fmu, fsd)):
                continue
            self.metrics_tree.insert(
                "", "end",
                values=(base, fmt(rmu), fmt(rsd), fmt(fmu), fmt(fsd))
            )
            #    
            

    # ---------- Export ----------
    def export_all(self):
        if self.t_raw is None or self.y_raw is None or not self.periods:
            messagebox.showinfo("Export", "Nothing to export yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")], title="Save outputs")
        if not path:
            return

        base = os.path.splitext(path)[0]
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            # Parameters sheet
            params = {
                "smoothing_level": self.filter_engine.smoothing_level,
                "ambient_offset_ms": self.meta_amb.get("offset_ms"),
                "ambient_scale": self.meta_amb.get("scale"),
                "n_periods": len(self.periods),
            }
            pd.DataFrame([params]).to_excel(writer, sheet_name="Parameters", index=False)

            # Periods sheet (durations)
            durs = [float(t_seg[-1]-t_seg[0]) for (t_seg, _y) in self.periods]
            pd.DataFrame({"period": list(range(1,len(durs)+1)), "duration_s": durs}).to_excel(writer, sheet_name="Periods", index=False)

            # Metrics (per-period)
            pd.DataFrame(self.metrics_period).to_excel(writer, sheet_name="Metrics_Period", index=False)

            # Metrics aggregated
            pd.DataFrame([self.metrics_agg]).to_excel(writer, sheet_name="Metrics_Aggregated", index=False)

            # NEW: Resampled periods and average (from current analysis signal)
            X, tau = resample_periods(self.periods, n_points=200)
            Xn = normalize_periods(X, mode="baseline")
            mu, sd = average_period(Xn)
            df_res = pd.DataFrame({"tau": tau})
            for i in range(Xn.shape[0]):
                df_res[f"period_{i+1}"] = Xn[i]
            df_res["mean"] = mu
            df_res["std"]  = sd
            df_res.to_excel(writer, sheet_name="Resampled_Periods", index=False)
            #

        # NEW: save figures alongside the xlsx
        # 1) Raw vs filtered
        fig1 = plt.figure(figsize=(8,3))
        t, y_base = self._current_signal()
        plt.plot(t, y_base, label="Raw" if self.y_corr is None else "Ambient-corrected", lw=1.0, alpha=0.7)
        if self.y_filt is not None:
            plt.plot(t, self.y_filt, label=f"Filtered (S={self.filter_engine.smoothing_level})", lw=1.2)
        plt.legend(bbox_to_anchor=(1.0, 1.3), loc="upper right"); 
        plt.xlabel("Time (s)"); plt.ylabel("Signal"); plt.tight_layout()
        fig1.savefig(base + "_signal.png", dpi=160)
        plt.close(fig1)

        # 2) Overlaid resampled periods + average
        try:
            if getattr(self, "periods", None) and len(self.periods) > 0:
                res = resample_periods(self.periods, n_points=200)
                try:
                    X, tau = res
                except Exception:
                    X = res
                    tau = np.linspace(0.0, 1.0, X.shape[1])

                kept_rows, labels = self._kept_row_indices_and_labels()
                if kept_rows:
                    X_kept = X[kept_rows, :]
                    Xn = normalize_periods(X_kept, mode="baseline")
                    mu, sd = average_period(Xn)

                fig2 = plt.figure(figsize=(8,3))
                ax2 = fig2.add_subplot(111)

                draw_periods_overlay(ax2, tau, Xn, mu, sd, labels=labels, labeled_max=12)
                fig2.savefig(base + "_periods_overlay.png", dpi=160)
                plt.close(fig2)  

        except Exception as e:
            # optional: log but don't crash export
            print("Export overlay failed:", e)    

        # Also dump a session.json alongside
        session = {
            "smoothing_level": self.filter_engine.smoothing_level,
            "peaks_min": self.peaks_min.tolist(),
            "peaks_max": self.peaks_max.tolist(),
            "removed_periods": [],  # future: track brushed removals
            "meta_ambient": self.meta_amb,
            "n_periods": len(self.periods),
        }
        try:
            with open(os.path.splitext(path)[0] + "_session.json", "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2)
        except Exception:
            pass
        self.sidebar.status.config(text=f"Exported: {os.path.basename(path)}")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
