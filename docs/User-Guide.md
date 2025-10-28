# KAI — Calcium Imaging Periodic Signal Analyzer
_User Guide_  
**Version:** 1.0 • **Last updated:** 2025-10-27

---

## 1) What this app does

KAI loads a **raw periodic calcium-imaging signal** (and an optional **ambient** signal), optionally **subtracts** ambient, **filters/smooths** the result, **detects peaks & segments** the trace into **periods**, lets you **curate** periods (remove outliers, insert missing minima), and then computes **metrics** (per-period and aggregated). Finally, it **exports** figures and a structured **Excel/CSV** bundle for downstream analysis.

The app runs as a **web UI** (Streamlit) and can also be used locally.

---

## 2) Inputs and sample data

- **Raw signal**: CSV (or Excel) with at least two columns, typically **time** and **signal**. Common headers: `time`/`t` (seconds or ms) and `signal`/`value`/`intensity`.
- **Ambient signal (optional)**: same shape as raw, used to remove measurement background before analysis.
- **Sampling**: non-uniform sampling is supported; the app resamples where needed for period overlays.
- **Sample files**: see the repository’s `data/` folder (e.g., `sample_raw_signal_data.csv`, `sample_ambient_signal_data.csv`).

> **Tip:** If your columns use different names, set them during load (the UI allows choosing which columns are time vs signal).

---

## 3) Typical workflow (TL;DR)

1. **Load data**  
   - Upload **Raw** (required) and **Ambient** (optional).  
   - Confirm which columns are **time** and **signal** (if prompted).  
   - If ambient is provided, KAI shows _raw – ambient_ as the working trace.

2. **Smooth / filter** (optional)  
   - Choose **Smoothing level S** (0–5).  
   - S=0 leaves the trace as-is. S=1–2 are gentle. S=3–5 progressively stronger (see §4).

3. **Detect peaks**  
   - Click **Detect peaks**. The app estimates pacing/cycle length and locates **peak maxima** and **minima**, forming **periods**.

4. **Curate periods**  
   - Click a **peak max** to **remove** its period (toggle).  
   - Click a **peak min** to **insert/remove** a boundary. (Min–max alternation is enforced so periods remain valid.)  
   - Repeat until the periods align with your expectation.

5. **Review overlay & metrics**  
   - **Overlay tab**: see all retained periods normalized/time-warped; view mean ± dispersion.  
   - **Metrics tab**: see per-period metrics and aggregation (mean ± SD/SEM, depending on configuration).

6. **Export**  
   - Click **Export** to save an Excel workbook (plus optional CSVs and figures).

---

## 4) Smoothing (S levels)

Select a smoothing strength that keeps morphology intact.

| S level | Intended effect | Notes |
|---:|---|---|
| **0** | No smoothing | Pure raw (or raw–ambient) trace |
| **1** | Gentle | Keep morphology; preferred default |
| **2** | Moderate | Visible denoising; still preserves shape |
| **3** | Strong | Use cautiously; may round sharp upstrokes |
| **4** | Very strong | Often **too smooth** for research; verify metrics |
| **5** | Heaviest | Diagnostic use only; may oversmooth to near-sinusoid |

> If you see over-smoothed sinusoids, reduce S to 1–2. For highly noisy data, try 2 first, then test 3 while monitoring morphology and APD metrics.

---

## 5) Peak detection & period editing

- **Detect peaks** uses pacing-aware heuristics and robust thresholds to find **peak maxima** and **minima**.  
- **Remove a period**: click its **peak max** (toggle on/off).  
- **Insert/remove a minimum**: click where the **min** should be; the app maintains proper min–max alternation.  
- **Goal**: Each **period** spans **min → next min** and contains a single physiological upstroke/peak.

> After editing, revisit the **Overlay** and **Metrics** tabs to verify that retained periods are consistent and informative.

---

## 6) Overlay visualization

- All kept periods are **time-normalized** to a common scale for direct comparison.  
- The **mean** (and optionally **±SD** band) is displayed.  
- Outlier periods you remove are excluded from the overlay and from aggregated metrics.

---

## 7) Metrics (per‑period and aggregated)

KAI computes standard transient morphology metrics for each retained period and aggregates them:

- **Amplitude**: peak value minus baseline (min).  
- **Cycle length (CL)**: time between consecutive minima.  
- **Rise time**: time from baseline (or defined low percentile) to peak.  
- **Decay time**: time from peak back to baseline (or defined high→low percent).  
- **Upstroke / downstroke slopes**: max positive and negative derivatives in rise/decay windows.  
- **Area under curve (AUC)**: integral over the period (baseline-subtracted).  
- **APD20 / APD50 / APD90**: “action potential duration” analogs for calcium transients — **time from peak** until the signal has **repolarized by 20/50/90%** of the **peak‑to‑baseline** amplitude.  
  - Concretely, KAI finds the **peak**, computes amplitude **A = peak − baseline**, then locates the **level‑crossings** at `peak − 0.2A`, `peak − 0.5A`, and `peak − 0.9A` on the **decay** limb; the durations to those crossings are APD20/50/90.  
  - Aggregations (e.g., mean ± SD) are shown in the **Metrics** tab and exported.

> **Note on correctness:** If APD values appear reversed (e.g., APD20 > APD90), check smoothing (S too high), period boundaries, or verify baseline estimation for that period.

---

## 8) Exported outputs

Click **Export** to generate a structured bundle (exact filenames may vary by session):

- **Excel workbook** (recommended):  
  - **Parameters**: session settings (smoothing level, detection params, etc.).  
  - **Aggregates**: mean/SD (and N) for each metric over kept periods.  
  - **PerPeriod_Raw** and **PerPeriod_Filtered**: per-period metrics for both pipelines.  
  - **Resampled_Periods**: time‑normalized periods for the overlay (matrix-like table).  
- **CSV mirrors** (optional): same content as above in CSV form.  
- **Figures** (optional): overlay plots, detection previews.  
- **Session JSON**: reproducibility snapshot (file paths, parameters, timestamps).

Use these artifacts for statistics, plotting in external tools, and reproducible pipelines.

---

## 9) Using the Streamlit web app

- Open the published web link (provided in the repository **README**).  
- **Left sidebar** guides you through: **Load → Smooth → Detect → Curate → Overlay → Metrics → Export**.  
- A **Help / User Guide** entry links back to this page and provides a PDF download (if included in the repo).

> The app shows status messages as you progress (e.g., “Peaks detected”, “0 periods kept”); read them if something looks off.

---

## 10) Local (optional) usage

If you prefer running locally:

1. Create a clean environment (Python ≥ 3.10).  
2. Install requirements: `pip install -r requirements.txt` (if provided).  
3. Run: `streamlit run app.py`  
4. Open the local URL shown in the terminal.

---

## 11) Good practices for reliable metrics

- Prefer **S=1–2** unless the signal is extremely noisy.  
- Manually **remove** periods with motion artifacts, clipped peaks, or missed minima.  
- Ensure **ambient** truly reflects your setup; otherwise, omit it.  
- Keep consistent **units** (time in seconds or milliseconds—just be explicit).  
- When publishing, export **Session JSON** and share it with data/figures for reproducibility.

---

## 12) Troubleshooting (FAQ)

**Q: The Metrics tab is empty.**  
A: Make sure you clicked **Detect peaks** and that at least **one period** is kept. Switch tabs once after detection to force a refresh if needed.

**Q: Everything looks over‑smoothed (near‑sinusoid).**  
A: Lower **S** to 1–2. Re‑detect peaks and re‑evaluate APD/overlay.

**Q: Period removal merged two periods or shifted boundaries.**  
A: Ensure you’re clicking the **peak max** of the period you want to toggle. If boundaries look off, insert a **minimum** at the correct location, then re‑detect if necessary.

**Q: “Wrong columns” after loading.**  
A: Use the column selectors in the loading step, or rename your columns to `time` and `signal` before upload.

**Q: APD20/APD50/APD90 seem swapped.**  
A: Verify baseline and decay crossings; high smoothing or incorrect minima can invert perceived durations. Reduce S and re‑check boundaries first.

**Q: Exported Excel is missing a sheet I expect.**  
A: Re‑run **Detect peaks** and ensure **Export** completes with at least one kept period. Also confirm you didn’t uncheck optional outputs.

---

## 13) Citing / Acknowledgments

If KAI supports your research, please cite your manuscript’s methods section accordingly.

---

## 14) Legacy quick start

A legacy quick start for early versions is kept under `docs/legacy/quick_start_guide.txt` for historical reference. The present guide supersedes it.

---

## 15) Changelog

- **1.0 (initial release)**: End‑to‑end pipeline (load → ambient subtraction → smoothing → peak detection → period curation → overlay → metrics → export); Streamlit UI with in‑app user guide link.
