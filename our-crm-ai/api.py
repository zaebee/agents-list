from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from models import CommandRequest, CommandResponse
import crm_service
from dashboard_api import app as dashboard_app
from billing_api import router as billing_router
from auth_routes import router as auth_router
from auth import get_current_user, require_feature_access
from auth_database import create_tables, seed_default_data, SessionLocal


class CommandExecutionError(Exception):
    pass


app = FastAPI(
    title="AI-CRM API",
    description="API for interacting with the AI-CRM and its team of agents.",
    version="1.0.0",
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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and seed default data."""
    create_tables()
    db = SessionLocal()
    try:
        seed_default_data(db)
    finally:
        db.close()

# Include routers
app.include_router(auth_router)
app.include_router(billing_router)
app.mount("/dashboard", dashboard_app)


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
async def execute_command(
    request: CommandRequest,
    current_user: dict = Depends(require_feature_access("command_execution"))
):
    """
    Receives and executes a natural language command.
    Requires authentication and command_execution feature access.
    """
    try:
        result = crm_service.execute_command(request.command)
        return CommandResponse(response=result)
    except Exception as e:
        raise CommandExecutionError(str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
