"""
Unit tests for CSV utilities.
"""
import pytest
from app.csv_utils import CSVValidator


class TestCSVValidator:
    """Test CSV validation and normalization."""
    
    def test_validate_valid_row(self):
        """Test validation of a valid product row."""
        row = {
            'SKU': 'TEST-001',
            'Name': 'Test Product',
            'Price': '19.99',
            'Stock': '100',
            'Description': 'A test product',
            'Category': 'Electronics',
            'Country of Origin': 'USA'
        }
        
        is_valid, error, normalized = CSVValidator.validate_row(row, 1)
        
        assert is_valid is True
        assert error == ""
        assert normalized['sku'] == 'TEST-001'
        assert normalized['sku_norm'] == 'test-001'
        assert normalized['name'] == 'Test Product'
        assert normalized['price'] == 19.99
        assert normalized['stock'] == 100
        assert normalized['category'] == 'Electronics'
        assert normalized['country_of_origin'] == 'USA'
        assert normalized['active'] is True
    
    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        row = {
            'SKU': 'TEST-001',
            # Missing 'Name'
            'Price': '19.99',
            'Stock': '100'
        }
        
        is_valid, error, normalized = CSVValidator.validate_row(row, 1)
        
        assert is_valid is False
        assert 'Name' in error
        assert normalized == {}
    
    def test_validate_invalid_price(self):
        """Test validation fails with invalid price."""
        row = {
            'SKU': 'TEST-001',
            'Name': 'Test Product',
            'Price': 'invalid',
            'Stock': '100'
        }
        
        is_valid, error, normalized = CSVValidator.validate_row(row, 1)
        
        assert is_valid is False
        assert 'price' in error.lower()
    
    def test_validate_negative_stock(self):
        """Test validation fails with negative stock."""
        row = {
            'SKU': 'TEST-001',
            'Name': 'Test Product',
            'Price': '19.99',
            'Stock': '-10'
        }
        
        is_valid, error, normalized = CSVValidator.validate_row(row, 1)
        
        assert is_valid is False
        assert 'stock' in error.lower()
    
    def test_sku_normalization(self):
        """Test SKU is normalized to lowercase."""
        row = {
            'SKU': 'UPPER-Case-SKU-123',
            'Name': 'Test',
            'Price': '10.00',
            'Stock': '5'
        }
        
        is_valid, error, normalized = CSVValidator.validate_row(row, 1)
        
        assert is_valid is True
        assert normalized['sku'] == 'UPPER-Case-SKU-123'
        assert normalized['sku_norm'] == 'upper-case-sku-123'
    
    def test_optional_fields(self):
        """Test validation succeeds with only required fields."""
        row = {
            'SKU': 'TEST-001',
            'Name': 'Minimal Product',
            'Price': '5.99',
            'Stock': '10'
        }
        
        is_valid, error, normalized = CSVValidator.validate_row(row, 1)
        
        assert is_valid is True
        assert normalized['description'] is None
        assert normalized['category'] is None
        assert normalized['country_of_origin'] is None
