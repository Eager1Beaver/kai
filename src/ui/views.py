from __future__ import annotations
import tkinter as tk
from tkinter import ttk

class Sidebar(ttk.Frame):
    def __init__(
            self, master, *, 
            on_load_raw, on_load_ambient, 
            on_detect, on_export, 
            on_toggle_edit, on_apply_offset_scale, 
            on_smooth_changed, on_set_pacing,
            ):
        super().__init__(master, padding=8)
        self.columnconfigure(0, weight=1)

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
        ttk.Button(frm, text="Apply", command=lambda: on_apply_offset_scale(self.offset_var.get(), self.scale_var.get())).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4,0))

        # Smoothing
        lab = ttk.Label(self, text="Smoothing", style="Heading.TLabel")
        lab.grid(row=4, column=0, sticky="w", pady=(8,4))
        self.smooth_var = tk.IntVar(value=0)
        #self.scale = ttk.Scale(self, from_=0, to=5, orient="horizontal", command=lambda v: on_smooth_changed(int(float(v))))
        self.scale = ttk.Scale(
            self, from_=0, to=5, orient="horizontal",
            command=lambda v: (self.smooth_label.config(text=f"S = {int(float(v))}"),
                            on_smooth_changed(int(float(v))))) #
        self.scale.grid(row=5, column=0, sticky="ew")
        self.smooth_label = ttk.Label(self, text="S = 0") #
        self.smooth_label.grid(row=5, column=0, sticky="e", padx=(0,4)) #
        ttk.Label(self, text="0 = raw · 5 = heavy").grid(row=6, column=0, sticky="w")

        # NEW: pacing
        pace = ttk.LabelFrame(self, text="Pacing (manual)", padding=6)
        pace.grid(row=7, column=0, sticky="ew", pady=(8,4))
        ttk.Label(pace, text="Hz:").grid(row=0, column=0, sticky="w")
        self.pace_var = tk.DoubleVar(value=0.0)
        ttk.Entry(pace, textvariable=self.pace_var, width=8).grid(row=0, column=1, padx=(4,0), sticky="w")
        ttk.Button(pace, text="Use", command=lambda: on_set_pacing(self.pace_var.get())).grid(row=0, column=2, padx=(6,0))

        # Actions
        ttk.Button(self, text="Detect Peaks", command=on_detect).grid(row=8, column=0, sticky="ew", pady=(8,0))
        self.edit_btn = ttk.Button(self, text="Toggle Edit Mode", command=on_toggle_edit)
        self.edit_btn.grid(row=9, column=0, sticky="ew", pady=(4,0))

        ttk.Button(self, text="Export XLSX/CSV", command=on_export).grid(row=10, column=0, sticky="ew", pady=(16,0))

        self.status = ttk.Label(self, text="Ready.", anchor="w")
        self.status.grid(row=11, column=0, sticky="ew", pady=(12,0))

class Tabs(ttk.Notebook):
    def __init__(self, master):
        super().__init__(master)
        self.signal_frame = ttk.Frame(self)
        self.periods_frame = ttk.Frame(self)
        self.metrics_frame = ttk.Frame(self)

        self.add(self.signal_frame, text="Signal")
        self.add(self.periods_frame, text="Periods")
        self.add(self.metrics_frame, text="Metrics")
