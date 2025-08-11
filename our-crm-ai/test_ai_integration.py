#!/usr/bin/env python3
"""
AI Integration Testing Script - AI Project Manager
Tests real AI agent integration with production database and validates functionality.
"""

import os
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_integration_framework import (
    AgentIntegrationFramework,
    AgentConfig,
    TaskExecution,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIIntegrationTester:
    """Test suite for AI agent integration."""

    def __init__(self):
        self.framework = AgentIntegrationFramework()
        self.test_results = []

    async def setup_test_agents(self) -> Dict[str, AgentConfig]:
        """Setup test agent configurations."""

        # Get API keys from environment
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "demo-key-replace-with-real-key")
        openai_key = os.getenv("OPENAI_API_KEY", "demo-key-replace-with-real-key")

        agents = {
            "business-analyst": AgentConfig(
                agent_id="business-analyst",
                agent_name="business-analyst",
                provider="anthropic",
                api_endpoint="https://api.anthropic.com/v1/messages",
                model="claude-3-sonnet-20240229",
                api_key=anthropic_key,
                specializations=[
                    "business analysis",
                    "requirements gathering",
                    "stakeholder management",
                ],
                max_tokens=4000,
                timeout=60.0,
            ),
            "backend-architect": AgentConfig(
                agent_id="backend-architect",
                agent_name="backend-architect",
                provider="openai",
                api_endpoint="https://api.openai.com/v1/chat/completions",
                model="gpt-4",
                api_key=openai_key,
                specializations=[
                    "system architecture",
                    "database design",
                    "API development",
                ],
                max_tokens=3000,
                timeout=45.0,
            ),
            "frontend-developer": AgentConfig(
                agent_id="frontend-developer",
                agent_name="frontend-developer",
                provider="openai",
                api_endpoint="https://api.openai.com/v1/chat/completions",
                model="gpt-4",
                api_key=openai_key,
                specializations=["React", "UI/UX design", "frontend optimization"],
                max_tokens=3000,
                timeout=45.0,
            ),
        }

        # Register agents with framework - This is now handled by the framework's __init__
        # for agent_name, config in agents.items():
        #     await self.framework.register_agent(config)

        return agents

    def log_test_result(
        self, test_name: str, success: bool, details: str = "", data: Any = None
    ):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "data": data,
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")

    async def test_api_key_validation(self, agents: Dict[str, AgentConfig]):
        """Test 1: Validate API key configuration."""
        print("\n🔑 Testing API Key Configuration...")

        for agent_name, config in agents.items():
            # Check if API key is configured
            has_real_key = config.api_key and not config.api_key.startswith("demo-key")

            if has_real_key:
                self.log_test_result(
                    f"API Key - {agent_name}",
                    True,
                    f"Real {config.provider} API key configured",
                )
            else:
                self.log_test_result(
                    f"API Key - {agent_name}",
                    False,
                    f"Demo key detected for {config.provider} - replace with real API key",
                    {
                        "provider": config.provider,
                        "key_preview": config.api_key[:20] + "...",
                    },
                )

    async def test_agent_health_checks(self, agents: Dict[str, AgentConfig]):
        """Test 2: Agent health checks."""
        print("\n🏥 Testing Agent Health Checks...")

        for agent_name, config in agents.items():
            try:
                # Only test health if we have real API keys
                if config.api_key and not config.api_key.startswith("demo-key"):
                    is_healthy = await self.framework.check_agent_health(agent_name)
                    self.log_test_result(
                        f"Health Check - {agent_name}",
                        is_healthy,
                        f"{config.provider} agent health: {'healthy' if is_healthy else 'unhealthy'}",
                    )
                else:
                    self.log_test_result(
                        f"Health Check - {agent_name}",
                        False,
                        f"Skipped - no real API key for {config.provider}",
                        {"requires": f"Real {config.provider} API key"},
                    )
            except Exception as e:
                self.log_test_result(
                    f"Health Check - {agent_name}",
                    False,
                    f"Health check failed: {str(e)}",
                )

    async def test_simple_task_execution(self, agents: Dict[str, AgentConfig]):
        """Test 3: Simple task execution."""
        print("\n🚀 Testing Simple Task Execution...")

        test_task = TaskExecution(
            task_id="test-001",
            agent_id="business-analyst",
            task_type="Analyze user requirements for e-commerce platform",
            prompt="Create a brief analysis of key requirements for building an e-commerce platform",
            context={"priority": "medium"},
        )

        try:
            # Only execute if we have a real API key
            ba_config = agents.get("business-analyst")
            if ba_config and not ba_config.api_key.startswith("demo-key"):
                result = await self.framework.execute_task(test_task)

                success = result.get("success", False)
                self.log_test_result(
                    "Simple Task Execution",
                    success,
                    f"Task executed, result length: {len(result.get('result', ''))}"
                    if success
                    else "Task execution failed",
                    {
                        "task_id": test_task.id,
                        "agent": test_task.agent_name,
                        "result_preview": result.get("result", "")[:200] + "..."
                        if result.get("result")
                        else None,
                    },
                )
            else:
                self.log_test_result(
                    "Simple Task Execution",
                    False,
                    "Skipped - no real Anthropic API key configured",
                    {"requires": "Real Anthropic API key in ANTHROPIC_API_KEY"},
                )
        except Exception as e:
            self.log_test_result(
                "Simple Task Execution", False, f"Task execution error: {str(e)}"
            )

    async def test_agent_routing_logic(self, agents: Dict[str, AgentConfig]):
        """Test 4: Agent routing and selection logic."""
        print("\n🎯 Testing Agent Routing Logic...")

        test_scenarios = [
            {
                "description": "Design database schema for user management",
                "expected_agent": "backend-architect",
            },
            {
                "description": "Analyze business requirements for mobile app",
                "expected_agent": "business-analyst",
            },
            {
                "description": "Create responsive React components for dashboard",
                "expected_agent": "frontend-developer",
            },
        ]

        for scenario in test_scenarios:
            try:
                best_agent = await self.framework.select_best_agent(
                    scenario["description"], available_agents=list(agents.keys())
                )

                correct_routing = best_agent == scenario["expected_agent"]
                self.log_test_result(
                    f"Agent Routing - {scenario['expected_agent']}",
                    correct_routing,
                    f"Selected '{best_agent}', expected '{scenario['expected_agent']}'",
                    {
                        "description": scenario["description"],
                        "selected": best_agent,
                        "expected": scenario["expected_agent"],
                    },
                )
            except Exception as e:
                self.log_test_result(
                    f"Agent Routing - {scenario['expected_agent']}",
                    False,
                    f"Routing error: {str(e)}",
                )

    async def test_database_integration(self):
        """Test 5: Database integration with PostgreSQL."""
        print("\n🗄️ Testing Database Integration...")

        try:
            # Test PostgreSQL connection from Docker
            import psycopg2

            db_config = {
                "host": "localhost",
                "port": 5433,  # External port mapping
                "database": "aipm_db",
                "user": "aipm_user",
                "password": os.getenv(
                    "DATABASE_PASSWORD", "$7vQ!4ZzncFwydj%tiBbAe*U4w2EvAi$"
                ),
            }

            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()

            # Test agent table
            cursor.execute("SELECT COUNT(*) FROM ai_crm.agents;")
            agent_count = cursor.fetchone()[0]

            # Test tasks table
            cursor.execute("SELECT COUNT(*) FROM ai_crm.tasks;")
            task_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.log_test_result(
                "Database Integration",
                True,
                f"PostgreSQL connected - {agent_count} agents, {task_count} tasks",
                {"agents": agent_count, "tasks": task_count},
            )

        except Exception as e:
            self.log_test_result(
                "Database Integration", False, f"Database connection failed: {str(e)}"
            )

    async def run_all_tests(self):
        """Run comprehensive AI integration tests."""
        print("🧪 AI Agent Integration Test Suite")
        print("=" * 50)

        # Setup
        agents = await self.setup_test_agents()

        # Run tests
        await self.test_api_key_validation(agents)
        await self.test_agent_health_checks(agents)
        await self.test_simple_task_execution(agents)
        await self.test_agent_routing_logic(agents)
        await self.test_database_integration()

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate test report."""
        print("\n" + "=" * 50)
        print("🎯 AI Integration Test Report")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print(
            f"📊 Summary: {passed_tests}/{total_tests} tests passed ({failed_tests} failed)"
        )
        print(f"⏱️  Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test_name']}: {result['details']}")

        print("\n🔧 Next Steps for Full AI Integration:")
        print(
            "   1. Add real Anthropic API key to ANTHROPIC_API_KEY environment variable"
        )
        print("   2. Add real OpenAI API key to OPENAI_API_KEY environment variable")
        print("   3. Restart Docker containers to pick up new API keys")
        print("   4. Re-run tests to verify full AI functionality")

        # Save report to file
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "timestamp": datetime.now().isoformat(),
            },
            "results": self.test_results,
        }

        with open("ai_integration_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print("\n📄 Detailed report saved to: ai_integration_test_report.json")


async def main():
    """Main test execution."""
    tester = AIIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
