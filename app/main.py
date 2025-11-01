from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload import router as upload_router
from app.routes.query import router as query_router

# ----------------------------------------------------
# 🚀 Excel AI Engine - Main FastAPI Application
# ----------------------------------------------------

app = FastAPI(
    title="Excel AI Engine",
    description="Upload, query, and analyze Excel data using natural and structured queries.",
    version="1.0.0",
)

# ----------------------------------------------------
# 🌐 CORS Configuration
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow requests from all domains (good for local dev)
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],       # Allow all headers
)

# ----------------------------------------------------
# 🔌 Include Routers
# ----------------------------------------------------
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(query_router, prefix="/query", tags=["Query"])

# ----------------------------------------------------
# 🏠 Root Endpoint
# ----------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Welcome to the Excel AI Engine API!",
        "docs": "Visit /docs for Swagger UI or /redoc for ReDoc documentation."
    }

# ----------------------------------------------------
# 💓 Health Check Endpoint
# ----------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
