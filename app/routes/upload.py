from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import uuid
from app.services.excel_ops import read_excel_sheets

router = APIRouter()
UPLOAD_DIR = Path('./data')
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post('/file')
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail='File must be an Excel file')
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    dest = UPLOAD_DIR / filename
    contents = await file.read()
    dest.write_bytes(contents)
    try:
        sheets = read_excel_sheets(str(dest))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to parse Excel: {e}')
    return {"file_path": str(dest), "sheets": list(sheets.keys())}

@router.post('/path')
async def use_path(file_path: str):
    p = Path(file_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail='File not found')
    try:
        sheets = read_excel_sheets(str(p))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to parse Excel: {e}')
    return {"file_path": str(p), "sheets": list(sheets.keys())}
