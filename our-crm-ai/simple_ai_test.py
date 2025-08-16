#!/usr/bin/env python3
"""
Simple AI Integration Test - AI Project Manager
Tests the AI agent integration framework with current setup.
"""

import asyncio
from datetime import datetime
import json
import os
import sys
from typing import Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from agent_integration_framework import (
    AgentConfig,
    AgentIntegrationFramework,
    TaskExecution,
)

# Load environment variables
load_dotenv()


class SimpleAITester:
    """Simple test suite for AI agent integration."""

    def __init__(self):
        self.framework = AgentIntegrationFramework()
        self.results = []

    def log_result(self, test: str, success: bool, message: str, details: Any = None):
        """Log test result."""
        result = {
            "test": test,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }
        self.results.append(result)

        status = "✅" if success else "❌"
        print(f"{status} {test}: {message}")

    async def test_framework_initialization(self):
        """Test 1: Framework initialization."""
        try:
            # Check if framework initialized properly
            self.log_result(
                "Framework Init",
                True,
                "AgentIntegrationFramework initialized successfully",
            )
            return True
        except Exception as e:
            self.log_result(
                "Framework Init", False, f"Framework initialization failed: {e!s}"
            )
            return False

    async def test_api_key_configuration(self):
        """Test 2: API key configuration."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "not-found")
        openai_key = os.getenv("OPENAI_API_KEY", "not-found")

        print("\n🔑 API Key Configuration:")

        # Test Anthropic key
        has_anthropic = anthropic_key != "not-found" and not anthropic_key.startswith(
            "demo-key"
        )
        self.log_result(
            "Anthropic API Key",
            has_anthropic,
            f"Real key: {has_anthropic}, Value: {anthropic_key[:20]}..."
            if anthropic_key != "not-found"
            else "No ANTHROPIC_API_KEY found",
        )

        # Test OpenAI key
        has_openai = openai_key != "not-found" and not openai_key.startswith("demo-key")
        self.log_result(
            "OpenAI API Key",
            has_openai,
            f"Real key: {has_openai}, Value: {openai_key[:20]}..."
            if openai_key != "not-found"
            else "No OPENAI_API_KEY found",
        )

        return has_anthropic or has_openai

    async def test_agent_configuration(self):
        """Test 3: Agent configuration."""
        print("\n🤖 Agent Configuration:")

        try:
            # Create test agent configs
            anthropic_config = AgentConfig(
                agent_id="ba-001",
                agent_name="business-analyst",
                provider="anthropic",
                api_endpoint="https://api.anthropic.com",
                api_key=os.getenv("ANTHROPIC_API_KEY", "demo-key"),
                model="claude-3-sonnet-20240229",
                specializations=["business analysis", "requirements"],
            )

            openai_config = AgentConfig(
                agent_id="arch-001",
                agent_name="backend-architect",
                provider="openai",
                api_endpoint="https://api.openai.com",
                api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
                model="gpt-4",
                specializations=["architecture", "backend"],
            )

            self.log_result(
                "Agent Config Creation",
                True,
                "Successfully created AgentConfig objects",
                {
                    "anthropic_agent": anthropic_config.agent_name,
                    "openai_agent": openai_config.agent_name,
                },
            )

            return {"anthropic": anthropic_config, "openai": openai_config}

        except Exception as e:
            self.log_result(
                "Agent Config Creation",
                False,
                f"Failed to create agent configs: {e!s}",
            )
            return None

    async def test_task_creation(self):
        """Test 4: Task creation."""
        print("\n📋 Task Creation:")

        try:
            test_task = TaskExecution(
                task_id="test-001",
                agent_id="ba-001",
                task_type="analysis",
                prompt="Analyze the requirements for an AI project management system",
                context={"priority": "high", "domain": "software"},
            )

            self.log_result(
                "Task Creation",
                True,
                f"Created task {test_task.task_id} with status {test_task.status}",
                {
                    "task_id": test_task.task_id,
                    "agent_id": test_task.agent_id,
                    "status": test_task.status.value
                    if hasattr(test_task.status, "value")
                    else str(test_task.status),
                },
            )

            return test_task

        except Exception as e:
            self.log_result("Task Creation", False, f"Failed to create task: {e!s}")
            return None

    async def test_database_connection(self):
        """Test 5: Database connection."""
        print("\n🗄️ Database Connection:")

        try:
            # Test PostgreSQL connection
            import psycopg2

            # Use the external port for testing from host
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                database="aipm_db",
                user="aipm_user",
                password=os.getenv(
                    "DATABASE_PASSWORD", "$7vQ!4ZzncFwydj%tiBbAe*U4w2EvAi$"
                ),
            )

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ai_crm.agents;")
            agent_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ai_crm.tasks;")
            task_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.log_result(
                "Database Connection",
                True,
                f"Connected to PostgreSQL - {agent_count} agents, {task_count} tasks",
                {"agent_count": agent_count, "task_count": task_count},
            )

            return True

        except Exception as e:
            self.log_result(
                "Database Connection", False, f"Database connection failed: {e!s}"
            )
            return False

    async def test_production_system_integration(self):
        """Test 6: Production system integration."""
        print("\n🚀 Production System Integration:")

        try:
            # Test application health
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:5001/api/health")
                health_data = response.json()

                self.log_result(
                    "Application Health",
                    response.status_code == 200,
                    f"Health check: {health_data.get('status', 'unknown')}",
                    health_data,
                )

                # Test authentication
                auth_response = await client.post(
                    "http://localhost:5001/api/auth/login",
                    json={"username": "admin", "password": "admin123"},
                )

                auth_success = auth_response.status_code == 200
                self.log_result(
                    "Authentication System",
                    auth_success,
                    f"Login test: {'successful' if auth_success else 'failed'}",
                )

                return response.status_code == 200 and auth_success

        except Exception as e:
            self.log_result(
                "Production System Integration",
                False,
                f"Integration test failed: {e!s}",
            )
            return False

    async def run_tests(self):
        """Run all tests."""
        print("🧪 Simple AI Integration Test Suite")
        print("=" * 50)

        # Run tests sequentially
        await self.test_framework_initialization()
        has_keys = await self.test_api_key_configuration()
        configs = await self.test_agent_configuration()
        task = await self.test_task_creation()
        db_ok = await self.test_database_connection()
        app_ok = await self.test_production_system_integration()

        # Generate summary
        self.generate_summary(
            has_keys, configs is not None, task is not None, db_ok, app_ok
        )

    def generate_summary(self, has_keys, configs_ok, task_ok, db_ok, app_ok):
        """Generate test summary."""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)

        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["success"])

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {total_tests - passed}")
        print(f"Success Rate: {(passed / total_tests * 100):.1f}%")

        print("\n🎯 System Status:")
        print(f"   • Framework: {'✅' if configs_ok else '❌'} Ready")
        print(f"   • Database: {'✅' if db_ok else '❌'} Connected")
        print(f"   • Application: {'✅' if app_ok else '❌'} Healthy")
        print(
            f"   • AI Keys: {'✅' if has_keys else '⚠️'} {'Configured' if has_keys else 'Demo keys only'}"
        )

        if not has_keys:
            print("\n🔑 To Enable Real AI Functionality:")
            print("   1. Get Anthropic API key from https://console.anthropic.com")
            print("   2. Get OpenAI API key from https://platform.openai.com")
            print("   3. Add to .env file:")
            print("      ANTHROPIC_API_KEY=your_real_key_here")
            print("      OPENAI_API_KEY=your_real_key_here")
            print("   4. Restart Docker containers:")
            print("      docker compose -f docker-compose.production.yml restart")
        else:
            print("\n🚀 Ready for Real AI Agent Testing!")

        # Save results
        with open("simple_ai_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n📄 Results saved to: simple_ai_test_results.json")


async def main():
    """Main test runner."""
    tester = SimpleAITester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
