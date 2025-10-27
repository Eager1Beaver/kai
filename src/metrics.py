
"""
kai.metrics
-----------
APD metrics and shape features for calcium-like periodic signals.

Design:
    Operate on **per-period raw segments** (t_seg, y_seg). For APDxx, we use the
    standard "level crossing" definition with respect to a baseline and a peak:
        - baseline: default = min value within the first 10% of samples (robust to drift)
        - peak: global max within the period
        - APD_p is defined between the **upstroke** crossing at level p and the **downstroke**
        crossing at level p, where p ∈ {0.2, 0.5, 0.9} for APD20/50/90.
    Crossing times are linearly interpolated in time.

Provided shape features:
    - time_to_peak (s), rise_10_90 (s), decay_90_10 (s)
    - max upstroke slope (units/s) and its angle (deg) on a [0,1] normalized amplitude
    - max downstroke slope (negative) and its angle (deg) on a [0,1] normalized amplitude
    - area_under_curve above baseline (units*s) using trapezoidal rule
"""

from __future__ import annotations
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np

# Utilities ---------

def _as_1d(a) -> np.ndarray:
    return np.asarray(a, dtype=float).reshape(-1)


def _central_diff(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Central difference derivative dy/dt with forward/backward ends."""
    t = _as_1d(t); y = _as_1d(y)
    dy = np.empty_like(y)
    dy[1:-1] = (y[2:] - y[:-2]) / (t[2:] - t[:-2])
    dy[0] = (y[1] - y[0]) / (t[1] - t[0])
    dy[-1] = (y[-1] - y[-2]) / (t[-1] - t[-2])
    return dy


def _level_value(baseline: float, peak: float, p: float) -> float:
    return baseline + p * (peak - baseline)


def _find_crossing_time(t: np.ndarray, y: np.ndarray, level: float, direction: str) -> Optional[float]:
    """
    Find time where y crosses 'level' going 'up' or 'down' by linear interpolation.
    Returns None if no such crossing found.
    """
    t = _as_1d(t); y = _as_1d(y)
    if direction not in ("up", "down"):
        raise ValueError("direction must be 'up' or 'down'")

    if direction == "up":
        mask = y[:-1] < level
        nxt = y[1:] >= level
    else:
        mask = y[:-1] > level
        nxt = y[1:] <= level

    idxs = np.where(mask & nxt)[0]
    if idxs.size == 0:
        return None
    i = int(idxs[0])
    # Linear interpolation between (t[i],y[i]) and (t[i+1],y[i+1])
    t0, t1 = t[i], t[i+1]
    y0, y1 = y[i], y[i+1]
    if y1 == y0:
        return float(t0)
    frac = (level - y0) / (y1 - y0)
    return float(t0 + frac * (t1 - t0))


def _baseline_peak(t: np.ndarray, y: np.ndarray, *, first_frac: float = 0.1) -> Tuple[float, float, int]:
    """Baseline = min(y) within first_frac of samples; peak = global max; also return index of peak."""
    n = len(y)
    k = max(1, int(first_frac * n))
    window = y[:k]
    baseline = float(np.min(window))
    peak_idx = int(np.argmax(y))
    peak = float(y[peak_idx])
    return baseline, peak, peak_idx


# APD metrics per period
def apd_metrics_for_period(t: np.ndarray, y: np.ndarray, levels: Sequence[float] = (20, 50, 90)) -> Dict[str, float]:
    """
    Compute APDxx for a single period segment (t,y) where 'xx' is percent repolarization.

    Parameters
    ----------
    t, y : 1D arrays of the period (monotonic t)
    levels : sequence of fractions in (0,1), default (0.2,0.5,0.9)

    Returns
    -------
    dict with keys 'APD20','APD50','APD90' (seconds). Missing crossings -> NaN.
    """
    t = _as_1d(t); y = _as_1d(y)
    if len(t) < 4:
        return {"APD20": np.nan, "APD50": np.nan, "APD90": np.nan}

    baseline, peak, _ = _baseline_peak(t, y)
    out: Dict[str, float] = {}

    for p in levels:
        # Convert percent repolarization to fraction of (peak - baseline)
        frac = 1.0 - (p/100)
        lvl = _level_value(baseline, peak, frac)
        tup = _find_crossing_time(t, y, lvl, "up")
        tdn = _find_crossing_time(t, y, lvl, "down")
        key = f"APD{int(p)}"
        out[key] = (tdn - tup) if (tup is not None and tdn is not None and tdn >= tup) else np.nan
    return out


# Shape metrics per period
def shape_metrics_for_period(t: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Compute shape features: time_to_peak, rise/decay times, slopes/angles, area.
    """
    t = _as_1d(t); y = _as_1d(y)
    if len(t) < 4:
        return {
            "time_to_peak": np.nan,
            "rise_10_90": np.nan,
            "decay_90_10": np.nan,
            "upstroke_max_slope": np.nan,
            "downstroke_min_slope": np.nan,
            "upstroke_angle_deg": np.nan,
            "downstroke_angle_deg": np.nan,
            "auc_above_baseline": np.nan,
        }

    baseline, peak, peak_idx = _baseline_peak(t, y)

    # time to peak
    ttp = float(t[peak_idx] - t[0])

    # crossings for 10% and 90% (relative to baseline->peak)
    lvl10 = _level_value(baseline, peak, 0.1)
    lvl90 = _level_value(baseline, peak, 0.9)
    t10_up = _find_crossing_time(t, y, lvl10, "up")
    t90_up = _find_crossing_time(t, y, lvl90, "up")
    t90_down = _find_crossing_time(t, y, lvl90, "down")
    t10_down = _find_crossing_time(t, y, lvl10, "down")

    rise_10_90 = (t90_up - t10_up) if (t10_up is not None and t90_up is not None) else np.nan
    decay_90_10 = (t10_down - t90_down) if (t10_down is not None and t90_down is not None) else np.nan

    # slopes & angles using central difference
    dy = _central_diff(t, y)
    upstroke_max_slope = float(np.max(dy[:peak_idx+1])) if peak_idx >= 0 else float('nan')
    downstroke_min_slope = float(np.min(dy[peak_idx:])) if peak_idx < len(dy) else float('nan')

    # Normalize amplitude to [0,1] for angle calculation
    amp = peak - baseline
    y_norm = (y - baseline) / amp if amp != 0 else np.zeros_like(y)
    dy_norm = _central_diff(t, y_norm)

    upstroke_angle_deg = float(np.degrees(np.arctan(np.max(dy_norm[:peak_idx+1])))) if peak_idx >= 0 else float('nan')
    downstroke_angle_deg = float(np.degrees(np.arctan(np.min(dy_norm[peak_idx:])))) if peak_idx < len(dy_norm) else float('nan')

    # area under curve above baseline
    auc = float(np.trapezoid(np.clip(y - baseline, 0, None), t))

    return {
        "time_to_peak": ttp,
        "rise_10_90": rise_10_90,
        "decay_90_10": decay_90_10,
        "upstroke_max_slope": upstroke_max_slope,
        "downstroke_min_slope": downstroke_min_slope,
        "upstroke_angle_deg": upstroke_angle_deg,
        "downstroke_angle_deg": downstroke_angle_deg,
        "auc_above_baseline": auc,
    }


# Aggregation
def metrics_for_periods(periods: Sequence[Tuple[np.ndarray, np.ndarray]]) -> List[Dict[str, float]]:
    """
    Compute metrics dict per (t_seg, y_seg).
    """
    out = []
    for (t_seg, y_seg) in periods:
        m = {}
        m.update(apd_metrics_for_period(t_seg, y_seg))
        m.update(shape_metrics_for_period(t_seg, y_seg))
        out.append(m)
    return out


def aggregate_metrics(period_metrics: Sequence[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate period metrics with mean/std. Returns a flat dict with keys like
    'APD90_mean', 'APD90_std', 'rise_10_90_mean', ...
    """
    if not period_metrics:
        return {}

    keys = sorted({k for d in period_metrics for k in d.keys()})
    agg: Dict[str, float] = {}
    for k in keys:
        vals = np.array([d.get(k, np.nan) for d in period_metrics], dtype=float)
        mu = float(np.nanmean(vals)) if np.any(np.isfinite(vals)) else float('nan')
        sd = float(np.nanstd(vals, ddof=1)) if np.sum(np.isfinite(vals)) > 1 else float('nan')
        agg[f"{k}_mean"] = mu
        agg[f"{k}_std"] = sd
    return agg


# Testing (optional)
if __name__ == "__main__":
    import sys, json
    sys.path.append("/data")

    summary = {}
    try:
        from src.io import load_signal
        from src.detect import find_peaks_adaptive
        from src.segment import build_period_indices, slice_periods
        from src.metrics import metrics_for_periods, aggregate_metrics

        t_raw, y_raw, _ = load_signal("/data/sample_raw_signal_data.csv")
        det = find_peaks_adaptive(t_raw, y_raw)
        info = build_period_indices(t_raw, det.peaks_min, det.peaks_max, strategy="min2min")
        periods = slice_periods(t_raw, y_raw, info.indices)
        per = metrics_for_periods(periods)
        agg = aggregate_metrics(per)
        summary = {
            "n_periods": len(periods),
            "example_period_metrics": per[0] if per else {},
            "APD90_mean": agg.get("APD90_mean", None),
            "rise_10_90_mean": agg.get("rise_10_90_mean", None)
        }
    except Exception as e:
        summary["metrics_test_error"] = str(e)

    print(json.dumps(summary, indent=2))