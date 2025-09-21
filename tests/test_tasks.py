import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database.models import User, Project, Task, ProjectMember, UserRole, TaskStatus, Priority
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
def project_with_member(setup_database):
    """Create a project with a member"""
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
    
    # Create developer user
    developer = User(
        email="dev@example.com",
        username="developer",
        full_name="Developer User",
        hashed_password=get_password_hash("devpassword123"),
        role=UserRole.DEVELOPER
    )
    db.add(developer)
    db.commit()
    db.refresh(developer)
    
    # Create project
    project = Project(
        name="Test Project",
        description="A test project",
        creator_id=admin.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Add developer as member
    member = ProjectMember(
        project_id=project.id,
        user_id=developer.id,
        role="member"
    )
    db.add(member)
    db.commit()
    
    # Get tokens
    admin_response = client.post("/api/auth/login", data={
        "username": "admin",
        "password": "adminpassword123"
    })
    admin_token = admin_response.json()["access_token"]
    
    dev_response = client.post("/api/auth/login", data={
        "username": "developer",
        "password": "devpassword123"
    })
    dev_token = dev_response.json()["access_token"]
    
    db.close()
    
    return {
        "project_id": project.id,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "dev_headers": {"Authorization": f"Bearer {dev_token}"},
        "developer_id": developer.id
    }

def test_create_task_success(project_with_member):
    """Test successful task creation"""
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "project_id": project_with_member["project_id"],
        "assignee_id": project_with_member["developer_id"],
        "priority": "high",
        "due_date": "2024-12-31T23:59:59"
    }
    
    response = client.post("/api/tasks/", json=task_data, headers=project_with_member["admin_headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["priority"] == task_data["priority"]
    assert data["assignee_id"] == task_data["assignee_id"]

def test_create_task_unauthorized(project_with_member):
    """Test task creation without proper permissions"""
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "project_id": project_with_member["project_id"]
    }
    
    # Try to create task without being a project member
    db = TestingSessionLocal()
    outsider = User(
        email="outsider@example.com",
        username="outsider",
        full_name="Outsider User",
        hashed_password=get_password_hash("outsiderpassword123"),
        role=UserRole.DEVELOPER
    )
    db.add(outsider)
    db.commit()
    db.refresh(outsider)
    
    outsider_response = client.post("/api/auth/login", data={
        "username": "outsider",
        "password": "outsiderpassword123"
    })
    outsider_token = outsider_response.json()["access_token"]
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    
    db.close()
    
    response = client.post("/api/tasks/", json=task_data, headers=outsider_headers)
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]

def test_get_my_tasks(project_with_member):
    """Test getting tasks assigned to current user"""
    # Create a task assigned to developer
    task_data = {
        "title": "My Task",
        "description": "A task for me",
        "project_id": project_with_member["project_id"],
        "assignee_id": project_with_member["developer_id"]
    }
    client.post("/api/tasks/", json=task_data, headers=project_with_member["admin_headers"])
    
    # Get my tasks
    response = client.get("/api/tasks/my-tasks", headers=project_with_member["dev_headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "My Task"
    assert data[0]["assignee_id"] == project_with_member["developer_id"]

def test_update_task_status(project_with_member):
    """Test updating task status"""
    # Create a task
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "project_id": project_with_member["project_id"],
        "assignee_id": project_with_member["developer_id"]
    }
    create_response = client.post("/api/tasks/", json=task_data, headers=project_with_member["admin_headers"])
    task_id = create_response.json()["id"]
    
    # Update task status
    update_data = {
        "status": "in_progress"
    }
    response = client.put(f"/api/tasks/{task_id}", json=update_data, headers=project_with_member["dev_headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"

def test_add_task_comment(project_with_member):
    """Test adding a comment to a task"""
    # Create a task
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "project_id": project_with_member["project_id"],
        "assignee_id": project_with_member["developer_id"]
    }
    create_response = client.post("/api/tasks/", json=task_data, headers=project_with_member["admin_headers"])
    task_id = create_response.json()["id"]
    
    # Add comment
    comment_data = {
        "content": "This is a test comment"
    }
    response = client.post(f"/api/tasks/{task_id}/comments", json=comment_data, headers=project_with_member["dev_headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == comment_data["content"]
    assert data["author_name"] == "Developer User"

def test_get_task_comments(project_with_member):
    """Test getting task comments"""
    # Create a task
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "project_id": project_with_member["project_id"],
        "assignee_id": project_with_member["developer_id"]
    }
    create_response = client.post("/api/tasks/", json=task_data, headers=project_with_member["admin_headers"])
    task_id = create_response.json()["id"]
    
    # Add a comment
    comment_data = {
        "content": "This is a test comment"
    }
    client.post(f"/api/tasks/{task_id}/comments", json=comment_data, headers=project_with_member["dev_headers"])
    
    # Get comments
    response = client.get(f"/api/tasks/{task_id}/comments", headers=project_with_member["dev_headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == comment_data["content"]

def test_delete_task(project_with_member):
    """Test deleting a task"""
    # Create a task
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "project_id": project_with_member["project_id"],
        "assignee_id": project_with_member["developer_id"]
    }
    create_response = client.post("/api/tasks/", json=task_data, headers=project_with_member["admin_headers"])
    task_id = create_response.json()["id"]
    
    # Delete task
    response = client.delete(f"/api/tasks/{task_id}", headers=project_with_member["admin_headers"])
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify task is deleted
    get_response = client.get(f"/api/tasks/{task_id}", headers=project_with_member["admin_headers"])
    assert get_response.status_code == 404
