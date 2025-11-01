# app/services/excel_agent.py
import pandas as pd
import os

def run_excel_agent(file_path: str, sheet_name: str, parsed: dict):
    """
    Executes operations on Excel based on parsed instruction.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        return {"error": f"Failed to read Excel: {e}"}

    op_type = parsed.get("type")

    try:
        if op_type == "math":
            a, b = parsed["columns"]
            new = parsed["new_column"]
            df[new] = df[a] + df[b]
        elif op_type == "aggregation":
            df = df.groupby(parsed["groupby"]).agg(parsed["agg"]).reset_index()
        elif op_type == "filter":
            df = df.query(parsed["expr"])
        elif op_type == "pivot":
            df = pd.pivot_table(df, index=parsed["index"], columns=parsed["columns"],
                                values=parsed["values"], aggfunc=parsed["aggfunc"]).reset_index()
        elif op_type == "date_extract":
            col = parsed["column"]
            df[parsed["new_column"]] = getattr(pd.to_datetime(df[col]), parsed["part"])
        else:
            return {"error": f"Unsupported operation: {op_type}"}

        return df.head(10).to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
