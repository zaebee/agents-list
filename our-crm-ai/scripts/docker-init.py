#!/usr/bin/env python3
"""
Docker initialization script for AI-CRM system.
Handles database setup and admin user creation in containerized environment.
"""

import logging
import os
import sys
import time

from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_database():
    """Wait for PostgreSQL database to be ready."""
    if "postgresql" not in os.getenv("DATABASE_URL", ""):
        logger.info("Using SQLite, no wait required")
        return

    from urllib.parse import urlparse

    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    parsed_url = urlparse(database_url)

    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 5432,
                user=parsed_url.username,
                password=parsed_url.password,
                database=parsed_url.path[1:]  # Remove leading slash
            )
            conn.close()
            logger.info("✅ Database connection successful!")
            return
        except psycopg2.OperationalError:
            retry_count += 1
            logger.info(f"⏳ Waiting for database... attempt {retry_count}/{max_retries}")
            time.sleep(2)

    raise Exception("❌ Failed to connect to database after maximum retries")

def initialize_database():
    """Initialize database tables and create admin user."""
    try:
        from auth_database import SessionLocal, create_tables, seed_default_data

        logger.info("📊 Creating database tables...")
        create_tables()

        logger.info("👤 Creating default admin user...")
        db = SessionLocal()
        try:
            seed_default_data(db)
            logger.info("✅ Database initialization complete!")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't fail startup, just log the error
        return False

    return True

def main():
    """Main initialization function."""
    logger.info("🚀 Starting AI-CRM Docker initialization...")

    # Load environment variables
    if os.path.exists('.env.docker'):
        load_dotenv('.env.docker')
        logger.info("📄 Loaded .env.docker configuration")
    else:
        load_dotenv()
        logger.info("📄 Loaded default .env configuration")

    # Wait for database
    wait_for_database()

    # Initialize database
    if initialize_database():
        logger.info("🎯 AI-CRM initialization completed successfully!")
        return 0
    else:
        logger.warning("⚠️ AI-CRM initialization completed with warnings")
        return 0  # Don't fail startup for database warnings

if __name__ == "__main__":
    sys.exit(main())
