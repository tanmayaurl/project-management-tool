from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models import Project, UserStory, ProjectMember, UserRole
from app.auth import get_current_active_user, User as AuthUser
from pydantic import BaseModel
import os
from groq import Groq
import json

router = APIRouter()

class ProjectDescription(BaseModel):
    project_description: str

class UserStoryResponse(BaseModel):
    id: int
    story: str
    created_at: str
    project_id: int

    class Config:
        from_attributes = True

class GenerateStoriesRequest(BaseModel):
    project_description: str
    project_id: int

class GenerateStoriesResponse(BaseModel):
    stories: List[str]
    project_id: int
    message: str

# Initialize Groq client
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print(f"Warning: GROQ API key not found. AI features will be disabled. Error: {e}")
    groq_client = None

async def generate_user_stories_with_ai(project_description: str) -> List[str]:
    """Generate user stories using GROQ AI"""
    if not groq_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available. Please configure GROQ_API_KEY."
        )
    
    try:
        prompt = f"""
        Generate detailed user stories for the following project description. 
        Return ONLY a JSON array of user stories in the format: "As a [role], I want to [action], so that [benefit]."
        
        Project Description: {project_description}
        
        Requirements:
        1. Generate 5-10 user stories
        2. Cover different user roles (customers, admins, managers, developers, etc.)
        3. Include both functional and non-functional requirements
        4. Make stories specific and actionable
        5. Return ONLY the JSON array, no other text
        
        Example format:
        [
            "As a customer, I want to browse products, so that I can choose what to buy.",
            "As an admin, I want to manage the product catalog, so that the website reflects correct inventory."
        ]
        """
        
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert product manager who creates detailed, actionable user stories. Always respond with valid JSON arrays only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            stories = json.loads(content)
            if isinstance(stories, list):
                return stories
            else:
                raise ValueError("Response is not a list")
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract stories from text
            lines = content.split('\n')
            stories = []
            for line in lines:
                line = line.strip()
                if line.startswith('"') and line.endswith('",') or line.startswith('"') and line.endswith('"'):
                    # Remove quotes and trailing comma
                    story = line.strip('"').rstrip(',')
                    if story.startswith('As a ') and ' so that ' in story:
                        stories.append(story)
            return stories if stories else ["As a user, I want to use this system, so that I can accomplish my goals."]
        
    except Exception as e:
        print(f"Error generating stories with AI: {e}")
        # Fallback to basic stories
        return [
            "As a user, I want to access the system, so that I can manage my projects.",
            "As a project manager, I want to create projects, so that I can organize work effectively.",
            "As a developer, I want to view assigned tasks, so that I can complete my work on time.",
            "As an admin, I want to manage users, so that I can control system access."
        ]

@router.post("/generate-user-stories", response_model=GenerateStoriesResponse)
async def generate_user_stories(
    request: GenerateStoriesRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Generate user stories for a project using AI"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to project
    if current_user.role != UserRole.ADMIN:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == request.project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Generate stories using AI
    stories = await generate_user_stories_with_ai(request.project_description)
    
    # Save stories to database
    saved_stories = []
    for story in stories:
        user_story = UserStory(
            story=story,
            project_id=request.project_id
        )
        db.add(user_story)
        saved_stories.append(story)
    
    db.commit()
    
    return GenerateStoriesResponse(
        stories=saved_stories,
        project_id=request.project_id,
        message=f"Successfully generated {len(saved_stories)} user stories"
    )

@router.get("/projects/{project_id}/user-stories", response_model=List[UserStoryResponse])
async def get_project_user_stories(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Get user stories for a project"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to project
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
    
    # Get user stories
    stories = db.query(UserStory).filter(UserStory.project_id == project_id).all()
    
    return [
        UserStoryResponse(
            id=story.id,
            story=story.story,
            created_at=story.created_at.isoformat(),
            project_id=story.project_id
        )
        for story in stories
    ]

@router.post("/generate-tasks-from-stories")
async def generate_tasks_from_stories(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user)
):
    """Generate tasks automatically from user stories (Optional bonus feature)"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to project
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
    
    # Get user stories
    stories = db.query(UserStory).filter(UserStory.project_id == project_id).all()
    
    if not stories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user stories found for this project"
        )
    
    # Generate tasks from stories (simplified implementation)
    created_tasks = []
    for story in stories:
        # Extract action from story
        if "I want to" in story.story:
            action_part = story.story.split("I want to")[1].split(" so that")[0].strip()
            task_title = f"Implement: {action_part}"
        else:
            task_title = f"Task for: {story.story[:50]}..."
        
        # Create task
        from app.database.models import Task, TaskStatus, Priority
        task = Task(
            title=task_title,
            description=f"Generated from user story: {story.story}",
            project_id=project_id,
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            creator_id=current_user.id
        )
        db.add(task)
        created_tasks.append(task_title)
    
    db.commit()
    
    return {
        "message": f"Successfully created {len(created_tasks)} tasks from user stories",
        "created_tasks": created_tasks
    }

@router.get("/health")
async def ai_health_check():
    """Check if AI service is available"""
    if groq_client:
        return {"status": "healthy", "ai_service": "available"}
    else:
        return {"status": "unavailable", "ai_service": "disabled", "message": "GROQ_API_KEY not configured"}
