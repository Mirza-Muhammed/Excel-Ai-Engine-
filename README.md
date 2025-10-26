# Excel AI Engine

Quickstart:
1. Create venv and install: `pip install -r requirements.txt`
2. Generate sample data: `python generate_data.py`
3. Run: `uvicorn app.main:app --reload --port 8000`
4. Open Swagger: http://localhost:8000/docs

Endpoints:
- POST /upload/file -> upload Excel
- POST /upload/path -> use existing path
- POST /query/run -> run natural-language query against a sheet
