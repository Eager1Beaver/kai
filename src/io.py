from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional
import numpy as np
import pandas as pd

_TIME_CANDIDATES = ["t", "time", "times", "ms", "sec", "s", "x"]
_VAL_CANDIDATES = ["i", "y", "value", "values", "signal", "amp", "intensity"]

def _pick_column(cols: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    cols_norm = [c.strip().lower() for c in cols]
    for cand in candidates:
        if cand in cols_norm:
            return list(cols)[cols_norm.index(cand)]
    return None

def _as_float_1d(a: Iterable) -> np.ndarray:
    arr = np.asarray(a, dtype=float).reshape(-1)
    return arr.astype(np.float64, copy=False)

def _ensure_str(pathlike) -> str:
    return str(pathlike)

@dataclass
class LoadInfo:
    path: str
    sheet: Optional[str]
    time_col: str
    value_col: str
    n_rows: int

def load_signal(path: str, *, sheet: Optional[str] = None,
                time_col: Optional[str] = None,
                value_col: Optional[str] = None,
                dropna: bool = True):
    fpath = _ensure_str(path)
    lower = fpath.lower()
    if lower.endswith(".csv"):
        df = pd.read_csv(fpath)
    elif lower.endswith((".xlsx", ".xls")):
        df = pd.read_excel(fpath, sheet_name=sheet)
    else:
        raise ValueError("Unsupported file type. Use .csv or .xlsx/.xls")

    if df.empty:
        raise ValueError("The file appears to be empty.")

    tcol = time_col or _pick_column(df.columns, _TIME_CANDIDATES)
    ycol = value_col or _pick_column(df.columns, _VAL_CANDIDATES)

    if tcol is None or ycol is None:
        numeric_df = df.select_dtypes(include=["number"])
        if numeric_df.shape[1] >= 2:
            if tcol is None:
                tcol = numeric_df.columns[0]
            if ycol is None:
                ycol = numeric_df.columns[1] if numeric_df.columns[0] == tcol else numeric_df.columns[0]
        else:
            raise ValueError("Could not auto-detect time/value columns. Please pass time_col= and value_col=.")

    if dropna:
        df = df[[tcol, ycol]].dropna()
    else:
        df = df[[tcol, ycol]]

    t = _as_float_1d(df[tcol].values)
    y = _as_float_1d(df[ycol].values)

    if not np.all(np.diff(t) > 0):
        order = np.argsort(t, kind="mergesort")
        t = t[order]
        y = y[order]

    info = LoadInfo(path=fpath, sheet=sheet, time_col=tcol, value_col=ycol, n_rows=len(t))
    return t, y, info

def resample_series(t_target: np.ndarray, t_src: np.ndarray, y_src: np.ndarray, *, offset_ms: float = 0.0) -> np.ndarray:
    t_target = _as_float_1d(t_target)
    t_src = _as_float_1d(t_src)
    y_src = _as_float_1d(y_src)
    if len(t_src) < 2:
        return np.full_like(t_target, y_src[0] if len(y_src) else np.nan, dtype=float)
    t_shift = t_src + (offset_ms / 1000.0)
    y_interp = np.interp(t_target, t_shift, y_src, left=y_src[0], right=y_src[-1])
    return y_interp

def subtract_ambient(t_raw: np.ndarray, y_raw: np.ndarray, t_amb: np.ndarray, y_amb: np.ndarray, *, offset_ms: float = 0.0, scale: float = 1.0):
    t_raw = _as_float_1d(t_raw)
    y_raw = _as_float_1d(y_raw)
    t_amb = _as_float_1d(t_amb)
    y_amb = _as_float_1d(y_amb)
    amb_interp = resample_series(t_raw, t_amb, y_amb, offset_ms=offset_ms)
    y_corr = y_raw - scale * amb_interp
    meta = {
        "offset_ms": float(offset_ms),
        "scale": float(scale),
        "ambient_mean": float(np.mean(amb_interp)),
        "ambient_std": float(np.std(amb_interp, ddof=1)) if len(amb_interp) > 1 else 0.0,
    }
    return y_corr, meta

# Testing (optional)
if __name__ == "__main__":
    import sys, json
    sys.path.append("data")

    summary = {}
    try:
        #from src.io import load_signal, subtract_ambient
        raw_csv = "/data/sample_raw_signal_data.csv"
        amb_csv = "/data/sample_ambient_signal_data.csv"
        t_raw, y_raw, info_raw = load_signal(raw_csv)
        t_amb, y_amb, info_amb = load_signal(amb_csv)
        y_corr, meta = subtract_ambient(t_raw, y_raw, t_amb, y_amb, offset_ms=0.0)
        summary["raw_info"] = info_raw.__dict__
        summary["amb_info"] = info_amb.__dict__
        summary["corr_preview"] = [float(y_corr[0]), float(y_corr[min(10, len(y_corr)-1)])]
        summary["meta"] = meta
    except Exception as e:
        summary["io_test_error"] = str(e)

    print(json.dumps(summary, indent=2))