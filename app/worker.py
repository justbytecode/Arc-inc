"""
Celery worker configuration and task definitions.
"""
from celery import Celery
from app.config import settings
from app.database import SessionLocal
from app.models import ImportJob, Webhook, WebhookLog
from app.csv_utils import stream_csv_reader, batch_items, CSVValidator, format_error_log
from app.db_operations import batch_upsert_products, simple_batch_upsert
from datetime import datetime
import os

# Initialize Celery app
celery_app = Celery(
    "csv_import_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,  # Process one task at a time for long-running imports
)


@celery_app.task(name="import_csv_task", bind=True)
def import_csv_task(self, job_id: str, file_path: str):
    """
    Import CSV file in background with streaming and batched upsert.
    
    Args:
        job_id: Unique job identifier
        file_path: Path to uploaded CSV file
    """
    db = SessionLocal()
    
    try:
        # Get import job
        import_job = db.query(ImportJob).filter(ImportJob.job_id == job_id).first()
        if not import_job:
            raise Exception(f"Import job {job_id} not found")
        
        # Update status to parsing
        import_job.status = "parsing"
        import_job.started_at = datetime.utcnow()
        db.commit()
        
        # Track progress
        total_rows = 0
        processed_rows = 0
        imported_rows = 0
        updated_rows = 0
        skipped_rows = 0
        errors = []
        
        # Stream and process CSV in batches
        csv_stream = stream_csv_reader(file_path)
        
        # First pass: count total rows for progress tracking
        import_job.status = "parsing"
        db.commit()
        
        # Process in batches
        import_job.status = "importing"
        db.commit()
        
        for batch_num, batch_rows in enumerate(batch_items(csv_stream, settings.BATCH_SIZE)):
            valid_products = []
            
            for row_num, row in enumerate(batch_rows, start=1):
                total_rows += 1
                processed_rows += 1
                
                # Validate row
                is_valid, error_msg, normalized = CSVValidator.validate_row(
                    row, 
                    batch_num * settings.BATCH_SIZE + row_num
                )
                
                if is_valid:
                    valid_products.append(normalized)
                else:
                    skipped_rows += 1
                    errors.append({
                        'row': batch_num * settings.BATCH_SIZE + row_num,
                        'error': error_msg,
                        'data': {k: v for k, v in row.items() if v}  # Non-empty fields only
                    })
            
            # Batch upsert valid products
            if valid_products:
                try:
                    inserted, updated = batch_upsert_products(db, valid_products)
                    imported_rows += inserted
                    updated_rows += updated
                except Exception as e:
                    # Fallback to simple upsert
                    try:
                        inserted, updated = simple_batch_upsert(db, valid_products)
                        imported_rows += inserted
                        updated_rows += updated
                    except Exception as fallback_error:
                        # Log batch error
                        errors.append({
                            'batch': batch_num,
                            'error': f"Batch upsert failed: {str(fallback_error)}"
                        })
                        skipped_rows += len(valid_products)
            
            # Update progress
            import_job.total_rows = total_rows
            import_job.processed_rows = processed_rows
            import_job.imported_rows = imported_rows
            import_job.updated_rows = updated_rows
            import_job.skipped_rows = skipped_rows
            import_job.error_log = format_error_log(errors, settings.MAX_ERROR_SAMPLES)
            db.commit()
        
        # Mark as completed
        import_job.status = "completed"
        import_job.finished_at = datetime.utcnow()
        import_job.total_rows = total_rows
        import_job.processed_rows = processed_rows
        import_job.imported_rows = imported_rows
        import_job.updated_rows = updated_rows
        import_job.skipped_rows = skipped_rows
        import_job.error_log = format_error_log(errors, settings.MAX_ERROR_SAMPLES)
        db.commit()
        
        # Queue webhook event
        queue_webhook_event(db, "import.completed", {
            "job_id": job_id,
            "total_rows": total_rows,
            "imported_rows": imported_rows,
            "updated_rows": updated_rows,
            "skipped_rows": skipped_rows
        })
        
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "completed",
            "total_rows": total_rows,
            "imported_rows": imported_rows,
            "updated_rows": updated_rows,
            "skipped_rows": skipped_rows
        }
        
    except Exception as e:
        # Mark as failed
        if import_job:
            import_job.status = "failed"
            import_job.finished_at = datetime.utcnow()
            import_job.error_message = str(e)
            db.commit()
        
        # Queue webhook event
        try:
            queue_webhook_event(db, "import.failed", {
                "job_id": job_id,
                "error": str(e)
            })
        except:
            pass
        
        raise
    
    finally:
        db.close()


@celery_app.task(name="delete_all_products_task", bind=True)
def delete_all_products_task(self):
    """
    Delete all products in batches with progress tracking.
    Will be fully implemented in Step 7.
    """
    # TODO: Implement in Step 7
    pass


@celery_app.task(name="deliver_webhook_task", bind=True, max_retries=5)
def deliver_webhook_task(self, webhook_log_id: int):
    """
    Deliver webhook with retry logic.
    Will be fully implemented in Step 8.
    
    Args:
        webhook_log_id: ID of the webhook log entry to deliver
    """
    # TODO: Implement in Step 8
    pass


def queue_webhook_event(db, event_type: str, payload: dict):
    """
    Queue webhook delivery for an event.
    
    Args:
        db: Database session
        event_type: Type of event (e.g., "import.completed")
        payload: Event payload data
    """
    import json
    
    # Find webhooks subscribed to this event
    webhooks = db.query(Webhook).filter(
        Webhook.enabled == True
    ).all()
    
    for webhook in webhooks:
        events = webhook.events.split(',') if webhook.events else []
        if event_type in events:
            # Create webhook log entry
            log = WebhookLog(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=json.dumps(payload),
                attempt=0,
                max_attempts=settings.WEBHOOK_MAX_RETRIES
            )
            db.add(log)
    
    db.commit()

