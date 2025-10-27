"""
scr.detect
----------
Adaptive peak detection for periodic calcium-like signals + edit helpers.

Features:
    - Robust sampling-rate estimation (median dt).
    - Optional pacing frequency estimation.
    - Adaptive peaks using MAD-based prominence and min-distance tied to pacing.
    - Returns alternating minima/maxima with basic invariants enforced.
    - Helpers to snap user clicks to local extrema and to add/remove peaks safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import find_peaks

# Utilities

def estimate_fs(t: np.ndarray) -> float:
    """Estimate sampling rate (Hz) from time vector using median dt."""
    t = np.asarray(t, dtype=float).reshape(-1)
    dt = np.diff(t)
    med = float(np.median(dt)) if len(dt) else np.nan
    if not np.isfinite(med) or med <= 0:
        raise ValueError("Cannot infer sampling rate from time vector.")
    return 1.0 / med


def _mad(x: np.ndarray) -> float:
    """Median absolute deviation with Gaussian consistency factor (~1.4826)."""
    x = np.asarray(x, dtype=float).ravel()
    med = np.median(x)
    return 1.4826 * float(np.median(np.abs(x - med)))


def estimate_pacing(t: np.ndarray, y: np.ndarray, *, kind: str = "max") -> Optional[float]:
    """
    Roughly estimate pacing frequency by a two-pass approach:
    1) quick peaks with thresholds; 2) median inter-peak interval.

    Returns
    -------
    fp : float or None
        Estimated frequency in Hz; None if insufficient data.
    """
    t = np.asarray(t, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    if len(t) < 5:
        return None

    fs = estimate_fs(t)
    # Use small prominence relative to data spread
    prom = max(1e-9, 0.2 * _mad(y))  # very lenient
    distance = max(1, int(0.05 * fs))  # at least 50 ms apart

    if kind == "min":
        peaks, _ = find_peaks(-y, prominence=prom, distance=distance)
    else:
        peaks, _ = find_peaks(y, prominence=prom, distance=distance)

    if len(peaks) < 2:
        return None

    ipi = np.diff(t[peaks])
    med_T = float(np.median(ipi))
    if med_T <= 0:
        return None
    return 1.0 / med_T


# Detection

@dataclass
class PeakResult:
    peaks_max: np.ndarray  # indices of maxima
    peaks_min: np.ndarray  # indices of minima
    pacing_hz: Optional[float]
    stats: Dict[str, float]  # e.g., {'prom_thresh':..., 'min_distance_samples':...}


def find_peaks_adaptive(
    t: np.ndarray,
    y: np.ndarray,
    *,
    fp_hint: Optional[float] = None,
    prefer: str = "max",
    width_ms: Optional[Tuple[float, float]] = None,
    ) -> PeakResult:
    """
    Adaptive peak detection producing alternating minima & maxima.

    Parameters
    ----------
    t, y : arrays
    fp_hint : float, optional
        If provided, sets min distance ~ 0.6 * period. If None, pacing is estimated.
    prefer : {'max','min'}
        Which extrema to detect first for alternation logic.
    width_ms : (lo, hi), optional
        Minimum/maximum widths (ms) passed to scipy.find_peaks (converted to samples).

    Returns
    -------
    PeakResult
    """
    t = np.asarray(t, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    if len(t) != len(y):
        raise ValueError("t and y must have same length")
    if len(t) < 5:
        return PeakResult(np.array([], dtype=int), np.array([], dtype=int), None, {})

    fs = estimate_fs(t)
    fp = fp_hint if (fp_hint is not None and fp_hint > 0) else estimate_pacing(t, y, kind="max")
    # Distance tied to pacing (more conservative than half-period to avoid doubles)
    if fp is not None and fp > 0:
        period_s = 1.0 / fp
        min_dist_samples = max(1, int(0.6 * period_s * fs))
    else:
        # 150 ms
        min_dist_samples = max(1, int(0.15 * fs))

    # Prominence threshold from noise estimate
    dy = np.diff(y)
    noise = _mad(dy) if len(dy) else _mad(y)
    prom = max(1e-12, 2.5 * noise)  # scale factor

    # Width bounds (samples) if provided
    wmin, wmax = None, None
    if width_ms is not None:
        lo, hi = width_ms
        if lo is not None:
            wmin = max(1, int((lo/1000.0) * fs))
        if hi is not None:
            wmax = max(wmin or 1, int((hi/1000.0) * fs))

    # Detect
    kwargs = dict(prominence=prom, distance=min_dist_samples)
    if wmin is not None or wmax is not None:
        kwargs["width"] = (wmin, wmax) if wmax is not None else (wmin, None)

    peaks_max, _ = find_peaks(y, **kwargs)
    peaks_min, _ = find_peaks(-y, **kwargs)

    # Enforce alternation by merging sequences
    pmax = np.asarray(peaks_max, dtype=int)
    pmin = np.asarray(peaks_min, dtype=int)

    if prefer == "min":
        seq = _merge_alternating(pmin, pmax, kind_first="min")
    else:
        seq = _merge_alternating(pmax, pmin, kind_first="max")

    # Split back to min/max in order
    mins, maxs = [], []
    for kind, idx in seq:
        if kind == "min":
            mins.append(idx)
        else:
            maxs.append(idx)

    return PeakResult(
        peaks_max=np.array(sorted(maxs), dtype=int),
        peaks_min=np.array(sorted(mins), dtype=int),
        pacing_hz=fp,
        stats={
            "fs_hz": float(fs),
            "prom_thresh": float(prom),
            "min_distance_samples": int(min_dist_samples),
            "n_max": int(len(peaks_max)),
            "n_min": int(len(peaks_min)),
            },
            )


def _merge_alternating(primary: np.ndarray, secondary: np.ndarray, *, kind_first: str) -> List[Tuple[str, int]]:
    """
    Merge two sorted index arrays into an alternating sequence, preferring 'primary' when close.
    kind_first: 'min' or 'max' corresponding to the 'primary' array.
    """
    seq: List[Tuple[str, int]] = []
    i, j = 0, 0
    last_kind = None
    while i < len(primary) or j < len(secondary):
        cand_primary = (primary[i], kind_first) if i < len(primary) else None
        kind_second = "max" if kind_first == "min" else "min"
        cand_secondary = (secondary[j], kind_second) if j < len(secondary) else None

        pick = None
        if cand_primary and (last_kind != kind_first):
            pick = cand_primary
            i += 1
        elif cand_secondary and (last_kind == kind_first or not cand_primary):
            pick = cand_secondary
            j += 1
        elif cand_primary:
            pick = cand_primary
            i += 1
        elif cand_secondary:
            pick = cand_secondary
            j += 1

        if pick is not None:
            idx, kind = pick
            # Avoid duplicates or same-kind repeats at the same location
            if not seq or (seq[-1][0] != kind or seq[-1][1] != idx):
                seq.append((kind, int(idx)))
                last_kind = kind
    return seq


# Helpers
def snap_to_local_extremum(t: np.ndarray, y: np.ndarray, x_click: float, *, radius_ms: float = 60.0) -> Tuple[int, str]:
    """
    Given a click time (x_click), return index of nearest local extremum within radius.
    Returns (index, 'min'|'max'). Raises ValueError if none found.
    """
    t = np.asarray(t, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    fs = estimate_fs(t)
    radius_samp = max(1, int((radius_ms/1000.0) * fs))
    # Find nearest sample
    idx0 = int(np.argmin(np.abs(t - x_click)))

    lo = max(1, idx0 - radius_samp)
    hi = min(len(y) - 2, idx0 + radius_samp)

    window = y[lo:hi+1]
    # Local max/min in window
    local_rel_max = np.argmax(window) + lo
    local_rel_min = np.argmin(window) + lo

    dmax = abs(t[local_rel_max] - x_click)
    dmin = abs(t[local_rel_min] - x_click)
    if min(dmax, dmin) > (radius_ms/1000.0):
        raise ValueError("No local extremum within radius.")

    if dmax <= dmin:
        return local_rel_max, "max"
    else:
        return local_rel_min, "min"


def insert_peak(peaks: np.ndarray, idx: int) -> np.ndarray:
    """Insert idx into sorted peaks array if not present."""
    peaks = np.asarray(peaks, dtype=int).ravel()
    if idx in peaks:
        return peaks
    return np.sort(np.append(peaks, idx))


def remove_peak(peaks: np.ndarray, idx: int, *, tol: int = 0) -> np.ndarray:
    """Remove idx (within tol samples) from peaks array if present."""
    peaks = np.asarray(peaks, dtype=int).ravel()
    mask = np.ones_like(peaks, dtype=bool)
    for k, p in enumerate(peaks):
        if abs(p - idx) <= tol:
            mask[k] = False
            break
    return peaks[mask]


def enforce_alternation(peaks_min: np.ndarray, peaks_max: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensure sequences alternate in time; if not, remove violations starting with the closer duplicate.
    """
    mins = np.asarray(peaks_min, dtype=int)
    maxs = np.asarray(peaks_max, dtype=int)
    all_pts = [(i, "min") for i in mins] + [(j, "max") for j in maxs]
    if not all_pts:
        return mins, maxs
    all_pts.sort(key=lambda x: x[0])

    # Remove consecutive same-kind points keeping the stronger alternation
    cleaned = []
    for _, (idx, kind) in enumerate(all_pts):
        if cleaned and cleaned[-1][1] == kind:
            # remove the closer duplicate (current or previous). Keep the one farther from neighbors.
            prev_idx, _ = cleaned[-1]
            # choose which to keep by distance to next different-kind (if available)
            keep_current = True  # default
            cleaned.pop()  # temporarily remove prev
            # keep the one that maximizes spacing with neighbors
            if cleaned:
                left_gap_prev = prev_idx - cleaned[-1][0]
                left_gap_curr = idx - cleaned[-1][0]
            else:
                left_gap_prev = left_gap_curr = 1e9
            # Decide keep
            if left_gap_prev > left_gap_curr:
                # keep prev, discard current
                cleaned.append((prev_idx, kind))
            else:
                # keep current (append below)
                pass
            if keep_current and (not cleaned or cleaned[-1][0] != idx or cleaned[-1][1] != kind):
                cleaned.append((idx, kind))
        else:
            cleaned.append((idx, kind))

    mins_new = np.array([i for i, k in cleaned if k == "min"], dtype=int)
    maxs_new = np.array([i for i, k in cleaned if k == "max"], dtype=int)
    return np.unique(mins_new), np.unique(maxs_new)


# Testing
if __name__ == "__main__":
    import sys, json, numpy as np
    sys.path.append("data")
    summary = {}
    try:
        from src.io import load_signal
        from src.detect import find_peaks_adaptive, estimate_pacing
        t_raw, y_raw, info = load_signal("/data/sample_raw_signal_data.csv")
        res = find_peaks_adaptive(t_raw, y_raw, fp_hint=None, prefer="max")
        fp_est = res.pacing_hz or estimate_pacing(t_raw, y_raw)
        summary["n_max"] = int(len(res.peaks_max))
        summary["n_min"] = int(len(res.peaks_min))
        summary["fp_hz"] = float(fp_est) if fp_est is not None else None
        if len(res.peaks_max) > 0:
            summary["first_peak_time"] = float(t_raw[res.peaks_max[0]])
    except Exception as e:
        summary["detect_error"] = str(e)

    print(json.dumps(summary, indent=2))