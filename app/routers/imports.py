"""
API router for import operations.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.auth import verify_token
from app.models import ImportJob
from app.schemas import ImportJobResponse
from app.worker import import_csv_task

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
    
    # Create import job record
    import_job = ImportJob(
        job_id=job_id,
        filename=file.filename,
        status="pending",
        started_at=datetime.utcnow()
    )
    
    db.add(import_job)
    db.commit()
    db.refresh(import_job)
    
    # TODO: Save file and enqueue Celery task in Step 5
    # For now, just return the job_id
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Import job created (processing not yet implemented)"
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
