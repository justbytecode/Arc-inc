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
    Uses task state updates for real-time progress.
    """
    db = SessionLocal()
    
    try:
        # Get total count
        total_count = db.query(Product).count()
        
        if total_count == 0:
            return {
                "status": "completed",
                "message": "No products to delete",
                "deleted": 0
            }
        
        deleted_count = 0
        batch_size = settings.BATCH_SIZE
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': total_count,
                'status': 'Deleting products...'
            }
        )
        
        # Delete in batches
        while True:
            # Get batch of IDs
            product_ids = db.query(Product.id).limit(batch_size).all()
            
            if not product_ids:
                break
            
            # Extract IDs from tuples
            ids_to_delete = [pid[0] for pid in product_ids]
            
            # Delete batch
            db.query(Product).filter(Product.id.in_(ids_to_delete)).delete(synchronize_session=False)
            db.commit()
            
            deleted_count += len(ids_to_delete)
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': deleted_count,
                    'total': total_count,
                    'status': f'Deleted {deleted_count}/{total_count} products...'
                }
            )
        
        return {
            "status": "completed",
            "message": f"Successfully deleted {deleted_count} products",
            "deleted": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Bulk delete failed: {str(e)}")
    
    finally:
        db.close()



@celery_app.task(name="deliver_webhook_task", bind=True, max_retries=5)
def deliver_webhook_task(self, webhook_log_id: int):
    """
    Deliver webhook with retry logic and exponential backoff.
    
    Args:
        webhook_log_id: ID of the webhook log entry to deliver
    """
    import requests
    import hmac
    import hashlib
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    
    try:
        # Get webhook log
        log = db.query(WebhookLog).filter(WebhookLog.id == webhook_log_id).first()
        if not log:
            raise Exception(f"Webhook log {webhook_log_id} not found")
        
        # Get webhook configuration
        webhook = db.query(Webhook).filter(Webhook.id == log.webhook_id).first()
        if not webhook:
            raise Exception(f"Webhook {log.webhook_id} not found")
        
        if not webhook.enabled:
            log.error_message = "Webhook is disabled"
            db.commit()
            return {"status": "skipped", "reason": "webhook disabled"}
        
        # Prepare payload
        payload = log.payload
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CSV-Import-Application/1.0',
            'X-Webhook-Event': log.event_type
        }
        
        # Add HMAC signature if secret is configured
        if webhook.hmac_secret:
            signature = hmac.new(
                webhook.hmac_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f'sha256={signature}'
        
        # Increment attempt count
        log.attempt += 1
        db.commit()
        
        # Make HTTP request
        try:
            response = requests.post(
                webhook.url,
                data=payload,
                headers=headers,
                timeout=settings.WEBHOOK_TIMEOUT
            )
            
            # Log response
            log.status_code = response.status_code
            log.response_body = response.text[:1000]  # Store first 1000 chars
            
            # Check if successful (2xx status codes)
            if 200 <= response.status_code < 300:
                log.delivered_at = datetime.utcnow()
                log.next_retry_at = None
                db.commit()
                
                return {
                    "status": "delivered",
                    "status_code": response.status_code,
                    "attempt": log.attempt
                }
            else:
                # Non-2xx response, schedule retry
                raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.RequestException as e:
            # Network error, schedule retry
            error_msg = f"Request failed: {str(e)}"
            log.error_message = error_msg
            
            # Schedule retry if attempts remain
            if log.attempt < log.max_attempts:
                # Exponential backoff
                retry_delays = settings.WEBHOOK_RETRY_DELAYS
                delay_index = min(log.attempt - 1, len(retry_delays) - 1)
                delay_seconds = retry_delays[delay_index]
                
                log.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                db.commit()
                
                # Retry task
                self.retry(countdown=delay_seconds, exc=e)
            else:
                # Max retries exceeded
                log.error_message = f"Max retries exceeded. Last error: {error_msg}"
                db.commit()
                
                return {
                    "status": "failed",
                    "error": "Max retries exceeded",
                    "attempts": log.attempt
                }
    
    except Exception as e:
        if log:
            log.error_message = str(e)
            db.commit()
        raise
    
    finally:
        db.close()



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
            db.flush()  # Get the log ID
            
            # Enqueue delivery task
            deliver_webhook_task.delay(log.id)
    
    db.commit()

