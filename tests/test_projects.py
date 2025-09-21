import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database.models import User, Project, ProjectMember, UserRole
from app.auth import get_password_hash
from tests.test_auth import setup_database, TestingSessionLocal

client = TestClient(app)

@pytest.fixture
def auth_headers(setup_database):
    """Create a test user and return auth headers"""
    db = TestingSessionLocal()
    
    # Create test user
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        role=UserRole.DEVELOPER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Login to get token
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    
    db.close()
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(setup_database):
    """Create an admin user and return auth headers"""
    db = TestingSessionLocal()
    
    # Create admin user
    admin = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpassword123"),
        role=UserRole.ADMIN
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    # Login to get token
    response = client.post("/api/auth/login", data={
        "username": "admin",
        "password": "adminpassword123"
    })
    token = response.json()["access_token"]
    
    db.close()
    return {"Authorization": f"Bearer {token}"}

def test_create_project_success(admin_headers):
    """Test successful project creation"""
    project_data = {
        "name": "Test Project",
        "description": "A test project",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-31T23:59:59"
    }
    
    response = client.post("/api/projects/", json=project_data, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["creator_name"] == "Admin User"
    assert data["member_count"] == 1  # Creator is automatically added

def test_create_project_unauthorized(auth_headers):
    """Test project creation without proper permissions"""
    project_data = {
        "name": "Test Project",
        "description": "A test project"
    }
    
    response = client.post("/api/projects/", json=project_data, headers=auth_headers)
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]

def test_get_projects(admin_headers):
    """Test getting projects list"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project"
    }
    client.post("/api/projects/", json=project_data, headers=admin_headers)
    
    # Get projects
    response = client.get("/api/projects/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Project"

def test_get_project_by_id(admin_headers):
    """Test getting a specific project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project"
    }
    create_response = client.post("/api/projects/", json=project_data, headers=admin_headers)
    project_id = create_response.json()["id"]
    
    # Get project by ID
    response = client.get(f"/api/projects/{project_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] == project_id

def test_update_project(admin_headers):
    """Test updating a project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project"
    }
    create_response = client.post("/api/projects/", json=project_data, headers=admin_headers)
    project_id = create_response.json()["id"]
    
    # Update project
    update_data = {
        "name": "Updated Project",
        "description": "An updated test project"
    }
    response = client.put(f"/api/projects/{project_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project"
    assert data["description"] == "An updated test project"

def test_delete_project(admin_headers):
    """Test deleting a project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project"
    }
    create_response = client.post("/api/projects/", json=project_data, headers=admin_headers)
    project_id = create_response.json()["id"]
    
    # Delete project
    response = client.delete(f"/api/projects/{project_id}", headers=admin_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify project is deleted
    get_response = client.get(f"/api/projects/{project_id}", headers=admin_headers)
    assert get_response.status_code == 404

def test_add_project_member(admin_headers, auth_headers):
    """Test adding a member to a project"""
    # Create a project first
    project_data = {
        "name": "Test Project",
        "description": "A test project"
    }
    create_response = client.post("/api/projects/", json=project_data, headers=admin_headers)
    project_id = create_response.json()["id"]
    
    # Get user ID from auth headers (we need to create a user first)
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    user_id = user.id
    db.close()
    
    # Add member
    member_data = {
        "user_id": user_id,
        "role": "member"
    }
    response = client.post(f"/api/projects/{project_id}/members", json=member_data, headers=admin_headers)
    assert response.status_code == 200
    assert "added successfully" in response.json()["message"]
