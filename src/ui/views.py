from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class Sidebar(ttk.Frame):
    def __init__(
            self, master, *, 
            on_load_raw, 
            on_load_ambient, 
            on_detect, 
            on_export, 
            on_toggle_edit, 
            on_apply_offset_scale, 
            on_smooth_changed, 
            on_set_pacing,
            ):
        super().__init__(master, padding=8)
        self._on_smooth_changed = on_smooth_changed
        self.columnconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Load section
        ttk.Label(self, text="Session", style="Heading.TLabel").grid(row=0, column=0, sticky="w", pady=(0,4))
        ttk.Button(self, text="Load Raw...", command=on_load_raw).grid(row=1, column=0, sticky="ew")
        ttk.Button(self, text="Load Ambient (optional)...", command=on_load_ambient).grid(row=2, column=0, sticky="ew")

        # Ambient alignment
        frm = ttk.LabelFrame(self, text="Ambient alignment", padding=6)
        frm.grid(row=3, column=0, sticky="ew", pady=(8,4))
        ttk.Label(frm, text="Offset (ms):").grid(row=0, column=0, sticky="w")
        self.offset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(frm, textvariable=self.offset_var, width=8).grid(row=0, column=1, sticky="w", padx=(4,0))
        ttk.Label(frm, text="Scale:").grid(row=1, column=0, sticky="w")
        self.scale_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frm, textvariable=self.scale_var, width=8).grid(row=1, column=1, sticky="w", padx=(4,0))
        ttk.Button(frm, text="Apply", 
                   command=lambda: on_apply_offset_scale(self.offset_var.get(), 
                                                         self.scale_var.get()))\
                                                            .grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4,0))

        # Set pacing
        pace = ttk.LabelFrame(self, text="Pacing (manual)", padding=6)
        pace.grid(row=4, column=0, sticky="ew", pady=(8,4))
        ttk.Label(pace, text="Hz:").grid(row=0, column=0, sticky="w")
        self.pace_var = tk.DoubleVar(value=1.0)
        ttk.Entry(pace, textvariable=self.pace_var, width=8).grid(row=0, column=1, padx=(4,0), sticky="w")
        ttk.Button(pace, text="Use", command=lambda: on_set_pacing(self.pace_var.get())).grid(row=0, column=2, padx=(6,0))
        self.pace_status = ttk.Label(pace, text="Current: auto", foreground="#555")
        self.pace_status.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4,0))

        # Smoothing
        lab = ttk.Label(self, text="Smoothing", style="Heading.TLabel")
        lab.grid(row=5, column=0, sticky="w", pady=(8,4))

        # Subframe so the scale can expand while the label sits at the right
        smooth_frame = ttk.Frame(self)
        smooth_frame.grid(row=6, column=0, sticky="ew")
        smooth_frame.grid_columnconfigure(0, weight=1)  # scale expands
        smooth_frame.grid_columnconfigure(1, weight=0)

        self.smooth_label = ttk.Label(smooth_frame, text="S = 0")
        self.smooth_label.grid(row=0, column=1, sticky="e", padx=(8,0))

        # Avoid re-entrancy when snapping
        self._snapping = False
        
        self.scale = ttk.Scale(
            smooth_frame, from_=0, to=5, orient="horizontal", length=260,
            command=lambda v: self._on_smooth_ui(v))
        self.scale.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(self, text="0 = raw . 5 = heavy")\
            .grid(row=7, column=0, sticky="w", pady=(2,0))

        # Actions
        ttk.Button(self, text="Detect Peaks", command=on_detect).grid(row=8, column=0, sticky="ew", pady=(8,0))
        self.edit_btn = ttk.Button(self, text="Toggle Edit Mode", command=on_toggle_edit)
        self.edit_btn.grid(row=9, column=0, sticky="ew", pady=(4,0))

        ttk.Button(self, text="Export XLSX/CSV", command=on_export).grid(row=10, column=0, sticky="ew", pady=(16,0))

        self.status = ttk.Label(self, text="Ready.", anchor="w")
        self.status.grid(row=11, column=0, sticky="ew", pady=(12,0))


    def _on_smooth_ui(self, v):
        # Ignore callbacks
        if self._snapping:
            return

        # Compute discrete step
        try:
            s = int(round(float(v)))
        except Exception:
            return
        if s < 0: s = 0
        if s > 5: s = 5

        # Update label immediately
        self.smooth_label.config(text=f"S = {s}")

        # Notify the app (filter pipeline, redraw, etc.)
        if self._on_smooth_changed:
            self._on_smooth_changed(s)

        # Visually snap the thumb *after* Tk finishes current callback
        # This avoids a re-entrant call stack and TclError.
        def _snap():
            self._snapping = True
            try:
                self.scale.set(s)  # this will trigger command, but early-return above
            finally:
                # Defer clearing by one more idle to ensure Tk settles
                self.after_idle(lambda: setattr(self, "_snapping", False))
        self.after_idle(_snap)


class Tabs(ttk.Notebook):
    def __init__(self, master):
        super().__init__(master)
        self.signal_frame = ttk.Frame(self)
        self.periods_frame = ttk.Frame(self)
        self.metrics_frame = ttk.Frame(self)
        self.overlay_frame = ttk.Frame(self)

        self.add(self.signal_frame, text="Signal")
        self.add(self.periods_frame, text="Periods")
        self.add(self.overlay_frame, text="Overlay") 
        self.add(self.metrics_frame, text="Metrics")       

        # Matplotlib canvas for overlay plot
        self.overlay_fig = plt.Figure(figsize=(7.5, 3.2), dpi=100)
        self.overlay_ax = self.overlay_fig.add_subplot(111)
        self.overlay_canvas = FigureCanvasTkAgg(self.overlay_fig, master=self.overlay_frame)
        self.overlay_canvas.get_tk_widget().pack(fill="both", expand=True)
