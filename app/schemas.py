"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Product schemas
class ProductBase(BaseModel):
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    country_of_origin: Optional[str] = Field(None, max_length=100)
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    country_of_origin: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    sku_norm: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Import schemas
class ImportJobResponse(BaseModel):
    id: int
    job_id: str
    filename: str
    file_size: Optional[int]
    status: str
    total_rows: int = 0
    processed_rows: int = 0
    imported_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    error_log: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ImportProgressUpdate(BaseModel):
    """Real-time progress update for SSE."""
    job_id: str
    status: str
    total_rows: int = 0
    processed_rows: int = 0
    imported_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    message: str = ""
    progress_percent: float = 0.0


# Webhook schemas
class WebhookBase(BaseModel):
    name: str = Field(..., max_length=255)
    url: HttpUrl
    events: List[str] = Field(..., min_items=1)
    hmac_secret: Optional[str] = Field(None, max_length=255)
    enabled: bool = True


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = Field(None, min_items=1)
    hmac_secret: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: List[str]
    hmac_secret: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebhookTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


# Webhook log schemas  
class WebhookLogResponse(BaseModel):
    id: int
    webhook_id: int
    event_type: str
    status_code: Optional[int]
    error_message: Optional[str]
    attempt: int
    max_attempts: int
    next_retry_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Pagination
class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
