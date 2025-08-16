#!/usr/bin/env python3
"""
Training Framework Setup Script - Automated setup and configuration.

This script handles initial setup, database creation, and configuration
for the AI-CRM Agent Training Framework.
"""

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sqlite3
import sys


def setup_logging():
    """Setup logging for the setup process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("setup_training_framework.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def check_dependencies():
    """Check if required dependencies are available."""
    required_modules = [
        "sqlite3",
        "asyncio",
        "threading",
        "dataclasses",
        "collections",
        "statistics",
        "enum",
        "uuid",
        "psutil",
        "cryptography",
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print("❌ Missing required dependencies:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nInstall missing dependencies with:")
        print("pip install psutil cryptography")
        return False

    return True


def create_directories():
    """Create necessary directories."""
    directories = ["data", "logs", "backups", "configs", "exports"]

    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {directory}")


def setup_databases():
    """Setup all required databases."""
    databases = ["training_data.db", "performance_optimization.db"]

    for db_name in databases:
        db_path = Path("data") / db_name

        try:
            # Initialize each component's database
            if "training_data" in db_name:
                from training_data_manager import TrainingDataCurator

                curator = TrainingDataCurator(str(db_path))
                logging.info(f"Initialized training data database: {db_path}")

            elif "performance_optimization" in db_name:
                from performance_optimizer import AgentOptimizer

                optimizer = AgentOptimizer(str(db_path))
                logging.info(
                    f"Initialized performance optimization database: {db_path}"
                )

        except Exception as e:
            logging.error(f"Failed to setup database {db_name}: {e}")
            return False

    return True


def create_default_config():
    """Create default configuration files."""

    # Main training config
    training_config = {
        "training_schedule": {
            "pm-agent-gateway": "0 2 * * *",
            "agent-selector": "0 3 * * *",
            "security-auditor": "0 4 */2 * *",
            "python-pro": "0 1 */2 * *",
            "javascript-pro": "0 1 */2 * *",
            "database-optimizer": "0 5 */2 * *",
            "*": "0 0 * * 0",
        },
        "batch_size": 3,
        "max_concurrent_training": 2,
        "auto_optimization": True,
        "performance_monitoring": True,
        "continuous_learning": True,
        "resource_limits": {
            "max_memory_gb": 4,
            "max_cpu_percent": 80,
            "max_training_duration_hours": 2,
        },
        "notification_settings": {
            "training_completion": True,
            "performance_alerts": True,
            "system_errors": True,
        },
    }

    config_path = Path("configs") / "integrated_training_config.json"
    with open(config_path, "w") as f:
        json.dump(training_config, f, indent=2)

    logging.info(f"Created training configuration: {config_path}")

    # Performance monitoring config
    monitoring_config = {
        "alert_thresholds": {
            "response_time": 5.0,
            "accuracy": 0.7,
            "memory_usage": 0.8,
            "cpu_usage": 0.9,
        },
        "monitoring_interval": 10.0,
        "alert_cooldown": 300,
    }

    monitoring_config_path = Path("configs") / "monitoring_config.json"
    with open(monitoring_config_path, "w") as f:
        json.dump(monitoring_config, f, indent=2)

    logging.info(f"Created monitoring configuration: {monitoring_config_path}")

    # Data validation rules config
    validation_config = {
        "min_input_length": 10,
        "max_input_length": 10000,
        "required_fields": ["agent_name", "input_text"],
        "privacy_patterns": [
            r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit card
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b[\w\.-]+@[\w\.-]+\.\w+\b",  # Email
        ],
        "quality_thresholds": {
            "minimum_score": 0.3,
            "good_score": 0.7,
            "excellent_score": 0.9,
        },
    }

    validation_config_path = Path("configs") / "validation_config.json"
    with open(validation_config_path, "w") as f:
        json.dump(validation_config, f, indent=2)

    logging.info(f"Created validation configuration: {validation_config_path}")


def setup_sample_data():
    """Setup sample training data for testing."""
    try:
        from training_data_manager import DataSource, TrainingDataCurator

        curator = TrainingDataCurator("data/training_data.db")

        # Create sample datasets for key agents
        key_agents = [
            "python-pro",
            "javascript-pro",
            "security-auditor",
            "database-optimizer",
        ]

        for agent in key_agents:
            dataset_id = curator.create_training_dataset(
                name=f"{agent} Sample Dataset",
                agent_name=agent,
                data_sources=[
                    DataSource.USER_INTERACTION,
                    DataSource.SYNTHETIC_GENERATION,
                ],
                description=f"Initial sample dataset for {agent}",
                tags=["sample", "initial", "testing"],
            )

            # Add sample training data
            sample_data = generate_sample_data(agent)
            results = curator.add_data_to_dataset(dataset_id, sample_data)

            logging.info(
                f"Created sample dataset for {agent}: {results['added']} examples added"
            )

    except Exception as e:
        logging.error(f"Failed to setup sample data: {e}")


def generate_sample_data(agent_name):
    """Generate sample training data for an agent."""

    sample_templates = {
        "python-pro": [
            {
                "input_text": "How do I optimize this Python loop for better performance?",
                "expected_output": "Consider using list comprehensions, built-in functions like map/filter, or numpy for numerical operations",
                "performance_score": 0.8,
            },
            {
                "input_text": "What is the best way to handle exceptions in Python?",
                "expected_output": "Use try-except blocks with specific exception types, avoid bare except clauses, and consider using finally for cleanup",
                "performance_score": 0.85,
            },
        ],
        "javascript-pro": [
            {
                "input_text": "How can I improve the performance of this JavaScript function?",
                "expected_output": "Consider using efficient algorithms, avoiding nested loops, using const/let appropriately, and leveraging browser APIs",
                "performance_score": 0.75,
            },
            {
                "input_text": "What are the best practices for asynchronous JavaScript?",
                "expected_output": "Use async/await for better readability, handle errors properly with try-catch, avoid callback hell",
                "performance_score": 0.9,
            },
        ],
        "security-auditor": [
            {
                "input_text": "Review this authentication code for security vulnerabilities",
                "expected_output": "Check for SQL injection, XSS, CSRF vulnerabilities, ensure proper password hashing, validate input sanitization",
                "performance_score": 0.95,
            }
        ],
        "database-optimizer": [
            {
                "input_text": "This query is running slowly, how can I optimize it?",
                "expected_output": "Add appropriate indexes, analyze query execution plan, consider query restructuring, check for N+1 problems",
                "performance_score": 0.8,
            }
        ],
    }

    templates = sample_templates.get(agent_name, [])

    sample_data = []
    for template in templates:
        sample_data.append(
            {
                "agent_name": agent_name,
                "data_source": "synthetic_generation",
                "input_text": template["input_text"],
                "expected_output": template["expected_output"],
                "performance_score": template["performance_score"],
                "context_data": {
                    "sample_data": True,
                    "created_at": datetime.now().isoformat(),
                },
                "tags": ["sample", "synthetic"],
            }
        )

    return sample_data


def create_systemd_service():
    """Create systemd service file for production deployment."""

    service_content = f"""[Unit]
Description=AI-CRM Agent Training Framework
After=network.target

[Service]
Type=simple
User=training-system
WorkingDirectory={os.getcwd()}
ExecStart=/usr/bin/python3 integrated_training_system.py start
Restart=always
RestartSec=10
Environment=PYTHONPATH={os.getcwd()}

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("configs") / "training-framework.service"
    with open(service_path, "w") as f:
        f.write(service_content)

    logging.info(f"Created systemd service file: {service_path}")
    print("\n📋 To install the service:")
    print(f"sudo cp {service_path} /etc/systemd/system/")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl enable training-framework")
    print("sudo systemctl start training-framework")


def create_docker_files():
    """Create Docker deployment files."""

    # Dockerfile
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p data logs backups configs exports

# Set permissions
RUN chmod +x *.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start the application
CMD ["python", "integrated_training_system.py", "start"]
"""

    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)

    # Docker Compose
    compose_content = """version: '3.8'

services:
  training-framework:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./configs:/app/configs
    environment:
      - ENVIRONMENT=production
      - DB_PATH=/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sqlite3; sqlite3.connect('/app/data/training_data.db').execute('SELECT 1')"]
      interval: 30s
      timeout: 10s
      retries: 3

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana_data:
"""

    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)

    # Requirements file
    requirements_content = """asyncio-mqtt==0.11.1
cryptography==41.0.3
psutil==5.9.5
schedule==1.2.0
requests==2.31.0
sqlite3
dataclasses
"""

    with open("requirements.txt", "w") as f:
        f.write(requirements_content)

    logging.info("Created Docker deployment files")


def run_health_checks():
    """Run health checks to verify setup."""

    print("\n🔍 Running health checks...")

    checks = [
        ("Database files exist", check_database_files),
        ("Configuration files exist", check_config_files),
        ("Python imports work", check_imports),
        ("Sample data available", check_sample_data),
    ]

    all_passed = True

    for check_name, check_func in checks:
        try:
            if check_func():
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name}: {e}")
            all_passed = False

    return all_passed


def check_database_files():
    """Check if database files exist."""
    required_dbs = ["data/training_data.db", "data/performance_optimization.db"]
    return all(Path(db).exists() for db in required_dbs)


def check_config_files():
    """Check if configuration files exist."""
    required_configs = [
        "configs/integrated_training_config.json",
        "configs/monitoring_config.json",
        "configs/validation_config.json",
    ]
    return all(Path(config).exists() for config in required_configs)


def check_imports():
    """Check if core modules can be imported."""
    try:
        from agent_training_framework import AgentTrainingPipeline
        from integrated_training_system import IntegratedTrainingSystem
        from performance_optimizer import AgentOptimizer
        from training_data_manager import TrainingDataCurator

        return True
    except ImportError:
        return False


def check_sample_data():
    """Check if sample data exists."""
    try:
        from training_data_manager import TrainingDataCurator

        curator = TrainingDataCurator("data/training_data.db")

        # Check if any datasets exist
        with sqlite3.connect("data/training_data.db") as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM training_datasets")
            count = cursor.fetchone()[0]
            return count > 0
    except Exception:
        return False


def main():
    """Main setup function."""
    print("🚀 AI-CRM Agent Training Framework Setup")
    print("=" * 50)

    setup_logging()

    # Pre-setup checks
    print("\n📋 Checking dependencies...")
    if not check_dependencies():
        return False

    print("✅ All dependencies available")

    # Setup steps
    setup_steps = [
        ("Creating directories", create_directories),
        ("Setting up databases", setup_databases),
        ("Creating configuration files", create_default_config),
        ("Setting up sample data", setup_sample_data),
        ("Creating systemd service", create_systemd_service),
        ("Creating Docker files", create_docker_files),
    ]

    print("\n🔧 Running setup steps...")

    for step_name, step_func in setup_steps:
        try:
            print(f"  {step_name}...")
            step_func()
            print(f"  ✅ {step_name} completed")
        except Exception as e:
            print(f"  ❌ {step_name} failed: {e}")
            logging.error(f"Setup step failed: {step_name}: {e}")
            return False

    # Final health checks
    if run_health_checks():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review configuration files in ./configs/")
        print("2. Start the system: python integrated_training_system.py start")
        print("3. Check status: python integrated_training_system.py status")
        print("4. View dashboard: python integrated_training_system.py dashboard")

        print("\n📁 Files created:")
        print("  - Configuration: ./configs/")
        print("  - Databases: ./data/")
        print("  - Logs: ./logs/")
        print("  - Docker: ./Dockerfile, ./docker-compose.yml")
        print("  - Service: ./configs/training-framework.service")

        return True
    else:
        print("\n❌ Setup completed with warnings. Check logs for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
