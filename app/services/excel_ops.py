import pandas as pd
from typing import Dict, Any


def read_excel_sheets(path: str) -> Dict[str, pd.DataFrame]:
    """
    Read all sheets from an Excel file into a dictionary.
    - Keys: sheet names
    - Values: corresponding pandas DataFrames
    """
    try:
        sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
        return sheets
    except FileNotFoundError:
        raise FileNotFoundError(f"Excel file not found: {path}")
    except Exception as e:
        raise Exception(f"Failed to read Excel file: {e}")


def write_sheets_to_file(sheets: Dict[str, pd.DataFrame], path: str):
    """
    Write multiple DataFrames to an Excel file as separate sheets.
    """
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=str(name)[:31], index=False)
    except Exception as e:
        raise Exception(f"Failed to write Excel file: {e}")


def execute_operation_on_sheet(df: pd.DataFrame, op: Dict[str, Any]) -> pd.DataFrame:
    """
    Execute a structured operation on a given DataFrame.
    Supported operations:
      - math (+, -, *, /)
      - aggregation (groupby, summary)
      - filter
      - pivot / unpivot
      - date_extract
      - sql_like (query expressions)
    """
    t = op.get("type")

    # --- Math Operations ---
    if t == "math":
        a, b = op["columns"][:2]
        new_col = op["new_column"]
        operator = op["op"]

        if operator == "+":
            df[new_col] = df[a] + df[b]
        elif operator == "-":
            df[new_col] = df[a] - df[b]
        elif operator == "*":
            df[new_col] = df[a] * df[b]
        elif operator == "/":
            df[new_col] = df[a] / df[b]
        else:
            raise ValueError(f"Unsupported math operator: {operator}")
        return df

    # --- Aggregation ---
    if t == "aggregation":
        method = op.get("method")
        if method == "groupby_agg":
            gb = df.groupby(op["groupby"]).agg(op["agg"]).reset_index()
            return gb
        elif method == "summary":
            res = {c: getattr(df[c], op["agg"])() for c in op["columns"]}
            return pd.DataFrame([res])
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")

    # --- Filter ---
    if t == "filter":
        try:
            return df.query(op["expr"])
        except Exception as e:
            raise ValueError(f"Invalid filter expression: {e}")

    # --- Pivot ---
    if t == "pivot":
        pv = pd.pivot_table(
            df,
            index=op["index"],
            columns=op["columns"],
            values=op["values"],
            aggfunc=op.get("aggfunc", "sum"),
        ).reset_index()

        # Clean multi-index column names if needed
        if hasattr(pv.columns, "names"):
            pv.columns = [
                "_".join([str(x) for x in col if x is not None]).strip()
                for col in pv.columns.values
            ]
        return pv

    # --- Unpivot (Melt) ---
    if t == "unpivot":
        melted = df.melt(
            id_vars=op["id_vars"],
            value_vars=op["value_vars"],
            var_name=op.get("var_name", "variable"),
            value_name=op.get("value_name", "value"),
        )
        return melted

    # --- Date Extraction ---
    if t == "date_extract":
        col = op["column"]
        part = op["part"]
        new_col = op["new_column"]

        s = pd.to_datetime(df[col], errors="coerce")

        if part == "month":
            df[new_col] = s.dt.month
        elif part == "year":
            df[new_col] = s.dt.year
        elif part == "day":
            df[new_col] = s.dt.day
        else:
            raise ValueError(f"Unsupported date part: {part}")

        return df

    # --- SQL-like Filtering ---
    if t == "sql_like":
        try:
            return df.query(op["expr"])
        except Exception as e:
            raise ValueError(f"SQL-like query failed: {e}")

    raise ValueError(f"Unsupported operation type: {t}")
