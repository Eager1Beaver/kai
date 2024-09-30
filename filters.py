import numpy as np
from scipy.signal import (
    butter, # low pass filter
    sosfiltfilt, # low pass filter
    savgol_filter # savgol_filter
    #find_peaks
    )

# gaussian_filter1d
from scipy.ndimage import gaussian_filter1d

###
def use_savgol_filter(y: np.ndarray, window_length: int = 65, polyorder:int = 5, mode = 'interp'):
    """
    y: signal data
    """
    filter_name = 'savgol_filter'
    y_savgol_filter = savgol_filter(y, window_length=window_length, polyorder=polyorder, mode=mode)
    return y_savgol_filter, filter_name

def use_gaussian_filter1d(y: np.ndarray, sigma: int = 12, truncate: int = 1):
    """
    y: signal data
    """
    filter_name = 'gaussian_filter1d'
    y_gaussian_filter1d = gaussian_filter1d(y, sigma=sigma, truncate=truncate)
    return y_gaussian_filter1d, filter_name

def use_lowpass_filter(y: np.ndarray, cutoff: float = 120, sample_rate: float = 5000, poles: int = 2, btype: str = 'lowpass'):
    """
    y: signal data
    """
    filter_name = 'lowpass_filter'
    sos = butter(N=poles, Wn=cutoff, fs=sample_rate, output='sos', btype=btype)
    y_lowpass_filter = sosfiltfilt(sos, y)
    return y_lowpass_filter, filter_name

def use_combined_filter_old(*args):
    """
    Provide full name of a desired filter with specified parameters.\n
    Example: combined_filter( savgol_filter(y, 50, 3), gaussian_filter1d(y, 3, 7) )
    """
    filters = []
    for arg in args: filters.append(arg)
    filter_name = 'combined_filter'
    y_combined_filter = np.average(filters, axis=0)
    return y_combined_filter, filter_name

def use_combined_filter(filters):
    """
    Provide a list containing Y values obtained from other desired filters
    """
    filter_name = 'combined_filter'
    y_combined_filter = np.average(filters, axis=0)
    return y_combined_filter, filter_name
