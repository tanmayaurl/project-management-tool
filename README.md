# Project Management Tool

### Full Name: Tanmaya Das
### Contact: tilottamadas184@gmail.com
### Submission Date: 21 September 2025

## 📝 Project Brief

This project is a simplified web application for managing software projects, built as a RESTful API. It includes core functionalities for project and task management, user roles, and basic reporting.

## 🚀 Tech Stack

- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL
- **Tools**: Postman, Git

## 📂 Functional Requirements

- **User Roles**: Admin, Project Manager, Developer with role-based access control.
- **Project Module**: CRUD operations for projects, team member assignment.
- **Task Module**: CRUD for tasks, status tracking (To Do, In Progress, Done), and deadlines.
- **Authentication**: JWT token-based security.
- **Reporting**: Endpoints for task counts by status and overdue tasks.
- **Bonus**: An AI-powered endpoint to generate user stories from a project description using the Groq API.

## 🔧 How to Run the Project

1.  **Clone the repository:**
    ```bash
    git clone 
    cd project-management-tool
    ```
2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    Create a `.env` file in the root directory and add your database and API keys.
    ```
    DATABASE_URL="postgresql://user:password@host:port/database"
    SECRET_KEY="your_jwt_secret_key"
    GROQ_API_KEY="your_groq_api_key"
    ```
5.  **Run the server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. You can access the auto-generated Swagger UI at `http://127.0.0.1:8000/docs`.

## 📌 API Endpoints Summary

-   **Users**: `POST /api/users/register`, `POST /api/users/login`, `GET /api/users/me`
-   **Projects**: `POST /api/projects/`, `GET /api/projects/`, `GET /api/projects/{id}`, `PUT /api/projects/{id}`, `DELETE /api/projects/{id}`
-   **Tasks**: `POST /api/tasks/`, `GET /api/tasks/`, `GET /api/tasks/{id}`, `PUT /api/tasks/{id}`, `DELETE /api/tasks/{id}`
-   **Reports**: `GET /api/reports/tasks-by-status/{project_id}`, `GET /api/reports/overdue-tasks`
-   **AI**: `POST /api/ai/generate-user-stories`

## 🔮 Assumptions & Improvements

-   **Assumptions**: This is a simplified prototype, so detailed features like advanced search, notifications, or a full-fledged commenting system were not implemented. Password hashing is used for security.
-   **Improvements**:
    -   Implement comprehensive unit and integration tests.
    -   Add a more detailed reporting dashboard.
    -   Create a real-time notification system for task updates.
    -   Containerize the application using Docker for easier deployment.
