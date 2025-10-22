# src/plots.py — Visualization utilities

import matplotlib.pyplot as plt
import numpy as np
import mplcursors
from typing import Optional, List

fig_w, fig_h = 12, 8
colors = plt.cm.gist_rainbow(np.linspace(0, 1, 30))

def pltBaseline_signal(x: np.ndarray, y: np.ndarray, label_suffix: str = '') -> None:
    plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y, label='baseline signal')
    plt.title(f'Input signal {label_suffix}')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def pltBaseline_and_Filtered_signal(x: np.ndarray, y: np.ndarray, y_filtered: np.ndarray, filter_name: str, filter_mode, label_suffix: str = '') -> None:
    plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y, label='baseline')
    plt.plot(x, y_filtered, label=filter_name, alpha=0.5, color='red')
    plt.title(f'Signal + {filter_name}, Mode {filter_mode} {label_suffix}')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def pltFiltered_signal(x: np.ndarray, y: np.ndarray, filter_name: str, filter_mode, label_suffix: str = '') -> None:
    plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y, label='filtered signal', color='red', alpha=0.5)
    plt.title(f'Filtered signal with {filter_name}, Mode {filter_mode} {label_suffix}')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def pltFiltered_signal_with_extrema_and_periodsDivision(x: np.ndarray, y: np.ndarray, peaks_min: np.ndarray, peaks_max: np.ndarray, shift_idxs: Optional[List[int]] = None) -> None:
    plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y, label='filtered signal')
    plt.plot(x[peaks_max], y[peaks_max], 'x', label='max')
    plt.plot(x[peaks_min], y[peaks_min], 'x', label='min')
    if shift_idxs is not None:
        plt.plot(x[shift_idxs], y[shift_idxs], 'o', label='50ms shifts', color='darkred')
    plt.vlines(x[peaks_min], y.min() - 1, y.max() + 2, linestyle='--', color='gray')
    for i in range(len(peaks_min) - 1):
        plt.text(x[peaks_max[i]], y.max() + 1, f'period {i+1}', fontsize=9)
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.title('Filtered signal with extrema and period divisions')
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def pltFiltered_norm_signal_clean_divided_reduced2zero(
    avg_time: np.ndarray,
    avg_curve: np.ndarray,
    all_times: List[np.ndarray],
    all_curves: List[np.ndarray],
    labels: List[int]
) -> None:
    plt.figure(figsize=(fig_w, fig_h))
    plt.plot(avg_time, avg_curve, color='black', label='average')
    for t, y, n in zip(all_times, all_curves, labels):
        plt.plot(t, y, alpha=0.5, label=f'period {n+1}', color=colors[n])
    plt.xlabel('time, s')
    plt.ylabel('normalized intensity')
    plt.title('Normalized periods and average curve')
    plt.legend()
    plt.grid(True)
    mplcursors.cursor(highlight=True).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))
    plt.tight_layout()
    plt.show()
###
def pltFiltered_signal_with_extrema(
        x, 
        y_selected, 
        peaks_min, 
        peaks_max) -> None:
    
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y_selected, label='filtered signal')
    plt.plot(x[peaks_max], y_selected[peaks_max], "x", label='max')
    plt.plot(x[peaks_min], y_selected[peaks_min], "x", label='min')
    plt.title('filtered signal with extrema')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()
    plt.show()
    ###
    
def pltFiltered_signal_with_extr_prdDiv_and_expectChanges(
        x, 
        y_selected, 
        peaks_min, 
        peaks_max, 
        min_shift50ms_idxs, 
        periods_to_del) -> None:
    
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.title('filtered signal + what will be removed (in red)')
    plt.plot(x, y_selected, label='filtered signal')
    plt.plot(x[peaks_max], y_selected[peaks_max], "x", label='max')
    plt.plot(x[peaks_min], y_selected[peaks_min], "x", label='min')
    if min_shift50ms_idxs != None:
        plt.plot(x[min_shift50ms_idxs], y_selected[min_shift50ms_idxs], "o", label='50ms_shifts', markersize=5, color='darkred')

    plt.vlines(x[peaks_min], min(y_selected[peaks_min])-1, max(y_selected[peaks_max])+2, linestyle='--', color='dimgrey')
    idx_of_max_peaks_max = list(y_selected[peaks_max]).index(max(y_selected[peaks_max]))
    rotation = 45 if len(peaks_min)-1 > 10 else 0
    for i in range(len(peaks_min)-1):
        plt.text(x[peaks_max[i]]-0.15, y_selected[peaks_max[idx_of_max_peaks_max]]+1, f'period {i+1}', fontsize = 10, rotation=rotation) 
    plt.ylim([min(y_selected[peaks_min])-2, max(y_selected[peaks_max])+4])

    plt.plot(x[:peaks_min[0]], y_selected[:peaks_min[0]], color='red') # drop left appendix
    plt.plot(x[peaks_min[-1]:], y_selected[peaks_min[-1]:], color='red') # drop right appendix
    # drop periods to del
    for p in periods_to_del:
        plt.plot(x[peaks_min[p-1]:peaks_min[p]], y_selected[peaks_min[p-1]:peaks_min[p]], color='red')
        plt.text(x[peaks_max[p-1]]-0.15, y_selected[peaks_max[idx_of_max_peaks_max]]+1, f'period {p}', fontsize = 10, color='red', rotation=rotation)

    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()
    plt.show()
    ###

def pltFiltered_norm_signal_clean_divided(
        periods_curves_time_sep,
        periods_curves,
        nums_periods,
        nums_periods_original_order) -> None:
      
    fig = plt.figure(figsize=(fig_w, fig_h))

    for i, n in zip(range(nums_periods), nums_periods_original_order):
        plt.plot(periods_curves_time_sep[i], periods_curves[i], label=f'period {n+1}', color=colors[n])
        #
    plt.title('filtered normalized signal after changes\n(NEW period numeration)')    
    plt.xlabel('time, s')
    plt.ylabel('normalized intensity')
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()
    plt.grid()
    mplcursors.cursor(highlight=True).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))
    plt.show()
    ###

def pltAvrg_period_angles(A1x, A2x, A1y, A2y, B1x, B2x, B1y, B2y) -> None:

    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.plot(A1x, A1y, 'x', label='peak25', color='black', markersize=12)
    plt.plot(A2x, A2y, 'x', label='peak75', color='black', markersize=12)
    plt.plot(B1x, B1y, '>', color='black', markersize=12)
    plt.plot(B2x, B2y, '>', color='darkred', markersize=12)
    plt.plot((A1x, A2x), (A1y, A2y), label='lineA', color='midnightblue')
    plt.plot((B1x, B2x), (B1y, B2y), label='lineB', color='midnightblue')
    plt.plot((B2x, B2x), (B1y, A2y), label='lineC', color='midnightblue')
    plt.xlabel('time, s')
    plt.ylabel('normalized intensity')
    plt.tight_layout()    
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.grid()
    plt.show()
    ###