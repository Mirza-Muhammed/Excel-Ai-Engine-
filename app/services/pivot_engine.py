# app/services/pivot_engine.py
import pandas as pd

def create_pivot(df: pd.DataFrame, index: list, columns: list, values: str, aggfunc='sum') -> pd.DataFrame:
    pivot = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc, fill_value=0)
    pivot_df = pivot.reset_index()
    # flatten columns
    pivot_df.columns = [("_".join(c) if isinstance(c, tuple) else c) for c in pivot_df.columns]
    return pivot_df

def unpivot(df: pd.DataFrame, id_vars: list, value_vars: list, var_name='variable', value_name='value') -> pd.DataFrame:
    return pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name)
