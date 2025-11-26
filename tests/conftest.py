"""
Pytest configuration and shared fixtures.
"""
import pytest
from typing import Generator


@pytest.fixture
def sample_csv_data() -> str:
    """Sample CSV data for testing."""
    return """SKU,Name,Description,Price,Stock,Category,Country of Origin
TEST-001,Test Product 1,A sample product,19.99,100,Electronics,USA
TEST-002,Test Product 2,Another sample,29.99,50,Books,UK
test-001,Test Product 1 Updated,Updated description,24.99,150,Electronics,USA
"""


@pytest.fixture
def sample_csv_rows() -> list:
    """Sample CSV rows as dictionaries."""
    return [
        {
            "SKU": "TEST-001",
            "Name": "Test Product 1",
            "Description": "A sample product",
            "Price": "19.99",
            "Stock": "100",
            "Category": "Electronics",
            "Country of Origin": "USA"
        },
        {
            "SKU": "TEST-002",
            "Name": "Test Product 2",
            "Description": "Another sample",
            "Price": "29.99",
            "Stock": "50",
            "Category": "Books",
            "Country of Origin": "UK"
        }
    ]
