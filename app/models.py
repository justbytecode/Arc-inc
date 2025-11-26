"""
Database models for CSV import application.
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, 
    Text, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Product(Base):
    """Product model with case-insensitive SKU handling."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # SKU fields - original and normalized (lowercase) for uniqueness
    sku = Column(String(100), nullable=False, index=True)
    sku_norm = Column(String(100), nullable=False, unique=True, index=True)
    
    # Product details
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    category = Column(String(100), index=True)
    country_of_origin = Column(String(100))
    
    # Status and timestamps
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name})>"


class ImportJob(Base):
    """Import job tracking with progress and error logging."""
    __tablename__ = "imports"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)  # Bytes
    
    # Status tracking
    status = Column(
        String(50), 
        nullable=False, 
        default="pending",
        index=True
    )  # pending, uploading, parsing, importing, completed, failed
    
    # Progress counters
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    imported_rows = Column(Integer, default=0)  # New inserts
    updated_rows = Column(Integer, default=0)   # Upserts
    skipped_rows = Column(Integer, default=0)   # Invalid/errors
    
    # Error tracking
    error_log = Column(Text)  # JSON array of first N errors
    error_message = Column(Text)  # Fatal error message if failed
    
    # Timestamps
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ImportJob(job_id={self.job_id}, status={self.status})>"


class Webhook(Base):
    """Webhook configuration for event delivery."""
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Webhook details
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    
    # Event subscriptions (stored as comma-separated)
    # Events: import.started, import.completed, import.failed, product.created, product.updated, product.deleted
    events = Column(Text, nullable=False)
    
    # Security
    hmac_secret = Column(String(255))  # Optional HMAC signature secret
    
    # Status
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    logs = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, name={self.name}, enabled={self.enabled})>"


class WebhookLog(Base):
    """Webhook delivery attempt logging."""
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, index=True)
    
    # Delivery details
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON payload
    
    # Response tracking
    status_code = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    
    # Retry tracking
    attempt = Column(Integer, default=1, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    next_retry_at = Column(DateTime)
    
    # Timestamps
    delivered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="logs")
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, event={self.event_type}, attempt={self.attempt})>"


# Create indexes
Index("idx_webhook_logs_retry", WebhookLog.webhook_id, WebhookLog.next_retry_at)
Index("idx_products_search", Product.name, Product.category, Product.active)
