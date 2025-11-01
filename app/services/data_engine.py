# app/services/data_engine.py
import os
import pandas as pd
from typing import Dict, Any

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_excel_path(file_path: str) -> str:
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    return file_path

def read_sheet(file_path: str, sheet_name: str = None) -> pd.DataFrame:
    path = get_excel_path(file_path)
    xls = pd.ExcelFile(path)
    if sheet_name is None:
        sheet_name = xls.sheet_names[0]
    if sheet_name not in xls.sheet_names:
        raise ValueError(f"Sheet {sheet_name} not found in {file_path}. Available: {xls.sheet_names}")
    df = pd.read_excel(path, sheet_name=sheet_name)
    return df

def write_sheet(df: pd.DataFrame, file_path: str, sheet_name: str = "Result", overwrite: bool = False) -> str:
    path = get_excel_path(file_path)
    out_path = os.path.splitext(path)[0] + f"_out.xlsx"
    if overwrite:
        out_path = path
    with pd.ExcelWriter(out_path, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return out_path

def summarize_df(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "rows": int(df.shape[0]),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict()
    }
