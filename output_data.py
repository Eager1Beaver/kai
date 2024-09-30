import pandas as pd

def outputCurves(
        periods_curves_time,
        periods_curves,
        periods_curves_time_new_avrg,
        periods_curves_new_avrg,
        nums_periods,
        nums_periods_original_order) -> None:
    """
    outputs curves data
    """
    # periods
    periods_curves_df = pd.DataFrame([
        curve for curve in periods_curves
        ])  

    # use time array with the biggest max value
    # update: it may have shorter length
    '''max_time_stamp_for_period = []
    for time_p in range(nums_periods):
        max_time_stamp = max(periods_curves_time[time_p])
        max_time_stamp_for_period.append(max_time_stamp)
        #
    idx_maxest_time_stamp = max_time_stamp_for_period.index(max(max_time_stamp_for_period))    
    periods_curves_time_df = pd.DataFrame([periods_curves_time[idx_maxest_time_stamp]])'''

    # use time array with the longest length
    len_of_each_time_period = []
    for n in range(nums_periods):
        len_of_each_time_period.append(len(periods_curves_time[n]))

    idx_biggest_len_time = len_of_each_time_period.index(max(len_of_each_time_period))
    periods_curves_time_df = pd.DataFrame([periods_curves_time[idx_biggest_len_time]]) #periods_curves_time_new

    ### avrg curve
    avrg_curve_df = pd.DataFrame([periods_curves_new_avrg])
    avrg_curve_time_df = pd.DataFrame([periods_curves_time_new_avrg])

    curves_df = pd.concat([
        avrg_curve_time_df, 
        avrg_curve_df,
        periods_curves_time_df,
        periods_curves_df
        ], axis=0)
    curves_dfT = curves_df.T
    #print(curves_dfT)

    periods_curves_time_df_name = ['time (periods)']
    #periods_curves_df_names = [f'intensity (period {p+1})' for p in range(nums_periods)]
    periods_curves_df_names = [f'intensity (period {p+1})' for p in nums_periods_original_order]

    avrg_curve_time_df_name = ['time (averaged_period)']
    avrg_curve_df_name = ['intensity (averaged_period)']

    columns_names = avrg_curve_time_df_name + avrg_curve_df_name + periods_curves_time_df_name + periods_curves_df_names
    curves_dfT.columns = columns_names
    curves_dfT.index.drop

    return curves_dfT

def outputAnglesTans(
        period_curves_angles,
        period_curves_tans,
        avrg_curve_angle,
        avrg_curve_tan,
        nums_periods,
        nums_periods_original_order) -> None:
    """
    outputs angles and tans data
    """
    # angles and tans
    period_curves_angles_tans_df = pd.DataFrame(
        [[angle, tan] for angle, tan in zip(period_curves_angles, period_curves_tans)]
    )
    avrg_curve_angle_tan_df = pd.DataFrame([[avrg_curve_angle, avrg_curve_tan]])

    angles_tans_df = pd.concat([
        avrg_curve_angle_tan_df,
        period_curves_angles_tans_df    
    ], axis=0)
    angles_tans_dfT = angles_tans_df.T
    #print(angles_tans_dfT)
    #periods_curves_df_names = [f'period {p+1}' for p in range(nums_periods)]
    periods_curves_df_names = [f'period {p+1}' for p in nums_periods_original_order]
    angles_tans_dfT.columns = ['averaged_period'] + periods_curves_df_names
    angles_tans_dfT.index = ['angle, deg', 'tangent']

    return angles_tans_dfT

def outputDurations(
        avrg_curve_apds,
        period_curves_apds90, 
        period_curves_apds50, 
        period_curves_apds20,
        nums_periods,
        nums_periods_original_order):
    """
    outputs durations of avrg curves and period curves
    """
    period_curves_apds_df = pd.DataFrame(
        [[apd90, apd50, apd20] for apd90, apd50, apd20 in zip(period_curves_apds90, period_curves_apds50,period_curves_apds20)]
    )
    avrg_curve_apds_df = pd.DataFrame([[avrg_curve_apds[0], avrg_curve_apds[1], avrg_curve_apds[2]]])

    durations_df = pd.concat([
        period_curves_apds_df,
        avrg_curve_apds_df
    ], axis=0)
    durations_dfT = durations_df.T
    #periods_curves_df_names = [f'period {p+1}' for p in range(nums_periods)]
    periods_curves_df_names = [f'period {p+1}' for p in nums_periods_original_order]
    durations_dfT.columns = ['averaged_period'] + periods_curves_df_names
    durations_dfT.index = ['Duration, 90%', 'Duration, 50%', 'Duration, 20%']

    return durations_dfT

def outputExcel(output_path, curves_dfT, angles_tans_dfT, durations_dfT, verbose: int = 0) -> None:
    """
    outputs all data to xlsx
    """
    #output_path = 'output_data.xlsx'
    if verbose in [1,2]: print(f'Data is saved to: {output_path}\n')
    with pd.ExcelWriter(output_path) as writer: 
        curves_dfT.to_excel(writer, sheet_name='output_processed_signal', index=False)  
        angles_tans_dfT.to_excel(writer, sheet_name='output_angles')
        durations_dfT.to_excel(writer, sheet_name='output_durations')
        #
    ###    