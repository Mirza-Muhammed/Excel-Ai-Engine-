# app/services/orchestrator.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import os

class ExcelExecutor:
    """
    Execute a JSON command against an Excel file (sheet).
    Command schema (examples):
      {
        "operation": "aggregate",
        "file_path": "data/sample.xlsx",
        "sheet_name": "Structured",
        "params": {
          "group_by": ["region"],
          "aggregations": {"sales": "sum", "score": "mean"},
          "filter": "status == 'open'"
        }
      }
    """

    @staticmethod
    def _load_df(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"file not found: {file_path}")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df

    @staticmethod
    def run_command(cmd: Dict[str, Any]) -> Dict[str, Any]:
        op = cmd.get("operation")
        file_path = cmd.get("file_path") or cmd.get("path")
        sheet = cmd.get("sheet_name")
        params = cmd.get("params", {})

        if not file_path:
            raise ValueError("file_path is required in command")

        df = ExcelExecutor._load_df(file_path, sheet)

        # Optional filter applied first
        filter_expr = params.get("filter")
        if filter_expr:
            try:
                df = df.query(filter_expr)
            except Exception as e:
                # return parse error
                return {"error": "filter error", "detail": str(e)}

        try:
            if op in ("aggregate", "aggregation", "agg", "group"):
                return ExcelExecutor._exec_aggregate(df, params)
            if op in ("math", "compute", "derive"):
                return ExcelExecutor._exec_math(df, params)
            if op in ("filter", "select"):
                return ExcelExecutor._exec_filter(df, params)
            if op == "join":
                return ExcelExecutor._exec_join(cmd, params)
            if op == "pivot":
                return ExcelExecutor._exec_pivot(df, params)
            if op in ("unpivot", "melt"):
                return ExcelExecutor._exec_unpivot(df, params)
            if op == "date":
                return ExcelExecutor._exec_date_ops(df, params)
            if op in ("nl_text", "text", "text_op"):
                # return DataFrame with additional columns (handled elsewhere)
                return {"error":"nl_text operations handled by llm_agent (not by executor)"}
            if op in ("head","preview","sample"):
                return {"result": df.head(200).to_dict(orient="records")}
            # default: return a head
            return {"result": df.head(200).to_dict(orient="records")}
        except Exception as e:
            return {"error": "execution_error", "detail": str(e)}

    @staticmethod
    def _exec_aggregate(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        group_by: List[str] = params.get("group_by", [])
        aggregations: Dict[str,str] = params.get("aggregations", {})  # {col: aggname}
        # normalize aggregator names
        agg_map = {}
        for c, a in aggregations.items():
            an = a.lower()
            if an in ("avg", "mean", "average"): agg_map[c] = "mean"
            elif an in ("sum",): agg_map[c] = "sum"
            elif an in ("min",): agg_map[c] = "min"
            elif an in ("max",): agg_map[c] = "max"
            elif an in ("count",): agg_map[c] = "count"
            else:
                agg_map[c] = an
        if group_by:
            res = df.groupby(group_by).agg(agg_map).reset_index()
        else:
            # overall aggregate
            res = df.agg(agg_map).to_frame().T.reset_index(drop=True)
        limit = params.get("limit")
        if limit:
            res = res.head(int(limit))
        return {"result": res.to_dict(orient="records")}

    @staticmethod
    def _exec_math(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        new_column = params.get("new_column")
        formula = params.get("formula")  # expected to be a Python expression using column names, e.g. "sales - cost"
        if not new_column or not formula:
            raise ValueError("math requires new_column and formula")
        # create safe eval environment
        local = {col: df[col] for col in df.columns}
        local["np"] = np
        # disallow builtins
        safe_globals = {"__builtins__": {}}
        try:
            df[new_column] = eval(formula, safe_globals, local)
        except Exception as e:
            raise RuntimeError(f"failed to eval formula: {e}")
        # optionally persist back to file if requested
        persist = params.get("persist", False)
        if persist and params.get("file_path"):
            df.to_excel(params["file_path"], index=False, sheet_name=params.get("sheet_name", "Sheet1"))
        return {"result": df.head(200).to_dict(orient="records")}

    @staticmethod
    def _exec_filter(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        limit = params.get("limit", 200)
        return {"result": df.head(limit).to_dict(orient="records")}

    @staticmethod
    def _exec_join(cmd: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        # join needs a separate right file or right sheet
        left_df = ExcelExecutor._load_df(cmd["file_path"], cmd.get("sheet_name"))
        right_path = params.get("right_file_path")
        right_sheet = params.get("right_sheet")
        how = params.get("how", "inner")
        on = params.get("on")  # list or single column
        if not right_path:
            raise ValueError("join requires right_file_path in params")
        right_df = ExcelExecutor._load_df(right_path, right_sheet)
        if isinstance(on, str):
            on = [on]
        if not on:
            on = list(set(left_df.columns).intersection(set(right_df.columns)))
            if not on:
                raise ValueError("no join keys found; please supply 'on' param")
        res = left_df.merge(right_df, how=how, on=on)
        return {"result": res.head(200).to_dict(orient="records")}

    @staticmethod
    def _exec_pivot(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        index = params.get("index", [])
        columns = params.get("columns")
        values = params.get("values")
        aggfunc = params.get("aggfunc", "sum")
        if not values:
            raise ValueError("pivot requires 'values' param")
        table = pd.pivot_table(df, index=index or None, columns=columns or None, values=values, aggfunc=aggfunc, fill_value=0)
        # flatten columns
        if isinstance(table, pd.DataFrame):
            table = table.reset_index()
        else:
            table = pd.DataFrame(table).reset_index()
        return {"result": table.head(200).to_dict(orient="records")}

    @staticmethod
    def _exec_unpivot(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        id_vars = params.get("id_vars", [])
        value_vars = params.get("value_vars", [])
        var_name = params.get("var_name", "variable")
        value_name = params.get("value_name", "value")
        if not value_vars:
            value_vars = [c for c in df.columns if c not in id_vars]
        res = pd.melt(df, id_vars=id_vars or [], value_vars=value_vars, var_name=var_name, value_name=value_name)
        return {"result": res.head(200).to_dict(orient="records")}

    @staticmethod
    def _exec_date_ops(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        op = params.get("op", "extract")
        cols = params.get("columns", [])
        if op == "extract":
            out = df.copy()
            for c in cols:
                out[c + "_year"] = pd.to_datetime(out[c], errors="coerce").dt.year
                out[c + "_month"] = pd.to_datetime(out[c], errors="coerce").dt.month
                out[c + "_day"] = pd.to_datetime(out[c], errors="coerce").dt.day
            return {"result": out.head(200).to_dict(orient="records")}
        if op == "datediff":
            a = params.get("col_a")
            b = params.get("col_b")
            unit = params.get("unit", "days")
            ad = pd.to_datetime(df[a], errors="coerce")
            bd = pd.to_datetime(df[b], errors="coerce")
            diff = (ad - bd)
            if unit == "days":
                df["date_diff_days"] = diff.dt.days
            else:
                df["date_diff_seconds"] = diff.dt.total_seconds()
            return {"result": df.head(200).to_dict(orient="records")}
        raise ValueError("unsupported date operation")
