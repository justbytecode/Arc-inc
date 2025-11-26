"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import imports, products, webhooks
import os

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

# Register routers
app.include_router(imports.router)
app.include_router(products.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "api": "running",
        "database": "configured",
        "redis": "configured"
    }


# Mount static files
# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
print(f"Mounting static files from: {static_path}")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def serve_index():
    """Serve the frontend index page."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Ensure static files are in app/static/"}


