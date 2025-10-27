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


def enforce_alternation(
        peaks_min: np.ndarray, peaks_max: np.ndarray,
        *, anchor: str = "min",
        ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensure sequences alternate in time; if not, remove violations starting with the closer duplicate.
    """
    mins = np.asarray(peaks_min, dtype=int)
    maxs = np.asarray(peaks_max, dtype=int)

    if anchor not in ("min", "max"):
        anchor = "min"

    if anchor == "min":
        # If fewer than two mins, there are no valid min→min periods; maxima irrelevant.
        if mins.size < 2:
            return mins, np.array([], dtype=int)
        keep = []
        for m0, m1 in zip(mins[:-1], mins[1:]):
            in_pair = maxs[(maxs > m0) & (maxs < m1)]
            if in_pair.size > 0:
                # keep all or 1; keeping all is harmless for display; segmentation doesn't depend on max
                keep.extend(in_pair.tolist())
        maxs = np.unique(np.asarray(keep, dtype=int)) if keep else np.array([], dtype=int)
        return mins, maxs
    else:
        # Symmetric for max2max (not used now, but safe)
        if maxs.size < 2:
            return np.array([], dtype=int), maxs
        keep = []
        for M0, M1 in zip(maxs[:-1], maxs[1:]):
            in_pair = mins[(mins > M0) & (mins < M1)]
            keep.extend(in_pair.tolist())
        mins = np.unique(np.asarray(keep, dtype=int)) if keep else np.array([], dtype=int)
        return mins, maxs


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