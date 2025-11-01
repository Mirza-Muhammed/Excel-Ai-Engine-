# app/services/date_engine.py
import pandas as pd

def ensure_datetime(df, col):
    return pd.to_datetime(df[col], errors='coerce')

def extract_date_parts(df, col: str, parts: list):
    s = ensure_datetime(df, col)
    res = df.copy()
    if 'year' in parts:
        res[f"{col}_year"] = s.dt.year
    if 'month' in parts:
        res[f"{col}_month"] = s.dt.month
    if 'day' in parts:
        res[f"{col}_day"] = s.dt.day
    if 'weekday' in parts:
        res[f"{col}_weekday"] = s.dt.weekday
    return res

def date_diff(df, start_col: str, end_col: str, new_col: str = "date_diff_days"):
    s = ensure_datetime(df, start_col)
    e = ensure_datetime(df, end_col)
    res = df.copy()
    res[new_col] = (e - s).dt.days
    return res
