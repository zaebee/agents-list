#!/usr/bin/env python3
"""
Database Migration Scripts - AI Project Manager

Production-ready database migration system with PostgreSQL support,
connection pooling, and data migration from SQLite to PostgreSQL.

Features:
- PostgreSQL schema creation
- SQLite to PostgreSQL data migration
- Connection pooling with asyncpg
- Transaction safety and rollback support
- Environment-based configuration
"""

import os
import asyncio
import logging
import sqlite3
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseMigrationError(Exception):
    """Database migration related errors."""

    pass


class PostgreSQLMigrator:
    """PostgreSQL database migration and management system."""

    def __init__(self):
        self.postgres_url = os.getenv(
            "DATABASE_URL",
            "postgresql://aipm_user:aipm_password@localhost:5432/aipm_db",
        )
        self.sqlite_path = os.getenv("SQLITE_DB_PATH", "business_analytics.db")
        self.pool = None

    async def create_connection_pool(self):
        """Create PostgreSQL connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.postgres_url, min_size=5, max_size=20, command_timeout=60
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            raise DatabaseMigrationError(f"Failed to create connection pool: {e}")

    async def close_connection_pool(self):
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def create_postgresql_schema(self):
        """Create PostgreSQL database schema."""
        schema_sql = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";

        -- Users table with enhanced security
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP WITH TIME ZONE,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP WITH TIME ZONE,
            
            CONSTRAINT valid_role CHECK (role IN ('admin', 'pm', 'stakeholder', 'viewer'))
        );

        -- Business projects table with enhanced tracking
        CREATE TABLE IF NOT EXISTS business_projects (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            business_goal TEXT,
            target_revenue NUMERIC(15,2),
            estimated_cost NUMERIC(15,2),
            actual_cost NUMERIC(15,2) DEFAULT 0,
            projected_roi NUMERIC(8,2),
            actual_roi NUMERIC(8,2) DEFAULT 0,
            start_date DATE,
            target_completion DATE,
            actual_completion DATE,
            status VARCHAR(20) DEFAULT 'planning',
            risk_score NUMERIC(3,2),
            team_size INTEGER,
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT valid_status CHECK (status IN ('planning', 'in_progress', 'completed', 'cancelled', 'on_hold')),
            CONSTRAINT valid_risk_score CHECK (risk_score >= 0 AND risk_score <= 1)
        );

        -- Project phases table
        CREATE TABLE IF NOT EXISTS project_phases (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID REFERENCES business_projects(id) ON DELETE CASCADE,
            phase_name VARCHAR(255) NOT NULL,
            assigned_agent VARCHAR(100),
            estimated_hours NUMERIC(8,2),
            actual_hours NUMERIC(8,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            start_date TIMESTAMP WITH TIME ZONE,
            completion_date TIMESTAMP WITH TIME ZONE,
            business_impact TEXT,
            quality_score NUMERIC(3,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT valid_phase_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'paused'))
        );

        -- Business metrics tracking
        CREATE TABLE IF NOT EXISTS business_metrics (
            id SERIAL PRIMARY KEY,
            project_id UUID REFERENCES business_projects(id) ON DELETE CASCADE,
            metric_name VARCHAR(100) NOT NULL,
            metric_value NUMERIC(15,2),
            target_value NUMERIC(15,2),
            measurement_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            confidence_level NUMERIC(3,2),
            
            CONSTRAINT valid_confidence CHECK (confidence_level >= 0 AND confidence_level <= 1)
        );

        -- Agent performance tracking with business context
        CREATE TABLE IF NOT EXISTS agent_business_performance (
            id SERIAL PRIMARY KEY,
            agent_name VARCHAR(100) NOT NULL,
            project_id UUID REFERENCES business_projects(id) ON DELETE CASCADE,
            phase_id UUID REFERENCES project_phases(id) ON DELETE CASCADE,
            task_completed BOOLEAN DEFAULT false,
            business_value_delivered NUMERIC(15,2),
            time_to_completion NUMERIC(8,2),
            quality_score NUMERIC(3,2),
            stakeholder_satisfaction NUMERIC(3,2),
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- User sessions for authentication
        CREATE TABLE IF NOT EXISTS user_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255),
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Workflow executions table
        CREATE TABLE IF NOT EXISTS workflow_executions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID REFERENCES business_projects(id) ON DELETE CASCADE,
            workflow_name VARCHAR(255),
            status VARCHAR(20) DEFAULT 'pending',
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            total_estimated_hours NUMERIC(8,2),
            total_actual_hours NUMERIC(8,2) DEFAULT 0,
            business_context JSONB,
            progress_percentage NUMERIC(5,2) DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT valid_workflow_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_projects_status ON business_projects(status);
        CREATE INDEX IF NOT EXISTS idx_projects_created_by ON business_projects(created_by);
        CREATE INDEX IF NOT EXISTS idx_projects_created_at ON business_projects(created_at);
        CREATE INDEX IF NOT EXISTS idx_phases_project_id ON project_phases(project_id);
        CREATE INDEX IF NOT EXISTS idx_phases_status ON project_phases(status);
        CREATE INDEX IF NOT EXISTS idx_metrics_project_id ON business_metrics(project_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_measurement_date ON business_metrics(measurement_date);
        CREATE INDEX IF NOT EXISTS idx_performance_agent ON agent_business_performance(agent_name);
        CREATE INDEX IF NOT EXISTS idx_performance_project ON agent_business_performance(project_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_workflows_project_id ON workflow_executions(project_id);
        CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflow_executions(status);

        -- Full-text search indexes
        CREATE INDEX IF NOT EXISTS idx_projects_name_search ON business_projects USING gin(name gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_projects_goal_search ON business_projects USING gin(business_goal gin_trgm_ops);

        -- Create trigger for updating updated_at timestamps
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER update_business_projects_updated_at BEFORE UPDATE ON business_projects
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER update_project_phases_updated_at BEFORE UPDATE ON project_phases
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """

        async with self.pool.acquire() as conn:
            try:
                await conn.execute(schema_sql)
                logger.info("PostgreSQL schema created successfully")
            except Exception as e:
                raise DatabaseMigrationError(f"Failed to create schema: {e}")

    async def migrate_sqlite_to_postgresql(self):
        """Migrate data from SQLite to PostgreSQL."""
        if not os.path.exists(self.sqlite_path):
            logger.info("No SQLite database found, skipping migration")
            return

        logger.info("Starting SQLite to PostgreSQL migration...")

        # Connect to SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row

        async with self.pool.acquire() as pg_conn:
            async with pg_conn.transaction():
                try:
                    # Migrate users table
                    await self._migrate_users(sqlite_conn, pg_conn)

                    # Migrate business projects
                    await self._migrate_business_projects(sqlite_conn, pg_conn)

                    # Migrate project phases
                    await self._migrate_project_phases(sqlite_conn, pg_conn)

                    # Migrate business metrics
                    await self._migrate_business_metrics(sqlite_conn, pg_conn)

                    logger.info("Data migration completed successfully")

                except Exception as e:
                    logger.error(f"Migration failed: {e}")
                    raise DatabaseMigrationError(f"Migration failed: {e}")
                finally:
                    sqlite_conn.close()

    async def _migrate_users(self, sqlite_conn, pg_conn):
        """Migrate users table."""
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        if not users:
            logger.info("No users to migrate")
            return

        for user in users:
            await pg_conn.execute(
                """
                INSERT INTO users (id, username, email, password_hash, role, is_active, 
                                 created_at, last_login, failed_login_attempts, locked_until)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) DO NOTHING
            """,
                user["id"],
                user["username"],
                user["email"],
                user["password_hash"],
                user["role"],
                bool(user["is_active"]),
                user["created_at"],
                user["last_login"],
                user["failed_login_attempts"],
                user["locked_until"],
            )

        logger.info(f"Migrated {len(users)} users")

    async def _migrate_business_projects(self, sqlite_conn, pg_conn):
        """Migrate business projects table."""
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM business_projects")
        projects = cursor.fetchall()

        if not projects:
            logger.info("No business projects to migrate")
            return

        for project in projects:
            await pg_conn.execute(
                """
                INSERT INTO business_projects (
                    id, name, business_goal, target_revenue, estimated_cost, actual_cost,
                    projected_roi, actual_roi, start_date, target_completion, actual_completion,
                    status, risk_score, team_size, created_by, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO NOTHING
            """,
                project["id"],
                project["name"],
                project["business_goal"],
                project["target_revenue"],
                project["estimated_cost"],
                project["actual_cost"],
                project["projected_roi"],
                project["actual_roi"],
                project["start_date"],
                project["target_completion"],
                project["actual_completion"],
                project["status"],
                project["risk_score"],
                project["team_size"],
                project.get("created_by"),
                project["created_at"],
            )

        logger.info(f"Migrated {len(projects)} business projects")

    async def _migrate_project_phases(self, sqlite_conn, pg_conn):
        """Migrate project phases table."""
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM project_phases")
        phases = cursor.fetchall()

        if not phases:
            logger.info("No project phases to migrate")
            return

        for phase in phases:
            await pg_conn.execute(
                """
                INSERT INTO project_phases (
                    id, project_id, phase_name, assigned_agent, estimated_hours, actual_hours,
                    status, start_date, completion_date, business_impact, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO NOTHING
            """,
                phase["id"],
                phase["project_id"],
                phase["phase_name"],
                phase["assigned_agent"],
                phase["estimated_hours"],
                phase["actual_hours"],
                phase["status"],
                phase["start_date"],
                phase["completion_date"],
                phase["business_impact"],
                phase.get("created_at", datetime.now().isoformat()),
            )

        logger.info(f"Migrated {len(phases)} project phases")

    async def _migrate_business_metrics(self, sqlite_conn, pg_conn):
        """Migrate business metrics table."""
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM business_metrics")
        metrics = cursor.fetchall()

        if not metrics:
            logger.info("No business metrics to migrate")
            return

        for metric in metrics:
            await pg_conn.execute(
                """
                INSERT INTO business_metrics (
                    project_id, metric_name, metric_value, target_value,
                    measurement_date, confidence_level
                )
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                metric["project_id"],
                metric["metric_name"],
                metric["metric_value"],
                metric["target_value"],
                metric["measurement_date"],
                metric["confidence_level"],
            )

        logger.info(f"Migrated {len(metrics)} business metrics")

    async def create_default_admin(self):
        """Create default admin user in PostgreSQL."""
        import bcrypt
        import uuid

        admin_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(
            "admin123".encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        async with self.pool.acquire() as conn:
            # Check if admin exists
            existing_admin = await conn.fetchrow(
                "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
            )

            if not existing_admin:
                await conn.execute(
                    """
                    INSERT INTO users (id, username, email, password_hash, role)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    admin_id,
                    "admin",
                    "admin@aipm.local",
                    password_hash,
                    "admin",
                )

                logger.info("Created default admin user: admin / admin123")

    async def run_migration(self):
        """Run complete database migration process."""
        try:
            logger.info("Starting database migration process...")

            # Create connection pool
            await self.create_connection_pool()

            # Create PostgreSQL schema
            await self.create_postgresql_schema()

            # Migrate data from SQLite
            await self.migrate_sqlite_to_postgresql()

            # Create default admin user
            await self.create_default_admin()

            logger.info("Database migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            raise
        finally:
            await self.close_connection_pool()


async def main():
    """Main migration function."""
    print("🗄️  AI Project Manager - Database Migration")
    print("=" * 50)
    print("Migrating from SQLite to PostgreSQL...")
    print()

    migrator = PostgreSQLMigrator()

    try:
        await migrator.run_migration()
        print("✅ Migration completed successfully!")
        print("🔐 Default admin credentials: admin / admin123")
        print("📊 Database ready for production use")

    except DatabaseMigrationError as e:
        print(f"❌ Migration failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
