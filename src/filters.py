"""
filters.py
-----------
Unified filtering facade for calcium imaging signals.
    - Provides a single perceptual smoothing scale S in {0..5}.
    - S=0 => no filtering.
    - S in 1..5 => applies a tuned backend (Savgol, Butterworth, Gaussian) with
        parameters derived from sampling rate and (optionally) pacing frequency.
    - Caches filtered outputs per (S, fs, fp, N) for instant live preview toggling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import numpy as np
from scipy.signal import butter, filtfilt, savgol_filter
from math import ceil

CacheKey = Tuple[int, float, Optional[float], int]  # (S, fs, fp, N)


def _round_to_odd(n: int) -> int:
    return n if n % 2 else max(1, n - 1)


@dataclass
class FilterConfig:
    """Holds tuning coefficients for each S level."""
    # Savgol coefficients (fractions of second * fs)
    savgol_k_small: float = 0.03
    savgol_k_large: float = 0.06
    savgol_poly_s1: int = 2
    savgol_poly_s2: int = 3

    # Butterworth mapping (order and cutoff multiplier vs pacing freq)
    # S=3 => order2 @ 3*fp, S=4 => order4 @ 2*fp
    butter_order_s3: int = 2
    butter_mult_s3: float = 3.0
    butter_order_s4: int = 4
    butter_mult_s4: float = 2.0
    butter_min_fc_hz: float = 0.2  # guard for very slow pacing

    # Gaussian std as fraction of second * fs (sigma in samples)
    gauss_sigma_k_s5: float = 0.04
    gauss_truncate: float = 3.0


@dataclass
class FilterEngine:
    """
    Unified smoothing interface.

    Parameters
    ----------
    smoothing_level : int
        Perceptual scale S in {0..5}. 0 = no filter.
    config : FilterConfig
        Tuning parameters; adjust once globally if needed.
    """
    smoothing_level: int = 0
    config: FilterConfig = field(default_factory=FilterConfig)
    _cache: Dict[CacheKey, np.ndarray] = field(default_factory=dict, init=False)

    def set_level(self, S: int) -> None:
        if not (0 <= S <= 5):
            raise ValueError("S must be in [0, 5]")
        self.smoothing_level = S

    # --- Public API -----------------------------------------------------
    def apply(
        self,
        t: np.ndarray,
        y: np.ndarray,
        pacing_freq_hz: Optional[float] = None,
    ) -> np.ndarray:
        """
        Apply smoothing to y given timestamps t.

        If `pacing_freq_hz` is provided, Butterworth cutoff is tied to pacing.
        """
        if y.ndim != 1 or t.ndim != 1:
            raise ValueError("t and y must be 1D arrays")
        if len(t) != len(y):
            raise ValueError("t and y must have the same length")
        if len(t) < 5:
            return y.copy()

        fs = self._infer_fs(t)
        S = self.smoothing_level
        key: CacheKey = (S, float(fs), float(pacing_freq_hz) if pacing_freq_hz is not None else None, len(y))

        if S == 0:
            return y.copy()

        if key in self._cache:
            return self._cache[key].copy()

        if S in (1, 2):
            out = self._apply_savgol(y, fs, S)
        elif S in (3, 4):
            out = self._apply_butterworth(y, fs, pacing_freq_hz, S)
        elif S == 5:
            out = self._apply_gaussian(y, fs)
        else:
            out = y.copy()

        self._cache[key] = out.copy()
        return out

    # --- Backends -------------------------------------------------------
    def _apply_savgol(self, y: np.ndarray, fs: float, S: int) -> np.ndarray:
        cfg = self.config
        if S == 1:
            win = max(5, _round_to_odd(int(cfg.savgol_k_small * fs)))
            poly = cfg.savgol_poly_s1
        else:  # S == 2
            win = max(7, _round_to_odd(int(cfg.savgol_k_large * fs)))
            poly = cfg.savgol_poly_s2

        win = min(win, len(y) - (1 - len(y) % 2))  # window <= len(y) and odd
        if win < poly + 2:  # fallback
            win = poly + 3 if (poly + 3) % 2 else poly + 4
        return savgol_filter(y, window_length=win, polyorder=poly, mode="interp")

    def _apply_butterworth(
        self,
        y: np.ndarray,
        fs: float,
        fp: Optional[float],
        S: int,
    ) -> np.ndarray:
        cfg = self.config
        if fp is None or fp <= 0:
            # Fallback cutoff if pacing unknown: 0.15*Nyquist
            fc = 0.15 * (fs / 2.0)
            # NEW: pick order by S so S=3 is modest, S=4 is heavier
            order = cfg.butter_order_s3 if S == 3 else cfg.butter_order_s4
        else:
            if S == 3:
                fc = max(cfg.butter_min_fc_hz, cfg.butter_mult_s3 * fp)
                order = cfg.butter_order_s3
            else:  # S == 4
                fc = max(cfg.butter_min_fc_hz, cfg.butter_mult_s4 * fp)
                order = cfg.butter_order_s4
        wn = min(0.999, fc / (fs / 2.0))
        b, a = butter(order, wn, btype="low", analog=False)
        return filtfilt(b, a, y, method="pad")

    def _apply_gaussian(self, y: np.ndarray, fs: float) -> np.ndarray:
        cfg = self.config
        sigma_samp = max(1.0, cfg.gauss_sigma_k_s5 * fs)
        # Build a discrete Gaussian kernel
        radius = int(ceil(cfg.gauss_truncate * sigma_samp))
        x = np.arange(-radius, radius + 1, dtype=float)
        k = np.exp(-(x**2) / (2 * sigma_samp**2))
        k /= k.sum()
        # Convolve with reflection padding at edges
        ypad = np.pad(y, (radius, radius), mode="reflect")
        out = np.convolve(ypad, k, mode="valid")
        return out

    # --- Helpers --------------------------------------------------------
    @staticmethod
    def _infer_fs(t: np.ndarray) -> float:
        dt = np.diff(t)
        # robust: median dt
        med = float(np.median(dt))
        if med <= 0:
            # fallback to mean
            med = float(np.mean(dt))
        if med <= 0:
            raise ValueError("Non-increasing time vector")
        return 1.0 / med
