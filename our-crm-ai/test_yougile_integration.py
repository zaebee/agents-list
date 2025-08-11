#!/usr/bin/env python3
"""
YouGile Integration Test Suite
Comprehensive tests for YouGile API integration with the refactored AI-CRM system.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

# Add current directory to path for imports
sys.path.append(".")

from models import (
    Task,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskStatus,
    TaskPriority,
)
from exceptions import ConfigurationError
from config_manager import ConfigurationManager
from repositories import YouGileTaskRepository
from crm_service import create_crm_service


class YouGileIntegrationTester:
    """Comprehensive YouGile integration tester."""

    def __init__(
        self, config_path: str = "config_enhanced.json", api_key: Optional[str] = None
    ):
        self.config_path = config_path
        self.api_key = api_key or os.getenv("YOUGILE_API_KEY")
        self.config_manager = None
        self.config = None
        self.repository = None
        self.service = None
        self.test_results = []

        if not self.api_key:
            raise ConfigurationError("YOUGILE_API_KEY environment variable not set")

    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up YouGile integration tests...")

        # Load configuration
        try:
            self.config_manager = ConfigurationManager(self.config_path)
            self.config = self.config_manager.get_config()
            print(f"✅ Configuration loaded from {self.config_path}")
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            raise

        # Create repository
        try:
            from models import CRMConfiguration

            legacy_config = CRMConfiguration(
                project_id=self.config.yougile.project_id,
                board_id=self.config.yougile.board_id,
                columns=self.config.yougile.columns,
                ai_owner_sticker=self.config.yougile.ai_owner_sticker,
            )
            self.repository = YouGileTaskRepository(self.api_key, legacy_config)
            print("✅ Repository created")
        except Exception as e:
            print(f"❌ Failed to create repository: {e}")
            raise

        # Create service
        try:
            self.service = await create_crm_service(self.api_key, self.config_path)
            print("✅ CRM service created")
        except Exception as e:
            print(f"❌ Failed to create CRM service: {e}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        if self.repository:
            await self.repository.close()
        if self.service:
            await self.service.close()

    def log_test_result(
        self, test_name: str, success: bool, details: str = "", error: str = ""
    ):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "error": error,
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")

    async def test_health_check(self):
        """Test API health check."""
        try:
            health = await self.repository.health_check()
            self.log_test_result("Health Check", health, f"API health status: {health}")
            return health
        except Exception as e:
            self.log_test_result("Health Check", False, error=str(e))
            return False

    async def test_task_creation(self) -> Optional[Task]:
        """Test task creation."""
        try:
            # Create test task
            task_request = TaskCreateRequest(
                title=f"[TEST] AI-CRM Integration Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description="This is a test task created by the AI-CRM integration test suite. It can be safely deleted.",
                priority=TaskPriority.MEDIUM,
                assigned_agent="api-documenter",
            )

            task = await self.repository.create_task(task_request)

            self.log_test_result(
                "Task Creation", True, f"Created task: {task.id} - '{task.title}'"
            )
            return task

        except Exception as e:
            self.log_test_result("Task Creation", False, error=str(e))
            return None

    async def test_task_retrieval(self, task: Task):
        """Test task retrieval."""
        try:
            retrieved_task = await self.repository.get_task(task.id)

            if retrieved_task:
                # Verify task data
                success = (
                    retrieved_task.id == task.id
                    and retrieved_task.title == task.title
                    and retrieved_task.assigned_agent == task.assigned_agent
                )

                self.log_test_result(
                    "Task Retrieval", success, f"Retrieved task: {retrieved_task.id}"
                )
                return retrieved_task
            else:
                self.log_test_result(
                    "Task Retrieval", False, error="Task not found after creation"
                )
                return None

        except Exception as e:
            self.log_test_result("Task Retrieval", False, error=str(e))
            return None

    async def test_task_update(self, task: Task):
        """Test task updates."""
        try:
            # Update task
            update_request = TaskUpdateRequest(
                title=f"{task.title} [UPDATED]",
                description=f"{task.description}\n\nUpdated at: {datetime.utcnow().isoformat()}",
            )

            updated_task = await self.repository.update_task(task.id, update_request)

            success = (
                updated_task.title != task.title and "[UPDATED]" in updated_task.title
            )

            self.log_test_result(
                "Task Update", success, f"Updated task: {updated_task.id}"
            )
            return updated_task

        except Exception as e:
            self.log_test_result("Task Update", False, error=str(e))
            return None

    async def test_task_status_transitions(self, task: Task):
        """Test task status transitions."""
        try:
            # Move to In Progress
            in_progress_task = await self.repository.move_task(
                task.id, TaskStatus.IN_PROGRESS
            )

            if in_progress_task.status != TaskStatus.IN_PROGRESS:
                raise Exception("Failed to move task to In Progress")

            # Move to Done
            done_task = await self.repository.move_task(task.id, TaskStatus.DONE)

            if done_task.status != TaskStatus.DONE:
                raise Exception("Failed to move task to Done")

            self.log_test_result(
                "Status Transitions",
                True,
                "Successfully transitioned: TODO → IN_PROGRESS → DONE",
            )
            return done_task

        except Exception as e:
            self.log_test_result("Status Transitions", False, error=str(e))
            return None

    async def test_task_comments(self, task: Task):
        """Test task comments."""
        try:
            # Add comment
            comment_text = f"Test comment added at {datetime.utcnow().isoformat()}"
            comment_success = await self.repository.add_comment(task.id, comment_text)

            if not comment_success:
                raise Exception("Failed to add comment")

            # Retrieve comments
            comments = await self.repository.get_comments(task.id)

            # Check if our comment exists
            comment_found = any(comment_text in str(comment) for comment in comments)

            self.log_test_result(
                "Task Comments",
                comment_found,
                f"Added and retrieved comments (count: {len(comments)})",
            )

        except Exception as e:
            self.log_test_result("Task Comments", False, error=str(e))

    async def test_task_listing(self):
        """Test task listing with filters."""
        try:
            # List all tasks
            all_tasks = await self.repository.list_tasks(limit=10)

            # List tasks by status
            todo_tasks = await self.repository.list_tasks(
                status=TaskStatus.TODO, limit=5
            )
            done_tasks = await self.repository.list_tasks(
                status=TaskStatus.DONE, limit=5
            )

            success = len(all_tasks) > 0

            self.log_test_result(
                "Task Listing",
                success,
                f"All: {len(all_tasks)}, TODO: {len(todo_tasks)}, DONE: {len(done_tasks)}",
            )

        except Exception as e:
            self.log_test_result("Task Listing", False, error=str(e))

    async def test_agent_assignment(self):
        """Test agent assignment through stickers."""
        try:
            # Test different agent assignments (use only agents with unique state IDs)
            test_agents = ["api-documenter", "frontend-developer", "business-analyst"]

            for agent in test_agents:
                if agent not in self.config.yougile.ai_owner_sticker["states"]:
                    continue

                task_request = TaskCreateRequest(
                    title=f"[TEST] Agent Assignment Test - {agent}",
                    description=f"Testing assignment to {agent}",
                    priority=TaskPriority.LOW,
                    assigned_agent=agent,
                )

                task = await self.repository.create_task(task_request)

                # Verify assignment
                retrieved_task = await self.repository.get_task(task.id)
                assignment_success = retrieved_task.assigned_agent == agent

                if not assignment_success:
                    raise Exception(f"Agent assignment failed for {agent}")

                # Clean up test task
                await self.repository.move_task(task.id, TaskStatus.DONE)

            self.log_test_result(
                "Agent Assignment",
                True,
                f"Successfully tested assignment for {len(test_agents)} agents",
            )

        except Exception as e:
            self.log_test_result("Agent Assignment", False, error=str(e))

    async def test_crm_service_integration(self):
        """Test full CRM service integration."""
        try:
            # Create task through service (with PM analysis)
            task_request = TaskCreateRequest(
                title="[TEST] CRM Service Integration Test",
                description="Test full integration through CRM service with PM analysis",
                priority=TaskPriority.HIGH,
                use_pm_analysis=True,
                auto_assign=True,
            )

            response = await self.service.create_task(task_request)

            success = (
                response.success
                and response.task is not None
                and response.pm_analysis is not None
                and len(response.agent_suggestions) > 0
            )

            details = f"Task: {response.task.id if response.task else 'None'}, "
            details += f"PM Analysis: {response.pm_analysis.complexity if response.pm_analysis else 'None'}, "
            details += f"Suggestions: {len(response.agent_suggestions)}"

            self.log_test_result("CRM Service Integration", success, details)

            # Clean up
            if response.task:
                await self.repository.move_task(response.task.id, TaskStatus.DONE)

        except Exception as e:
            self.log_test_result("CRM Service Integration", False, error=str(e))

    async def test_error_handling(self):
        """Test error handling scenarios."""
        try:
            # Test with invalid task ID
            try:
                result = await self.repository.get_task("invalid-task-id-123")
                error_handled = result is None  # get_task should return None for 404
            except Exception:
                error_handled = True  # Any exception is also acceptable

            # Test with invalid configuration
            try:
                invalid_request = TaskCreateRequest(
                    title="",  # Empty title should fail
                    description="Test invalid request",
                )
                await self.repository.create_task(invalid_request)
                validation_handled = False
            except Exception:
                validation_handled = True

            success = error_handled and validation_handled

            self.log_test_result(
                "Error Handling",
                success,
                f"Invalid ID handled: {error_handled}, Validation handled: {validation_handled}",
            )

        except Exception as e:
            self.log_test_result("Error Handling", False, error=str(e))

    async def run_all_tests(self):
        """Run all integration tests."""
        print("🧪 Starting YouGile Integration Test Suite")
        print("=" * 60)

        # Setup
        await self.setup()

        try:
            # Basic connectivity
            if not await self.test_health_check():
                print("❌ Health check failed - aborting tests")
                return

            # Core CRUD operations
            test_task = await self.test_task_creation()
            if test_task:
                retrieved_task = await self.test_task_retrieval(test_task)
                if retrieved_task:
                    updated_task = await self.test_task_update(retrieved_task)
                    if updated_task:
                        await self.test_task_status_transitions(updated_task)
                        await self.test_task_comments(updated_task)

            # Additional tests
            await self.test_task_listing()
            await self.test_agent_assignment()
            await self.test_crm_service_integration()
            await self.test_error_handling()

        finally:
            await self.cleanup()

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate test report."""
        print("\n" + "=" * 60)
        print("📊 YOUGILE INTEGRATION TEST REPORT")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test_name']}: {result['error']}")

        print("\n✅ Passed Tests:")
        for result in self.test_results:
            if result["success"]:
                print(f"  • {result['test_name']}")

        # Save detailed report
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
            },
            "detailed_results": self.test_results,
            "environment": {
                "config_file": self.config_path,
                "api_endpoint": self.repository.base_url if self.repository else None,
                "project_id": self.config.yougile.project_id if self.config else None,
            },
        }

        with open("yougile_integration_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        print("\n📄 Detailed report saved to: yougile_integration_test_report.json")

        # Return success status
        return failed_tests == 0


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="YouGile Integration Test Suite")
    parser.add_argument(
        "--config", default="config_enhanced.json", help="Configuration file path"
    )
    parser.add_argument(
        "--api-key", help="YouGile API key (overrides environment variable)"
    )

    args = parser.parse_args()

    try:
        tester = YouGileIntegrationTester(args.config, args.api_key)
        success = await tester.run_all_tests()

        print(f"\n🎯 Integration test {'PASSED' if success else 'FAILED'}")
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Test suite failed to run: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
