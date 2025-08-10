#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI-CRM Refactored Architecture
Tests all major components: models, repositories, services, gateways, selectors, and configuration.
"""

import asyncio
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

import pytest

# Import components to test
from models import (
    Task, Agent, TaskStatus, TaskPriority, TaskComplexity,
    TaskCreateRequest, TaskUpdateRequest, TaskResponse,
    AgentSuggestion, PMAnalysisRequest, PMAnalysisResult,
    RoutingContext
)
from exceptions import (
    CRMError, TaskNotFoundError, AgentNotFoundError, 
    ValidationError, AnalysisError, WorkflowError, ConfigurationError
)
from repositories import YouGileTaskRepository, AgentRepository
from crm_service import CRMService
from pm_gateway_refactored import PMAgentGatewayRefactored, TaskAnalyzer, WorkflowEngine
from agent_selector_enhanced import EnhancedAgentSelector, LearningSystem, SemanticMatcher
from agent_routing import SmartAgentRouter, WorkloadBalancer, ContextAnalyzer, RoutingStrategy
from workflow_persistence import (
    FileWorkflowStorage, SQLiteWorkflowStorage, 
    WorkflowPersistenceManager, create_file_persistence_manager
)
from config_manager import ConfigurationManager, MainConfig, YouGileConfig, AIProviderConfig


class TestModels(unittest.TestCase):
    """Test Pydantic data models."""
    
    def test_task_creation(self):
        """Test Task model validation."""
        task = Task(
            id="test-123",
            title="Test Task",
            description="A test task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM
        )
        
        self.assertEqual(task.id, "test-123")
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.priority, TaskPriority.MEDIUM)
        self.assertIsInstance(task.created_at, datetime)
    
    def test_task_validation_errors(self):
        """Test Task validation failures."""
        with self.assertRaises(ValidationError):
            Task(title="")  # Empty title should fail
        
        with self.assertRaises(ValidationError):
            Task(title="x" * 201)  # Too long title should fail
    
    def test_agent_model(self):
        """Test Agent model."""
        agent = Agent(
            name="test-agent",
            description="Test agent",
            keywords=["test", "automation"],
            max_concurrent_tasks=5,
            average_response_time_hours=2.0
        )
        
        self.assertEqual(agent.name, "test-agent")
        self.assertEqual(agent.max_concurrent_tasks, 5)
        self.assertEqual(agent.current_workload, 0)
        self.assertTrue(agent.is_available)
    
    def test_task_create_request(self):
        """Test TaskCreateRequest model."""
        request = TaskCreateRequest(
            title="New Feature",
            description="Implement new feature",
            priority=TaskPriority.HIGH
        )
        
        self.assertEqual(request.title, "New Feature")
        self.assertEqual(request.priority, TaskPriority.HIGH)
        self.assertTrue(request.use_pm_analysis)  # Default value
    
    def test_pm_analysis_result(self):
        """Test PMAnalysisResult model."""
        result = PMAnalysisResult(
            task_type="complex_task",
            complexity=TaskComplexity.COMPLEX,
            priority=TaskPriority.HIGH,
            estimated_hours=24.0,
            required_agents=["backend-architect", "frontend-developer"],
            recommended_agent="backend-architect",
            subtasks=[],
            risk_factors=["Legacy system integration"],
            success_criteria=["All tests passing"],
            recommendation="Break into subtasks"
        )
        
        self.assertEqual(result.task_type, "complex_task")
        self.assertEqual(result.complexity, TaskComplexity.COMPLEX)
        self.assertEqual(len(result.required_agents), 2)
        self.assertEqual(len(result.risk_factors), 1)


class TestExceptions(unittest.TestCase):
    """Test exception hierarchy."""
    
    def test_crm_error_hierarchy(self):
        """Test exception inheritance."""
        error = TaskNotFoundError("Task not found", "task-123")
        
        self.assertIsInstance(error, CRMError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Task not found")
        self.assertEqual(error.task_id, "task-123")
    
    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("Invalid config", {"key": "value"})
        
        self.assertEqual(error.message, "Invalid config")
        self.assertEqual(error.details["key"], "value")


class TestTaskAnalyzer(unittest.TestCase):
    """Test PM Gateway task analyzer."""
    
    def setUp(self):
        self.analyzer = TaskAnalyzer()
    
    def test_complexity_analysis(self):
        """Test task complexity analysis."""
        # Simple task
        simple_complexity = self.analyzer.analyze_complexity(
            "Fix button color", 
            "Change the submit button color to blue"
        )
        self.assertEqual(simple_complexity, TaskComplexity.SIMPLE)
        
        # Complex task
        complex_complexity = self.analyzer.analyze_complexity(
            "Redesign system architecture", 
            "Complete platform migration with new architecture"
        )
        self.assertEqual(complex_complexity, TaskComplexity.COMPLEX)
    
    def test_priority_analysis(self):
        """Test task priority analysis."""
        # Urgent task
        urgent_priority = self.analyzer.analyze_priority(
            "Production down", 
            "Critical system outage affecting all users"
        )
        self.assertEqual(urgent_priority, TaskPriority.URGENT)
        
        # Low priority task
        low_priority = self.analyzer.analyze_priority(
            "Update documentation", 
            "Refresh user guide with latest features"
        )
        self.assertEqual(low_priority, TaskPriority.LOW)
    
    def test_effort_estimation(self):
        """Test effort estimation."""
        simple_effort = self.analyzer.estimate_effort(TaskComplexity.SIMPLE)
        self.assertEqual(simple_effort, 2.0)
        
        epic_effort = self.analyzer.estimate_effort(TaskComplexity.EPIC)
        self.assertEqual(epic_effort, 80.0)
    
    def test_risk_identification(self):
        """Test risk factor identification."""
        risks = self.analyzer.identify_risk_factors(
            "Legacy system migration", 
            "Migrate old database to new schema with external API integration"
        )
        
        self.assertGreater(len(risks), 0)
        self.assertTrue(any("legacy" in risk.lower() for risk in risks))
        self.assertTrue(any("migration" in risk.lower() for risk in risks))


class TestWorkflowEngine(unittest.TestCase):
    """Test workflow engine."""
    
    def setUp(self):
        self.engine = WorkflowEngine()
    
    def test_workflow_template_selection(self):
        """Test workflow template selection."""
        # Data analysis task
        template = self.engine.select_workflow_template(
            "Sales data analysis", 
            "Analyze quarterly sales metrics and create report",
            TaskComplexity.MODERATE
        )
        self.assertEqual(template, "data_analysis")
        
        # Bug fix task
        template = self.engine.select_workflow_template(
            "Fix login error", 
            "Users unable to login, getting authentication error",
            TaskComplexity.SIMPLE
        )
        self.assertEqual(template, "bug_fix")
    
    def test_workflow_creation(self):
        """Test workflow creation."""
        workflow = self.engine.create_workflow(
            "New API endpoint",
            "Create REST API for user management",
            TaskComplexity.MODERATE,
            ["backend-architect", "api-documenter"]
        )
        
        self.assertIn("template", workflow)
        self.assertIn("steps", workflow)
        self.assertIn("total_hours", workflow)
        self.assertIn("estimated_days", workflow)
        self.assertGreater(len(workflow["steps"]), 0)
        self.assertGreater(workflow["total_hours"], 0)
    
    def test_task_decomposition(self):
        """Test complex task decomposition."""
        workflow = {
            "steps": [
                {"step": "design", "agent": "backend-architect", "duration_hours": 4},
                {"step": "implementation", "agent": "python-pro", "duration_hours": 8},
                {"step": "testing", "agent": "test-automator", "duration_hours": 2}
            ]
        }
        
        subtasks = self.engine.decompose_complex_task(
            "User Authentication System",
            "Implement complete user authentication with JWT",
            workflow
        )
        
        self.assertEqual(len(subtasks), 3)
        self.assertEqual(subtasks[0]["phase"], 1)
        self.assertEqual(subtasks[1]["depends_on"], subtasks[0]["title"])
        self.assertIn("Design", subtasks[0]["title"])


@pytest.mark.asyncio
class TestAsyncComponents:
    """Test async components using pytest-asyncio."""
    
    async def test_workflow_persistence_file(self):
        """Test file-based workflow persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileWorkflowStorage(temp_dir)
            
            # Test save and load
            workflow_data = {
                "title": "Test Workflow",
                "description": "Test workflow description",
                "status": "active",
                "steps": [{"step": "test", "agent": "test-agent"}]
            }
            
            success = await storage.save_workflow("test-workflow", workflow_data)
            assert success
            
            loaded_data = await storage.load_workflow("test-workflow")
            assert loaded_data is not None
            assert loaded_data["title"] == "Test Workflow"
            assert loaded_data["workflow_id"] == "test-workflow"
            
            # Test update
            updates = {"status": "completed"}
            success = await storage.update_workflow("test-workflow", updates)
            assert success
            
            updated_data = await storage.load_workflow("test-workflow")
            assert updated_data["status"] == "completed"
            
            # Test list workflows
            workflows = await storage.list_workflows()
            assert len(workflows) == 1
            assert workflows[0]["title"] == "Test Workflow"
            
            # Test cleanup
            cleaned = await storage.cleanup_old_workflows(days=0)
            assert cleaned == 1  # Should clean up completed workflow
    
    async def test_workflow_persistence_manager(self):
        """Test workflow persistence manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = create_file_persistence_manager(temp_dir, enable_caching=True)
            
            # Test save workflow state
            workflow_data = {"analysis": "test", "complexity": "moderate"}
            success = await manager.save_workflow_state(
                "task-123", 
                "Test Task",
                "Test description",
                workflow_data
            )
            assert success
            
            # Test load workflow state (should hit cache)
            loaded_data = await manager.load_workflow_state("task-123")
            assert loaded_data is not None
            assert loaded_data["title"] == "Test Task"
            assert loaded_data["analysis"] == "test"
            
            # Test update workflow status
            success = await manager.update_workflow_status("task-123", "in_progress")
            assert success
            
            # Test complete workflow
            completion_data = {"result": "success", "time_taken": 5.5}
            success = await manager.complete_workflow("task-123", completion_data)
            assert success
            
            # Test health check
            health = await manager.health_check()
            assert health["backend_healthy"]
            assert health["cache_enabled"]
    
    async def test_enhanced_agent_selector(self):
        """Test enhanced agent selector."""
        selector = EnhancedAgentSelector(enable_semantic=False)  # Disable semantic for testing
        await selector.initialize()
        
        # Test agent suggestions
        suggestions = await selector.suggest_agents(
            "Create a Python API endpoint with database integration",
            max_suggestions=3
        )
        
        assert len(suggestions) <= 3
        assert all(isinstance(s, AgentSuggestion) for s in suggestions)
        assert all(s.confidence > 0 for s in suggestions)
        
        # Check that appropriate agents are suggested
        agent_names = [s.agent_name for s in suggestions]
        assert any("python" in name or "backend" in name for name in agent_names)
    
    async def test_learning_system(self):
        """Test agent learning system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "learning.json"
            learning_system = LearningSystem(str(storage_path))
            
            # Record task outcomes
            from agent_selector_enhanced import TaskOutcome
            
            outcome1 = TaskOutcome(
                task_id="task-1",
                task_description="Fix Python bug in authentication",
                assigned_agent="python-pro",
                success=True,
                completion_time_hours=3.5,
                user_rating=4.5
            )
            
            outcome2 = TaskOutcome(
                task_id="task-2", 
                task_description="Create React component for user profile",
                assigned_agent="frontend-developer",
                success=True,
                completion_time_hours=6.0,
                user_rating=4.0
            )
            
            learning_system.record_outcome(outcome1)
            learning_system.record_outcome(outcome2)
            
            # Test performance scoring
            python_score = learning_system.get_agent_performance_score(
                "python-pro", 
                "Fix authentication bug in Python service"
            )
            assert python_score > 0.5  # Should be good performance
            
            # Test insights
            insights = learning_system.get_performance_insights()
            assert insights["total_outcomes"] == 2
            assert insights["overall_success_rate"] == 1.0
    
    async def test_smart_agent_router(self):
        """Test smart agent routing."""
        # Mock agent repository
        mock_repo = Mock()
        
        # Create test agents
        agents = [
            Agent(name="python-pro", max_concurrent_tasks=5, current_workload=1),
            Agent(name="frontend-developer", max_concurrent_tasks=3, current_workload=2),
            Agent(name="backend-architect", max_concurrent_tasks=4, current_workload=0)
        ]
        
        async def mock_get_agent(name):
            return next((a for a in agents if a.name == name), None)
        
        mock_repo.get_agent = mock_get_agent
        
        router = SmartAgentRouter(mock_repo)
        
        # Create agent suggestions
        suggestions = [
            AgentSuggestion(agent_name="python-pro", confidence=85.0, reasoning="Python expert"),
            AgentSuggestion(agent_name="backend-architect", confidence=75.0, reasoning="Architecture match"),
            AgentSuggestion(agent_name="frontend-developer", confidence=60.0, reasoning="General match")
        ]
        
        # Create routing context
        context = RoutingContext(
            task_priority=TaskPriority.HIGH,
            task_complexity=TaskComplexity.MODERATE,
            estimated_hours=6.0
        )
        
        # Test different routing strategies
        strategies = [
            RoutingStrategy.BEST_MATCH,
            RoutingStrategy.LOAD_BALANCED,
            RoutingStrategy.PRIORITY_AWARE,
            RoutingStrategy.CONTEXT_AWARE
        ]
        
        for strategy in strategies:
            agent_name, routing_score = await router.route_task(
                suggestions, context, strategy, "Create Python API endpoint"
            )
            
            assert agent_name in [s.agent_name for s in suggestions]
            assert routing_score.agent_name == agent_name
            assert routing_score.composite_score > 0


class TestConfigurationManager(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_loading(self):
        """Test configuration loading and validation."""
        # Create test config file
        test_config = {
            "ai_provider": {
                "provider": "openai",
                "model": "gpt-4",
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "yougile": {
                "project_id": "test-project",
                "board_id": "test-board",
                "columns": {
                    "To Do": "col-1",
                    "In Progress": "col-2", 
                    "Done": "col-3"
                }
            },
            "agents": {
                "enabled_agents": ["python-pro", "frontend-developer"],
                "agent_configs": {
                    "python-pro": {
                        "name": "python-pro",
                        "description": "Python expert",
                        "keywords": ["python", "api", "backend"]
                    },
                    "frontend-developer": {
                        "name": "frontend-developer",
                        "description": "Frontend expert", 
                        "keywords": ["react", "javascript", "ui"]
                    }
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Test loading
        config_manager = ConfigurationManager(str(self.config_path))
        config = config_manager.load_config()
        
        self.assertIsInstance(config, MainConfig)
        self.assertEqual(config.ai_provider.provider, "openai")
        self.assertEqual(config.ai_provider.model, "gpt-4")
        self.assertEqual(config.yougile.project_id, "test-project")
        self.assertEqual(len(config.agents.enabled_agents), 2)
    
    def test_environment_overrides(self):
        """Test environment variable overrides."""
        # Set environment variables
        os.environ["AI_CRM_DEBUG"] = "true"
        os.environ["AI_CRM_LOG_LEVEL"] = "DEBUG"
        os.environ["AI_CRM_MAX_CONCURRENT"] = "20"
        
        try:
            config_manager = ConfigurationManager(str(self.config_path))
            
            # Create minimal config
            minimal_config = {
                "ai_provider": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo"
                },
                "yougile": {
                    "project_id": "test",
                    "board_id": "test",
                    "columns": {"To Do": "1", "In Progress": "2", "Done": "3"}
                },
                "agents": {
                    "enabled_agents": ["general-purpose"],
                    "agent_configs": {
                        "general-purpose": {"name": "general-purpose"}
                    }
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(minimal_config, f)
            
            config = config_manager.load_config()
            
            # Check environment overrides
            self.assertTrue(config.debug)
            self.assertEqual(config.logging.level.value, "DEBUG")
            self.assertEqual(config.performance.max_concurrent_requests, 20)
            
        finally:
            # Cleanup environment
            del os.environ["AI_CRM_DEBUG"]
            del os.environ["AI_CRM_LOG_LEVEL"]
            del os.environ["AI_CRM_MAX_CONCURRENT"]
    
    def test_config_validation_errors(self):
        """Test configuration validation errors."""
        # Invalid config - missing required fields
        invalid_config = {
            "ai_provider": {
                "provider": "invalid_provider",  # Invalid provider
                "model": "test-model"
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        config_manager = ConfigurationManager(str(self.config_path))
        
        with self.assertRaises(ConfigurationError):
            config_manager.load_config()
    
    def test_runtime_validation(self):
        """Test runtime configuration validation."""
        # Create valid config
        valid_config = {
            "ai_provider": {
                "provider": "openai",
                "model": "gpt-4"
            },
            "yougile": {
                "project_id": "test-project",
                "board_id": "test-board",
                "columns": {"To Do": "1", "In Progress": "2", "Done": "3"}
            },
            "agents": {
                "enabled_agents": ["test-agent"],
                "agent_configs": {
                    "test-agent": {"name": "test-agent"}
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(valid_config, f)
        
        config_manager = ConfigurationManager(str(self.config_path))
        config = config_manager.load_config()
        
        # Test runtime validation
        validation_result = config_manager.validate_runtime_config()
        
        # Should have issues due to missing API keys
        self.assertFalse(validation_result["valid"])
        self.assertGreater(len(validation_result["issues"]), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for combined components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.test_config = {
            "ai_provider": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "test-key"
            },
            "yougile": {
                "project_id": "test-project",
                "board_id": "test-board", 
                "columns": {"To Do": "1", "In Progress": "2", "Done": "3"},
                "api_key": "test-yougile-key"
            },
            "agents": {
                "enabled_agents": ["python-pro", "frontend-developer"],
                "agent_configs": {
                    "python-pro": {
                        "name": "python-pro",
                        "description": "Python expert",
                        "keywords": ["python", "api", "backend"],
                        "max_concurrent_tasks": 5
                    },
                    "frontend-developer": {
                        "name": "frontend-developer", 
                        "description": "Frontend expert",
                        "keywords": ["react", "javascript", "ui"],
                        "max_concurrent_tasks": 3
                    }
                }
            },
            "workflow": {
                "storage_backend": "file",
                "storage_path": str(Path(self.temp_dir) / "workflows")
            }
        }
        
        self.config_path = Path(self.temp_dir) / "config.json"
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up test environment.""" 
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('repositories.httpx.AsyncClient')
    @patch.dict(os.environ, {'AI_CRM_YOUGILE_API_KEY': 'test-key'})
    async def test_full_task_creation_flow(self, mock_client):
        """Test complete task creation flow."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "task-123",
            "title": "Test Task",
            "description": "Test description",
            "columnId": "1"
        }
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Create CRM service
        from crm_service import create_crm_service
        
        service = await create_crm_service(
            api_key="test-key",
            config_path=str(self.config_path)
        )
        
        # Create task request
        task_request = TaskCreateRequest(
            title="Create Python API endpoint",
            description="Implement REST API for user management with authentication",
            priority=TaskPriority.HIGH,
            use_pm_analysis=True,
            auto_assign=True
        )
        
        # Execute task creation
        response = await service.create_task(task_request)
        
        # Verify response
        self.assertTrue(response.success)
        self.assertIsNotNone(response.task)
        self.assertEqual(response.task.title, "Create Python API endpoint")
        self.assertIsNotNone(response.pm_analysis)
        self.assertIsNotNone(response.agent_suggestions)
        
        # Verify PM analysis
        pm_analysis = response.pm_analysis
        self.assertIn(pm_analysis.complexity, [TaskComplexity.MODERATE, TaskComplexity.COMPLEX])
        self.assertEqual(pm_analysis.priority, TaskPriority.HIGH)
        self.assertGreater(pm_analysis.estimated_hours, 0)
        self.assertGreater(len(pm_analysis.required_agents), 0)
        
        # Verify agent suggestions
        self.assertGreater(len(response.agent_suggestions), 0)
        agent_names = [s.agent_name for s in response.agent_suggestions]
        self.assertTrue(any("python" in name for name in agent_names))


def run_async_test(coro):
    """Helper to run async tests in unittest."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Test runner and utilities
class TestRunner:
    """Test runner with reporting capabilities."""
    
    @staticmethod
    def run_all_tests():
        """Run all test suites and return results."""
        # Discover and run tests
        loader = unittest.TestLoader()
        
        # Load unittest-based tests
        test_suites = [
            loader.loadTestsFromTestCase(TestModels),
            loader.loadTestsFromTestCase(TestExceptions), 
            loader.loadTestsFromTestCase(TestTaskAnalyzer),
            loader.loadTestsFromTestCase(TestWorkflowEngine),
            loader.loadTestsFromTestCase(TestConfigurationManager),
        ]
        
        # Combine all test suites
        combined_suite = unittest.TestSuite(test_suites)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
        result = runner.run(combined_suite)
        
        return {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            "details": {
                "failures": [str(failure) for failure in result.failures],
                "errors": [str(error) for error in result.errors]
            }
        }
    
    @staticmethod
    def run_async_tests():
        """Run async tests using pytest."""
        try:
            import subprocess
            import sys
            
            # Run pytest for async tests
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                __file__ + "::TestAsyncComponents",
                "-v", "--tb=short"
            ], capture_output=True, text=True)
            
            return {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except Exception as e:
            return {
                "return_code": -1,
                "error": str(e),
                "success": False
            }
    
    @staticmethod
    def generate_test_report() -> Dict[str, Any]:
        """Generate comprehensive test report."""
        print("🧪 Running AI-CRM Test Suite...")
        print("=" * 50)
        
        # Run synchronous tests
        print("\n📋 Running Unit Tests...")
        sync_results = TestRunner.run_all_tests()
        
        # Run async tests
        print("\n🔄 Running Async Tests...")
        async_results = TestRunner.run_async_tests()
        
        # Generate report
        total_tests = sync_results["tests_run"]
        total_failures = sync_results["failures"]
        total_errors = sync_results["errors"]
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": total_tests - total_failures - total_errors,
                "failed": total_failures,
                "errors": total_errors,
                "success_rate": sync_results["success_rate"],
                "async_tests_success": async_results["success"]
            },
            "sync_test_results": sync_results,
            "async_test_results": async_results,
            "recommendations": []
        }
        
        # Add recommendations based on results
        if total_failures > 0:
            report["recommendations"].append(
                f"Fix {total_failures} failing tests before deployment"
            )
        
        if total_errors > 0:
            report["recommendations"].append(
                f"Resolve {total_errors} test errors"
            )
        
        if not async_results["success"]:
            report["recommendations"].append(
                "Review async test failures and fix integration issues"
            )
        
        if sync_results["success_rate"] > 0.9:
            report["recommendations"].append(
                "Test suite passing well - ready for integration testing"
            )
        
        return report


if __name__ == "__main__":
    # Run tests when executed directly
    test_runner = TestRunner()
    report = test_runner.generate_test_report()
    
    print("\n" + "=" * 50)
    print("📊 TEST REPORT SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1%}")
    print(f"Async Tests: {'✅ PASSED' if report['summary']['async_tests_success'] else '❌ FAILED'}")
    
    if report["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    
    print("\n" + "=" * 50)