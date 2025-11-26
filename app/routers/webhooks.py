"""
API router for webhook CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.auth import verify_token
from app.models import Webhook, WebhookLog
from app.schemas import (
    WebhookCreate, WebhookUpdate, WebhookResponse, 
    WebhookTestResponse, WebhookLogResponse
)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all webhooks."""
    query = db.query(Webhook)
    
    if enabled is not None:
        query = query.filter(Webhook.enabled == enabled)
    
    webhooks = query.order_by(Webhook.created_at.desc()).all()
    
    # Convert events from string to list
    result = []
    for webhook in webhooks:
        webhook_dict = {
            "id": webhook.id,
            "name": webhook.name,
            "url": webhook.url,
            "events": webhook.events.split(",") if webhook.events else [],
            "hmac_secret": webhook.hmac_secret,
            "enabled": webhook.enabled,
            "created_at": webhook.created_at,
            "updated_at": webhook.updated_at
        }
        result.append(webhook_dict)
    
    return result


@router.post("", response_model=dict, dependencies=[Depends(verify_token)])
async def create_webhook(
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db)
):
    """Create a new webhook."""
    # Convert events list to comma-separated string
    events_str = ",".join(webhook_data.events)
    
    webhook = Webhook(
        name=webhook_data.name,
        url=str(webhook_data.url),
        events=events_str,
        hmac_secret=webhook_data.hmac_secret,
        enabled=webhook_data.enabled
    )
    
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    return {
        "id": webhook.id,
        "name": webhook.name,
        "url": webhook.url,
        "events": webhook_data.events,
        "enabled": webhook.enabled
    }


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db)
):
    """Get webhook by ID."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    
    return {
        "id": webhook.id,
        "name": webhook.name,
        "url": webhook.url,
        "events": webhook.events.split(",") if webhook.events else [],
        "hmac_secret": webhook.hmac_secret,
        "enabled": webhook.enabled,
        "created_at": webhook.created_at,
        "updated_at": webhook.updated_at
    }


@router.put("/{webhook_id}", response_model=WebhookResponse, dependencies=[Depends(verify_token)])
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """Update webhook by ID."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    
    # Update fields
    update_dict = webhook_data.model_dump(exclude_unset=True)
    
    # Convert events list to string if present
    if "events" in update_dict and update_dict["events"]:
        update_dict["events"] = ",".join(update_dict["events"])
    
    # Convert URL to string if present
    if "url" in update_dict and update_dict["url"]:
        update_dict["url"] = str(update_dict["url"])
    
    for key, value in update_dict.items():
        setattr(webhook, key, value)
    
    db.commit()
    db.refresh(webhook)
    
    return {
        "id": webhook.id,
        "name": webhook.name,
        "url": webhook.url,
        "events": webhook.events.split(",") if webhook.events else [],
        "hmac_secret": webhook.hmac_secret,
        "enabled": webhook.enabled,
        "created_at": webhook.created_at,
        "updated_at": webhook.updated_at
    }


@router.delete("/{webhook_id}", dependencies=[Depends(verify_token)])
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db)
):
    """Delete webhook by ID."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    
    db.delete(webhook)
    db.commit()
    
    return {"message": f"Webhook {webhook_id} deleted successfully"}


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse, dependencies=[Depends(verify_token)])
async def test_webhook(
    webhook_id: int,
    db: Session = Depends(get_db)
):
    """
    Test webhook delivery by sending a test event.
    """
    import requests
    import json
    import time
    
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    
    # Create test payload
    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "This is a test webhook delivery"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CSV-Import-Application/1.0',
        'X-Webhook-Event': 'webhook.test'
    }
    
    # Add HMAC signature if configured
    if webhook.hmac_secret:
        import hmac
        import hashlib
        
        payload_str = json.dumps(test_payload)
        signature = hmac.new(
            webhook.hmac_secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers['X-Webhook-Signature'] = f'sha256={signature}'
    
    try:
        start_time = time.time()
        response = requests.post(
            webhook.url,
            json=test_payload,
            headers=headers,
            timeout=30
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "response_time_ms": round(response_time_ms, 2),
            "error": None if 200 <= response.status_code < 300 else response.text[:200]
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "error": str(e)
        }



@router.get("/{webhook_id}/logs", response_model=List[WebhookLogResponse])
async def get_webhook_logs(
    webhook_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get webhook delivery logs."""
    logs = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id
    ).order_by(
        WebhookLog.created_at.desc()
    ).limit(limit).all()
    
    return logs
