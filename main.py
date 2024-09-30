from input_data import *
from pipeline import *
from filters import *
from output_data import *
from plots import *

from gui import MainWindow, PeriodsWindow, FiltersUtilityWindow

'''
checked with ambient data added; angles and tangents are different because of scale
with ambient data, amplitudes are about 10 times larger
'''

def main_func():
    # GLOBAL
    app.isExit = 'no'
    #pace_frequency = glistGlobalParams[0] # USER_DEFINED
    #y_transpone_move = glistGlobalParams[1] #
    #verbose = glistGlobalParams[2] # USER_DEFINED  #how much to print and plot? GLOBAL
    pace_frequency, y_transpone_move, verbose = app.setGlobalParams()
    #print(f'set verbose: {verbose}, type: {type(verbose)}')
    input_path = app.setInputDataPath() #gInputDataPath

    input_ambient_data_path = app.setInputBaselineDataPath()
    use_optional_ambient_data = False; withAmbient = ''
    if input_ambient_data_path != -1: use_optional_ambient_data = True; withAmbient = 'minus ambient'

    output_path = app.setOutputDataPath() #gOutputDataPath

    # input baseline data
    baseline_data_df = inputExcel(input_path, verbose=verbose)
    # input optional ambient data
    if use_optional_ambient_data:
        ambient_data_df = inputAmbientDataExcel(input_ambient_data_path, verbose=verbose)
    print('Data loaded and read\n')

    # get pacing frequency (to calculate distance/points between two  adjacent peaks)
    pace_freq = getPace_freq(pace_frequency, verbose=verbose)

    # get distance_between_peaks
    distance_between_peaks = getDistance_between_peaks(baseline_data_df, pace_freq, verbose=verbose)

    # convert time and signal columns to numpy arrays
    x, y = convert_df_data_cols_to_numpy(baseline_data_df)
    if use_optional_ambient_data:
        x_ambient, y_ambient = convert_ambient_data_df_to_numpy(ambient_data_df)
        #x = x - x_ambient # new x
        y = y - y_ambient # new y

    # pltBaseline_signal
    if verbose in [1,2]: # NOT ALWAYS
        pltBaseline_signal(x, y, withAmbient)
    ########
    # check if want to abort
    isExit = app.setIsExit()
    if isExit == 'yes': return None
    ######
    # filter utility 
    sub_app_FiltersUtility = FiltersUtilityWindow(x, y)
    app.wait_window(sub_app_FiltersUtility)
    ######

    # get filtered signal
    setFilterName, setFilterMode, setFilterPrmtrs = sub_app_FiltersUtility.setOneFilter()
    if setFilterName == 'Gaussian filter':
        #y_filtered = sub_app_FiltersUtility.getY_gaussian_filter()
        y_filtered, _ = use_gaussian_filter1d(y, setFilterPrmtrs[0], setFilterPrmtrs[1])
    elif setFilterName == 'Lowpass filter':
        #y_filtered = sub_app_FiltersUtility.getY_lowpass_filter()
        y_filtered, _ = use_lowpass_filter(y, setFilterPrmtrs[0], setFilterPrmtrs[1], setFilterPrmtrs[2])
    elif setFilterName == 'Savgol filter':
        #y_filtered = sub_app_FiltersUtility.getY_savgol_filter()
        y_filtered, _ = use_savgol_filter(y, setFilterPrmtrs[0], setFilterPrmtrs[1])
    else: 
        #y_filtered = sub_app_FiltersUtility.getY_combined_filter()
        y_combined_filters = []
        if setFilterMode[0] != 0:
            y_combined_gaussian_filter, _ = use_gaussian_filter1d(y, setFilterPrmtrs[0][0], setFilterPrmtrs[0][1])
            y_combined_filters.append(y_combined_gaussian_filter)
        if setFilterMode[1] != 0:
            y_combined_lowpass_filter, _ = use_lowpass_filter(y, setFilterPrmtrs[1][0], setFilterPrmtrs[1][1], setFilterPrmtrs[1][2])
            y_combined_filters.append(y_combined_lowpass_filter)
        if setFilterMode[2] != 0:
            y_combined_savgol_filter, _ = use_savgol_filter(y, setFilterPrmtrs[2][0], setFilterPrmtrs[2][1])
            y_combined_filters.append(y_combined_savgol_filter)     
        y_filtered, _ = use_combined_filter(y_combined_filters)

    filter_name = setFilterName
    filter_mode = setFilterMode
    #y_filtered, filter_name = use_lowpass_filter(y)
    if verbose in [1,2]: print(f'Chosen filter: {filter_name}, Mode {filter_mode}\n') # filter_name

    # select a filtered curve to use (maybe deprecate)
    y_selected = y_filtered

    # pltBaseline_and_Filtered_signal
    if verbose in [1,2]: # ALWAYS
        pltBaseline_and_Filtered_signal(
            x, 
            y, 
            y_filtered, 
            filter_name,
            filter_mode,
            withAmbient)
        ###
    # check if want to abort
    isExit = app.setIsExit()
    if isExit == 'yes': return None 
    #    
    if verbose in [1,2]: # ALWAYS    
        pltFiltered_signal(
        x, 
        y_selected, 
        filter_name,
        filter_mode,
        withAmbient)

    # check if want to abort
    isExit = app.setIsExit()
    if isExit == 'yes': return None
    app.buttonAbortMain.config(state='disabled') 

    ########

    # get max peaks
    peaks_max = getMax_peaks(y_selected, distance_between_peaks, verbose=verbose)

    # get min peaks
    peaks_min = getMin_peaks(y_selected, distance_between_peaks, verbose=verbose)

    # get indexes of 50ms shifts from mins (don't output X values of these shifts)
    #if use_optional_ambient_data == False:
    min_shift50ms_idxs, _ = get50ms_min_shifts(x, peaks_min, verbose=verbose)
    #else: min_shift50ms_idxs = None     

    # get avrg intensities for each period
    #if use_optional_ambient_data == False:
    avrg_intensities = getAvrg_intensities(y_selected, peaks_min, min_shift50ms_idxs, verbose=verbose)
    #else: avrg_intensities = None    

    ### repeat the following stage if need to delete more periods         
    period_stage = 1
    while period_stage == 1:
    
        ######
        # BEGIN: decide which periods to be deleted
        sub_app_Periods = PeriodsWindow(peaks_min) # app, 
        #sub_app.grab_set()
        ######

        # pltFiltered_signal_with_extrema_and_periodsDivision
        if verbose: # ALWAYS
            pltFiltered_signal_with_extrema_and_periodsDivision(
                x, 
                y_selected, 
                peaks_min, 
                peaks_max, 
                min_shift50ms_idxs)
                ### 

        # END: decide which periods to be deleted
        app.wait_window(sub_app_Periods)
        #periods_to_del = [2] # USER_DEFINED #which periods to delete
        periods_to_del = sub_app_Periods.setPeriodsToDelete() #periods_to_del_nmb # list of periods to del (starts with 1)
            
        if verbose: # ALWAYS
            pltFiltered_signal_with_extr_prdDiv_and_expectChanges(
            x, 
            y_selected, 
            peaks_min, 
            peaks_max, 
            min_shift50ms_idxs, 
            periods_to_del)
            ###

        # extract full periods (except those to be deleted) 
        #from filtered signal and normalize each period
        periods_curves, periods_curves_time, periods_curves_time_sep = \
            extract_normalize_clean_periods(x, y_selected, 
                                            peaks_min, 
                                            periods_to_del, 
                                            avrg_intensities,
                                            y_transpone_move)

        # get number of periods, new numerations after dropping periods_to_del
        nums_periods, nums_periods_original_order = getNumber_of_periods(
            periods_curves, 
            peaks_min,
            periods_to_del, 
            verbose=verbose)
        
        # pltFiltered_norm_signal_clean_divided
        if verbose in [2]: # NOT ALWAYS
            pltFiltered_norm_signal_clean_divided(
            periods_curves_time_sep,
            periods_curves,
            nums_periods,
            nums_periods_original_order)
            ###

        # get time and signal of averaged curve
        # the length of these arrays is the one of the smallest length of periods_curves
        periods_curves_new_avrg, periods_curves_time_new_avrg = \
            getAvrg_curve(periods_curves, periods_curves_time, nums_periods, verbose=verbose)
        
        #
        if verbose in [1,2]: # ALWAYS
            pltFiltered_norm_signal_clean_divided_reduced2zero(
            periods_curves_time_new_avrg,
            periods_curves_new_avrg,
            periods_curves_time,
            periods_curves,
            nums_periods_original_order)
            ###

        out = app.repeatPeriodsStage()
        if out == 1:
            period_stage = 0
        else: period_stage = 1	
    # got out of period_stage

    # get angle and corresponding tangent of avrg curve
    avrg_curve_angle, avrg_curve_tan = \
        getAngle_dvdt_avrg_curve(periods_curves_time_new_avrg, 
                                 periods_curves_new_avrg, 
                                 verbose=verbose)

    # get angles and correspodning tangents of all full periods
    period_curves_angles, period_curves_tans = \
        getAngle_dvdt_period_curves(periods_curves_time, 
                                    periods_curves, 
                                    nums_periods, 
                                    verbose=verbose)
    
    # get durations of avrg curve
    avrg_curve_apds = getAvrg_cruve_durations(periods_curves_new_avrg, periods_curves_time_new_avrg, verbose=verbose)

    # get durations of all full periods
    period_curves_apds90, period_curves_apds50, period_curves_apds20 = getPeriods_curves_durations(
        periods_curves, 
        periods_curves_time,
        nums_periods,
        verbose=verbose)
    
    # put curves in a dataframe to further save
    curves_dfT = outputCurves(
        periods_curves_time,
        periods_curves,
        periods_curves_time_new_avrg,
        periods_curves_new_avrg,
        nums_periods,
        nums_periods_original_order)
    
    # put angles and tangents in a dataframe to further save
    angles_tans_dfT = outputAnglesTans(
        period_curves_angles,
        period_curves_tans,
        avrg_curve_angle,
        avrg_curve_tan,
        nums_periods,
        nums_periods_original_order)
    
    # put durations of avrg curve and period curves in a dataframe to further save
    durations_dfT = outputDurations(
        avrg_curve_apds,
        period_curves_apds90, 
        period_curves_apds50, 
        period_curves_apds20,
        nums_periods,
        nums_periods_original_order)
    
    # save all data to xlsx file
    outputExcel(output_path, curves_dfT, angles_tans_dfT, durations_dfT, verbose=verbose)
    print('Output saved\n')
    
    return 0
######

# root was here
#######


#

if __name__ == '__main__':
    print('Program started\n\n')
    print(
        '        #####################################################################\n\
        #                                                                   #\n\
        #    ___  ___  _______   ___       ___       ________  ___          #\n\
        #   |\  \|\  \|\  ___ \ |\  \     |\  \     |\   __  \|\  \         #\n\
        #   \ \  \\\  \ \   __/|\ \  \    \ \  \    \ \  \|\  \ \  \         #\n\
        #    \ \   __  \ \  \_|/_\ \  \    \ \  \    \ \  \\\  \ \  \        #\n\
        #     \ \  \ \  \ \  \_|\ \ \  \____\ \  \____\ \  \\\  \ \__\       #\n\
        #      \ \__\ \__\ \_______\ \_______\ \_______\ \_______\|__|      #\n\
        #       \|__|\|__|\|_______|\|_______|\|_______|\|_______|   ___    #\n\
        #                                                           |\__\   #\n\
        #                                                           \|__|   #\n\
        #                                                                   #\n\
        #####################################################################\n\
        ')
    
    print('\n')
    print('Open Quick Start Guide for help')
    print('\n')

    '''with open('quick_start_guide.txt', 'r') as quick_start_guide:
        #lines = [next(quick_start_guide) for _ in range(38)]
        #print(quick_start_guide.read()) # quick_start_guide.read() lines

        lines = quick_start_guide.readlines()
        third_line = lines[:38] #reads the 3rd line in the doc
        print(third_line)'''

    """print(f'\nGlobal parameters:\n\
        1) Pacing frequency (Hz) --- period of stimulus \n\ 
        2) Y transposition --- OY starting point processed signal \n\
        3) Verbose --- detalization of output info \n\
        \t 0 --- silent\n\
        \t 1 --- major plots and messages\n\
        \t 2 --- all plots and messages\n')"""
    
    '''print('I. Buttons\n\
          Set global parameters --- pass the values of the global parameters ')'''

    ###
    app = MainWindow(main_func)
    app.mainloop()
    #
    print('Program finished\n')

