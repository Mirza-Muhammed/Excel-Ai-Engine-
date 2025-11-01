# app/routes/query.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Any, Dict
from app.services.data_engine import read_sheet, write_sheet, summarize_df
from app.services.math_operations import apply_math, aggregate
from app.services.join_engine import perform_join
from app.services.pivot_engine import create_pivot, unpivot
from app.services.date_engine import extract_date_parts, date_diff
from app.services.unstructured_text import analyze_text_column
from app.llm_agent.orchestrator import ExcelAIOrchestrator
import os, json

router = APIRouter()
orchestrator = ExcelAIOrchestrator(fast_mode=True)  # fast_mode avoids LLM for simple queries

class QueryPayload(BaseModel):
    file_path: str
    sheet_name: Optional[str] = None
    operation: str
    params: Optional[Dict[str, Any]] = {}

class NaturalQuery(BaseModel):
    file_path: str
    sheet_name: Optional[str] = None
    query: str

def ensure_exists(file_path: str):
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return file_path

@router.post("/run")
async def run_query(request: Request):
    data = await request.json()
    # Natural-language path
    if "query" in data:
        nat = NaturalQuery(**data)
        file_path = ensure_exists(nat.file_path)
        df = read_sheet(file_path, nat.sheet_name)
        parsed = orchestrator.interpret_query(nat.query, columns=list(df.columns))
        # normalize parsed -> QueryPayload-like
        op = parsed.get("operation") or "unknown"
        params = parsed.get("parameters") or parsed.get("params") or {}
        payload = QueryPayload(file_path=file_path, sheet_name=nat.sheet_name, operation=op, params=params)
        return handle_structured(payload)
    # Structured path
    payload = QueryPayload(**data)
    payload.file_path = ensure_exists(payload.file_path)
    return handle_structured(payload)

def handle_structured(payload: QueryPayload):
    df = read_sheet(payload.file_path, payload.sheet_name)
    op = payload.operation.lower()
    try:
        if op == "aggregate":
            column = payload.params.get("column")
            agg = payload.params.get("agg")
            group_by = payload.params.get("group_by")
            if not column or not agg:
                raise HTTPException(status_code=400, detail="aggregate requires 'column' and 'agg'")
            result = aggregate(df, column, agg, group_by)
            return {"operation":"aggregate","column":column,"agg":agg,"result":result}

        if op == "math":
            operation = payload.params.get("math_op") or payload.params.get("operation")
            target_cols = payload.params.get("target_cols", [])
            new_col = payload.params.get("new_col")
            operand = payload.params.get("operand")
            res_df = apply_math(df, operation, target_cols, new_col=new_col, operand=operand)
            out = write_sheet(res_df, payload.file_path)
            return {"operation":"math","math_op":operation,"output_file":out,"summary":summarize_df(res_df)}

        if op == "join":
            other_file = payload.params.get("other_file")
            other_sheet = payload.params.get("other_sheet")
            on = payload.params.get("on")
            how = payload.params.get("how","inner")
            if not other_file or not on:
                raise HTTPException(status_code=400, detail="join requires other_file and on columns list")
            right = read_sheet(other_file, other_sheet)
            result_df = perform_join(df, right, on=on, how=how)
            out = write_sheet(result_df, payload.file_path)
            return {"operation":"join","how":how,"output_file":out,"summary":summarize_df(result_df)}

        if op == "pivot":
            index = payload.params.get("index")
            columns = payload.params.get("columns")
            values = payload.params.get("values")
            aggfunc = payload.params.get("aggfunc","sum")
            if not index or not columns or not values:
                raise HTTPException(status_code=400, detail="pivot requires index, columns, and values")
            pivot_df = create_pivot(df, index=index, columns=columns, values=values, aggfunc=aggfunc)
            out = write_sheet(pivot_df, payload.file_path)
            return {"operation":"pivot","output_file":out,"summary":summarize_df(pivot_df)}

        if op == "unpivot":
            id_vars = payload.params.get("id_vars")
            value_vars = payload.params.get("value_vars")
            if not id_vars or not value_vars:
                raise HTTPException(status_code=400, detail="unpivot requires id_vars and value_vars")
            unp = unpivot(df, id_vars=id_vars, value_vars=value_vars)
            out = write_sheet(unp, payload.file_path)
            return {"operation":"unpivot","output_file":out,"summary":summarize_df(unp)}

        if op == "date_extract":
            col = payload.params.get("column")
            parts = payload.params.get("parts", ["year","month","day"])
            if not col:
                raise HTTPException(status_code=400, detail="date_extract requires column")
            res_df = extract_date_parts(df, col, parts)
            out = write_sheet(res_df, payload.file_path)
            return {"operation":"date_extract","output_file":out,"summary":summarize_df(res_df)}

        if op == "date_diff":
            start = payload.params.get("start_col")
            end = payload.params.get("end_col")
            new_col = payload.params.get("new_col","date_diff_days")
            if not start or not end:
                raise HTTPException(status_code=400, detail="date_diff requires start_col and end_col")
            res_df = date_diff(df, start, end, new_col)
            out = write_sheet(res_df, payload.file_path)
            return {"operation":"date_diff","output_file":out,"summary":summarize_df(res_df)}

        if op == "filter":
            condition = payload.params.get("condition")
            if not condition:
                raise HTTPException(status_code=400, detail="filter requires condition")
            res_df = df.query(condition)
            out = write_sheet(res_df, payload.file_path)
            return {"operation":"filter","rows":int(res_df.shape[0]),"output_file":out,"summary":summarize_df(res_df)}

        if op == "text_analyze":
            text_col = payload.params.get("text_col")
            if not text_col:
                raise HTTPException(status_code=400, detail="text_analyze requires text_col")
            add_summary = payload.params.get("add_summary", True)
            add_sentiment = payload.params.get("add_sentiment", True)
            res_df = analyze_text_column(df, text_col, add_summary=add_summary, add_sentiment=add_sentiment)
            out = write_sheet(res_df, payload.file_path)
            return {"operation":"text_analyze","output_file":out,"summary":summarize_df(res_df)}

        raise HTTPException(status_code=400, detail=f"Unsupported operation: {op}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
