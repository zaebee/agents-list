#!/usr/bin/env python3
"""
Production Monitoring System - AI Project Manager

Comprehensive monitoring, metrics collection, and alerting system
for production deployment with health checks and performance tracking.

Features:
- Application performance monitoring (APM)
- Database connection monitoring
- Agent performance tracking
- Custom business metrics
- Prometheus metrics export
- Health check endpoints
- Alert management
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
import os
import time
from typing import Any

import aioredis
from dotenv import load_dotenv
from flask import Flask, Response, jsonify
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
import psutil

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for a component."""

    name: str
    status: str  # healthy, unhealthy, degraded
    last_check: datetime
    details: dict[str, Any]
    response_time_ms: float = 0


class MetricsCollector:
    """Prometheus metrics collector for AI Project Manager."""

    def __init__(self):
        # Application metrics
        self.http_requests_total = Counter(
            "aipm_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )

        self.http_request_duration = Histogram(
            "aipm_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
        )

        # Database metrics
        self.db_connections_active = Gauge(
            "aipm_db_connections_active", "Active database connections"
        )

        self.db_query_duration = Histogram(
            "aipm_db_query_duration_seconds", "Database query duration", ["query_type"]
        )

        self.db_query_errors = Counter(
            "aipm_db_query_errors_total", "Database query errors", ["error_type"]
        )

        # Agent metrics
        self.agent_tasks_total = Counter(
            "aipm_agent_tasks_total", "Total agent tasks", ["agent_id", "status"]
        )

        self.agent_task_duration = Histogram(
            "aipm_agent_task_duration_seconds", "Agent task duration", ["agent_id"]
        )

        self.agent_cost_total = Counter(
            "aipm_agent_cost_total",
            "Total agent costs in USD",
            ["agent_id", "provider"],
        )

        self.agent_quality_score = Gauge(
            "aipm_agent_quality_score", "Agent quality score", ["agent_id"]
        )

        # Business metrics
        self.projects_total = Gauge("aipm_projects_total", "Total projects", ["status"])

        self.project_value = Gauge(
            "aipm_project_value_usd",
            "Project value in USD",
            ["project_id", "metric_type"],
        )

        self.roi_percentage = Gauge(
            "aipm_roi_percentage", "Project ROI percentage", ["project_id"]
        )

        # System metrics
        self.system_cpu_usage = Gauge(
            "aipm_system_cpu_usage_percent", "System CPU usage percentage"
        )

        self.system_memory_usage = Gauge(
            "aipm_system_memory_usage_bytes", "System memory usage in bytes"
        )

        self.system_disk_usage = Gauge(
            "aipm_system_disk_usage_bytes", "System disk usage in bytes"
        )

        # Application info
        self.app_info = Info("aipm_application_info", "Application information")

        # Set application info
        self.app_info.info(
            {
                "version": "2.0.0",
                "environment": os.getenv("FLASK_ENV", "development"),
                "deployment_date": datetime.now().isoformat(),
            }
        )

    def record_http_request(
        self, method: str, endpoint: str, status: int, duration: float
    ):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status=str(status)
        ).inc()

        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_db_query(self, query_type: str, duration: float, error: str = None):
        """Record database query metrics."""
        self.db_query_duration.labels(query_type=query_type).observe(duration)

        if error:
            self.db_query_errors.labels(error_type=error).inc()

    def record_agent_task(
        self,
        agent_id: str,
        status: str,
        duration: float,
        cost: float,
        quality: float,
        provider: str,
    ):
        """Record agent task metrics."""
        self.agent_tasks_total.labels(agent_id=agent_id, status=status).inc()
        self.agent_task_duration.labels(agent_id=agent_id).observe(duration)
        self.agent_cost_total.labels(agent_id=agent_id, provider=provider).inc(cost)
        self.agent_quality_score.labels(agent_id=agent_id).set(quality)

    def update_business_metrics(
        self,
        projects_by_status: dict[str, int],
        project_values: dict[str, dict[str, float]],
    ):
        """Update business metrics."""
        # Update project counts
        for status, count in projects_by_status.items():
            self.projects_total.labels(status=status).set(count)

        # Update project values and ROI
        for project_id, values in project_values.items():
            if "estimated_cost" in values:
                self.project_value.labels(
                    project_id=project_id, metric_type="cost"
                ).set(values["estimated_cost"])
            if "target_revenue" in values:
                self.project_value.labels(
                    project_id=project_id, metric_type="revenue"
                ).set(values["target_revenue"])
            if "projected_roi" in values:
                self.roi_percentage.labels(project_id=project_id).set(
                    values["projected_roi"]
                )

    def update_system_metrics(self):
        """Update system resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.system_cpu_usage.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.system_memory_usage.set(memory.used)

        # Disk usage
        disk = psutil.disk_usage("/")
        self.system_disk_usage.set(disk.used)

    def update_db_connections(self, active_connections: int):
        """Update database connection metrics."""
        self.db_connections_active.set(active_connections)


class HealthChecker:
    """Health check system for all components."""

    def __init__(self):
        self.health_status: dict[str, HealthStatus] = {}
        self.redis_client = None

    async def initialize(self):
        """Initialize health checker."""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = await aioredis.from_url(redis_url)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")

    async def check_database_health(self) -> HealthStatus:
        """Check PostgreSQL database health."""
        try:
            from postgres_manager import db_manager

            start_time = time.time()
            health_data = await db_manager.health_check()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus(
                name="database",
                status="healthy" if health_data["status"] == "healthy" else "unhealthy",
                last_check=datetime.now(),
                details=health_data,
                response_time_ms=response_time,
            )

        except Exception as e:
            status = HealthStatus(
                name="database",
                status="unhealthy",
                last_check=datetime.now(),
                details={"error": str(e)},
                response_time_ms=0,
            )

        self.health_status["database"] = status
        return status

    async def check_redis_health(self) -> HealthStatus:
        """Check Redis cache health."""
        try:
            if not self.redis_client:
                raise Exception("Redis client not initialized")

            start_time = time.time()
            await self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus(
                name="redis",
                status="healthy",
                last_check=datetime.now(),
                details={"ping": "success"},
                response_time_ms=response_time,
            )

        except Exception as e:
            status = HealthStatus(
                name="redis",
                status="unhealthy",
                last_check=datetime.now(),
                details={"error": str(e)},
                response_time_ms=0,
            )

        self.health_status["redis"] = status
        return status

    async def check_agent_health(self) -> HealthStatus:
        """Check AI agents health."""
        try:
            from agent_integration_framework import agent_framework

            start_time = time.time()
            health_results = await agent_framework.health_check_all_agents()
            response_time = (time.time() - start_time) * 1000

            healthy_agents = sum(
                1 for is_healthy in health_results.values() if is_healthy
            )
            total_agents = len(health_results)

            status_value = "healthy" if healthy_agents > 0 else "unhealthy"
            if 0 < healthy_agents < total_agents:
                status_value = "degraded"

            status = HealthStatus(
                name="agents",
                status=status_value,
                last_check=datetime.now(),
                details={
                    "healthy_agents": healthy_agents,
                    "total_agents": total_agents,
                    "agent_status": health_results,
                },
                response_time_ms=response_time,
            )

        except Exception as e:
            status = HealthStatus(
                name="agents",
                status="unhealthy",
                last_check=datetime.now(),
                details={"error": str(e)},
                response_time_ms=0,
            )

        self.health_status["agents"] = status
        return status

    async def check_system_health(self) -> HealthStatus:
        """Check system resource health."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Determine overall status
            status_value = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status_value = "unhealthy"
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                status_value = "degraded"

            status = HealthStatus(
                name="system",
                status=status_value,
                last_check=datetime.now(),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "uptime": time.time() - psutil.boot_time(),
                },
                response_time_ms=0,
            )

        except Exception as e:
            status = HealthStatus(
                name="system",
                status="unhealthy",
                last_check=datetime.now(),
                details={"error": str(e)},
                response_time_ms=0,
            )

        self.health_status["system"] = status
        return status

    async def check_all_health(self) -> dict[str, HealthStatus]:
        """Check health of all components."""
        checks = [
            self.check_database_health(),
            self.check_redis_health(),
            self.check_agent_health(),
            self.check_system_health(),
        ]

        await asyncio.gather(*checks, return_exceptions=True)
        return self.health_status

    def get_overall_health(self) -> str:
        """Get overall system health status."""
        if not self.health_status:
            return "unknown"

        statuses = [status.status for status in self.health_status.values()]

        if all(status == "healthy" for status in statuses):
            return "healthy"
        elif any(status == "unhealthy" for status in statuses):
            return "unhealthy"
        else:
            return "degraded"


class ProductionMonitoring:
    """Main production monitoring system."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        self.start_time = datetime.now()

    async def initialize(self):
        """Initialize monitoring system."""
        await self.health_checker.initialize()
        logger.info("Production monitoring system initialized")

    async def collect_metrics_periodically(self):
        """Collect metrics periodically in background."""
        while True:
            try:
                # Update system metrics
                self.metrics.update_system_metrics()

                # Update business metrics (if database is available)
                try:
                    from postgres_manager import db_manager

                    dashboard_data = await db_manager.get_executive_dashboard_data()

                    # Extract metrics
                    projects_by_status = dashboard_data.get(
                        "project_status_breakdown", {}
                    )
                    project_values = {}

                    for project in dashboard_data.get("recent_projects", []):
                        project_values[project["id"]] = {
                            "estimated_cost": project.get("estimated_cost", 0) or 0,
                            "target_revenue": project.get("target_revenue", 0) or 0,
                            "projected_roi": project.get("projected_roi", 0) or 0,
                        }

                    self.metrics.update_business_metrics(
                        projects_by_status, project_values
                    )

                except Exception as e:
                    logger.warning(f"Failed to collect business metrics: {e}")

                # Health checks
                await self.health_checker.check_all_health()

                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def create_monitoring_app(self) -> Flask:
        """Create Flask app for monitoring endpoints."""
        app = Flask(__name__)

        @app.route("/metrics")
        def metrics_endpoint():
            """Prometheus metrics endpoint."""
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

        @app.route("/health")
        def health_endpoint():
            """Simple health check endpoint."""
            overall_health = self.health_checker.get_overall_health()
            status_code = 200 if overall_health == "healthy" else 503

            return jsonify(
                {
                    "status": overall_health,
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": (
                        datetime.now() - self.start_time
                    ).total_seconds(),
                }
            ), status_code

        @app.route("/health/detailed")
        def detailed_health_endpoint():
            """Detailed health check endpoint."""
            overall_health = self.health_checker.get_overall_health()
            status_code = 200 if overall_health == "healthy" else 503

            health_details = {}
            for name, status in self.health_checker.health_status.items():
                health_details[name] = {
                    "status": status.status,
                    "last_check": status.last_check.isoformat(),
                    "response_time_ms": status.response_time_ms,
                    "details": status.details,
                }

            return jsonify(
                {
                    "overall_status": overall_health,
                    "components": health_details,
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": (
                        datetime.now() - self.start_time
                    ).total_seconds(),
                }
            ), status_code

        @app.route("/metrics/business")
        def business_metrics_endpoint():
            """Business-specific metrics endpoint."""
            try:
                # This would integrate with your actual business analytics
                return jsonify(
                    {
                        "projects": {
                            "total": 0,  # Would be populated from database
                            "active": 0,
                            "completed": 0,
                        },
                        "agents": {
                            "total_tasks": 0,
                            "success_rate": 0.0,
                            "average_cost": 0.0,
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        return app


# Global monitoring instance
monitoring_system = ProductionMonitoring()


async def initialize_monitoring():
    """Initialize the monitoring system."""
    await monitoring_system.initialize()

    # Start background metrics collection
    asyncio.create_task(monitoring_system.collect_metrics_periodically())

    return monitoring_system


def create_monitoring_app():
    """Create the monitoring Flask app."""
    return monitoring_system.create_monitoring_app()


async def main():
    """Test the monitoring system."""
    print("📊 Production Monitoring System Test")
    print("=" * 50)

    # Initialize monitoring
    await initialize_monitoring()

    # Run health checks
    print("\n🔍 Running health checks...")
    health_status = await monitoring_system.health_checker.check_all_health()

    for name, status in health_status.items():
        status_emoji = (
            "✅"
            if status.status == "healthy"
            else "⚠️"
            if status.status == "degraded"
            else "❌"
        )
        print(
            f"   {status_emoji} {name.title()}: {status.status} ({status.response_time_ms:.1f}ms)"
        )

    print(
        f"\n🎯 Overall Status: {monitoring_system.health_checker.get_overall_health()}"
    )

    # Test metrics collection
    print("\n📈 Testing metrics...")
    monitoring_system.metrics.update_system_metrics()
    print("   System metrics updated")

    # Create monitoring app
    app = monitoring_system.create_monitoring_app()
    print("\n🚀 Monitoring endpoints available:")
    print("   - /health")
    print("   - /health/detailed")
    print("   - /metrics")
    print("   - /metrics/business")


if __name__ == "__main__":
    asyncio.run(main())
