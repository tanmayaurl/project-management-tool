from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.database.models import Task, Project, User, TaskComment, TaskStatus, Priority, ProjectMember
from app.auth import get_current_active_user, require_role, UserRole, User as AuthUser
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    assignee_id: Optional[int] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskCommentCreate(BaseModel):
    content: str

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: Priority
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    project_id: int
    project_name: str
    assignee_id: Optional[int]
    assignee_name: Optional[str]
    creator_id: int
    creator_name: str
    comment_count: int

    class Config:
        from_attributes = True

class TaskCommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    author_id: int
    author_name: str

    class Config:
        from_attributes = True

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Create a new task"""
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to project
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task_data.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create tasks in this project"
            )
    
    # Check if assignee exists and has access to project
    if task_data.assignee_id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
        
        # Check if assignee is a member of the project
        if current_user.role != UserRole.ADMIN:
            assignee_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == task_data.project_id,
                ProjectMember.user_id == task_data.assignee_id
            ).first()
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee is not a member of this project"
                )
    
    # Create task
    task = Task(
        title=task_data.title,
        description=task_data.description,
        project_id=task_data.project_id,
        assignee_id=task_data.assignee_id,
        priority=task_data.priority,
        due_date=task_data.due_date,
        creator_id=current_user.id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return await get_task_response(task, db)

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get tasks with optional filters"""
    query = db.query(Task)
    
    # Apply filters
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if status:
        query = query.filter(Task.status == status)
    
    # If not admin, only show tasks from projects user is member of
    if current_user.role != UserRole.ADMIN:
        project_ids = db.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        ).subquery()
        query = query.filter(Task.project_id.in_(project_ids))
    
    tasks = query.offset(skip).limit(limit).all()
    return [await get_task_response(task, db) for task in tasks]

@router.get("/my-tasks", response_model=List[TaskResponse])
async def get_my_tasks(
    status: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get tasks assigned to current user"""
    query = db.query(Task).filter(Task.assignee_id == current_user.id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    return [await get_task_response(task, db) for task in tasks]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return await get_task_response(task, db)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Update task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        # Check if user is assignee, creator, or project member with manager role
        is_assignee = task.assignee_id == current_user.id
        is_creator = task.creator_id == current_user.id
        
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        is_manager = member and member.role in ["owner", "manager"]
        
        if not (is_assignee or is_creator or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Check if new assignee exists and has access to project
    if task_update.assignee_id:
        assignee = db.query(User).filter(User.id == task_update.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
        
        # Check if assignee is a member of the project
        if current_user.role != UserRole.ADMIN:
            assignee_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == task.project_id,
                ProjectMember.user_id == task_update.assignee_id
            ).first()
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee is not a member of this project"
                )
    
    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    return await get_task_response(task, db)

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Delete task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        # Only creator or project manager can delete
        is_creator = task.creator_id == current_user.id
        
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        is_manager = member and member.role in ["owner", "manager"]
        
        if not (is_creator or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

@router.post("/{task_id}/comments", response_model=TaskCommentResponse)
async def add_task_comment(
    task_id: int,
    comment_data: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Add comment to task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Create comment
    comment = TaskComment(
        content=comment_data.content,
        task_id=task_id,
        author_id=current_user.id
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return await get_comment_response(comment, db)

@router.get("/{task_id}/comments", response_model=List[TaskCommentResponse])
async def get_task_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get task comments"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).all()
    return [await get_comment_response(comment, db) for comment in comments]

async def get_task_response(task: Task, db: Session) -> TaskResponse:
    """Helper function to create task response with additional data"""
    # Get project name
    project = db.query(Project).filter(Project.id == task.project_id).first()
    project_name = project.name if project else "Unknown"
    
    # Get assignee name
    assignee_name = None
    if task.assignee_id:
        assignee = db.query(User).filter(User.id == task.assignee_id).first()
        assignee_name = assignee.full_name if assignee else "Unknown"
    
    # Get creator name
    creator = db.query(User).filter(User.id == task.creator_id).first()
    creator_name = creator.full_name if creator else "Unknown"
    
    # Get comment count
    comment_count = db.query(TaskComment).filter(TaskComment.task_id == task.id).count()
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        created_at=task.created_at,
        updated_at=task.updated_at,
        project_id=task.project_id,
        project_name=project_name,
        assignee_id=task.assignee_id,
        assignee_name=assignee_name,
        creator_id=task.creator_id,
        creator_name=creator_name,
        comment_count=comment_count
    )

async def get_comment_response(comment: TaskComment, db: Session) -> TaskCommentResponse:
    """Helper function to create comment response with additional data"""
    # Get author name
    author = db.query(User).filter(User.id == comment.author_id).first()
    author_name = author.full_name if author else "Unknown"
    
    return TaskCommentResponse(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        author_id=comment.author_id,
        author_name=author_name
    )
