#!/usr/bin/env python3
"""
FastAPI Web API for AI-CRM System
Provides RESTful endpoints for the existing CLI functionality.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import uvicorn
import logging

# Import authentication components
from database import create_tables, get_db, User, seed_default_data, SessionLocal
from auth import require_subscription_tier, require_feature_access, check_feature_access
from auth_routes import router as auth_router
from user_routes import router as user_router
from security import setup_security_middleware
from database import SubscriptionTier

# Add the CRM directory to Python path for imports
# In Docker container, this will be /app/crm, locally it's ../our-crm-ai
crm_path = (
    Path("/app/crm")
    if Path("/app/crm").exists()
    else Path(__file__).parent.parent.parent / "our-crm-ai"
)
sys.path.insert(0, str(crm_path))

try:
    from cli import load_config
    from api_client import make_api_request, handle_api_error
    from commands import validate_task_id, suggest_owner_for_task
    from agent_selector import suggest_agents, AGENT_KEYWORDS
    from pm_agent_gateway import PMAgentGateway
except ImportError as e:
    print(f"Error importing CRM modules: {e}")
    print("Please ensure the CRM system is properly set up")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="AI-CRM Web API",
    description="RESTful API for the AI-powered YouGile CRM system with authentication",
    version="2.0.0",
)

# Setup security middleware
setup_security_middleware(app)

# Include authentication and user management routers
app.include_router(auth_router)
app.include_router(user_router)


# Pydantic models for request/response
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    owner: Optional[str] = None
    no_ai_suggest: bool = False


class TaskUpdate(BaseModel):
    owner: Optional[str] = None


class TaskMove(BaseModel):
    column: str = Field(..., pattern="^(To Do|In Progress|Done)$")


class TaskComment(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class AgentSuggestion(BaseModel):
    agent: str
    confidence: float
    matched_keywords: List[str]
    reasoning: str


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    column_name: str
    owner: Optional[str] = None
    archived: bool = False


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None


# Global config - loaded at startup
config = None


@app.on_event("startup")
async def startup_event():
    """Load configuration and initialize database on startup."""
    global config

    try:
        # Initialize database
        logger.info("Creating database tables...")
        create_tables()

        # Seed default data
        db = SessionLocal()
        try:
            seed_default_data(db)
            logger.info("Database initialized successfully")
        finally:
            db.close()

        # Load CRM configuration
        config = load_config()
        if not config:
            raise RuntimeError("Failed to load CRM configuration")

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI-CRM Web API",
        "version": "1.0.0",
        "description": "RESTful API for AI-powered task management",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "config_loaded": config is not None}


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    archived: bool = False,
    current_user: User = Depends(require_feature_access("task_creation")),
    db=Depends(get_db),
):
    """List all tasks grouped by status."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    try:
        all_tasks = []

        # Get tasks from each column
        params = {
            "limit": 1000,
        }
        response = make_api_request(
            "GET", "https://yougile.com/api-v2/task-list", params=params
        )
        response.raise_for_status()

        tasks = response.json().get("content", [])
        for task in tasks:
            # Extract AI owner if present
            owner = None
            owner_sticker_config = config.get("ai_owner_sticker", {})
            sticker_id = owner_sticker_config.get("id")
            task_stickers = task.get("stickers", {})

            if sticker_id and sticker_id in task_stickers:
                owner_state_id = task_stickers[sticker_id]
                states_map = {
                    v: k for k, v in owner_sticker_config.get("states", {}).items()
                }
                owner = states_map.get(owner_state_id)

            # Map column ID to column name
            column_name = "Unknown"
            column_id = task.get("columnId")
            if column_id:
                for name, col_id in config["columns"].items():
                    if str(col_id) == str(column_id):
                        column_name = name
                        break

            all_tasks.append(
                TaskResponse(
                    id=task["id"],
                    title=task["title"],
                    description=task.get("description", ""),
                    column_name=column_name,
                    owner=owner,
                    archived=task.get("archived", False),
                )
            )

        # Filter tasks by archived status
        if archived:
            return [task for task in all_tasks if task.archived]
        else:
            return [task for task in all_tasks if not task.archived]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")


@app.post("/tasks", response_model=ApiResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(require_feature_access("task_creation")),
    db=Depends(get_db),
):
    """Create a new task with AI agent suggestions."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    # Check monthly task limits for free tier
    if current_user.subscription_tier == SubscriptionTier.FREE:
        # Reset monthly counter if needed
        from datetime import datetime, timezone

        current_date = datetime.now(timezone.utc)
        if (
            current_user.last_task_reset.month != current_date.month
            or current_user.last_task_reset.year != current_date.year
        ):
            current_user.monthly_tasks_created = 0
            current_user.last_task_reset = current_date
            db.commit()

        # Check if user has reached their monthly limit
        has_access = await check_feature_access(
            "task_creation", current_user, db, current_user.monthly_tasks_created + 1
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Monthly task limit reached. Upgrade to Pro for unlimited tasks.",
            )

    try:
        todo_column_id = config["columns"].get("To Do")
        if not todo_column_id:
            raise HTTPException(
                status_code=500, detail="'To Do' column not found in configuration"
            )

        task_payload = {
            "title": task_data.title,
            "description": task_data.description,
            "columnId": todo_column_id,
        }

        # Handle AI Owner assignment
        owner = task_data.owner

        # If no owner specified and AI suggestion is enabled
        if not owner and not task_data.no_ai_suggest:
            suggested_owner = suggest_owner_for_task(
                task_data.title, task_data.description
            )
            if suggested_owner:
                owner = suggested_owner

        if owner:
            owner_sticker_config = config.get("ai_owner_sticker")
            if not owner_sticker_config:
                raise HTTPException(
                    status_code=500, detail="AI owner sticker not configured"
                )

            sticker_id = owner_sticker_config.get("id")
            owner_state_id = owner_sticker_config.get("states", {}).get(owner)

            if not owner_state_id:
                available_agents = list(owner_sticker_config.get("states", {}).keys())
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid owner '{owner}'. Available: {available_agents[:10]}",
                )

            task_payload["stickers"] = {sticker_id: owner_state_id}

        response = make_api_request(
            "POST", "https://yougile.com/api-v2/tasks", json=task_payload
        )

        if response.status_code == 201:
            task_id = response.json().get("id")

            # Update user's monthly task counter
            current_user.monthly_tasks_created += 1
            db.commit()

            return ApiResponse(
                success=True,
                message=f"Task created successfully with ID: {task_id}",
                data={"task_id": task_id, "owner": owner},
            )
        else:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to create task"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


@app.put("/tasks/{task_id}/move", response_model=ApiResponse)
async def move_task(
    task_id: str,
    move_data: TaskMove,
    current_user: User = Depends(require_feature_access("task_creation")),
):
    """Move a task to a different column."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    try:
        target_column_id = config["columns"].get(move_data.column)
        if not target_column_id:
            available_columns = list(config["columns"].keys())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid column '{move_data.column}'. Available: {available_columns}",
            )

        update_data = {"columnId": target_column_id}
        response = make_api_request(
            "PUT", f"https://yougile.com/api-v2/tasks/{task_id}", json=update_data
        )

        if response.status_code == 200:
            return ApiResponse(
                success=True, message=f"Task moved to '{move_data.column}' successfully"
            )
        else:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to move task"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving task: {str(e)}")


@app.put("/tasks/{task_id}", response_model=ApiResponse)
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    current_user: User = Depends(require_feature_access("task_creation")),
):
    """Update a task (currently supports owner assignment)."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    if not update_data.owner:
        raise HTTPException(status_code=400, detail="No update data provided")

    try:
        owner_sticker_config = config.get("ai_owner_sticker")
        if not owner_sticker_config:
            raise HTTPException(
                status_code=500, detail="AI owner sticker not configured"
            )

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(update_data.owner)

        if not owner_state_id:
            available_agents = list(owner_sticker_config.get("states", {}).keys())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid owner '{update_data.owner}'. Available: {available_agents[:10]}",
            )

        task_payload = {"stickers": {sticker_id: owner_state_id}}
        response = make_api_request(
            "PUT", f"https://yougile.com/api-v2/tasks/{task_id}", json=task_payload
        )

        if response.status_code == 200:
            return ApiResponse(
                success=True,
                message=f"Task assigned to '{update_data.owner}' successfully",
            )
        else:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to update task"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")


@app.get("/tasks/{task_id}")
async def get_task_details(
    task_id: str, current_user: User = Depends(require_feature_access("task_creation"))
):
    """Get detailed information about a specific task."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    try:
        # Get task details
        task_response = make_api_request(
            "GET", f"https://yougile.com/api-v2/tasks/{task_id}"
        )
        task_response.raise_for_status()
        task = task_response.json()

        # Extract owner
        owner = None
        owner_sticker_config = config.get("ai_owner_sticker", {})
        sticker_id = owner_sticker_config.get("id")
        task_stickers = task.get("stickers", {})

        if sticker_id and sticker_id in task_stickers:
            owner_state_id = task_stickers[sticker_id]
            states_map = {
                v: k for k, v in owner_sticker_config.get("states", {}).items()
            }
            owner = states_map.get(owner_state_id)

        # Get task comments
        comments = []
        chat_response = make_api_request(
            "GET", f"https://yougile.com/api-v2/chats/{task_id}/messages"
        )
        if chat_response.status_code == 200:
            messages = chat_response.json().get("content", [])
            comments = [{"text": msg.get("text", "")} for msg in reversed(messages)]

        return {
            "id": task.get("id"),
            "title": task.get("title"),
            "description": task.get("description", ""),
            "owner": owner,
            "comments": comments,
            "archived": task.get("archived", False),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching task details: {str(e)}"
        )


@app.post("/tasks/{task_id}/comments", response_model=ApiResponse)
async def add_comment(
    task_id: str,
    comment_data: TaskComment,
    current_user: User = Depends(require_feature_access("task_creation")),
):
    """Add a comment to a task."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    try:
        comment_payload = {"text": comment_data.message}
        response = make_api_request(
            "POST",
            f"https://yougile.com/api-v2/chats/{task_id}/messages",
            json=comment_payload,
        )

        if response.status_code == 201:
            return ApiResponse(success=True, message="Comment added successfully")
        else:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to add comment"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")


@app.get("/agents", response_model=List[str])
async def list_agents(
    current_user: User = Depends(require_feature_access("ai_agent_access")),
    db=Depends(get_db),
):
    """Get all available AI agents based on subscription tier."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    owner_sticker_config = config.get("ai_owner_sticker", {})
    agents = list(owner_sticker_config.get("states", {}).keys())
    return sorted(agents)


@app.post("/agents/suggest", response_model=List[AgentSuggestion])
async def suggest_agents_for_task(
    task_data: TaskCreate,
    current_user: User = Depends(require_feature_access("ai_agent_access")),
):
    """Get AI agent suggestions for a task."""
    try:
        combined_text = f"{task_data.title} {task_data.description}"
        suggestions = suggest_agents(combined_text, max_suggestions=5)

        return [
            AgentSuggestion(
                agent=s["agent"],
                confidence=s["confidence"],
                matched_keywords=s["matched_keywords"],
                reasoning=s["reasoning"],
            )
            for s in suggestions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting suggestions: {str(e)}"
        )


@app.post("/pm/analyze")
async def pm_analyze_task(
    task_data: TaskCreate,
    current_user: User = Depends(require_subscription_tier(SubscriptionTier.PRO)),
):
    """Use PM Agent Gateway to analyze a task comprehensively (Pro+ only)."""
    try:
        # Try multiple config file locations
        config_files = [
            crm_path / "config_enhanced.json",
            crm_path / "config.json",
            crm_path / "config_dev.json",
        ]

        config_path = None
        for config_file in config_files:
            if config_file.exists():
                config_path = str(config_file)
                break

        if not config_path:
            raise Exception("No valid config file found")

        pm_gateway = PMAgentGateway(config_path)
        result = pm_gateway.create_managed_task(task_data.title, task_data.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PM analysis failed: {str(e)}")


@app.get("/analytics/task-completion")
async def get_task_completion_analytics(
    current_user: User = Depends(require_feature_access("analytics_dashboard")),
):
    """Get task completion analytics (Pro+ only)."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    try:
        # Get all tasks to analyze completion rates
        all_tasks = []
        for column_name, column_id in config["columns"].items():
            params = {"columnId": column_id, "limit": 1000}
            response = make_api_request(
                "GET", "https://yougile.com/api-v2/task-list", params=params
            )
            response.raise_for_status()

            tasks = response.json().get("content", [])
            for task in tasks:
                all_tasks.append({**task, "column_name": column_name})

        # Calculate statistics
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t["column_name"] == "Done"])
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return {
            "totalTasks": total_tasks,
            "completedTasks": completed_tasks,
            "completionRate": completion_rate,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch task completion analytics: {str(e)}",
        )


@app.get("/analytics/agent-performance")
async def get_agent_performance_analytics(
    current_user: User = Depends(require_feature_access("analytics_dashboard")),
):
    """Get agent performance analytics (Pro+ only)."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    try:
        # Get all tasks to analyze agent performance
        all_tasks = []
        for column_name, column_id in config["columns"].items():
            params = {"columnId": column_id, "limit": 1000}
            response = make_api_request(
                "GET", "https://yougile.com/api-v2/task-list", params=params
            )
            response.raise_for_status()

            tasks = response.json().get("content", [])
            for task in tasks:
                # Extract owner
                owner = None
                owner_sticker_config = config.get("ai_owner_sticker", {})
                sticker_id = owner_sticker_config.get("id")
                task_stickers = task.get("stickers", {})

                if sticker_id and sticker_id in task_stickers:
                    owner_state_id = task_stickers[sticker_id]
                    states_map = {
                        v: k for k, v in owner_sticker_config.get("states", {}).items()
                    }
                    owner = states_map.get(owner_state_id)

                if owner:
                    all_tasks.append(
                        {**task, "column_name": column_name, "owner": owner}
                    )

        # Calculate agent performance
        agent_performance = {}
        for task in all_tasks:
            agent = task.get("owner")
            if agent:
                if agent not in agent_performance:
                    agent_performance[agent] = {
                        "totalTasks": 0,
                        "completedTasks": 0,
                        "successRate": 0,
                    }

                agent_performance[agent]["totalTasks"] += 1
                if task["column_name"] == "Done":
                    agent_performance[agent]["completedTasks"] += 1

                agent_performance[agent]["successRate"] = (
                    agent_performance[agent]["completedTasks"]
                    / agent_performance[agent]["totalTasks"]
                    * 100
                )

        return agent_performance

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch agent performance analytics: {str(e)}",
        )


@app.get("/analytics/executive-dashboard")
async def get_executive_dashboard_analytics(
    current_user: User = Depends(
        require_subscription_tier(SubscriptionTier.ENTERPRISE)
    ),
):
    """Get executive dashboard analytics (Enterprise only)."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    try:
        # Get system overview
        available_agents = len(config.get("agents", {}).get("agent_configs", {}))
        active_integrations = 2  # YouGile + API
        system_health = 95  # Mock health percentage

        # Get agent performance for top performers
        agent_performance = await get_agent_performance_analytics()
        top_performing_agents = sorted(
            [(agent, data["successRate"]) for agent, data in agent_performance.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Calculate workflow efficiency (mock calculation)
        workflow_efficiency = 87.5

        # Get task completion rate
        task_completion = await get_task_completion_analytics()

        return {
            "systemOverview": {
                "totalAgents": available_agents,
                "activeIntegrations": active_integrations,
                "systemHealth": system_health,
            },
            "performanceKPIs": {
                "taskCompletionRate": task_completion["completionRate"],
                "topPerformingAgents": [
                    {"agent": agent, "successRate": rate}
                    for agent, rate in top_performing_agents
                ],
                "workflowEfficiency": workflow_efficiency,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch executive dashboard analytics: {str(e)}",
        )


@app.get("/analytics/export")
async def export_analytics(
    format: str = "csv",
    current_user: User = Depends(require_feature_access("analytics_dashboard")),
):
    """Export analytics data (Pro+ only)."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")

    try:
        # Get all analytics data
        task_completion = await get_task_completion_analytics()
        agent_performance = await get_agent_performance_analytics()
        executive_dashboard = await get_executive_dashboard_analytics()

        data = {
            "taskCompletion": task_completion,
            "agentPerformance": agent_performance,
            "executiveDashboard": executive_dashboard,
            "exportedAt": "2025-08-10T09:58:00Z",  # Current timestamp
        }

        if format == "json":
            from fastapi.responses import JSONResponse

            return JSONResponse(content=data)

        # For CSV format, flatten the data
        # This is a simplified CSV export - in production you'd want more sophisticated formatting
        import io
        import csv
        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers and data for task completion
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Tasks", task_completion["totalTasks"]])
        writer.writerow(["Completed Tasks", task_completion["completedTasks"]])
        writer.writerow(
            ["Completion Rate", f"{task_completion['completionRate']:.2f}%"]
        )
        writer.writerow([])  # Empty row

        # Write agent performance
        writer.writerow(["Agent", "Total Tasks", "Completed Tasks", "Success Rate"])
        for agent, data in agent_performance.items():
            writer.writerow(
                [
                    agent,
                    data["totalTasks"],
                    data["completedTasks"],
                    f"{data['successRate']:.2f}%",
                ]
            )

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=analytics_export.csv"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export analytics: {str(e)}"
        )


if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("YOUGILE_API_KEY"):
        print("❌ Error: YOUGILE_API_KEY environment variable not set.")
        sys.exit(1)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
