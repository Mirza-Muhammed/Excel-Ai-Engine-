from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.routes.upload import router as upload_router
from app.routes.query import router as query_router

app = FastAPI(
    title="Excel AI Engine",
    description="Upload Excel files and run natural-language queries on them.",
    version="0.1.0"
)

# Allow CORS for testing from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routers
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(query_router, prefix="/query", tags=["Query"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Excel AI Engine API! Visit /docs to explore."}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}
