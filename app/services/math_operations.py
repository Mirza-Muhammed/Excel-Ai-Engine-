# app/services/math_operations.py
import pandas as pd
from typing import Dict, Any

def apply_math(df: pd.DataFrame, operation: str, target_cols: list, new_col: str = None, operand=None) -> pd.DataFrame:
    op = operation.lower()
    result_df = df.copy()
    if op in {"add", "sub", "mul", "div"}:
        if operand is not None and len(target_cols) == 1:
            a = target_cols[0]
            new_col = new_col or f"{a}_{op}_{operand}"
            if op == "add":
                result_df[new_col] = result_df[a] + operand
            elif op == "sub":
                result_df[new_col] = result_df[a] - operand
            elif op == "mul":
                result_df[new_col] = result_df[a] * operand
            elif op == "div":
                result_df[new_col] = result_df[a] / operand if operand != 0 else None
        elif len(target_cols) == 2:
            a, b = target_cols
            new_col = new_col or f"{a}_{op}_{b}"
            if op == "add":
                result_df[new_col] = result_df[a] + result_df[b]
            elif op == "sub":
                result_df[new_col] = result_df[a] - result_df[b]
            elif op == "mul":
                result_df[new_col] = result_df[a] * result_df[b]
            elif op == "div":
                result_df[new_col] = result_df[a] / result_df[b].replace({0: pd.NA})
        else:
            raise ValueError("Invalid math parameters")
    else:
        raise ValueError("Unsupported math operation")
    return result_df

def aggregate(df: pd.DataFrame, column: str, agg: str, group_by: list = None):
    agg = agg.lower()
    if group_by:
        grouped = df.groupby(group_by)[column]
        if agg in {"sum"}:
            return grouped.sum().to_dict()
        if agg in {"avg", "mean"}:
            return grouped.mean().to_dict()
        if agg == "min":
            return grouped.min().to_dict()
        if agg == "max":
            return grouped.max().to_dict()
        if agg == "count":
            return grouped.count().to_dict()
        raise ValueError("Unsupported aggregation")
    else:
        mapping = {"sum":"sum","avg":"mean","mean":"mean","min":"min","max":"max","count":"count"}
        func = mapping.get(agg)
        if not func:
            raise ValueError("Unsupported aggregation")
        return getattr(df[column], func)()
