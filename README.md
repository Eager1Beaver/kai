# KAI — Calcium Imaging Periodic Signal Analyzer

Analyze periodic **calcium-imaging** traces end‑to‑end: load raw (+ optional ambient), subtract background, smooth, detect peaks, segment into periods, curate, compute metrics (incl. APD20/50/90), visualize overlays, and export a complete Excel/CSV bundle — either in a **web UI (Streamlit)** or a **local desktop UI (Tkinter)**.

---

## ✨ Highlights

- **Two UIs**: Streamlit web app (`app_streamlit.py`) and a fast local Tk app (`main.py` → `src/ui/app.py`).
- **Ambient subtraction** with manual **offset** (ms) and **scale** controls.
- **Single smoothing dial (S=0..5)** with tuned Savitzky–Golay / Butterworth / Gaussian backends.
- **Adaptive peak detection** with pacing‑aware spacing and robust thresholds.
- **Interactive period curation**: click maxima to toggle whole periods; click minima to add/remove boundaries.
- **Overlay view**: time‑normalize periods, show mean ± dispersion.
- **Rich metrics** (per‑period and aggregated), incl. **APD20/50/90**, rise/decay, slopes/angles, AUC.
- **Reproducible exports**: structured Excel workbook, figures, and a session JSON snapshot.

---

## 📦 Repository layout

```
.
├── app_streamlit.py          # Entry point for the Streamlit web app
├── kai.code-workspace        # VS Code workspace (optional)
├── main.py                   # Entry point for the local Tkinter desktop app
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── data/
│   ├── samples/              # Sample CSV / Excel inputs
│   └── output/               # Example outputs (your session exports land elsewhere you choose)
├── docs/
│   └── User-Guide.md         # Detailed user guide
└── src/
    ├── detect.py             # Adaptive peak detection + edit helpers
    ├── filters.py            # Unified smoothing interface (S=0..5)
    ├── io.py                 # Robust CSV/XLSX loading, ambient subtraction
    ├── metrics.py            # APD & shape metrics; aggregation
    ├── segment.py            # Period building, resampling, normalization, averaging
    ├── version.py            # Package/version info (if used)
    └── ui/
        ├── app.py            # Tkinter application
        ├── plot.py           # Embedded Matplotlib plots + overlay
        └── views.py          # Sidebar, tabs, and widgets for the local UI
```

> For a step‑by‑step walkthrough, see **docs/User-Guide.md**.

---

## 🚀 Quick start

### Option A — Open the web app (Streamlit)

- **Web app:** `https://kai-caipulse.streamlit.app/`

> The web app mirrors the workflow below: **Load → Smooth → Detect → Curate → Overlay → Metrics → Export**.

### Option B — Run locally (desktop Tk app)
1) Create an environment (Python **3.12+** recommended).  
2) Install deps:
```bash
pip install -r requirements.txt
```
3) Launch the desktop UI:
```bash
python main.py
```

### Option C — Run Streamlit locally
```bash
pip install -r requirements.txt
streamlit run app_streamlit.py
```

---

## 🗂️ Input data format

- **CSV or Excel** with at least two columns: a **time** column (`t`, `time`, `s`, `ms`, etc.) and a **signal** column (`y`, `signal`, `value`, `intensity`, ...).  
- **Ambient** (optional) is the same format as raw. It will be resampled to the raw timestamps and scaled/shifted as configured.
- Non‑monotonic time is auto‑sorted; non‑uniform sampling is supported downstream.

Sample files live under `data/samples/`.

---

## 🧭 Typical workflow

1. **Load** raw (required) and ambient (optional).  
2. **Subtract ambient** (if provided): set **Offset (ms)** and **Scale**, click **Apply**.  
3. **Smooth**: choose **S** between 0 and 5 (0 = off; 1–2 gentle; 3–5 strong).  
4. **Detect peaks**: adaptive, pacing‑aware maxima/minima.  
5. **Curate periods**:  
   - Click a **peak max** to toggle its **period** (remove/restore).  
   - Click a **peak min** to **insert/remove** a boundary. Alternation is enforced for validity.  
6. **Review overlay**: normalized time axis (τ ∈ [0,1]) for kept periods, with **mean ± SD** band.  
7. **Inspect metrics**: per‑period and aggregated (see next section).  
8. **Export**: Excel workbook + figures + session JSON.

---

## 🔬 Metrics (per‑period and aggregated)

For each retained period, KAI computes:

- **APD20 / APD50 / APD90** — durations from **peak** down to **20/50/90% repolarization** of `(peak − baseline)` using level crossings (decay limb).  
- **time_to_peak** — from segment start to peak.  
- **rise_10_90**, **decay_90_10** — timing between 10%↔90% levels on up/down strokes.  
- **upstroke_max_slope**, **downstroke_min_slope** — extremal derivatives (units/s).  
- **upstroke_angle_deg**, **downstroke_angle_deg** — angles after normalizing amplitude to [0,1].  
- **auc_above_baseline** — trapezoidal area of `(y − baseline)+`.

Aggregations provide **mean** and **std** across kept periods. The **Metrics** tab displays a table with columns:
`Metric | Raw mean | Raw std | Filt mean | Filt std`.

---

## 🖼️ Exports

The **Export** action writes:

- **Excel (.xlsx)** with sheets:
  - `Parameters` — session settings (smoothing level, ambient params, counts).
  - `Periods` — per‑period durations.
  - `Metrics_Period_Raw` and `Metrics_Period_Filt` — per‑period metrics tables.
  - `Metrics_Aggregated_Raw` and `Metrics_Aggregated_Filt` — one‑row aggregates.
  - `Resampled_Periods` — normalized periods matrix + `mean` and `std`.
- **Figures**: a raw/filtered preview and a **periods overlay** PNG.
- **Session JSON**: current peaks, removed periods, smoothing level, ambient params.
<!--
> You choose the output filename/location via a save dialog.
-->
---

## 🛠️ Smoothing levels at a glance

| S | Backend (tuned) | Typical use |
|--:|------------------|-------------|
| 0 | —                | Use raw (or raw−ambient) |
| 1 | Savitzky–Golay (short) | Gentle denoise; preserves morphology |
| 2 | Savitzky–Golay (longer) | Moderate denoise |
| 3 | Butterworth (low‑pass)  | Strong smoothing (use sparingly) |
| 4 | Butterworth (lower cutoff) | Very strong (verify metrics) |
| 5 | Gaussian conv.        | Heaviest smoothing (diagnostic only) |

If traces start looking like an ideal sinusoid, reduce **S** to 1–2.

---

## ❓ Troubleshooting

- **Metrics tab is empty** → Run **Detect peaks** and ensure at least one period remains after curation.  
- **Period removal merges neighbors** → Click the **max** of the period to toggle it; to fix a boundary, click to add a **min** at the correct position and recompute.  
- **APD ordering looks odd (e.g., APD20 > APD90)** → Reduce smoothing, verify minima, and re‑detect.  
- **“t and y must have the same length”** → Confirm your time and signal columns align after any preprocessing/import.  
- **Oversmoothing** → Prefer **S=1–2**, especially for APD analyses.

---

## 🧪 Reproducibility tips

- Keep the **Session JSON** with your exports.  
- Use consistent **units**; declare them in your methods.  
- Share the exact **smoothing level** and whether ambient subtraction was used.

---

## 📄 License & citation

- **License:** MIT.  
- **How to cite:** In Methods, cite this repository as _KAI — Calcium Imaging Periodic Signal Analyzer (version X.Y)_.

---

## 🤝 Contributing

Issues and PRs are welcome. Please include a minimal dataset (or use `data/samples/`) and steps to reproduce.

---

## Acknowledgments

Developed for calcium‑imaging transient analysis with a focus on period‑wise metrics and transparent, reproducible exports.
