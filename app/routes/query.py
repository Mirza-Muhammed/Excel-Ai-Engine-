from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import os

router = APIRouter()

class QueryRequest(BaseModel):
    file_path: str
    sheet_name: str = "Structured"
    query: str
    output_path: str = ""  # Optional, if you want to save results

@router.post("/run")
async def run_query(req: QueryRequest):
    try:
        # Check if file exists
        if not os.path.exists(req.file_path):
            raise HTTPException(status_code=404, detail="Excel file not found")

        # Read the Excel sheet
        df = pd.read_excel(req.file_path, sheet_name=req.sheet_name)

        q_lower = req.query.lower().strip()

        result_data = None

        # Helper: find the column case-insensitively
        def find_column(col_name):
            for c in df.columns:
                if c.lower() == col_name.lower():
                    return c
            return None

        # --- Simple operations ---
        if "sum of" in q_lower:
            col = req.query.lower().replace("sum of", "").strip().strip("'\"")
            matched_col = find_column(col)
            if not matched_col:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
            result_data = {"operation": "sum", "column": matched_col, "result": df[matched_col].sum()}

        elif "average of" in q_lower:
            col = req.query.lower().replace("average of", "").strip().strip("'\"")
            matched_col = find_column(col)
            if not matched_col:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
            result_data = {"operation": "average", "column": matched_col, "result": df[matched_col].mean()}

        elif "min of" in q_lower:
            col = req.query.lower().replace("min of", "").strip().strip("'\"")
            matched_col = find_column(col)
            if not matched_col:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
            result_data = {"operation": "min", "column": matched_col, "result": df[matched_col].min()}

        elif "max of" in q_lower:
            col = req.query.lower().replace("max of", "").strip().strip("'\"")
            matched_col = find_column(col)
            if not matched_col:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
            result_data = {"operation": "max", "column": matched_col, "result": df[matched_col].max()}

        else:
            # If query not recognized, return first 5 rows as preview
            result_data = {"preview": df.head().to_dict(orient="records")}

        # Save results to output_path if provided
        if req.output_path:
            pd.DataFrame([result_data]).to_excel(req.output_path, index=False)
            result_data["saved_to"] = req.output_path

        return result_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
