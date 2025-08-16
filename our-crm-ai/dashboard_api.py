import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analytics_engine import AnalyticsEngine
from business_pm_gateway import BusinessPMGateway
from database import get_db_connection, init_database, init_default_users
from security import authenticate_user, create_access_token, get_current_user

# Initialize database
init_database()
init_default_users()

app = FastAPI(
    title="AI-CRM Dashboard API",
    description="API for the AI-CRM dashboard.",
    version="2.0.0",
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://zae.life:3000",
    "http://zae.life",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analytics_engine = AnalyticsEngine()
business_gateway = BusinessPMGateway()


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class Task(BaseModel):
    id: str
    description: str
    agent_id: str | None = None
    status: str


class TaskCreate(BaseModel):
    description: str
    agent_id: str | None = None


class LoginResponse(BaseModel):
    token: str
    user: User


@app.post("/api/auth/login", response_model=LoginResponse)
async def login_for_access_token(form_data: LoginRequest):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"token": access_token, "user": user}


@app.get("/api/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    return {"user": current_user}


@app.get("/api/executive-dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user)):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get total tasks
        cursor.execute("SELECT COUNT(*) as total_tasks FROM project_phases")
        total_tasks = cursor.fetchone()["total_tasks"]

        # Get completed tasks
        cursor.execute(
            "SELECT COUNT(*) as completed_tasks FROM project_phases WHERE status = 'completed'"
        )
        completed_tasks = cursor.fetchone()["completed_tasks"]

        # Get revenue
        cursor.execute(
            "SELECT SUM(target_revenue) as revenue FROM business_projects WHERE status = 'completed'"
        )
        revenue = cursor.fetchone()["revenue"] or 0

    return {
        "totalTasks": total_tasks,
        "completedTasks": completed_tasks,
        "revenue": revenue,
        "performance": 87,  # Placeholder
    }


@app.get("/api/health")
async def health_check():
    # In a real application, you would check if the config is loaded
    return {"status": "ok", "config_loaded": True}


@app.get("/api/agents")
async def list_agents(current_user: User = Depends(get_current_user)):
    # This is a placeholder. In a real application, this data would come from a database.
    agents = [
        {
            "id": "business-analyst",
            "name": "Business Analyst",
            "description": "Analyzes business requirements and stakeholder needs",
            "status": "available",
        },
        {
            "id": "backend-architect",
            "name": "Backend Architect",
            "description": "Designs system architecture and backend solutions",
            "status": "available",
        },
        {
            "id": "frontend-developer",
            "name": "Frontend Developer",
            "description": "Creates user interfaces and frontend solutions",
            "status": "available",
        },
    ]
    return {"agents": agents, "total": len(agents)}


@app.get("/api/agents/status")
async def agent_system_status(current_user: User = Depends(get_current_user)):
    return {"system_status": "ready", "active_agents": 3}


class AnalyzeRequest(BaseModel):
    task_description: str


@app.post("/api/agents/analyze")
async def analyze__task_for_agents(
    request: AnalyzeRequest, current_user: User = Depends(get_current_user)
):
    description_lower = request.task_description.lower()
    if "business" in description_lower:
        suggested_agent = "business-analyst"
    elif "backend" in description_lower:
        suggested_agent = "backend-architect"
    else:
        suggested_agent = "frontend-developer"
    return {"suggested_agent": suggested_agent}


class ExecuteRequest(BaseModel):
    agent_id: str
    task: str


@app.post("/api/agents/execute")
async def execute_agent_task(
    request: ExecuteRequest, current_user: User = Depends(get_current_user)
):
    # Placeholder for task execution
    return {"status": "success", "task_id": "123"}


@app.get("/api/tasks", response_model=list[Task])
async def get_tasks(current_user: User = Depends(get_current_user)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, phase_name as description, assigned_agent as agent_id, status FROM project_phases"
        )
        tasks = [dict(row) for row in cursor.fetchall()]
    return tasks


@app.post("/api/tasks", response_model=Task)
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        new_task_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO project_phases (id, phase_name, assigned_agent, status) VALUES (?, ?, ?, ?)",
            (new_task_id, task.description, task.agent_id, "pending"),
        )
        conn.commit()
    return {"id": new_task_id, **task.dict(), "status": "pending"}


@app.put("/api/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str, updates: dict, current_user: User = Depends(get_current_user)
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # This is a simplified update. A real application would have more robust logic.
        for key, value in updates.items():
            cursor.execute(
                f"UPDATE project_phases SET {key} = ? WHERE id = ?", (value, task_id)
            )
        conn.commit()
        cursor.execute(
            "SELECT id, phase_name as description, assigned_agent as agent_id, status FROM project_phases WHERE id = ?",
            (task_id,),
        )
        task = dict(cursor.fetchone())
    return task


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM project_phases WHERE id = ?", (task_id,))
        conn.commit()
    return {"status": "success"}


@app.post("/api/tasks/{task_id}/execute")
async def execute_task_by_id(
    task_id: str, current_user: User = Depends(get_current_user)
):
    # Placeholder
    return {"status": "executing", "task_id": task_id}


@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str, current_user: User = Depends(get_current_user)):
    # Placeholder
    return {"status": "paused", "task_id": task_id}


@app.post("/api/tasks/{task_id}/stop")
async def stop_task(task_id: str, current_user: User = Depends(get_current_user)):
    # Placeholder
    return {"status": "stopped", "task_id": task_id}


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    try:
        with open(file.filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    return {"filename": file.filename}
