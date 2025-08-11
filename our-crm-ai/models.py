from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    ARCHIVED = "Archived"


# DEPRECATED: These will be removed once the test suite is updated.
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EPIC = "epic"


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

    @validator("title")
    def title_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("title must not be empty")
        if len(v) > 200:
            raise ValueError("title must not be longer than 200 characters")
        return v


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
    max_concurrent_tasks: int = 5
    success_rate: float = 0.95
    average_response_time_hours: float = 4.0

    @property
    def is_available(self) -> bool:
        return self.current_workload < self.max_concurrent_tasks


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


# DEPRECATED: These will be removed once the test suite is updated.
class TaskResponse(BaseModel):
    success: bool
    task: Optional[Task] = None
    pm_analysis: Optional[Dict] = None
    agent_suggestions: Optional[List] = None


class AgentSuggestion(BaseModel):
    agent_name: str
    confidence: float
    reasoning: str
    matched_keywords: List[str] = []
    workload_factor: float = 1.0
    availability_status: str = "unknown"


class PMAnalysisRequest(BaseModel):
    title: str
    description: str
    auto_assign: bool = True


class PMAnalysisResult(BaseModel):
    task_type: str
    complexity: TaskComplexity
    priority: TaskPriority
    estimated_hours: float
    required_agents: List[str]
    recommended_agent: str
    subtasks: List[Dict]
    risk_factors: List[str]
    success_criteria: List[str]
    recommendation: str


class RoutingContext(BaseModel):
    task_priority: TaskPriority
    task_complexity: TaskComplexity
    estimated_hours: float
    previous_agent: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    deadline: Optional[datetime] = None
