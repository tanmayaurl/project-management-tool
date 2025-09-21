import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.session import get_db, Base
from app.database.models import User, UserRole
from app.auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123",
        "role": "developer"
    }

@pytest.fixture
def admin_user():
    return {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "password": "adminpassword123",
        "role": "admin"
    }

def test_register_user(setup_database, test_user):
    """Test user registration"""
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]
    assert data["role"] == test_user["role"]
    assert "id" in data

def test_register_duplicate_user(setup_database, test_user):
    """Test registration with duplicate email"""
    # First registration
    client.post("/api/auth/register", json=test_user)
    
    # Second registration with same email
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(setup_database, test_user):
    """Test successful login"""
    # Register user first
    client.post("/api/auth/register", json=test_user)
    
    # Login
    response = client.post("/api/auth/login", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(setup_database, test_user):
    """Test login with invalid credentials"""
    # Register user first
    client.post("/api/auth/register", json=test_user)
    
    # Login with wrong password
    response = client.post("/api/auth/login", data={
        "username": test_user["username"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_current_user(setup_database, test_user):
    """Test getting current user info"""
    # Register and login
    client.post("/api/auth/register", json=test_user)
    login_response = client.post("/api/auth/login", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_protected_endpoint_without_token(setup_database):
    """Test accessing protected endpoint without token"""
    response = client.get("/api/me")
    assert response.status_code == 401

def test_protected_endpoint_with_invalid_token(setup_database):
    """Test accessing protected endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/me", headers=headers)
    assert response.status_code == 401
