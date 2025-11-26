"""
Integration tests for CSV import functionality.
"""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Product, ImportJob
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create and drop tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestCSVImportIntegration:
    """Integration tests for CSV import."""
    
    def test_upload_csv_creates_import_job(self):
        """Test that uploading a CSV creates an import job record."""
        # Create sample CSV
        csv_content = """SKU,Name,Description,Price,Stock,Category,Country of Origin
TEST-001,Product 1,Description 1,19.99,100,Electronics,USA
TEST-002,Product 2,Description 2,29.99,50,Books,UK
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/imports",
                    files={"file": ("test.csv", f, "text/csv")},
                    headers={"Authorization": f"Bearer {settings.AUTH_TOKEN}"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "pending"
            
            # Verify job was created in database (would be done by Celery worker)
            # Note: In integration test, Celery won't run, so we just check job creation
            
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)
    
    def test_get_import_status(self):
        """Test retrieving import job status."""
        # Create a test import job
        db = next(override_get_db())
        import_job = ImportJob(
            job_id="test-job-123",
            filename="test.csv",
            status="completed",
            total_rows=10,
            processed_rows=10,
            imported_rows=8,
            updated_rows=2,
            skipped_rows=0
        )
        db.add(import_job)
        db.commit()
        
        # Get status
        response = client.get("/api/imports/test-job-123/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "completed"
        assert data["total_rows"] == 10
        assert data["imported_rows"] == 8
        assert data["updated_rows"] == 2
    
    def test_sku_case_insensitive_upsert(self):
        """Test that SKU matching is case-insensitive in create/update operations."""
        db = next(override_get_db())
        
        # Create product with lowercase SKU
        product = Product(
            sku="test-sku-001",
            sku_norm="test-sku-001",
            name="Original Product",
            price=10.00,
            stock=5
        )
        db.add(product)
        db.commit()
        
        # Try to create with UPPERCASE SKU (should be treated as duplicate)
        response = client.post(
            "/api/products",
            json={
                "sku": "TEST-SKU-001",  # Same SKU, different case
                "name": "Duplicate Product",
                "price": 20.00,
                "stock": 10
            },
            headers={"Authorization": f"Bearer {settings.AUTH_TOKEN}"}
        )
        
        # Should fail with conflict
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


class TestProductCRUD:
    """Integration tests for product CRUD operations."""
    
    def test_create_product(self):
        """Test creating a product."""
        response = client.post(
            "/api/products",
            json={
                "sku": "NEW-001",
                "name": "New Product",
                "price": 15.99,
                "stock": 25,
                "category": "Test",
                "active": True
            },
            headers={"Authorization": f"Bearer {settings.AUTH_TOKEN}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "NEW-001"
        assert data["sku_norm"] == "new-001"
        assert data["name"] == "New Product"
    
    def test_list_products_pagination(self):
        """Test product listing with pagination."""
        db = next(override_get_db())
        
        # Create multiple products
        for i in range(30):
            product = Product(
                sku=f"TEST-{i:03d}",
                sku_norm=f"test-{i:03d}",
                name=f"Product {i}",
                price=10.00 + i,
                stock=i
            )
            db.add(product)
        db.commit()
        
        # Get first page
        response = client.get("/api/products?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 30
        assert data["total_pages"] == 3
    
    def test_filter_products_by_sku(self):
        """Test filtering products by SKU."""
        db = next(override_get_db())
        
        # Create test products
        for sku in ["ABC-001", "ABC-002", "XYZ-001"]:
            product = Product(
                sku=sku,
                sku_norm=sku.lower(),
                name=f"Product {sku}",
                price=10.00,
                stock=5
            )
            db.add(product)
        db.commit()
        
        # Filter by "ABC"
        response = client.get("/api/products?sku=abc")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all("abc" in item["sku"].lower() for item in data["items"])
