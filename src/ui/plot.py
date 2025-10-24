
from __future__ import annotations
import numpy as np
from typing import Callable, Optional, Tuple, Sequence
import matplotlib
matplotlib.use("Agg")  # safe default; app.py can switch to TkAgg at runtime
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
        #if self.y_filt is not None:
        #    self._filt_line, = self.ax.plot(self.t, self.y_filt, lw=1.2, label="Filtered")
        if self.peaks_min.size > 0:
            self._min_scatter = self.ax.scatter(self.t[self.peaks_min], y_for_peaks[self.peaks_min],
                                                s=18, c="tab:blue", marker="v", label="min")
        if self.peaks_max.size > 0:
            self._max_scatter = self.ax.scatter(self.t[self.peaks_max], y_for_peaks[self.peaks_max],
                                                s=18, c="tab:orange", marker="^", label="max")
        # NEW: draw removed spans in light red under everything
        for (t0, t1) in getattr(self, "_removed_spans", []):
            self.ax.axvspan(t0, t1, color="red", alpha=0.15, linewidth=0)
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
