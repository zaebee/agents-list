#!/usr/bin/env python3
"""
AI-CRM Data Models
Pydantic models for type safety and validation across the CRM system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EPIC = "epic"


class AgentCategory(str, Enum):
    """AI agent category classification."""
    PROGRAMMING = "programming"
    FRONTEND_MOBILE = "frontend_mobile"
    ARCHITECTURE_BACKEND = "architecture_backend"
    INFRASTRUCTURE_DEVOPS = "infrastructure_devops"
    DATA_AI = "data_ai"
    SECURITY_QUALITY = "security_quality"
    DOCUMENTATION = "documentation"
    BUSINESS_SUPPORT = "business_support"
    SPECIALIZED = "specialized"


class Agent(BaseModel):
    """AI Agent model with capabilities and metadata."""
    name: str = Field(..., description="Agent name/identifier")
    category: AgentCategory = Field(..., description="Agent category")
    keywords: List[str] = Field(default_factory=list, description="Capability keywords")
    specializations: List[str] = Field(default_factory=list, description="Specific specializations")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence for assignment")
    average_response_time_hours: float = Field(default=8.0, gt=0, description="Average task completion time")
    success_rate: float = Field(default=0.95, ge=0.0, le=1.0, description="Historical success rate")
    current_workload: int = Field(default=0, ge=0, description="Current number of assigned tasks")
    max_concurrent_tasks: int = Field(default=5, gt=0, description="Maximum concurrent task capacity")
    is_available: bool = Field(default=True, description="Agent availability status")
    
    @property
    def workload_percentage(self) -> float:
        """Calculate current workload as percentage of capacity."""
        return (self.current_workload / self.max_concurrent_tasks) * 100
    
    @property
    def is_overloaded(self) -> bool:
        """Check if agent is at or over capacity."""
        return self.current_workload >= self.max_concurrent_tasks


class TaskSticker(BaseModel):
    """Task sticker/label configuration."""
    sticker_id: str = Field(..., description="YouGile sticker ID")
    state_id: str = Field(..., description="Sticker state ID")
    label: str = Field(..., description="Human-readable label")


class TaskMetadata(BaseModel):
    """Task metadata and enrichment data."""
    source: Optional[str] = Field(None, description="Task source (manual, github, slack, etc.)")
    source_id: Optional[str] = Field(None, description="External source identifier")
    source_url: Optional[str] = Field(None, description="Link to original source")
    tags: List[str] = Field(default_factory=list, description="Custom tags")
    business_value: Optional[str] = Field(None, description="Business value assessment")
    effort_estimate_hours: Optional[float] = Field(None, gt=0, description="Effort estimate in hours")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")


class Task(BaseModel):
    """Core Task model with full CRM integration."""
    id: Optional[str] = Field(None, description="YouGile task ID")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(default="", max_length=10000, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Current task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    complexity: Optional[TaskComplexity] = Field(None, description="Analyzed complexity")
    
    # Agent assignment
    assigned_agent: Optional[str] = Field(None, description="Assigned AI agent name")
    assignment_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Assignment confidence score")
    suggested_agents: List[str] = Field(default_factory=list, description="Alternative agent suggestions")
    
    # Column/Board management
    column_id: Optional[str] = Field(None, description="YouGile column ID")
    board_id: Optional[str] = Field(None, description="YouGile board ID")
    
    # Stickers and labels
    stickers: Dict[str, str] = Field(default_factory=dict, description="YouGile stickers (sticker_id -> state_id)")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Metadata
    metadata: TaskMetadata = Field(default_factory=TaskMetadata, description="Additional task metadata")
    
    @field_validator('assigned_agent')
    @classmethod
    def validate_assigned_agent(cls, v):
        """Validate assigned agent name format."""
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Agent name must be alphanumeric with hyphens/underscores")
        return v
    
    @model_validator(mode='before')
    @classmethod
    def validate_completion(cls, values):
        """Validate completion logic."""
        if isinstance(values, dict):
            status = values.get('status')
            completed_at = values.get('completed_at')
            
            if status == TaskStatus.DONE and not completed_at:
                values['completed_at'] = datetime.utcnow()
            elif status != TaskStatus.DONE and completed_at:
                values['completed_at'] = None
        
        return values


class CRMConfiguration(BaseModel):
    """CRM configuration model with validation."""
    # YouGile API configuration
    project_id: UUID = Field(..., description="YouGile project ID")
    board_id: UUID = Field(..., description="YouGile board ID")
    api_base_url: str = Field(default="https://yougile.com/api-v2", description="YouGile API base URL")
    
    # Column configuration
    columns: Dict[str, UUID] = Field(..., description="Column name to UUID mapping")
    
    # AI Owner sticker configuration  
    ai_owner_sticker: Dict[str, Any] = Field(..., description="AI owner sticker configuration")
    
    # Agent configuration
    available_agents: Dict[str, Agent] = Field(default_factory=dict, description="Available AI agents")
    
    # System settings
    default_timeout_seconds: int = Field(default=30, gt=0, description="Default API timeout")
    max_retries: int = Field(default=3, ge=0, description="Maximum API retry attempts")
    retry_delay_seconds: float = Field(default=1.0, gt=0, description="Retry delay")
    
    @field_validator('columns')
    @classmethod
    def validate_required_columns(cls, v):
        """Ensure required columns exist."""
        required = {'To Do', 'In Progress', 'Done'}
        if not required.issubset(set(v.keys())):
            missing = required - set(v.keys())
            raise ValueError(f"Missing required columns: {missing}")
        return v
    
    @field_validator('api_base_url')
    @classmethod
    def validate_api_url(cls, v):
        """Validate API URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("API URL must start with http:// or https://")
        return v.rstrip('/')


class TaskCreateRequest(BaseModel):
    """Request model for task creation."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    assigned_agent: Optional[str] = Field(None)
    use_pm_analysis: bool = Field(default=True, description="Use PM Gateway for analysis")
    auto_assign: bool = Field(default=True, description="Auto-assign optimal agent")
    metadata: Optional[TaskMetadata] = Field(default_factory=TaskMetadata)


class TaskUpdateRequest(BaseModel):
    """Request model for task updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = Field(None)
    priority: Optional[TaskPriority] = Field(None)
    assigned_agent: Optional[str] = Field(None)
    metadata: Optional[TaskMetadata] = Field(None)


class TaskResponse(BaseModel):
    """Response model for task operations."""
    task: Optional[Task] = Field(None, description="Task data")
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    pm_analysis: Optional['PMAnalysisResult'] = Field(None, description="PM analysis results")
    agent_suggestions: List['AgentSuggestion'] = Field(default_factory=list, description="Agent suggestions")


class AgentSuggestion(BaseModel):
    """Agent suggestion with confidence and reasoning."""
    agent_name: str = Field(..., description="Suggested agent name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Suggestion reasoning")
    matched_keywords: List[str] = Field(default_factory=list, description="Matched capability keywords")
    workload_factor: float = Field(default=1.0, description="Workload adjustment factor")
    availability_status: str = Field(default="available", description="Agent availability")


class AgentSuggestionResponse(BaseModel):
    """Response for agent suggestion requests."""
    suggestions: List[AgentSuggestion] = Field(..., description="Ordered agent suggestions")
    task_analysis: Dict[str, Any] = Field(default_factory=dict, description="Task analysis metadata")
    recommendation: str = Field(..., description="Primary recommendation")


class PMAnalysisRequest(BaseModel):
    """PM Gateway analysis request."""
    title: str = Field(..., min_length=1)
    description: str = Field(default="")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    auto_assign: bool = Field(default=True)


class PMAnalysisResult(BaseModel):
    """PM Gateway analysis result."""
    task_type: str = Field(..., description="Analysis result type")
    complexity: TaskComplexity = Field(..., description="Analyzed complexity")
    priority: TaskPriority = Field(..., description="Recommended priority")
    estimated_hours: float = Field(..., gt=0, description="Effort estimate")
    required_agents: List[str] = Field(..., description="Required agent types")
    recommended_agent: Optional[str] = Field(None, description="Primary agent recommendation")
    subtasks: List[Dict[str, Any]] = Field(default_factory=list, description="Decomposed subtasks")
    risk_factors: List[str] = Field(default_factory=list, description="Risk assessment")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")
    recommendation: str = Field(..., description="Analysis recommendation")


class CRMStats(BaseModel):
    """CRM system statistics."""
    total_tasks: int = Field(default=0, ge=0)
    tasks_by_status: Dict[TaskStatus, int] = Field(default_factory=dict)
    tasks_by_priority: Dict[TaskPriority, int] = Field(default_factory=dict)
    tasks_by_agent: Dict[str, int] = Field(default_factory=dict)
    average_completion_time_hours: Optional[float] = Field(None, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    most_active_agents: List[str] = Field(default_factory=list)
    system_health: str = Field(default="unknown", description="Overall system health")


class APIError(BaseModel):
    """API error response model."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
