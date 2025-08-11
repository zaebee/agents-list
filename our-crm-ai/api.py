from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import CommandRequest, CommandResponse
import crm_service


class CommandExecutionError(Exception):
    pass


app = FastAPI(
    title="AI-CRM API",
    description="API for interacting with the AI-CRM and its team of agents.",
    version="1.0.0",
)


@app.exception_handler(CommandExecutionError)
async def command_execution_exception_handler(
    request: Request, exc: CommandExecutionError
):
    return JSONResponse(
        status_code=400,
        content={"message": f"Command execution failed: {exc}"},
    )


@app.get("/health", summary="Check API health")
async def health_check():
    """
    Returns a 200 OK response if the API is healthy.
    """
    return {"status": "ok"}


@app.post(
    "/api/command",
    response_model=CommandResponse,
    summary="Execute a natural language command",
)
async def execute_command(request: CommandRequest):
    """
    Receives and executes a natural language command.
    """
    try:
        result = crm_service.execute_command(request.command)
        return CommandResponse(response=result)
    except Exception as e:
        raise CommandExecutionError(str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
