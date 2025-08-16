import logging
import sqlite3
import uuid

import bcrypt

logger = logging.getLogger(__name__)


def get_db_connection(db_path: str = "business_analytics.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: str = "business_analytics.db"):
    """Initialize database with enhanced security and users table."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Users table for authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME
            )
        """)

        # Enhanced business projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                business_goal TEXT,
                target_revenue REAL,
                estimated_cost REAL,
                actual_cost REAL DEFAULT 0,
                projected_roi REAL,
                actual_roi REAL DEFAULT 0,
                start_date TEXT,
                target_completion TEXT,
                actual_completion TEXT,
                status TEXT DEFAULT 'planning',
                risk_score REAL,
                team_size INTEGER,
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)

        # Project phases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_phases (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                phase_name TEXT,
                assigned_agent TEXT,
                estimated_hours REAL,
                actual_hours REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                start_date TEXT,
                completion_date TEXT,
                business_impact TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES business_projects (id)
            )
        """)

        # Business metrics tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                target_value REAL,
                measurement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence_level REAL,
                FOREIGN KEY (project_id) REFERENCES business_projects (id)
            )
        """)

        # Session tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                token_hash TEXT,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        conn.commit()


def init_default_users(db_path: str = "business_analytics.db"):
    """Create default admin user if none exists."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            admin_id = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt())

            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    admin_id,
                    "admin",
                    "admin@aipm.local",
                    password_hash.decode("utf-8"),
                    "admin",
                ),
            )

            conn.commit()
            logger.info("Created default admin user: admin / admin123")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
