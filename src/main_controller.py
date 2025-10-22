# src/main_controller.py — Core controller logic

from src.input_data import inputExcel, inputAmbientDataExcel
from src.pipeline import (
    getPace_freq,
    getDistance_between_peaks,
    convert_df_data_cols_to_numpy,
    convert_ambient_data_df_to_numpy,
    getMax_peaks,
    getMin_peaks,
    get50ms_min_shifts,
    getAvrg_intensities,
    extract_normalize_clean_periods,
    getNumber_of_periods,
    getAvrg_curve,
    getAngle_dvdt_avrg_curve,
    getAngle_dvdt_period_curves,
    getAvrg_cruve_durations,
    getPeriods_curves_durations
)
from src.filters import (
    use_gaussian_filter1d,
    use_lowpass_filter,
    use_savgol_filter,
    use_combined_filter
)
from src.output_data import *
from src.plots import *
from src.gui import MainWindow, PeriodsWindow, FiltersUtilityWindow

def main_func():
    app.isExit = 'no'
    pace_frequency, y_transpone_move, verbose = app.setGlobalParams()
    input_path = app.setInputDataPath()
    input_ambient_data_path = app.setInputBaselineDataPath()
    use_optional_ambient_data = input_ambient_data_path != -1
    withAmbient = 'minus ambient' if use_optional_ambient_data else ''
    output_path = app.setOutputDataPath()

    baseline_data_df = inputExcel(input_path, verbose=verbose)
    if use_optional_ambient_data:
        ambient_data_df = inputAmbientDataExcel(input_ambient_data_path, verbose=verbose)

    pace_freq = getPace_freq(pace_frequency, verbose=verbose)
    distance_between_peaks = getDistance_between_peaks(baseline_data_df, pace_freq, verbose=verbose)
    x, y = convert_df_data_cols_to_numpy(baseline_data_df)
    if use_optional_ambient_data:
        x_ambient, y_ambient = convert_ambient_data_df_to_numpy(ambient_data_df)
        y = y - y_ambient

    if verbose in [1,2]:
        pltBaseline_signal(x, y, withAmbient)

    if should_exit(): return None

    sub_app_FiltersUtility = FiltersUtilityWindow(x, y)
    app.wait_window(sub_app_FiltersUtility)

    setFilterName, setFilterMode, setFilterPrmtrs = sub_app_FiltersUtility.setOneFilter()
    if setFilterName == 'Gaussian filter':
        y_filtered, _ = use_gaussian_filter1d(y, *setFilterPrmtrs)
    elif setFilterName == 'Lowpass filter':
        y_filtered, _ = use_lowpass_filter(y, *setFilterPrmtrs)
    elif setFilterName == 'Savgol filter':
        y_filtered, _ = use_savgol_filter(y, *setFilterPrmtrs)
    else:
        y_combined_filters = []
        if setFilterMode[0]:
            y_combined_filters.append(use_gaussian_filter1d(y, *setFilterPrmtrs[0])[0])
        if setFilterMode[1]:
            y_combined_filters.append(use_lowpass_filter(y, *setFilterPrmtrs[1])[0])
        if setFilterMode[2]:
            y_combined_filters.append(use_savgol_filter(y, *setFilterPrmtrs[2])[0])
        y_filtered, _ = use_combined_filter(y_combined_filters)

    y_selected = y_filtered

    if verbose in [1,2]:
        pltBaseline_and_Filtered_signal(x, y, y_filtered, setFilterName, setFilterMode, withAmbient)
        pltFiltered_signal(x, y_selected, setFilterName, setFilterMode, withAmbient)

    if app.setIsExit() == 'yes': return None
    app.buttonAbortMain.config(state='disabled')

    if should_exit(): return None

    peaks_max = getMax_peaks(y_selected, distance_between_peaks, verbose=verbose)
    peaks_min = getMin_peaks(y_selected, distance_between_peaks, verbose=verbose)
    min_shift50ms_idxs, _ = get50ms_min_shifts(x, peaks_min, verbose=verbose)
    avrg_intensities = getAvrg_intensities(y_selected, peaks_min, min_shift50ms_idxs, verbose=verbose)

    while True:
        sub_app_Periods = PeriodsWindow(peaks_min)
        if verbose:
            pltFiltered_signal_with_extrema_and_periodsDivision(x, y_selected, peaks_min, peaks_max, min_shift50ms_idxs)
        app.wait_window(sub_app_Periods)
        periods_to_del = sub_app_Periods.setPeriodsToDelete()

        if verbose:
            pltFiltered_signal_with_extr_prdDiv_and_expectChanges(x, y_selected, peaks_min, peaks_max, min_shift50ms_idxs, periods_to_del)

        periods_curves, periods_curves_time, periods_curves_time_sep = extract_normalize_clean_periods(
            x, y_selected, peaks_min, periods_to_del, avrg_intensities, y_transpone_move)

        nums_periods, nums_periods_original_order = getNumber_of_periods(periods_curves, peaks_min, periods_to_del, verbose=verbose)

        if verbose == 2:
            pltFiltered_norm_signal_clean_divided(periods_curves_time_sep, periods_curves, nums_periods, nums_periods_original_order)

        periods_curves_new_avrg, periods_curves_time_new_avrg = getAvrg_curve(
            periods_curves, periods_curves_time, nums_periods, verbose=verbose)

        if verbose in [1,2]:
            pltFiltered_norm_signal_clean_divided_reduced2zero(
                periods_curves_time_new_avrg, periods_curves_new_avrg,
                periods_curves_time, periods_curves, nums_periods_original_order)
            if app.repeatPeriodsStage():
                break

    avrg_curve_angle, avrg_curve_tan = getAngle_dvdt_avrg_curve(
        periods_curves_time_new_avrg, periods_curves_new_avrg, verbose=verbose)

    period_curves_angles, period_curves_tans = getAngle_dvdt_period_curves(
        periods_curves_time, periods_curves, nums_periods, verbose=verbose)

    avrg_curve_apds = getAvrg_cruve_durations(
        periods_curves_new_avrg, periods_curves_time_new_avrg, verbose=verbose)

    period_curves_apds90, period_curves_apds50, period_curves_apds20 = getPeriods_curves_durations(
        periods_curves, periods_curves_time, nums_periods, verbose=verbose)

    curves_dfT = outputCurves(
        periods_curves_time, periods_curves,
        periods_curves_time_new_avrg, periods_curves_new_avrg,
        nums_periods, nums_periods_original_order)

    angles_tans_dfT = outputAnglesTans(
        period_curves_angles, period_curves_tans,
        avrg_curve_angle, avrg_curve_tan,
        nums_periods, nums_periods_original_order)

    durations_dfT = outputDurations(
        avrg_curve_apds,
        period_curves_apds90, period_curves_apds50, period_curves_apds20,
        nums_periods, nums_periods_original_order)

    outputExcel(output_path, curves_dfT, angles_tans_dfT, durations_dfT, verbose=verbose)
    print('Output saved')

    return 0

def should_exit():
    return app.setIsExit() == 'yes'

def launch_app():
    global app
    app = MainWindow(main_func)
    app.mainloop()
