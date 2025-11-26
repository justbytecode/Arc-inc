"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CSV Import Application",
    description="Production-grade CSV import system with real-time progress tracking",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CSV Import Application",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "database": "not_configured",
        "redis": "not_configured"
    }
