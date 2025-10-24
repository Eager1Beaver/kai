from __future__ import annotations
import os, json, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure TkAgg backend for interactive use
import matplotlib
matplotlib.use("TkAgg")

from src.filters import FilterEngine
from src.io import load_signal, subtract_ambient
from src.detect import find_peaks_adaptive, snap_to_local_extremum, insert_peak, remove_peak, enforce_alternation
from src.segment import build_period_indices, slice_periods, resample_periods, normalize_periods, average_period
from src.metrics import metrics_for_periods, aggregate_metrics

from .plot import SignalPlot
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
        self.metrics_tree.pack(fill="both", expand=True)

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
        self.sidebar.status.config(text=f"Pacing set to {self.pacing_hz_manual or 'auto'} Hz")
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
        y_det = self.y_filt if self.y_filt is not None else y_base
        self.seg_info = build_period_indices(t, self.peaks_min, self.peaks_max, strategy="min2min")
        self.periods = slice_periods(t, y_det, self.seg_info.indices)
        #t, y = self._current_signal()
        #self.seg_info = build_period_indices(t, self.peaks_min, self.peaks_max, strategy="min2min")
        #self.periods = slice_periods(t, y, self.seg_info.indices)

        # Also slice RAW (ambient-corrected/raw) periods on the same indices
        periods_raw = slice_periods(t, y_base, self.seg_info.indices)

        # Metrics
        per_f = metrics_for_periods(self.periods)
        per_r = metrics_for_periods(periods_raw)
        agg_f = aggregate_metrics(per_f)
        agg_r = aggregate_metrics(per_r)

        # Merge both into a flat dict for rendering/export
        self.metrics_period = {"filtered": per_f, "raw": per_r}
        self.metrics_agg = {}
        for k in set(k for d in per_f+per_r for k in d.keys()):
            self.metrics_agg[f"{k}_raw_mean"]  = agg_r.get(f"{k}_mean",  float("nan"))
            self.metrics_agg[f"{k}_raw_std"]   = agg_r.get(f"{k}_std",   float("nan"))
            self.metrics_agg[f"{k}_filt_mean"] = agg_f.get(f"{k}_mean",  float("nan"))
            self.metrics_agg[f"{k}_filt_std"]  = agg_f.get(f"{k}_std",   float("nan"))
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

    def _render_metrics_tab(self):
        # Clear
        for row in self.metrics_tree.get_children(): self.metrics_tree.delete(row)
        if not self.metrics_agg: return
        keys_priority = ["APD20","APD50","APD90","time_to_peak","rise_10_90","decay_90_10",
                        "upstroke_angle_deg","downstroke_angle_deg","auc_above_baseline"]
        for base in keys_priority:
            vals = (
                base,
                self.metrics_agg.get(f"{base}_raw_mean", float("nan")),
                self.metrics_agg.get(f"{base}_raw_std", float("nan")),
                self.metrics_agg.get(f"{base}_filt_mean", float("nan")),
                self.metrics_agg.get(f"{base}_filt_std", float("nan")),
            )
            self.metrics_tree.insert("", "end",
                values=(vals[0], *(f"{v:.6g}" for v in vals[1:])))

        '''for row in self.metrics_tree.get_children():
            self.metrics_tree.delete(row)
        if not self.metrics_agg:
            return
        # Insert top metrics (a selection to keep it readable)
        keys_priority = [
            "APD20_mean","APD50_mean","APD90_mean",
            "time_to_peak_mean","rise_10_90_mean","decay_90_10_mean",
            "upstroke_angle_deg_mean","downstroke_angle_deg_mean",
            "auc_above_baseline_mean",
        ]
        for key in keys_priority:
            mean = self.metrics_agg.get(key, float("nan"))
            std = self.metrics_agg.get(key.replace("_mean", "_std"), float("nan"))
            self.metrics_tree.insert("", "end", values=(key, f"{mean:.6g}", f"{std:.6g}"))'''

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
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper right"); 
        plt.xlabel("Time (s)"); plt.ylabel("Signal"); plt.tight_layout()
        fig1.savefig(base + "_signal.png", dpi=160)
        plt.close(fig1)

        # 2) Overlaid resampled periods + average
        if len(self.periods) > 0:
            X, tau = resample_periods(self.periods, n_points=200)
            Xn = normalize_periods(X, mode="baseline")
            mu, sd = average_period(Xn)
            fig2 = plt.figure(figsize=(8,3))
            for row in Xn:
                plt.plot(tau, row, alpha=0.25)
            plt.plot(tau, mu, lw=1.6, label="mean")
            plt.legend(); plt.xlabel("Normalized time τ"); plt.ylabel("Norm. amplitude")
            plt.tight_layout()
            fig2.savefig(base + "_periods_overlay.png", dpi=160)
            plt.close(fig2)    

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
