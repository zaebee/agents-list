from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Comment:
    """Represents a comment in the CRM."""

    author: str
    text: str


@dataclass
class TaskContext:
    """Represents the complete state and details of a specific task from the CRM."""

    taskId: str
    title: str
    description: str
    owner: str
    status: str
    comments: List[Comment] = field(default_factory=list)
    relatedFiles: List[str] = field(default_factory=list)


@dataclass
class AgentActionContext:
    """Represents the context for an agent action, linking it to a task."""

    taskId: str


@dataclass
class AgentAction:
    """Represents an action requested by one agent from another."""

    actionName: str
    targetAgentRole: str
    parameters: Dict[str, Any]
    context: Optional[AgentActionContext] = None


@dataclass
class AgentResponse:
    """Represents the response from an agent after completing an action."""

    status: str  # "success" or "failure"
    message: str
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        if self.status not in ["success", "failure"]:
            raise ValueError("Status must be either 'success' or 'failure'")
