# Project Management Tool

A modern Project Management Tool with FastAPI backend, PostgreSQL (or SQLite for dev), JWT auth, role-based authorization (Admin/Manager/Developer), and a React frontend. Includes an AI-powered User Story generator via Groq.

## Features
- Users: register/login, roles (admin/manager/developer)
- Projects: CRUD, members, progress
- Tasks: CRUD, assignee, status, due dates, comments
- Dashboard: metrics and charts
- AI: generate user stories with Groq and save to project
- RESTful design, clean architecture, tests, and docs

## Tech Stack
- Backend: FastAPI (Python), SQLAlchemy, Alembic, JWT (python-jose), Pydantic v2
- DB: PostgreSQL (prod) / SQLite (dev quickstart)
- Frontend: React + React Query + TailwindCSS
- AI: Groq API (optional)

## Quickstart (Windows PowerShell)

1) Python venv and deps
```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Environment
Create a `.env` in the repo root:
```
# Database
DATABASE_URL=sqlite:///./dev.db

# JWT
SECRET_KEY=change-this-in-prod
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI (optional)
GROQ_API_KEY=your_groq_api_key
```

3) Run backend
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs at http://localhost:8000/api/docs

4) Frontend
```powershell
cd frontend
npm install
# Create frontend/.env
# REACT_APP_API_URL=http://localhost:8000
npm start
```
UI at http://localhost:3000

## Roles & Permissions
- Admin: manage all users/projects/tasks
- Manager: create/edit projects, assign tasks
- Developer: view assigned tasks, update status, comment

## API Overview
- Auth
  - POST `/api/auth/register`
  - POST `/api/auth/login`
- Users
  - GET `/api/users` (admin)
  - GET `/api/users/me`
  - PUT `/api/users/{id}`
  - DELETE `/api/users/{id}` (admin)
- Projects
  - POST `/api/projects/` (admin/manager)
  - GET `/api/projects/`
  - GET `/api/projects/{id}`
  - PUT `/api/projects/{id}`
  - DELETE `/api/projects/{id}`
  - POST `/api/projects/{id}/members`
- Tasks
  - POST `/api/tasks/`
  - GET `/api/tasks`
  - GET `/api/tasks/my-tasks`
  - GET `/api/tasks/{id}`
  - PUT `/api/tasks/{id}`
  - DELETE `/api/tasks/{id}`
  - POST `/api/tasks/{id}/comments`
  - GET `/api/tasks/{id}/comments`
- AI
  - POST `/api/ai/generate-user-stories`
  - GET `/api/ai/projects/{project_id}/user-stories`
  - POST `/api/ai/generate-tasks-from-stories`

Import `_deliverables/postman_collection.json` in Postman for ready-made requests.

## Testing
```powershell
pytest -q
```

## Docker (Backend + Postgres)
1) Create `.env` with Postgres connection:
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/pmtool
SECRET_KEY=change-in-prod
ACCESS_TOKEN_EXPIRE_MINUTES=60
GROQ_API_KEY=your_groq_api_key
```

2) Run
```powershell
docker compose up --build
```
- API: http://localhost:8000
- Swagger: http://localhost:8000/api/docs

## Notes
- For production, use Postgres and set a strong `SECRET_KEY`.
- Set `GROQ_API_KEY` to enable AI features.
- CORS is wide open for dev; restrict in prod.

## Author
Your Name — Contact in README.
