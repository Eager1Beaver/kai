# src/filters.py — Filtering utilities

from typing import Tuple, List
import numpy as np
from scipy.signal import butter, sosfiltfilt, savgol_filter
from scipy.ndimage import gaussian_filter1d

def use_savgol_filter(y: np.ndarray, window_length: int = 65, polyorder: int = 5, mode: str = 'interp') -> Tuple[np.ndarray, str]:
    """
    Applies Savitzky-Golay filter to smooth the signal.

    Args:
        y (np.ndarray): Input signal.
        window_length (int): Length of the filter window (must be odd).
        polyorder (int): Order of the polynomial to fit.
        mode (str): Mode for handling boundaries.

    Returns:
        Tuple[np.ndarray, str]: Filtered signal, filter name.
    """
    return savgol_filter(y, window_length=window_length, polyorder=polyorder, mode=mode), 'savgol_filter'

def use_gaussian_filter1d(y: np.ndarray, sigma: float = 12.0, truncate: float = 1.0) -> Tuple[np.ndarray, str]:
    """
    Applies Gaussian filter to smooth the signal.

    Args:
        y (np.ndarray): Input signal.
        sigma (float): Standard deviation for Gaussian kernel.
        truncate (float): Truncate filter at this many standard deviations.

    Returns:
        Tuple[np.ndarray, str]: Filtered signal, filter name.
    """
    return gaussian_filter1d(y, sigma=sigma, truncate=truncate), 'gaussian_filter1d'

def use_lowpass_filter(y: np.ndarray, cutoff: float = 120.0, sample_rate: float = 5000.0, poles: int = 2, btype: str = 'lowpass') -> Tuple[np.ndarray, str]:
    """
    Applies a lowpass Butterworth filter to the signal.

    Args:
        y (np.ndarray): Input signal.
        cutoff (float): Cutoff frequency.
        sample_rate (float): Sampling rate of the signal.
        poles (int): Number of poles in the filter.
        btype (str): Filter type, typically 'lowpass'.

    Returns:
        Tuple[np.ndarray, str]: Filtered signal, filter name.
    """
    sos = butter(N=poles, Wn=cutoff, fs=sample_rate, output='sos', btype=btype)
    return sosfiltfilt(sos, y), 'lowpass_filter'

def use_combined_filter(filtered_signals: List[np.ndarray]) -> Tuple[np.ndarray, str]:
    """
    Combines multiple filtered signals by averaging them element-wise.

    Args:
        filtered_signals (List[np.ndarray]): List of pre-filtered signal arrays.

    Returns:
        Tuple[np.ndarray, str]: Combined filtered signal, filter name.
    """
    if not filtered_signals:
        raise ValueError("No filters provided for combination.")
    return np.mean(filtered_signals, axis=0), 'combined_filter'
