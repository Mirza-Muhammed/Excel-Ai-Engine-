from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pathlib import Path
import uuid
from app.services.excel_ops import read_excel_sheets

router = APIRouter()

# Directory to store uploaded files
UPLOAD_DIR = Path('./data')
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload an Excel file. Only .xls or .xlsx are allowed.
    Returns the saved file path and available sheets.
    """
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xls or .xlsx)")

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    dest = UPLOAD_DIR / filename

    try:
        contents = await file.read()
        dest.write_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    try:
        sheets = read_excel_sheets(str(dest))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {e}")

    return {"file_path": str(dest), "sheets": list(sheets.keys())}


@router.post("/path")
async def use_path(file_path: str = Form(...)):
    """
    Use an existing Excel file path instead of uploading.
    Returns the file path and available sheets.
    """
    p = Path(file_path)

    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    if not p.suffix.lower() in ('.xls', '.xlsx'):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xls or .xlsx)")

    try:
        sheets = read_excel_sheets(str(p))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {e}")

    return {"file_path": str(p), "sheets": list(sheets.keys())}
