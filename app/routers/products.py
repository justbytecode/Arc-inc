"""
API router for product CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
from math import ceil

from app.database import get_db
from app.auth import verify_token
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse, PaginatedResponse

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=dict)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sku: Optional[str] = None,
    name: Optional[str] = None,
    category: Optional[str] = None,
    active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List products with server-side pagination and filtering.
    """
    query = db.query(Product)
    
    # Apply filters
    if sku:
        query = query.filter(Product.sku_norm.contains(sku.lower()))
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if category:
        query = query.filter(Product.category == category)
    if active is not None:
        query = query.filter(Product.active == active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "items": products,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total > 0 else 0
    }


@router.post("", response_model=ProductResponse, dependencies=[Depends(verify_token)])
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product.
    """
    # Normalize SKU for uniqueness check
    sku_norm = product_data.sku.lower()
    
    # Check for existing SKU (case-insensitive)
    existing = db.query(Product).filter(Product.sku_norm == sku_norm).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{product_data.sku}' already exists (case-insensitive)"
        )
    
    # Create product
    product = Product(
        **product_data.model_dump(),
        sku_norm=sku_norm
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    
    return product


@router.put("/{product_id}", response_model=ProductResponse, dependencies=[Depends(verify_token)])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    
    # Update fields
    update_dict = product_data.model_dump(exclude_unset=True)
    
    # If SKU is being updated, update sku_norm and check uniqueness
    if "sku" in update_dict:
        new_sku_norm = update_dict["sku"].lower()
        if new_sku_norm != product.sku_norm:
            existing = db.query(Product).filter(
                Product.sku_norm == new_sku_norm,
                Product.id != product_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with SKU '{update_dict['sku']}' already exists"
                )
            update_dict["sku_norm"] = new_sku_norm
    
    for key, value in update_dict.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    
    return product


@router.delete("/{product_id}", dependencies=[Depends(verify_token)])
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    
    db.delete(product)
    db.commit()
    
    return {"message": f"Product {product_id} deleted successfully"}


@router.post("/delete_all", dependencies=[Depends(verify_token)])
async def delete_all_products(
    confirmation: str = Query(..., description="Type 'DELETE ALL' to confirm"),
    db: Session = Depends(get_db)
):
    """
    Delete all products in background (protected by typed confirmation).
    Returns task_id for progress tracking.
    """
    if confirmation != "DELETE ALL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation string must be 'DELETE ALL'"
        )
    
    from app.worker import delete_all_products_task
    
    # Enqueue background task
    task = delete_all_products_task.delay()
    
    return {
        "message": "Bulk delete job started",
        "task_id": task.id,
        "status": "processing"
    }

