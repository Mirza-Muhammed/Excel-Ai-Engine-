# app/services/join_engine.py
import pandas as pd

def perform_join(left: pd.DataFrame, right: pd.DataFrame, on: list, how: str = "inner", lsuffix: str = "_l", rsuffix: str = "_r") -> pd.DataFrame:
    how = how.lower()
    if how not in {"inner", "left", "right", "outer"}:
        raise ValueError("Unsupported join type")
    return left.merge(right, how=how, on=on, suffixes=(lsuffix, rsuffix))
