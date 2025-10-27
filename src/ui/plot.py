from __future__ import annotations
import numpy as np
from typing import Callable, Optional, Sequence
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class SignalPlot:
    """
    Matplotlib plot embedded in Tk for raw/filtered signals and editable peaks.
    """
    def __init__(self, parent, on_click_peak: Optional[Callable[[float], None]] = None):
        self.parent = parent
        self.fig = Figure(figsize=(6, 3), dpi=100, tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.widget = self.canvas.get_tk_widget()
        self.on_click_peak = on_click_peak

        self.t: Optional[np.ndarray] = None
        self.y_raw: Optional[np.ndarray] = None
        self.y_filt: Optional[np.ndarray] = None
        self.peaks_min: np.ndarray = np.array([], dtype=int)
        self.peaks_max: np.ndarray = np.array([], dtype=int)
        self._cid = self.canvas.mpl_connect("button_press_event", self._on_click)
        self._edit_enabled = False

        self._raw_line = None
        self._filt_line = None
        self._min_scatter = None
        self._max_scatter = None

        self._filt_legend_label = "Filtered"

    def get_widget(self):
        return self.widget

    def set_data(self, t: np.ndarray, y_raw: np.ndarray, y_filt: Optional[np.ndarray] = None):
        self.t = t
        self.y_raw = y_raw
        self.y_filt = y_filt
        self._redraw()

    def set_filter_label(self, text: str):
        self._filt_legend_label = text    

    def set_peaks(self, peaks_min: Sequence[int], peaks_max: Sequence[int]):
        self.peaks_min = np.asarray(peaks_min, dtype=int)
        self.peaks_max = np.asarray(peaks_max, dtype=int)
        self._redraw()

    def enable_edit(self, enabled: bool):
        self._edit_enabled = bool(enabled)

    def set_removed_spans(self, spans):  # spans = list of (t_start, t_end)
        self._removed_spans = list(spans or [])
        self._redraw()

    def set_period_boundaries(self, boundaries, removed=set()):
        """
        boundaries: list of (t_start, t_end, idx) for each period in time axis
        removed: set of integer period indices that the user marked for deletion
        """
        self._period_bounds = list(boundaries or [])
        self._periods_removed = set(removed or set())
        self._redraw()

    def _draw_period_boundaries(self):
        if not hasattr(self, "_period_bounds"): return
        for (t0, t1, k) in self._period_bounds:
            color = "red" if k in self._periods_removed else "k"
            # dashed separators
            self.ax.axvline(t0, color=color, ls="--", lw=0.8, alpha=0.5)
            self.ax.axvline(t1, color=color, ls="--", lw=0.8, alpha=0.5)
            # label number
            tx = 0.5*(t0+t1)
            ymin, ymax = self.ax.get_ylim()
            ty = ymin + 0.92*(ymax-ymin)
            self.ax.text(tx, ty, f"{k}", ha="center", va="top",
                        fontsize=9, color=color, bbox=dict(facecolor="white", alpha=0.6, lw=0))    

    def _clear_extrema_artists(self):
        for art in getattr(self, "_extrema_artists", []):
            try: art.remove()
            except Exception: pass
        self._extrema_artists = []

    def _draw_extrema_arrows(self, t, y, idxs_up, idxs_dn):
        self._clear_extrema_artists()
        # arrow heights as a fraction of signal span
        if len(y) == 0: return
        yspan = max(1e-9, (np.nanmax(y) - np.nanmin(y)))
        h = 0.12 * yspan
        for i in idxs_up:
            a = self.ax.annotate("", xy=(t[i], y[i]+h*0.5), xytext=(t[i], y[i]-h*0.5),
                                arrowprops=dict(arrowstyle='-|>', lw=1.2, color='red'))
            self._extrema_artists.append(a)
        for i in idxs_dn:
            a = self.ax.annotate("", xy=(t[i], y[i]-h*0.5), xytext=(t[i], y[i]+h*0.5),
                                arrowprops=dict(arrowstyle='-|>', lw=1.2, color='red'))
            self._extrema_artists.append(a)    

    def _redraw(self):
        self.ax.clear()
        if self.t is None or self.y_raw is None:
            self.ax.set_title("Load a signal to begin")
            self.canvas.draw_idle()
            return
        y_for_peaks = self.y_filt if self.y_filt is not None else self.y_raw
        self._raw_line, = self.ax.plot(self.t, self.y_raw, lw=1.0, alpha=0.7, label="Raw")
        if self.y_filt is not None:
            self._filt_line, = self.ax.plot(self.t, self.y_filt, lw=1.2, label=self._filt_legend_label)
        if self.peaks_min.size > 0:
            self._min_scatter = self.ax.scatter(self.t[self.peaks_min], y_for_peaks[self.peaks_min],
                                                s=18, c="tab:blue", marker="v", label="min")
        if self.peaks_max.size > 0:
            self._max_scatter = self.ax.scatter(self.t[self.peaks_max], y_for_peaks[self.peaks_max],
                                                s=18, c="tab:orange", marker="^", label="max")
        # Draw arrows for extrema
        if hasattr(self, "peaks_max") and hasattr(self, "peaks_min"):
            self._draw_extrema_arrows(self.t, y_for_peaks, self.peaks_max, self.peaks_min)    
        # Draw removed spans in light red under everything
        for (t0, t1) in getattr(self, "_removed_spans", []):
            self.ax.axvspan(t0, t1, color="red", alpha=0.15, linewidth=0)

        self._draw_period_boundaries()
    
        self.ax.legend(loc="upper right")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Signal (a.u.)")
        self.ax.grid(True, alpha=0.2)
        self.canvas.draw_idle()

    def _on_click(self, event):
        if not self._edit_enabled or self.t is None or self.y_raw is None:
            return
        if event.inaxes != self.ax:
            return
        if self.on_click_peak is not None and event.xdata is not None:
            try:
                self.on_click_peak(float(event.xdata))
            except Exception:
                pass


def draw_periods_overlay(ax, tau, Xn, mean, std, *, labels=None, labeled_max=12):
    """
    tau: (P, ) normalized time
    Xn:  (N, P) normalized periods
    mean, std: (P, )
    labels: optional list[str] of length N, e.g., ["Period 1", "Period 3", ...]
    labeled_max: how many individual periods to label in legend (cap to avoid clutter)
    """
    ax.clear()

    # In case of empty input
    if Xn is None or len(np.shape(Xn)) != 2 or Xn.shape[0] == 0:
        ax.set_title("No periods available")
        ax.figure.tight_layout()
        return

    # Draw individual periods
    n = Xn.shape[0]
    for i in range(n):
        lbl = None
        if labels is not None and i < len(labels):
            lbl = labels[i] if i < labeled_max else None
        else:
            lbl = (f"Period {i+1}" if i < labeled_max else None)
        ax.plot(tau, Xn[i], alpha=0.35, lw=1.0, label=lbl)

    # Mean and \pm std band
    ax.plot(tau, mean, lw=1.8, label="Mean")
    if std is not None and np.all(np.isfinite(std)):
        ax.fill_between(tau, mean-std, mean+std, alpha=0.15, linewidth=0)

    ax.set_xlabel("Normalized time τ")
    ax.set_ylabel("Normalized amplitude")
    
    # Place outside if many handles
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, ncol=2, fontsize=9, frameon=True, loc="upper right")
    ax.figure.tight_layout()