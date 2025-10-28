# click handlers -> calls detect/segment utilities

# src/ui_streamlit/events.py
from __future__ import annotations
import numpy as np
from typing import Tuple
from src.detect import snap_to_local_extremum, insert_peak, remove_peak, enforce_alternation
from src.segment import build_period_indices

def nearest_max_by_time(t, peaks_max, x_clicked) -> int:
    j = int(peaks_max[np.argmin(np.abs(t[peaks_max] - x_clicked))])
    return j

def handle_click_insert_remove_min(state, x_clicked: float):
    # use filtered working signal if available, else raw
    t = state.get("t_work") if state.get("t_work") is not None else state["t_raw"]
    y = state.get("y_work") if state.get("y_work") is not None else state["y_raw"]
    
    j, kind = snap_to_local_extremum(t, y, x_clicked)
    if kind != "min":
        return False, "Clicked near a MAX. Switch mode to 'Remove by MAX'."
    pm = set(state["peaks_min"].tolist())
    if j in pm:
        state["peaks_min"] = remove_peak(state["peaks_min"], j)
    else:
        state["peaks_min"] = insert_peak(state["peaks_min"], j)
    state["peaks_min"], state["peaks_max"] = enforce_alternation(state["peaks_min"], state["peaks_max"])
    return True, "MIN toggled."

def handle_click_toggle_remove_by_max(state, x_clicked: float):
    t_raw, peaks_max = state["t_raw"], state["peaks_max"]
    if peaks_max.size == 0:
        return False, "No detected maxima."
    j = nearest_max_by_time(t_raw, peaks_max, x_clicked)
    if j in state["removed_max_idxs"]:
        state["removed_max_idxs"].remove(j)
        return True, f"Restored period at max index {j}."
    else:
        state["removed_max_idxs"].add(j)
        return True, f"Removed period at max index {j}."
