"""
CSV import utilities for streaming processing.
"""
import csv
import io
import json
from typing import Generator, Dict, Any, List, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime


class CSVImportError(Exception):
    """Custom exception for CSV import errors."""
    pass


class CSVValidator:
    """Validates and normalizes CSV rows."""
    
    REQUIRED_FIELDS = ['SKU', 'Name', 'Price', 'Stock']
    OPTIONAL_FIELDS = ['Description', 'Category', 'Country of Origin']
    
    @staticmethod
    def validate_row(row: Dict[str, Any], line_number: int) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate and normalize a CSV row.
        
        Returns:
            (is_valid, error_message, normalized_data)
        """
        errors = []
        
        # Check required fields
        for field in CSVValidator.REQUIRED_FIELDS:
            if field not in row or not row[field].strip():
                errors.append(f"Missing required field '{field}'")
        
        if errors:
            return False, "; ".join(errors), {}
        
        # Normalize and validate data
        try:
            normalized = {
                'sku': row['SKU'].strip(),
                'sku_norm': row['SKU'].strip().lower(),
                'name': row['Name'].strip()[:255],  # Truncate to max length
                'description': row.get('Description', '').strip() or None,
                'category': row.get('Category', '').strip()[:100] or None,
                'country_of_origin': row.get('Country of Origin', '').strip()[:100] or None,
                'active': True
            }
            
            # Validate and convert price
            try:
                price_str = row['Price'].strip().replace('$', '').replace(',', '')
                price = Decimal(price_str)
                if price < 0:
                    errors.append("Price cannot be negative")
                normalized['price'] = price
            except (ValueError, InvalidOperation):
                errors.append(f"Invalid price value: {row['Price']}")
            
            # Validate and convert stock
            try:
                stock = int(row['Stock'].strip())
                if stock < 0:
                    errors.append("Stock cannot be negative")
                normalized['stock'] = stock
            except ValueError:
                errors.append(f"Invalid stock value: {row['Stock']}")
            
            if errors:
                return False, "; ".join(errors), {}
            
            return True, "", normalized
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", {}


def stream_csv_reader(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Stream CSV file line by line to avoid loading entire file into memory.
    
    Yields:
        Dictionary for each row with field names as keys
    """
    with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
        # Detect delimiter
        sample = f.read(4096)
        f.seek(0)
        
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
        except csv.Error:
            # Default to comma
            dialect = csv.excel
        
        reader = csv.DictReader(f, dialect=dialect)
        
        # Normalize field names (strip whitespace)
        reader.fieldnames = [field.strip() if field else field for field in reader.fieldnames]
        
        for row in reader:
            yield row


def batch_items(items: Generator, batch_size: int) -> Generator[List, None, None]:
    """
    Batch a generator into chunks of specified size.
    
    Args:
        items: Generator of items
        batch_size: Number of items per batch
        
    Yields:
        Lists of items up to batch_size
    """
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    
    if batch:  # Yield remaining items
        yield batch


def format_error_log(errors: List[Dict[str, Any]], max_errors: int = 100) -> str:
    """
    Format error list as JSON string, keeping only first N errors.
    
    Args:
        errors: List of error dictionaries
        max_errors: Maximum number of errors to store
        
    Returns:
        JSON string of error list
    """
    limited_errors = errors[:max_errors]
    return json.dumps(limited_errors, indent=2)
