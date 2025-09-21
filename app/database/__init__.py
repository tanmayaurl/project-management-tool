from .session import engine, Base, get_db
from .models import User, Project, Task, TaskComment, ProjectMember, UserStory, UserRole, TaskStatus, Priority

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)
