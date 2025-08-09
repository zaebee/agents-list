#!/usr/bin/env python3
"""
FastAPI Web API for AI-CRM System
Provides RESTful endpoints for the existing CLI functionality.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json

# Add the CRM directory to Python path for imports
crm_path = Path(__file__).parent.parent.parent / "our-crm-ai"
sys.path.insert(0, str(crm_path))

try:
    from crm_enhanced import (
        load_config, make_api_request, validate_task_id, handle_api_error,
        suggest_owner_for_task
    )
    from agent_selector import suggest_agents, AGENT_KEYWORDS
    from pm_agent_gateway import PMAgentGateway
except ImportError as e:
    print(f"Error importing CRM modules: {e}")
    print("Please ensure the CRM system is properly set up")
    sys.exit(1)

# FastAPI app initialization
app = FastAPI(
    title="AI-CRM Web API",
    description="RESTful API for the AI-powered YouGile CRM system",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

# Global config - loaded at startup
config = None

@app.on_event("startup")
async def startup_event():
    """Load configuration on startup."""
    global config
    config = load_config()
    if not config:
        raise RuntimeError("Failed to load CRM configuration")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI-CRM Web API", 
        "version": "1.0.0",
        "description": "RESTful API for AI-powered task management"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "config_loaded": config is not None}

@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks():
    """List all tasks grouped by status."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")
    
    try:
        all_tasks = []
        
        # Get tasks from each column
        for column_name, column_id in config["columns"].items():
            params = {"columnId": column_id, "limit": 1000}
            response = make_api_request("GET", f"https://yougile.com/api-v2/task-list", params=params)
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
                    states_map = {v: k for k, v in owner_sticker_config.get("states", {}).items()}
                    owner = states_map.get(owner_state_id)
                
                all_tasks.append(TaskResponse(
                    id=task["id"],
                    title=task["title"],
                    description=task.get("description", ""),
                    column_name=column_name,
                    owner=owner
                ))
        
        return all_tasks
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

@app.post("/tasks", response_model=ApiResponse)
async def create_task(task_data: TaskCreate):
    """Create a new task with AI agent suggestions."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")
    
    try:
        todo_column_id = config["columns"].get("To Do")
        if not todo_column_id:
            raise HTTPException(status_code=500, detail="'To Do' column not found in configuration")

        task_payload = {
            "title": task_data.title,
            "description": task_data.description,
            "columnId": todo_column_id
        }

        # Handle AI Owner assignment
        owner = task_data.owner
        
        # If no owner specified and AI suggestion is enabled
        if not owner and not task_data.no_ai_suggest:
            suggested_owner = suggest_owner_for_task(task_data.title, task_data.description)
            if suggested_owner:
                owner = suggested_owner

        if owner:
            owner_sticker_config = config.get("ai_owner_sticker")
            if not owner_sticker_config:
                raise HTTPException(status_code=500, detail="AI owner sticker not configured")

            sticker_id = owner_sticker_config.get("id")
            owner_state_id = owner_sticker_config.get("states", {}).get(owner)

            if not owner_state_id:
                available_agents = list(owner_sticker_config.get("states", {}).keys())
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid owner '{owner}'. Available: {available_agents[:10]}"
                )

            task_payload["stickers"] = {sticker_id: owner_state_id}

        response = make_api_request("POST", "https://yougile.com/api-v2/tasks", json=task_payload)

        if response.status_code == 201:
            task_id = response.json().get("id")
            return ApiResponse(
                success=True,
                message=f"Task created successfully with ID: {task_id}",
                data={"task_id": task_id, "owner": owner}
            )
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to create task")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@app.put("/tasks/{task_id}/move", response_model=ApiResponse)
async def move_task(task_id: str, move_data: TaskMove):
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
                detail=f"Invalid column '{move_data.column}'. Available: {available_columns}"
            )

        update_data = {"columnId": target_column_id}
        response = make_api_request("PUT", f"https://yougile.com/api-v2/tasks/{task_id}", json=update_data)

        if response.status_code == 200:
            return ApiResponse(
                success=True,
                message=f"Task moved to '{move_data.column}' successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to move task")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving task: {str(e)}")

@app.put("/tasks/{task_id}", response_model=ApiResponse)
async def update_task(task_id: str, update_data: TaskUpdate):
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
            raise HTTPException(status_code=500, detail="AI owner sticker not configured")

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(update_data.owner)

        if not owner_state_id:
            available_agents = list(owner_sticker_config.get("states", {}).keys())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid owner '{update_data.owner}'. Available: {available_agents[:10]}"
            )

        task_payload = {"stickers": {sticker_id: owner_state_id}}
        response = make_api_request("PUT", f"https://yougile.com/api-v2/tasks/{task_id}", json=task_payload)

        if response.status_code == 200:
            return ApiResponse(
                success=True,
                message=f"Task assigned to '{update_data.owner}' successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to update task")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@app.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get detailed information about a specific task."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")
    
    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    try:
        # Get task details
        task_response = make_api_request("GET", f"https://yougile.com/api-v2/tasks/{task_id}")
        task_response.raise_for_status()
        task = task_response.json()

        # Extract owner
        owner = None
        owner_sticker_config = config.get("ai_owner_sticker", {})
        sticker_id = owner_sticker_config.get("id")
        task_stickers = task.get("stickers", {})

        if sticker_id and sticker_id in task_stickers:
            owner_state_id = task_stickers[sticker_id]
            states_map = {v: k for k, v in owner_sticker_config.get("states", {}).items()}
            owner = states_map.get(owner_state_id)

        # Get task comments
        comments = []
        chat_response = make_api_request("GET", f"https://yougile.com/api-v2/chats/{task_id}/messages")
        if chat_response.status_code == 200:
            messages = chat_response.json().get("content", [])
            comments = [{"text": msg.get("text", "")} for msg in reversed(messages)]

        return {
            "id": task.get("id"),
            "title": task.get("title"),
            "description": task.get("description", ""),
            "owner": owner,
            "comments": comments
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task details: {str(e)}")

@app.post("/tasks/{task_id}/comments", response_model=ApiResponse)
async def add_comment(task_id: str, comment_data: TaskComment):
    """Add a comment to a task."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")
    
    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    try:
        comment_payload = {"text": comment_data.message}
        response = make_api_request("POST", f"https://yougile.com/api-v2/chats/{task_id}/messages", json=comment_payload)

        if response.status_code == 201:
            return ApiResponse(
                success=True,
                message="Comment added successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to add comment")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

@app.get("/agents", response_model=List[str])
async def list_agents():
    """Get all available AI agents."""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")
    
    owner_sticker_config = config.get("ai_owner_sticker", {})
    agents = list(owner_sticker_config.get("states", {}).keys())
    return sorted(agents)

@app.post("/agents/suggest", response_model=List[AgentSuggestion])
async def suggest_agents_for_task(task_data: TaskCreate):
    """Get AI agent suggestions for a task."""
    try:
        combined_text = f"{task_data.title} {task_data.description}"
        suggestions = suggest_agents(combined_text, max_suggestions=5)
        
        return [
            AgentSuggestion(
                agent=s['agent'],
                confidence=s['confidence'],
                matched_keywords=s['matched_keywords'],
                reasoning=s['reasoning']
            )
            for s in suggestions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@app.post("/pm/analyze")
async def pm_analyze_task(task_data: TaskCreate):
    """Use PM Agent Gateway to analyze a task comprehensively."""
    try:
        pm_gateway = PMAgentGateway(str(crm_path / "config.json"))
        result = pm_gateway.create_managed_task(task_data.title, task_data.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PM analysis failed: {str(e)}")

if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("YOUGILE_API_KEY"):
        print("❌ Error: YOUGILE_API_KEY environment variable not set.")
        sys.exit(1)
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )