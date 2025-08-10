from pydantic import BaseModel

class CommandRequest(BaseModel):
    """Request model for executing a command."""
    command: str

class CommandResponse(BaseModel):
    """Response model for executing a command."""
    response: str