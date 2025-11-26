"""
Database operations for CSV import.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Tuple
import tempfile
import os

from app.models import Product
from app.config import settings


def batch_upsert_products(db: Session, products: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Perform high-performance batch upsert using PostgreSQL COPY + INSERT ON CONFLICT.
    
    Strategy:
    1. COPY data into a temporary table (fast bulk load)
    2. INSERT ... ON CONFLICT DO UPDATE from temp table to products table
    3. Return counts of inserted vs updated rows
    
    Args:
        db: Database session
        products: List of normalized product dictionaries
        
    Returns:
        (inserted_count, updated_count)
    """
    if not products:
        return 0, 0
    
    try:
        # Create temporary table with same structure as products
        db.execute(text("""
            CREATE TEMP TABLE temp_products (
                sku VARCHAR(100),
                sku_norm VARCHAR(100),
                name VARCHAR(255),
                description TEXT,
                price NUMERIC(10, 2),
                stock INTEGER,
                category VARCHAR(100),
                country_of_origin VARCHAR(100),
                active BOOLEAN
            ) ON COMMIT DROP
        """))
        
        # Prepare data for COPY (write to temp CSV)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8') as tmp_file:
            tmp_path = tmp_file.name
            
            for product in products:
                # Format row for COPY (tab-separated, NULL for None values)
                row = [
                    product['sku'],
                    product['sku_norm'],
                    product['name'],
                    product['description'] or '\\N',
                    str(product['price']),
                    str(product['stock']),
                    product['category'] or '\\N',
                    product['country_of_origin'] or '\\N',
                    't' if product['active'] else 'f'
                ]
                tmp_file.write('\t'.join(row) + '\n')
        
        # Use COPY to load data into temp table
        with open(tmp_path, 'r', encoding='utf-8') as f:
            raw_conn = db.connection().connection  # Get raw psycopg2 connection
            cursor = raw_conn.cursor()
            cursor.copy_from(
                f,
                'temp_products',
                columns=('sku', 'sku_norm', 'name', 'description', 'price', 'stock', 
                        'category', 'country_of_origin', 'active'),
                null='\\N'
            )
            cursor.close()
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Track inserted and updated counts using CTEs
        result = db.execute(text("""
            WITH upserted AS (
                INSERT INTO products (sku, sku_norm, name, description, price, stock, 
                                     category, country_of_origin, active, created_at, updated_at)
                SELECT sku, sku_norm, name, description, price, stock, 
                       category, country_of_origin, active, NOW(), NOW()
                FROM temp_products
                ON CONFLICT (sku_norm) DO UPDATE SET
                    sku = EXCLUDED.sku,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    stock = EXCLUDED.stock,
                    category = EXCLUDED.category,
                    country_of_origin = EXCLUDED.country_of_origin,
                    active = EXCLUDED.active,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted
            )
            SELECT 
                COUNT(*) FILTER (WHERE inserted) AS inserted_count,
                COUNT(*) FILTER (WHERE NOT inserted) AS updated_count
            FROM upserted
        """))
        
        row = result.fetchone()
        inserted_count = row[0] if row else 0
        updated_count = row[1] if row else 0
        
        db.commit()
        
        return inserted_count, updated_count
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Batch upsert failed: {str(e)}")


def simple_batch_upsert(db: Session, products: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Simpler batch upsert using individual statements (fallback method).
    Use this if COPY method fails.
    
    Args:
        db: Database session
        products: List of normalized product dictionaries
        
    Returns:
        (inserted_count, updated_count)
    """
    inserted = 0
    updated = 0
    
    for product_data in products:
        # Check if exists
        existing = db.query(Product).filter(
            Product.sku_norm == product_data['sku_norm']
        ).first()
        
        if existing:
            # Update
            for key, value in product_data.items():
                setattr(existing, key, value)
            updated += 1
        else:
            # Insert
            product = Product(**product_data)
            db.add(product)
            inserted += 1
    
    db.commit()
    return inserted, updated
