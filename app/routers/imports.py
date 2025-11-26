"""
API router for import operations.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.auth import verify_token
from app.models import ImportJob
from app.schemas import ImportJobResponse
from app.worker import import_csv_task
from app.config import settings

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("", response_model=dict, dependencies=[Depends(verify_token)])
async def create_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file and start import job.
    Returns job_id for progress tracking.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted"
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(settings.UPLOAD_DIR, f"{job_id}.csv")
    
    try:
        # Read and save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Create import job record
    import_job = ImportJob(
        job_id=job_id,
        filename=file.filename,
        file_size=file_size,
        status="pending",
        started_at=datetime.utcnow()
    )
    
    db.add(import_job)
    db.commit()
    db.refresh(import_job)
    
    # Enqueue Celery task for background processing
    try:
        import_csv_task.delay(job_id, file_path)
    except Exception as e:
        import_job.status = "failed"
        import_job.error_message = f"Failed to queue import task: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start import: {str(e)}"
        )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Import job queued for processing"
    }


@router.get("/{job_id}/status", response_model=ImportJobResponse)
async def get_import_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get import job status and progress.
    Public endpoint (no auth) for SSE clients.
    """
    import_job = db.query(ImportJob).filter(ImportJob.job_id == job_id).first()
    
    if not import_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found"
        )
    
    return import_job

