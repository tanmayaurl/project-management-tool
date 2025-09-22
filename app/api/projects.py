from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.database.models import Project, User, ProjectMember, Task, TaskStatus
from app.auth import get_current_active_user, require_role
from app.database.models import UserRole, User as AuthUser
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    creator_id: int
    creator_name: str
    member_count: int
    task_count: int
    completed_tasks: int
    progress_percentage: float

    class Config:
        from_attributes = True

class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str = "member"

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Create a new project"""
    # Only managers and admins can create projects
    if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can create projects"
        )
    
    # Create project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        creator_id=current_user.id
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Add creator as project member
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)
    db.commit()
    
    return await get_project_response(project, db)

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get projects accessible to current user"""
    if current_user.role == UserRole.ADMIN:
        # Admin can see all projects
        projects = db.query(Project).offset(skip).limit(limit).all()
    else:
        # Regular users can only see projects they're members of
        projects = db.query(Project).join(ProjectMember).filter(
            ProjectMember.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    return [await get_project_response(project, db) for project in projects]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to this project
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return await get_project_response(project, db)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Update project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member or member.role not in ["owner", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return await get_project_response(project, db)

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Delete project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member or member.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can delete project"
            )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}

@router.post("/{project_id}/members")
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Add member to project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member or member.role not in ["owner", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Check if user is already a member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_data.user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project"
        )
    
    # Add member
    member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(member)
    db.commit()
    
    return {"message": "Member added successfully"}

@router.delete("/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Remove member from project"""
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member or member.role not in ["owner", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Find and remove member
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}

async def get_project_response(project: Project, db: Session) -> ProjectResponse:
    """Helper function to create project response with additional data"""
    # Get creator name
    creator = db.query(User).filter(User.id == project.creator_id).first()
    creator_name = creator.full_name if creator else "Unknown"
    
    # Get member count
    member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project.id).count()
    
    # Get task statistics
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    task_count = len(tasks)
    completed_tasks = len([task for task in tasks if task.status == TaskStatus.DONE])
    progress_percentage = (completed_tasks / task_count * 100) if task_count > 0 else 0
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
        updated_at=project.updated_at,
        creator_id=project.creator_id,
        creator_name=creator_name,
        member_count=member_count,
        task_count=task_count,
        completed_tasks=completed_tasks,
        progress_percentage=round(progress_percentage, 2)
    )
