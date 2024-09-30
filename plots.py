import matplotlib.pyplot as plt
import numpy as np
#import random
import mplcursors

'''
after mplcursors installation there were conflicts with
numpy (ver 2.0.0 is incompatible with some other libs), pandas, matplotlib (ver 3.9.0)
had to reinstall numpy and pandas as
    pip install numpy==1.26.4 pandas==2.2.1
and then matplotlib as
    pip install matplotlib==3.7.1
but got 'NoneType' object has no attribute 'canvas'
maybe install   pip install matplotlib==3.5.1      
'''

palette = np.linspace(0,1,30)
#for c in palette:
#	print(f'\n{c}')
colors = plt.cm.gist_rainbow(palette)

'''def pick_color_ver1():
    b = round(random.uniform(0.1,0.99), 2)
    col = plt.cm.rainbow(b) # random from 0 to 1
    return col'''

fig_w, fig_h = 12, 8

def pltBaseline_signal(x, y, withAmbient) -> None:
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y, label='baseline signal')
    plt.title(f'Input signal {withAmbient}')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()
    plt.grid()
    plt.show()
    ###

def pltBaseline_and_Filtered_signal(
        x, 
        y, 
        y_filtered, 
        filter_name: str,
        filter_mode,
        withAmbient) -> None:
    
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x,y, label='baseline signal')
    plt.plot(x,y_filtered, color='red', alpha=0.5, label=filter_name)
    plt.title(f'input signal {withAmbient} + {filter_name}, Mode {filter_mode}')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()
    plt.grid()
    plt.show()
    ###

def pltFiltered_signal(
        x, 
        y_selected, 
        filter_name: str,
        filter_mode,
        withAmbient) -> None:
    
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.plot(x, y_selected, alpha=0.5, color='red', label='filtered signal')
    #plt.title(f'{y_selected =}'.split('=')[0])
    plt.title(f'input signal {withAmbient} filtered with {filter_name}, Mode {filter_mode}')
    plt.xlabel('time, s')
    plt.ylabel('intensity')
    plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()
    plt.grid()
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

def pltFiltered_signal_with_extrema_and_periodsDivision(
        x, 
        y_selected, 
        peaks_min, 
        peaks_max, 
        min_shift50ms_idxs) -> None:
    
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.title('filtered signal with extrema and periods division')
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
   
def pltFiltered_norm_signal_clean_divided_reduced2zero(
        periods_curves_time_new_avrg,
        periods_curves_new_avrg,
        periods_curves_time,
        periods_curves,
        nums_periods_original_order) -> None:
    
    fig = plt.figure(figsize=(fig_w, fig_h))
    plt.plot(periods_curves_time_new_avrg, periods_curves_new_avrg, color='black', label='avrg')

    #period_num = 1
    for curve_time, curve, n in zip(periods_curves_time, periods_curves, nums_periods_original_order):
        plt.plot(curve_time, curve, label=f'period {n+1}', alpha=0.5, color=colors[n])
        #period_num += 1
        #

    plt.xlabel('time, s')
    plt.ylabel('normalized intensity')
    #plt.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    plt.tight_layout()    
    plt.legend(loc='best')
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
