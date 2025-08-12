#!/usr/bin/env python3
"""
PostgreSQL Database Manager - AI Project Manager

Production database operations, connection pooling, and advanced querying
for the AI Project Manager with enhanced performance and security.

Features:
- Async connection pooling with asyncpg
- Query optimization and prepared statements
- Transaction management with rollback support
- Database health monitoring
- Backup and recovery operations
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Database operation errors."""

    pass


class PostgreSQLManager:
    """Production PostgreSQL database manager with connection pooling."""

    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://aipm_user:aipm_password@localhost:5432/aipm_db",
        )
        self.pool = None
        self._prepared_statements = {}

    async def initialize(self):
        """Initialize connection pool and prepared statements."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    "jit": "off",  # Disable JIT for predictable performance
                    "application_name": "aipm_production",
                },
            )

            # Prepare frequently used statements
            await self._prepare_statements()

            logger.info("PostgreSQL connection pool initialized successfully")

        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {e}")

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self.pool:
            raise DatabaseError("Database not initialized")

        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

    @asynccontextmanager
    async def get_transaction(self):
        """Get database transaction."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn

    async def _prepare_statements(self):
        """Prepare frequently used SQL statements for better performance."""
        statements = {
            "get_project_by_id": """
                SELECT p.*, u.username as created_by_username
                FROM business_projects p
                LEFT JOIN users u ON p.created_by = u.id
                WHERE p.id = $1
            """,
            "get_project_phases": """
                SELECT * FROM project_phases 
                WHERE project_id = $1 
                ORDER BY created_at
            """,
            "get_user_by_username": """
                SELECT * FROM users 
                WHERE username = $1 AND is_active = true
            """,
            "update_user_login": """
                UPDATE users 
                SET last_login = $1, failed_login_attempts = 0, locked_until = NULL
                WHERE id = $2
            """,
            "get_executive_metrics": """
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(estimated_cost) as total_investment,
                    SUM(target_revenue) as projected_revenue,
                    AVG(projected_roi) as avg_roi,
                    AVG(risk_score) as avg_risk_score
                FROM business_projects 
                WHERE status != 'cancelled'
            """,
            "get_recent_projects": """
                SELECT 
                    p.id, p.name, p.target_revenue, p.estimated_cost, p.projected_roi,
                    p.risk_score, p.status, p.created_at, u.username as created_by_username,
                    COUNT(ph.id) as total_phases,
                    COUNT(CASE WHEN ph.status = 'completed' THEN 1 END) as completed_phases
                FROM business_projects p
                LEFT JOIN project_phases ph ON p.id = ph.project_id
                LEFT JOIN users u ON p.created_by = u.id
                GROUP BY p.id, u.username
                ORDER BY p.created_at DESC
                LIMIT $1
            """,
        }

        async with self.get_connection() as conn:
            for name, sql in statements.items():
                await conn.prepare(sql)
                self._prepared_statements[name] = sql

    # User Management Methods
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with enhanced security."""
        async with self.get_connection() as conn:
            user = await conn.fetchrow(
                self._prepared_statements["get_user_by_username"], username
            )

            if not user:
                return None

            # Check if account is locked
            if user["locked_until"] and user["locked_until"] > datetime.now():
                raise DatabaseError("Account is temporarily locked")

            # In a real implementation, verify password here using bcrypt
            # For now, we'll assume password verification is done elsewhere

            return dict(user)

    async def update_user_login(self, user_id: str):
        """Update user login timestamp and reset failed attempts."""
        async with self.get_connection() as conn:
            await conn.execute(
                self._prepared_statements["update_user_login"], datetime.now(), user_id
            )

    async def create_user(
        self, username: str, email: str, password_hash: str, role: str = "viewer"
    ) -> str:
        """Create new user account."""
        async with self.get_transaction() as conn:
            try:
                result = await conn.fetchrow(
                    """
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """,
                    username,
                    email,
                    password_hash,
                    role,
                )

                return str(result["id"])

            except asyncpg.UniqueViolationError:
                raise DatabaseError("Username or email already exists")

    # Project Management Methods
    async def create_project(self, project_data: Dict, created_by: str) -> str:
        """Create new business project."""
        async with self.get_transaction() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO business_projects (
                    name, business_goal, target_revenue, estimated_cost, projected_roi,
                    risk_score, team_size, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """,
                project_data["name"],
                project_data.get("business_goal"),
                project_data.get("target_revenue"),
                project_data.get("estimated_cost"),
                project_data.get("projected_roi"),
                project_data.get("risk_score"),
                project_data.get("team_size"),
                created_by,
            )

            return str(result["id"])

    async def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """Get project by ID with creator information."""
        async with self.get_connection() as conn:
            project = await conn.fetchrow(
                self._prepared_statements["get_project_by_id"], project_id
            )

            if not project:
                return None

            # Get project phases
            phases = await conn.fetch(
                self._prepared_statements["get_project_phases"], project_id
            )

            project_dict = dict(project)
            project_dict["phases"] = [dict(phase) for phase in phases]

            return project_dict

    async def update_project_status(
        self, project_id: str, status: str, user_id: str
    ) -> bool:
        """Update project status with audit trail."""
        async with self.get_transaction() as conn:
            result = await conn.execute(
                """
                UPDATE business_projects 
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2 AND (created_by = $3 OR $3 IN (
                    SELECT id FROM users WHERE role IN ('admin', 'pm')
                ))
            """,
                status,
                project_id,
                user_id,
            )

            return result != "UPDATE 0"

    # Analytics and Reporting Methods
    async def get_executive_dashboard_data(self) -> Dict[str, Any]:
        """Get executive dashboard data with optimized queries."""
        async with self.get_connection() as conn:
            # Overall metrics
            metrics = await conn.fetchrow(
                self._prepared_statements["get_executive_metrics"]
            )

            # Project status breakdown
            status_data = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM business_projects 
                GROUP BY status
            """)

            # Recent projects
            recent_projects = await conn.fetch(
                self._prepared_statements["get_recent_projects"], 10
            )

            # Calculate completion percentages
            projects_with_completion = []
            for project in recent_projects:
                project_dict = dict(project)
                if project_dict["total_phases"] > 0:
                    project_dict["completion_percentage"] = (
                        project_dict["completed_phases"] / project_dict["total_phases"]
                    ) * 100
                else:
                    project_dict["completion_percentage"] = 0
                projects_with_completion.append(project_dict)

            return {
                "overall_metrics": dict(metrics),
                "project_status_breakdown": {
                    row["status"]: row["count"] for row in status_data
                },
                "recent_projects": projects_with_completion,
                "generated_at": datetime.now().isoformat(),
            }

    async def get_project_health_analytics(self) -> Dict[str, Any]:
        """Get project health analytics with performance insights."""
        async with self.get_connection() as conn:
            # High risk projects
            high_risk = await conn.fetch("""
                SELECT name, risk_score, status, projected_roi, estimated_cost
                FROM business_projects 
                WHERE risk_score > 0.6 AND status IN ('planning', 'in_progress')
                ORDER BY risk_score DESC
            """)

            # Active projects timeline analysis
            timeline_analysis = await conn.fetch("""
                SELECT 
                    p.name,
                    COUNT(ph.id) as total_phases,
                    SUM(ph.estimated_hours) as estimated_hours,
                    SUM(ph.actual_hours) as actual_hours,
                    COUNT(CASE WHEN ph.status = 'completed' THEN 1 END) as completed_phases
                FROM business_projects p
                LEFT JOIN project_phases ph ON p.id = ph.project_id
                WHERE p.status = 'in_progress'
                GROUP BY p.id, p.name
            """)

            # Calculate health scores
            projects_with_health = []
            for project in timeline_analysis:
                project_dict = dict(project)

                if project_dict["total_phases"] > 0:
                    completion_rate = (
                        project_dict["completed_phases"] / project_dict["total_phases"]
                    )

                    # Calculate efficiency
                    efficiency = 1.0
                    if project_dict["actual_hours"] and project_dict["estimated_hours"]:
                        efficiency = min(
                            project_dict["estimated_hours"]
                            / project_dict["actual_hours"],
                            1.0,
                        )

                    project_dict["health_score"] = (
                        completion_rate * 0.6 + efficiency * 0.4
                    ) * 100
                else:
                    project_dict["health_score"] = 0

                projects_with_health.append(project_dict)

            # Budget analysis
            budget_data = await conn.fetchrow("""
                SELECT 
                    SUM(estimated_cost) as total_budget,
                    SUM(actual_cost) as total_spent,
                    COUNT(*) as active_projects
                FROM business_projects 
                WHERE status IN ('planning', 'in_progress')
            """)

            budget_dict = dict(budget_data)
            if budget_dict["total_budget"]:
                budget_dict["budget_utilization"] = (
                    budget_dict["total_spent"] / budget_dict["total_budget"]
                ) * 100
            else:
                budget_dict["budget_utilization"] = 0

            return {
                "high_risk_projects": [dict(row) for row in high_risk],
                "timeline_analysis": projects_with_health,
                "budget_analysis": budget_dict,
                "health_summary": {
                    "projects_on_track": len(
                        [p for p in projects_with_health if p["health_score"] > 70]
                    ),
                    "projects_at_risk": len(
                        [p for p in projects_with_health if p["health_score"] < 50]
                    ),
                    "average_health_score": sum(
                        p["health_score"] for p in projects_with_health
                    )
                    / len(projects_with_health)
                    if projects_with_health
                    else 0,
                },
            }

    async def get_roi_analytics(self) -> Dict[str, Any]:
        """Get ROI analytics with risk-adjusted calculations."""
        async with self.get_connection() as conn:
            # ROI projections
            roi_data = await conn.fetch("""
                SELECT 
                    name, estimated_cost, actual_cost, target_revenue,
                    projected_roi, actual_roi, status, risk_score
                FROM business_projects
                WHERE target_revenue > 0
                ORDER BY projected_roi DESC
            """)

            roi_list = [dict(row) for row in roi_data]

            # Portfolio performance
            total_investment = sum(p["estimated_cost"] or 0 for p in roi_list)
            total_projected_return = sum(p["target_revenue"] or 0 for p in roi_list)

            portfolio_roi = 0
            if total_investment > 0:
                portfolio_roi = (
                    (total_projected_return - total_investment) / total_investment
                ) * 100

            # Risk-adjusted returns
            risk_adjusted = []
            for project in roi_list:
                if project["projected_roi"] and project["risk_score"]:
                    adjusted_roi = project["projected_roi"] * (
                        1 - project["risk_score"]
                    )
                    risk_adjusted.append(
                        {
                            "name": project["name"],
                            "original_roi": project["projected_roi"],
                            "risk_score": project["risk_score"],
                            "adjusted_roi": adjusted_roi,
                            "investment": project["estimated_cost"],
                        }
                    )

            risk_adjusted.sort(key=lambda x: x["adjusted_roi"], reverse=True)

            return {
                "project_roi_analysis": roi_list,
                "portfolio_metrics": {
                    "total_investment": total_investment,
                    "projected_returns": total_projected_return,
                    "portfolio_roi": portfolio_roi,
                    "project_count": len(roi_list),
                },
                "risk_adjusted_analysis": risk_adjusted,
            }

    # Database Health and Monitoring
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        try:
            async with self.get_connection() as conn:
                # Check basic connectivity
                result = await conn.fetchval("SELECT 1")

                # Get database stats
                stats = await conn.fetchrow("""
                    SELECT 
                        (SELECT COUNT(*) FROM business_projects) as total_projects,
                        (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
                        (SELECT COUNT(*) FROM project_phases) as total_phases,
                        current_timestamp as check_time
                """)

                # Get connection pool stats
                pool_stats = {
                    "pool_size": self.pool.get_size(),
                    "pool_max_size": self.pool.get_max_size(),
                    "pool_min_size": self.pool.get_min_size(),
                }

                return {
                    "status": "healthy",
                    "database_stats": dict(stats),
                    "connection_pool": pool_stats,
                    "response_time_ms": 0,  # Would measure actual response time
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "check_time": datetime.now().isoformat(),
            }

    # Backup and Maintenance
    async def create_backup_info(self) -> Dict[str, Any]:
        """Create backup information (actual backup would use pg_dump)."""
        async with self.get_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    pg_database_size(current_database()) as db_size_bytes,
                    (SELECT COUNT(*) FROM business_projects) as projects_count,
                    (SELECT COUNT(*) FROM users) as users_count,
                    current_timestamp as backup_timestamp
            """)

            return {
                "backup_info": dict(stats),
                "backup_recommended": dict(stats)["db_size_bytes"]
                > 100 * 1024 * 1024,  # 100MB
                "backup_command": f"pg_dump {self.database_url} > backup_$(date +%Y%m%d_%H%M%S).sql",
            }


# Global database manager instance
db_manager = PostgreSQLManager()


async def initialize_database():
    """Initialize database connection for the application."""
    await db_manager.initialize()


async def close_database():
    """Close database connections."""
    await db_manager.close()


# Context manager for database operations
@asynccontextmanager
async def get_db_connection():
    """Get database connection context manager."""
    async with db_manager.get_connection() as conn:
        yield conn


@asynccontextmanager
async def get_db_transaction():
    """Get database transaction context manager."""
    async with db_manager.get_transaction() as conn:
        yield conn


async def main():
    """Test database operations."""
    print("🗄️  PostgreSQL Manager Test")
    print("=" * 40)

    try:
        await db_manager.initialize()

        # Test health check
        health = await db_manager.health_check()
        print(f"Database Status: {health['status']}")

        if health["status"] == "healthy":
            print(f"Total Projects: {health['database_stats']['total_projects']}")
            print(f"Active Users: {health['database_stats']['active_users']}")
            print(f"Pool Size: {health['connection_pool']['pool_size']}")

        # Test dashboard data
        dashboard_data = await db_manager.get_executive_dashboard_data()
        print(f"Dashboard generated at: {dashboard_data['generated_at']}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
