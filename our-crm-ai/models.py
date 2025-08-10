from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    ARCHIVED = "Archived"


class TaskMetadata(BaseModel):
    """Metadata for a task."""
    priority: str = "medium"
    tags: List[str] = []
    dependencies: List[str] = []


class Task(BaseModel):
    """Core Task model."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: str = "medium"
    assigned_agent: Optional[str] = None
    column_id: Optional[str] = None
    board_id: Optional[str] = None
    stickers: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: TaskMetadata = Field(default_factory=TaskMetadata)


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    title: str
    description: str
    priority: str = "medium"
    assigned_agent: Optional[str] = None
    metadata: Optional[TaskMetadata] = None


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assigned_agent: Optional[str] = None
    priority: Optional[str] = None
    metadata: Optional[TaskMetadata] = None


class Agent(BaseModel):
    """Agent model."""
    name: str
    category: str
    keywords: List[str] = []
    specializations: List[str] = []
    current_workload: int = 0
    success_rate: float = 0.95
    average_response_time_hours: float = 4.0


class CRMConfiguration(BaseModel):
    """CRM configuration model."""
    project_id: str
    board_id: str
    columns: Dict[str, str]
    ai_owner_sticker: Dict[str, Any]
    api_base_url: str = "https://yougile.com/api-v2"
    default_timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    available_agents: Dict[str, Agent] = {}


class CRMStats(BaseModel):
    """CRM statistics model."""
    total_tasks: int
    tasks_by_status: Dict[TaskStatus, int]
    agent_workload: Dict[str, int]


class CommandRequest(BaseModel):
    """Request model for executing a command."""
    command: str


class CommandResponse(BaseModel):
    """Response model for executing a command."""
    response: str


class Risk(BaseModel):
    """Risk model."""
    id: str
    description: str
    severity: str  # e.g., "High", "Medium", "Low"
    project_id: str


class Project(BaseModel):
    """Project model."""
    id: str
    title: str
    description: str
    tasks: List[Task] = []
    risks: List[Risk] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    id: str
    title: str
    description: str


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    title: Optional[str] = None
    description: Optional[str] = None


class HandoffProtocol(BaseModel):
    """Defines the contract for handing off a task between agents."""
    from_agent: str
    to_agent: str
    required_artifacts: List[str] = Field(default_factory=list)
    validation_criteria: List[str] = Field(default_factory=list)
