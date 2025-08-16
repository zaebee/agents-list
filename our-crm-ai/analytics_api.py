import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from analytics_engine import initialize_analytics

app = FastAPI(
    title="Analytics API",
    description="API for analytics and metrics collection",
    version="1.0.0",
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# Secure CORS configuration - only allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://crm.zae.life",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Initialize analytics engine
analytics_engine = initialize_analytics()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.get("/api/v1/analytics/task-completion", summary="Get task completion metrics")
async def get_task_completion_metrics():
    """
    Endpoint to retrieve task completion metrics

    Returns:
        JSON: Task completion analytics
    """
    try:
        # In a real scenario, you'd fetch tasks from a database or task management system
        sample_tasks = [
            {"status": "completed", "duration": 3600},
            {"status": "in_progress", "duration": 1800},
            {"status": "completed", "duration": 7200},
        ]
        metrics = analytics_engine.collect_task_completion_metrics(sample_tasks)
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving task completion metrics: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve metrics")


@app.get("/api/v1/analytics/agent-performance", summary="Get agent performance metrics")
async def get_agent_performance():
    """
    Endpoint to retrieve agent performance metrics

    Returns:
        JSON: Agent performance analytics
    """
    try:
        # In a real scenario, you'd fetch agent logs from a database
        sample_agent_logs = [
            {"agent_name": "CustomerSupportAgent", "status": "completed"},
            {"agent_name": "SalesAgent", "status": "in_progress"},
            {"agent_name": "CustomerSupportAgent", "status": "completed"},
        ]
        performance = analytics_engine.analyze_agent_performance(sample_agent_logs)
        return performance
    except Exception as e:
        logger.error(f"Error retrieving agent performance: {e}")
        raise HTTPException(
            status_code=500, detail="Unable to retrieve performance data"
        )


@app.get("/api/v1/analytics/executive-dashboard", summary="Get executive dashboard")
async def get_executive_dashboard():
    """
    Endpoint to retrieve executive-level dashboard

    Returns:
        JSON: High-level business metrics and insights
    """
    try:
        dashboard = analytics_engine.generate_executive_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Error generating executive dashboard: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate dashboard")


# FastAPI handles 404 and 500 errors automatically
# Custom error handlers can be added using exception handlers if needed


def create_analytics_app():
    """
    Create and configure FastAPI application for analytics

    Returns:
        FastAPI: Configured FastAPI application
    """
    return app


if __name__ == "__main__":
    import uvicorn

    analytics_app = create_analytics_app()
    # In production, use uvicorn or another ASGI server
    uvicorn.run(analytics_app, host="0.0.0.0", port=5000)
