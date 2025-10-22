# src/output_data.py — Data output utilities

import pandas as pd
from typing import List

def outputCurves(
    periods_curves_time: List,
    periods_curves: List,
    periods_curves_time_new_avrg: List,
    periods_curves_new_avrg: List,
    nums_periods: int,
    nums_periods_original_order: List[int]
) -> pd.DataFrame:
    """Prepare DataFrame with individual and averaged period curves."""
    periods_curves_df = pd.DataFrame(periods_curves)
    periods_curves_time_df = pd.DataFrame([periods_curves_time[max(range(len(periods_curves_time)), key=lambda i: len(periods_curves_time[i]))]])

    avrg_curve_df = pd.DataFrame([periods_curves_new_avrg])
    avrg_curve_time_df = pd.DataFrame([periods_curves_time_new_avrg])

    curves_df = pd.concat([
        avrg_curve_time_df, 
        avrg_curve_df,
        periods_curves_time_df,
        periods_curves_df
    ], axis=0).T

    columns_names = (
        ['time (averaged_period)', 'intensity (averaged_period)', 'time (periods)'] +
        [f'intensity (period {p+1})' for p in nums_periods_original_order]
    )
    curves_df.columns = columns_names
    return curves_df

def outputAnglesTans(
    period_curves_angles: List[float],
    period_curves_tans: List[float],
    avrg_curve_angle: float,
    avrg_curve_tan: float,
    nums_periods: int,
    nums_periods_original_order: List[int]
) -> pd.DataFrame:
    """Prepare DataFrame with angle and tangent data."""
    angles_tans_df = pd.concat([
        pd.DataFrame([[avrg_curve_angle, avrg_curve_tan]]),
        pd.DataFrame(list(zip(period_curves_angles, period_curves_tans)))
    ], axis=0).T
    angles_tans_df.columns = ['averaged_period'] + [f'period {p+1}' for p in nums_periods_original_order]
    angles_tans_df.index = ['angle, deg', 'tangent']
    return angles_tans_df

def outputDurations(
    avrg_curve_apds: List[float],
    period_curves_apds90: List[float],
    period_curves_apds50: List[float],
    period_curves_apds20: List[float],
    nums_periods: int,
    nums_periods_original_order: List[int]
) -> pd.DataFrame:
    """Prepare DataFrame with APD durations (D90/D50/D20)."""
    durations_df = pd.concat([
        pd.DataFrame(list(zip(period_curves_apds90, period_curves_apds50, period_curves_apds20))),
        pd.DataFrame([avrg_curve_apds])
    ], axis=0).T
    durations_df.columns = ['averaged_period'] + [f'period {p+1}' for p in nums_periods_original_order]
    durations_df.index = ['Duration, 90%', 'Duration, 50%', 'Duration, 20%']
    return durations_df

def outputExcel(
    output_path: str,
    curves_dfT: pd.DataFrame,
    angles_tans_dfT: pd.DataFrame,
    durations_dfT: pd.DataFrame,
    verbose: int = 0
) -> None:
    """Save processed results to an Excel file."""
    if verbose in [1, 2]:
        print(f'Data is saved to: {output_path}\n')
    with pd.ExcelWriter(output_path) as writer:
        curves_dfT.to_excel(writer, sheet_name='output_processed_signal', index=False)
        angles_tans_dfT.to_excel(writer, sheet_name='output_angles')
        durations_dfT.to_excel(writer, sheet_name='output_durations')
