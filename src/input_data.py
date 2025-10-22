# src/input_data.py — Input data loading utilities

import pandas as pd
from typing import Union

def inputExcel(input_path: str, verbose: int = 0) -> pd.DataFrame:
    """
    Loads baseline data from an Excel or CSV file.

    Args:
        input_path (str): Path to input Excel or CSV file.
        verbose (int): Level of verbosity.

    Returns:
        pd.DataFrame: Dataframe containing 't' and 'i' columns.
    """
    try:
        data_df = pd.read_excel(input_path, sheet_name='data')
    except Exception:
        data_df = pd.read_csv(input_path)

    if verbose >= 2:
        print(f"Data loaded from: {input_path}\n")
        print(f"Loaded data:\n{data_df.head()}\n")

    return data_df

def inputAmbientDataExcel(input_ambient_data_path: str, verbose: int = 0) -> pd.DataFrame:
    """
    Loads ambient baseline data from an Excel or CSV file.

    Args:
        input_ambient_data_path (str): Path to ambient data file.
        verbose (int): Level of verbosity.

    Returns:
        pd.DataFrame: Dataframe containing 't' and 'i' columns.
    """
    try:
        ambient_data_df = pd.read_excel(input_ambient_data_path, sheet_name='data')
    except Exception:
        ambient_data_df = pd.read_csv(input_ambient_data_path)

    if verbose >= 2:
        print(f"Data loaded from: {input_ambient_data_path}\n")
        print(f"Loaded data:\n{ambient_data_df.head()}\n")

    return ambient_data_df
