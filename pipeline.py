import numpy as np
from scipy.signal import find_peaks

def getPace_freq(pace_frequency, verbose=0):
    #pace_freq:float = 1 # USER_DEFINED
    if verbose == 2: print(f'Pacing frequency: {pace_frequency}')
    return pace_frequency

def getDistance_between_peaks(data_df, pace_freq, verbose: int = 0):
    nmb_points_in_sec = len(data_df['t'])/data_df['t'].iloc[-1] # time
    distance_between_peaks = nmb_points_in_sec/pace_freq - 27# 50/2, 50
    if verbose in [1,2]:
        print(f'Number of points in 1 second: {nmb_points_in_sec}\n\
              Distance between peaks (in points): {distance_between_peaks}\n')
    return distance_between_peaks

def convert_df_data_cols_to_numpy(data_df):
    x = data_df['t'].to_numpy()
    y = data_df['i'].to_numpy()
    return x, y

def convert_ambient_data_df_to_numpy(ambient_data_df):
    x_ambient = ambient_data_df['t'].to_numpy()
    y_ambient = ambient_data_df['i'].to_numpy()
    return x_ambient, y_ambient 

def getMax_peaks(y_selected, distance_between_peaks, verbose: int = 0):
    peaks_max, _ = find_peaks(y_selected, distance=distance_between_peaks)
    if verbose == 2: print(f'Indices of peaks (max): {peaks_max}')
    return peaks_max

def getMin_peaks(y_selected, distance_between_peaks, verbose: int = 0):
    y_selected_reflected = y_selected*(-1)
    peaks_min, _ = find_peaks(y_selected_reflected, distance=distance_between_peaks)
    if verbose == 2: print(f'Indices of peaks (min): {peaks_min}')
    return peaks_min

def get50ms_min_shifts(x, peaks_min, verbose=0):
    min_shifts50ms = x[peaks_min] - 0.05
    min_shift50ms_idxs = []
    for val in min_shifts50ms:
        min_shift50ms_idxs.append(np.abs(x - val).argmin())
        #
    if verbose == 2: print(f'Values of 50ms shifts: {min_shifts50ms}\n\
                           Indices of 50ms shifts: {min_shift50ms_idxs}')    
    return min_shift50ms_idxs, min_shifts50ms

def getAvrg_intensities(y_selected, peaks_min, min_shift50ms_idxs, verbose: int = 0):
    avrg_intensities = []
    for shift_idx, min_idx in zip(min_shift50ms_idxs, peaks_min):
        avrg_intensities.append(abs(np.average(y_selected[shift_idx:min_idx])))
        #
    if verbose == 2: print(f'Average intensities for every period: {avrg_intensities}')    
    return avrg_intensities

def extract_normalize_clean_periods(
        x, 
        y_selected, 
        peaks_min, 
        periods_to_del, 
        avrg_intensities,
        y_transpone_move = -1):
    periods_curves = []
    periods_curves_time = []
    periods_curves_time_sep = []
    for min_idx, peaks_num in enumerate(peaks_min):
        #print(min_idx, peaks_num)
        next_min_idx = min_idx + 1
        if (next_min_idx in periods_to_del) or (next_min_idx > list(peaks_min).index(list(peaks_min)[-1])):
            continue#break
        else:
            if avrg_intensities != None:
                period_curve = y_selected[peaks_min[min_idx]:peaks_min[next_min_idx]]/avrg_intensities[min_idx]
                period_curve_first_el = period_curve[0]
                y_transpone_move_auto = 0 - period_curve_first_el
                periods_curves.append( period_curve + y_transpone_move_auto )
            else:
                periods_curves.append( y_selected[peaks_min[min_idx]:peaks_min[next_min_idx]] )
            periods_curves_time.append(x[peaks_min[min_idx]:peaks_min[next_min_idx]]-x[peaks_num])
            periods_curves_time_sep.append(x[peaks_min[min_idx]:peaks_min[next_min_idx]])
            #
        #
    #
    return periods_curves, periods_curves_time, periods_curves_time_sep     

def getNumber_of_periods(periods_curves, peaks_min, periods_to_del, verbose: int = 0):
    nums_periods = np.asarray(periods_curves, dtype='object').shape[0]
    if verbose == 2: print(f'\nThere are {nums_periods} periods in total (after cleaning)')

    nums_periods_original_order = []
    peaks_min_original_order = enumerate(peaks_min)
    for i, val in peaks_min_original_order:
        if i+1 not in periods_to_del and i+1 <= list(peaks_min).index(list(peaks_min)[-1]):
            nums_periods_original_order.append(i)
    if verbose == 2: print(f'\nPeriods after cleaning with original order {nums_periods_original_order}, in total: {len(nums_periods_original_order)}')        
    return nums_periods, nums_periods_original_order

def getAvrg_curve(periods_curves, periods_curves_time, nums_periods, verbose: int = 0):
    np.random.seed(42)
    len_of_each_period = []
    for n in range(nums_periods):
        len_of_each_period.append(len(periods_curves[n]))

    smallest_len = np.min(len_of_each_period)

    num_of_elmts_to_del_each_period = np.abs(len_of_each_period - smallest_len)

    periods_curves_new = []
    periods_curves_time_new = []

    if verbose == 2:
        print(f'Period with the smallest length (in points): {smallest_len}\n\
              Number of elements to be deleted for each period: {num_of_elmts_to_del_each_period}\n')

    for n in range(nums_periods):    
        mask = []
        i = 0
        del_total = num_of_elmts_to_del_each_period[n]
        while i < del_total:
            r = np.random.randint(low=1, high=len_of_each_period[n])
            if r not in mask:
                mask.append(r)
                i += 1
                #print(r);
        #
        #if verbose == 2 and n == 1: print(f'len mask for period {n}:', len(mask), '\n')        
        periods_curves_new.append(
            [
                val for val in periods_curves[n] if list(periods_curves[n]).index(val) not in mask
                ]
            )
        periods_curves_time_new.append(
            [
                val for val in periods_curves_time[n] if list(periods_curves_time[n]).index(val) not in mask
                ]
            )
        #
    #
    periods_curves_new_avrg = np.average(periods_curves_new, axis=0) # , axis=0
    periods_curves_time_new_avrg = np.average(periods_curves_time_new, axis=0) # , axis=0    

    return periods_curves_new_avrg, periods_curves_time_new_avrg

def getAngle_tan(A1x, A2x, A1y, A2y, B2y):
    length_of_cat_adjecent = np.sqrt( np.power(A2x-A1x,2) + np.power(B2y-A1y,2) )
    length_of_cat_opposite = np.sqrt( np.power(A2x-A2x,2) + np.power(B2y-A2y,2) )
    #print('opposite', length_of_cat_opposite,' adjecent', length_of_cat_adjecent)
    tang = length_of_cat_opposite/length_of_cat_adjecent
    angle = np.arctan(tang)*180/np.pi
    return angle, tang

def getAngle_dvdt_avrg_curve(periods_curves_time_new_avrg, periods_curves_new_avrg, verbose: int = 0):
    fPeriodPeak = np.max(periods_curves_new_avrg)
    #fPeriodMin = np.min(periods_curves_new_avrg)
    fPeriodPeak75idx = np.abs(periods_curves_new_avrg[:list(periods_curves_new_avrg).index(fPeriodPeak)] - (fPeriodPeak*0.75)).argmin()
    fPeriodPeak25idx= np.abs(periods_curves_new_avrg[:list(periods_curves_new_avrg).index(fPeriodPeak)] - (fPeriodPeak*0.25)).argmin()
    #print('fPeriodPeak75idx ', fPeriodPeak75idx, 'fPeriodPeak25idx ', fPeriodPeak25idx)

    A1x, A2x = periods_curves_time_new_avrg[fPeriodPeak25idx], periods_curves_time_new_avrg[fPeriodPeak75idx]   
    A1y, A2y = periods_curves_new_avrg[fPeriodPeak25idx], periods_curves_new_avrg[fPeriodPeak75idx]
    B1x, B2x = A1x, A2x
    B1y, B2y = A1y, A1y
    
    # geometrical approach
    angle, tang = getAngle_tan(A1x, A2x, A1y, A2y, B2y)

    if verbose == 2:
        import matplotlib.pyplot as plt
        print(f'angle geometrically computed for the avrg curve: {angle}')
        print(f'tang geometrically computed for the avrg curve: {tang}')

        #print('A1x ', A1x, ' A1y ', A1y)
        #print('A2x ', A2x, ' A2y ', A2y)
        #print('B1x ', B1x, ' B1y ', B1y)
        #print('B2x ', B2x, ' B2y ', B2y)
        fig = plt.figure(figsize=(10,6)) # 12,8
        plt.plot(A1x, A1y, 'x', label='peak25', color='darkred', markersize=15)
        plt.plot(A2x, A2y, 'x', label='peak75', color='darkred', markersize=15)
        plt.plot(B1x, B1y, '>', color='green', markersize=15)
        plt.plot(B2x, B2y, '>', color='green', markersize=15)
        plt.plot((A1x, A2x), (A1y, A2y), label='lineA', color='midnightblue')
        plt.plot((B1x, B2x), (B1y, B2y), label='lineB', color='midnightblue')
        plt.plot((B2x, B2x), (B1y, A2y), label='lineC', color='midnightblue')
        plt.scatter(periods_curves_time_new_avrg, periods_curves_new_avrg, color='black', label='avrg')
        plt.xlabel('time, s')
        plt.ylabel('normalized intensity')
        plt.tight_layout()    
        plt.legend(loc='best') # 
        plt.grid()
        plt.show()
        print('\n')
        #
    return angle, tang
    ###

def getAngle_dvdt_period_curves(periods_curves_time, periods_curves, nums_periods, verbose: int = 0):

    fPeriod_dIdtMaxs = []
    fPeriod_angles = []
    for p in range(nums_periods):
        fPeriodPeak = np.max(periods_curves[p])
        #fPeriodMin = np.min(periods_curves[p])
        fPeriodPeak75idx = np.abs(periods_curves[p][:list(periods_curves[p]).index(fPeriodPeak)] - (fPeriodPeak*0.75)).argmin()
        fPeriodPeak25idx= np.abs(periods_curves[p][:list(periods_curves[p]).index(fPeriodPeak)] - (fPeriodPeak*0.25)).argmin()
        #print('fPeriodPeak75idx ', fPeriodPeak75idx, 'fPeriodPeak25idx ', fPeriodPeak25idx)

        A1x, A2x = periods_curves_time[p][fPeriodPeak25idx], periods_curves_time[p][fPeriodPeak75idx]   
        A1y, A2y = periods_curves[p][fPeriodPeak25idx], periods_curves[p][fPeriodPeak75idx]
        B1x, B2x = A1x, A2x
        B1y, B2y = A1y, A1y

        angle, tang = getAngle_tan(A1x, A2x, A1y, A2y, B2y)
        
        fPeriod_angles.append(angle)
        fPeriod_dIdtMaxs.append(tang) 

        if verbose == 2:
            import matplotlib.pyplot as plt
            print(f'angle geometrically computed for period {p+1}: {angle}')
            print(f'tang geometrically computed for period {p+1}: {tang}')  
            #print('A1x ', A1x, ' A1y ', A1y)
            #print('A2x ', A2x, ' A2y ', A2y)
            #print('B1x ', B1x, ' B1y ', B1y)
            #print('B2x ', B2x, ' B2y ', B2y)

            #plt.plot(A1x, A1y, 'x', label='peak25', markersize=12)
            #plt.plot(A2x, A2y, 'x', label='peak75', markersize=12)   
            #if p == 0:
            #    plt.plot((A1x, A2x), (A1y, A2y), label='lineA', color='midnightblue')
            #    plt.plot((B1x, B2x), (B1y, B2y), label='lineB', color='midnightblue')
            #    plt.plot((B2x, B2x), (B1y, A2y), label='lineC', color='midnightblue')  
            #plt.scatter(periods_curves_time[p], periods_curves[p], label=f'period {p}', alpha=0.5)
            print('\n')
            #
    #
    return fPeriod_angles, fPeriod_dIdtMaxs

def getPeriods_curves_durations(
        periods_curves, 
        periods_curves_time,
        nums_periods,
        verbose: int = 0):
    period_curves_apds20 = []
    period_curves_apds50 = []
    period_curves_apds90 = []
    for period in range(nums_periods):
        period_peak_val = max(periods_curves[period])
        period_peak_idx = list(periods_curves[period]).index(period_peak_val)

        period_peak90 = 0.1*period_peak_val
        period_peak90_idx_begin = np.abs(periods_curves[period][:period_peak_idx] - period_peak90).argmin()
        period_peak90_idx_end = np.abs(periods_curves[period][period_peak_idx:] - period_peak90).argmin() + period_peak_idx # list(periods_curves).index(periods_curves[period][-1])
        apd90 = periods_curves_time[period][period_peak90_idx_end] - periods_curves_time[period][period_peak90_idx_begin]
        period_curves_apds90.append(apd90)

        period_peak50 = 0.5*period_peak_val
        period_peak50_idx_begin = np.abs(periods_curves[period][:period_peak_idx] - period_peak50).argmin()
        period_peak50_idx_end = np.abs(periods_curves[period][period_peak_idx:] - period_peak50).argmin() + period_peak_idx
        apd50 = periods_curves_time[period][period_peak50_idx_end] - periods_curves_time[period][period_peak50_idx_begin]
        period_curves_apds50.append(apd50)

        period_peak20 = 0.8*period_peak_val
        period_peak20_idx_begin = np.abs(periods_curves[period][:period_peak_idx] - period_peak20).argmin()
        period_peak20_idx_end = np.abs(periods_curves[period][period_peak_idx:] - period_peak20).argmin() + period_peak_idx
        apd20 = periods_curves_time[period][period_peak20_idx_end] - periods_curves_time[period][period_peak20_idx_begin]
        period_curves_apds20.append(apd20)

    return period_curves_apds90, period_curves_apds50, period_curves_apds20

def getAvrg_cruve_durations(periods_curves_new_avrg, periods_curves_time_new_avrg, verbose: int = 0):
    avrg_curve_apds = []
    avrg_curve_peak_val = max(periods_curves_new_avrg)
    avrg_curve_peak_idx = list(periods_curves_new_avrg).index(avrg_curve_peak_val)
    #print(f'avrg_curve_peak_val: {avrg_curve_peak_val}, avrg_curve_peak_idx: {avrg_curve_peak_idx}')

    avrg_curve_peak90 = 0.1*avrg_curve_peak_val
    avrg_curve_peak90_idx_begin = np.abs(periods_curves_new_avrg[:avrg_curve_peak_idx] - avrg_curve_peak90).argmin()
    avrg_curve_peak90_idx_end = np.abs(periods_curves_new_avrg[avrg_curve_peak_idx:] - avrg_curve_peak90).argmin() + avrg_curve_peak_idx # list(periods_curves_new_avrg).index(periods_curves_new_avrg[-1])
    avrg_curve_apd90 = periods_curves_time_new_avrg[avrg_curve_peak90_idx_end] - periods_curves_time_new_avrg[avrg_curve_peak90_idx_begin]
    avrg_curve_apds.append(avrg_curve_apd90)

    avrg_curve_peak50 = 0.5*avrg_curve_peak_val
    avrg_curve_peak50_idx_begin = np.abs(periods_curves_new_avrg[:avrg_curve_peak_idx] - avrg_curve_peak50).argmin()
    avrg_curve_peak50_idx_end = np.abs(periods_curves_new_avrg[avrg_curve_peak_idx:] - avrg_curve_peak50).argmin() + avrg_curve_peak_idx
    avrg_curve_apd50 = periods_curves_time_new_avrg[avrg_curve_peak50_idx_end] - periods_curves_time_new_avrg[avrg_curve_peak50_idx_begin]
    avrg_curve_apds.append(avrg_curve_apd50)

    avrg_curve_peak20 = 0.8*avrg_curve_peak_val
    avrg_curve_peak20_idx_begin = np.abs(periods_curves_new_avrg[:avrg_curve_peak_idx] - avrg_curve_peak20).argmin()
    avrg_curve_peak20_idx_end = np.abs(periods_curves_new_avrg[avrg_curve_peak_idx:] - avrg_curve_peak20).argmin() + avrg_curve_peak_idx
    avrg_curve_apd20 = periods_curves_time_new_avrg[avrg_curve_peak20_idx_end] - periods_curves_time_new_avrg[avrg_curve_peak20_idx_begin]
    avrg_curve_apds.append(avrg_curve_apd20)

    if verbose == 2: # 2
        import matplotlib.pyplot as plt
        print(f'Durations for the avrg curve:\nD90: {avrg_curve_apds[0]}\nD50: {avrg_curve_apds[1]}\nD20: {avrg_curve_apds[2]}')

        fig = plt.figure(figsize=(10,6)) # 12,8

        A1x = periods_curves_time_new_avrg[avrg_curve_peak90_idx_begin]
        A1y = periods_curves_new_avrg[avrg_curve_peak90_idx_begin]
        A2x = periods_curves_time_new_avrg[avrg_curve_peak90_idx_end]
        A2y = periods_curves_new_avrg[avrg_curve_peak90_idx_end]

        B1x = periods_curves_time_new_avrg[avrg_curve_peak50_idx_begin]
        B1y = periods_curves_new_avrg[avrg_curve_peak50_idx_begin]
        B2x = periods_curves_time_new_avrg[avrg_curve_peak50_idx_end]
        B2y = periods_curves_new_avrg[avrg_curve_peak50_idx_end]

        C1x = periods_curves_time_new_avrg[avrg_curve_peak20_idx_begin]
        C1y = periods_curves_new_avrg[avrg_curve_peak20_idx_begin]
        C2x = periods_curves_time_new_avrg[avrg_curve_peak20_idx_end]
        C2y = periods_curves_new_avrg[avrg_curve_peak20_idx_end]


        #plt.plot(A1x, A1y, 'x', label='peak25', color='black', markersize=12)
        #plt.plot(A2x, A2y, 'x', label='peak75', color='black', markersize=12)
        #plt.plot(B1x, B1y, '>', color='black', markersize=12) 
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak_idx], periods_curves_new_avrg[avrg_curve_peak_idx], 'D', color='darkred', label='peak',markersize=12)
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak90_idx_begin], periods_curves_new_avrg[avrg_curve_peak90_idx_begin], 'x', color='darkred', markersize=20)
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak50_idx_begin], periods_curves_new_avrg[avrg_curve_peak50_idx_begin], 'x', color='midnightblue', markersize=20)
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak20_idx_begin], periods_curves_new_avrg[avrg_curve_peak20_idx_begin], 'x', color='darkgreen', markersize=20)
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak90_idx_end], periods_curves_new_avrg[avrg_curve_peak90_idx_end], 'x', color='darkred', markersize=12)
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak50_idx_end], periods_curves_new_avrg[avrg_curve_peak50_idx_end], 'x', color='midnightblue', markersize=12)
        plt.plot(periods_curves_time_new_avrg[avrg_curve_peak20_idx_end], periods_curves_new_avrg[avrg_curve_peak20_idx_end], 'x', color='darkgreen', markersize=12)
        plt.plot((A1x, A2x), (A1y, A2y), label='D90', color='darkred')
        plt.plot((B1x, B2x), (B1y, B2y), label='D50', color='midnightblue')
        plt.plot((C1x, C2x), (C1y, C2y), label='D20', color='darkgreen')
        plt.scatter(periods_curves_time_new_avrg, periods_curves_new_avrg, color='black', label='avrg')
        plt.xlabel('time, s')
        plt.ylabel('normalized intensity')
        plt.tight_layout()    
        plt.legend(loc='best') # bbox_to_anchor=(1.01, 1.0), loc='upper left'
        plt.grid()
        plt.show()
        print('\n')
        
    return avrg_curve_apds