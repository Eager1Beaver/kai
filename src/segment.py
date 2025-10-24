
"""
kai.segment
-----------
Period segmentation + normalization utilities.

Goals
-----
- Build cycles (periods) from detected extrema (min/max).
- Offer robust strategies: min→min or max→max cycles, with guard rails.
- Produce per-period arrays and resample to a common grid for averaging/overlay.
- Provide basic normalization options (baseline shift, amplitude scaling).

Key API
-------
- build_period_indices(t, peaks_min, peaks_max, *, strategy="min2min")
- slice_periods(t, y, idx_periods) -> List[Tuple[np.ndarray, np.ndarray]]
- resample_periods(periods, *, n_points=200) -> (X, tau) where
    X shape = (n_periods, n_points), tau in [0,1]
- normalize_periods(X, *, mode="baseline", eps=1e-9) -> Xn
- average_period(Xn) -> (mu, sigma)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import numpy as np


@dataclass
class SegmentationInfo:
    strategy: str                  # "min2min" or "max2max"
    n_periods: int
    dropped_edges: int             # periods dropped due to incomplete edges
    durations: np.ndarray          # seconds (if t in seconds)
    indices: List[Tuple[int,int]]  # (start_idx, end_idx) inclusive start, exclusive end


# ---------------- Core segmentation ----------------

def _sorted_unique(a: Iterable[int]) -> np.ndarray:
    a = np.asarray(list(a), dtype=int).ravel()
    if a.size == 0:
        return a
    return np.unique(a)


def build_period_indices(
    t: np.ndarray,
    peaks_min: Sequence[int],
    peaks_max: Sequence[int],
    *,
    strategy: str = "min2min",
) -> SegmentationInfo:
    """
    Build (start,end) indices of periods according to strategy.

    A period is defined as [anchor_k, anchor_{k+1}) where anchors are either
    consecutive minima ("min2min") or maxima ("max2max").

    Returns SegmentationInfo with durations and list of index pairs.
    """
    t = np.asarray(t, dtype=float).ravel()
    mins = _sorted_unique(peaks_min)
    maxs = _sorted_unique(peaks_max)

    if strategy not in ("min2min", "max2max"):
        raise ValueError("strategy must be 'min2min' or 'max2max'")

    anchors = mins if strategy == "min2min" else maxs
    idx_periods: List[Tuple[int,int]] = []

    # Need at least two anchors
    if len(anchors) >= 2:
        for a, b in zip(anchors[:-1], anchors[1:]):
            if b > a + 1:
                idx_periods.append((int(a), int(b)))
    # Edge handling: ignore partial periods at edges by design

    durations = np.array([t[j-1] - t[i] for (i,j) in idx_periods], dtype=float) if idx_periods else np.array([], dtype=float)
    info = SegmentationInfo(
        strategy=strategy,
        n_periods=len(idx_periods),
        dropped_edges=0 if len(anchors) < 2 else 0,  # keeping count field for future use
        durations=durations,
        indices=idx_periods,
    )
    return info


def slice_periods(
    t: np.ndarray,
    y: np.ndarray,
    idx_periods: Sequence[Tuple[int,int]],
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Slice (t,y) into per-period arrays using [start,end) index pairs.
    """
    t = np.asarray(t, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    out: List[Tuple[np.ndarray, np.ndarray]] = []
    for i, j in idx_periods:
        i = int(i); j = int(j)
        if i < 0 or j > len(t) or j <= i + 1:
            continue
        out.append((t[i:j], y[i:j]))
    return out


# ---------------- Resampling & normalization ----------------

def _resample_to_n_points(t: np.ndarray, y: np.ndarray, n_points: int) -> np.ndarray:
    """
    Resample one period y(t) to a uniform grid of n_points in [0,1] via linear interp.
    """
    # Normalize local time to [0,1]
    t0, t1 = float(t[0]), float(t[-1])
    if t1 <= t0:
        # Degenerate: return constant vector
        return np.full(n_points, y[0], dtype=float)
    tau = (t - t0) / (t1 - t0)
    grid = np.linspace(0.0, 1.0, n_points)
    return np.interp(grid, tau, y)


def resample_periods(
    periods: Sequence[Tuple[np.ndarray, np.ndarray]],
    *,
    n_points: int = 200,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resample all periods to a common grid.

    Returns
    -------
    X : (n_periods, n_points) array
    tau : (n_points,) array, normalized time in [0,1].
    """
    if n_points < 2:
        raise ValueError("n_points must be >= 2")
    X = []
    for (t_seg, y_seg) in periods:
        X.append(_resample_to_n_points(t_seg, y_seg, n_points))
    X = np.vstack(X) if X else np.zeros((0, n_points), dtype=float)
    tau = np.linspace(0.0, 1.0, n_points)
    return X, tau


def normalize_periods(
    X: np.ndarray,
    *,
    mode: str = "baseline",
    eps: float = 1e-9,
) -> np.ndarray:
    """
    Normalize per-period arrays.

    Modes
    -----
    - "none": no change
    - "baseline": subtract first sample (baseline shift)
    - "minmax": (x - min) / (max - min + eps)
    - "zscore": (x - mean) / (std + eps)
    """
    X = np.asarray(X, dtype=float)
    if X.size == 0:
        return X

    if mode == "none":
        return X.copy()

    if mode == "baseline":
        baseline = X[:, :1]
        return X - baseline

    if mode == "minmax":
        xmin = np.min(X, axis=1, keepdims=True)
        xmax = np.max(X, axis=1, keepdims=True)
        return (X - xmin) / (xmax - xmin + eps)

    if mode == "zscore":
        mu = np.mean(X, axis=1, keepdims=True)
        sd = np.std(X, axis=1, ddof=1, keepdims=True)
        return (X - mu) / (sd + eps)

    raise ValueError("Unknown normalization mode")


def average_period(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute per-sample mean and std across periods.
    """
    X = np.asarray(X, dtype=float)
    if X.size == 0:
        return np.array([]), np.array([])
    mu = np.mean(X, axis=0)
    sd = np.std(X, axis=0, ddof=1) if X.shape[0] > 1 else np.zeros_like(mu)
    return mu, sd


# Smoke test: load sample, detect peaks, segment min->min, resample & average
if __name__ == "__main__":
    import sys, json, numpy as np
    sys.path.append("/data")

    summary = {}
    try:
        from src.io import load_signal
        from src.detect import find_peaks_adaptive
        from src.segment import build_period_indices, slice_periods, resample_periods, normalize_periods, average_period

        t_raw, y_raw, _ = load_signal("/data/sample_raw_signal_data.csv")
        det = find_peaks_adaptive(t_raw, y_raw)
        info = build_period_indices(t_raw, det.peaks_min, det.peaks_max, strategy="min2min")
        periods = slice_periods(t_raw, y_raw, info.indices)
        X, tau = resample_periods(periods, n_points=128)
        Xn = normalize_periods(X, mode="baseline")
        mu, sd = average_period(Xn)
        summary = {
            "n_periods": len(periods),
            "resampled_shape": X.shape,
            "mu_len": len(mu),
            "first_duration_s": float(info.durations[0]) if len(info.durations) else None
        }
    except Exception as e:
        summary["error"] = str(e)

    print(json.dumps(summary, indent=2))