#import os
import pandas as pd

def inputExcel(input_path, verbose: int = 0):
    """
    input baseline data\n
    verbose: how much info to print
    """
    #file_name = 'data_7t'
    #cwd = os.getcwd()
    #input_path = cwd + '/' + file_name + '.csv'
    #data_df = pd.read_csv(input_path) # USER_DEFINED
    try:
        data_df = pd.read_excel(input_path, sheet_name='data')
    except:
        data_df = pd.read_csv(input_path)
    if verbose in [2]: print(f'Data loaded from: {input_path}\n')
    if verbose in [2]: print(f'Loaded data:\n{data_df.head(5)}\n')
    return data_df
    ###

def inputAmbientDataExcel(input_ambient_data_path, verbose: int = 0):
    """
    input ambient data\n
    verbose: how much info to print
    """
    #file_name = 'data_7t'
    #cwd = os.getcwd()
    #input_path = cwd + '/' + file_name + '.csv'
    #data_df = pd.read_csv(input_path) # USER_DEFINED
    try:
        ambient_data_df = pd.read_excel(input_ambient_data_path, sheet_name='data')
    except:
        ambient_data_df = pd.read_csv(input_ambient_data_path)
    if verbose in [2]: print(f'Data loaded from: {input_ambient_data_path}\n')
    if verbose in [2]: print(f'Loaded data:\n{ambient_data_df.head(5)}\n')
    return ambient_data_df
    ###    