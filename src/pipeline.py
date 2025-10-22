# src/pipeline.py — Signal processing pipeline utilities

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from typing import List, Tuple

def getPace_freq(pace_frequency: float, verbose: int = 0) -> float:
    if verbose == 2:
        print(f'Pacing frequency: {pace_frequency}')
    return pace_frequency

def getDistance_between_peaks(data_df: pd.DataFrame, pace_freq: float, verbose: int = 0) -> float:
    nmb_points_in_sec = len(data_df['t']) / data_df['t'].iloc[-1]
    distance = nmb_points_in_sec / pace_freq - 27
    if verbose in [1, 2]:
        print(f'Number of points in 1 second: {nmb_points_in_sec}\n'
              f'Distance between peaks (in points): {distance}\n')
    return distance

def convert_df_data_cols_to_numpy(data_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    return data_df['t'].to_numpy(), data_df['i'].to_numpy()

def convert_ambient_data_df_to_numpy(ambient_data_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    return ambient_data_df['t'].to_numpy(), ambient_data_df['i'].to_numpy()

def getMax_peaks(y: np.ndarray, distance: float, verbose: int = 0) -> np.ndarray:
    peaks, _ = find_peaks(y, distance=distance)
    if verbose == 2:
        print(f'Indices of max peaks: {peaks}')
    return peaks

def getMin_peaks(y: np.ndarray, distance: float, verbose: int = 0) -> np.ndarray:
    peaks, _ = find_peaks(-y, distance=distance)
    if verbose == 2:
        print(f'Indices of min peaks: {peaks}')
    return peaks

def get50ms_min_shifts(x: np.ndarray, peaks_min: np.ndarray, verbose: int = 0) -> Tuple[List[int], np.ndarray]:
    target_times = x[peaks_min] - 0.05
    indices = [np.abs(x - t).argmin() for t in target_times]
    if verbose == 2:
        print(f'50ms shift times: {target_times}\nShift indices: {indices}')
    return indices, target_times

def getAvrg_intensities(y: np.ndarray, peaks_min: np.ndarray, shift_indices: List[int], verbose: int = 0) -> List[float]:
    intensities = [abs(np.mean(y[start:end])) for start, end in zip(shift_indices, peaks_min)]
    if verbose == 2:
        print(f'Average intensities: {intensities}')
    return intensities

def extract_normalize_clean_periods(
    x: np.ndarray,
    y: np.ndarray,
    peaks_min: np.ndarray,
    periods_to_del: List[int],
    avrg_intensities: List[float],
    y_transpone_move = -1
) -> Tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray]]:
    curves, times, raw_times = [], [], []
    for i in range(len(peaks_min) - 1):
        if (i + 1) in periods_to_del:
            continue
        start, end = peaks_min[i], peaks_min[i + 1]
        segment = y[start:end]
        if avrg_intensities:
            segment = segment / avrg_intensities[i]
            segment += -segment[0]  # Normalize start to 0
        curves.append(segment)
        times.append(x[start:end] - x[start])
        raw_times.append(x[start:end])
    return curves, times, raw_times

def getNumber_of_periods(periods: List[np.ndarray], peaks_min: np.ndarray, periods_to_del: List[int], verbose: int = 0) -> Tuple[int, List[int]]:
    valid_indices = [i for i in range(len(peaks_min) - 1) if (i + 1) not in periods_to_del]
    if verbose == 2:
        print(f'Valid period indices: {valid_indices}')
    return len(periods), valid_indices

def getAvrg_curve(periods: List[np.ndarray], times: List[np.ndarray], num: int, verbose: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    lengths = [len(p) for p in periods]
    min_len = min(lengths)
    trimmed = [p[:min_len] for p in periods]
    trimmed_times = [t[:min_len] for t in times]
    if verbose == 2:
        print(f'Shortest period length: {min_len}')
    return np.mean(trimmed, axis=0), np.mean(trimmed_times, axis=0)

def getAngle_tan(A1x, A2x, A1y, A2y, B2y):
    adj = np.sqrt((A2x - A1x) ** 2 + (B2y - A1y) ** 2)
    opp = np.sqrt((B2y - A2y) ** 2)
    tang = opp / adj
    angle = np.degrees(np.arctan(tang))
    return angle, tang

def getAngle_dvdt_avrg_curve(x: np.ndarray, y: np.ndarray, verbose: int = 0) -> Tuple[float, float]:
    peak_val = np.max(y)
    idx_75 = np.abs(y[:np.argmax(y)] - 0.75 * peak_val).argmin()
    idx_25 = np.abs(y[:np.argmax(y)] - 0.25 * peak_val).argmin()
    A1x, A2x = x[idx_25], x[idx_75]
    A1y, A2y = y[idx_25], y[idx_75]
    angle, tang = getAngle_tan(A1x, A2x, A1y, A2y, A1y)
    if verbose == 2:
        print(f'Average curve angle: {angle}, tangent: {tang}')
    return angle, tang

def getAngle_dvdt_period_curves(times: List[np.ndarray], curves: List[np.ndarray], num: int, verbose: int = 0) -> Tuple[List[float], List[float]]:
    angles, tangents = [], []
    for i in range(num):
        y = curves[i]
        x = times[i]
        peak_val = np.max(y)
        idx_75 = np.abs(y[:np.argmax(y)] - 0.75 * peak_val).argmin()
        idx_25 = np.abs(y[:np.argmax(y)] - 0.25 * peak_val).argmin()
        A1x, A2x = x[idx_25], x[idx_75]
        A1y, A2y = y[idx_25], y[idx_75]
        angle, tang = getAngle_tan(A1x, A2x, A1y, A2y, A1y)
        angles.append(angle)
        tangents.append(tang)
        if verbose == 2:
            print(f'Period {i+1} angle: {angle}, tangent: {tang}')
    return angles, tangents

def getPeriods_curves_durations(curves: List[np.ndarray], times: List[np.ndarray], num: int, verbose: int = 0) -> Tuple[List[float], List[float], List[float]]:
    apd90, apd50, apd20 = [], [], []
    for i in range(num):
        y = curves[i]
        x = times[i]
        peak = max(y)
        idx = np.argmax(y)
        for target, acc in [(0.1, apd90), (0.5, apd50), (0.8, apd20)]:
            level = peak * target
            start = np.abs(y[:idx] - level).argmin()
            end = np.abs(y[idx:] - level).argmin() + idx
            acc.append(x[end] - x[start])
    return apd90, apd50, apd20

def getAvrg_cruve_durations(y: np.ndarray, x: np.ndarray, verbose: int = 0) -> List[float]:
    durations = []
    peak = max(y)
    idx = np.argmax(y)
    for target in [0.1, 0.5, 0.8]:
        level = peak * target
        start = np.abs(y[:idx] - level).argmin()
        end = np.abs(y[idx:] - level).argmin() + idx
        durations.append(x[end] - x[start])
    if verbose == 2:
        print(f'Average durations D90: {durations[0]}, D50: {durations[1]}, D20: {durations[2]}')
    return durations
