import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'our-crm-ai'))

from analytics_engine import AnalyticsEngine
from models import Project, Task, Risk, TaskStatus

class TestAnalyticsEngine(unittest.TestCase):

    def _create_mock_projects(self):
        """Helper to create a list of mock Project objects."""
        return [
            Project(
                id="proj1",
                title="Project Alpha",
                description="First project",
                tasks=[
                    Task(id="t1", title="Task 1", description="", status=TaskStatus.DONE, assigned_agent="python-pro"),
                    Task(id="t2", title="Task 2", description="", status=TaskStatus.IN_PROGRESS, assigned_agent="frontend-developer"),
                ],
                risks=[]
            ),
            Project(
                id="proj2",
                title="Project Beta",
                description="Second project",
                tasks=[
                    Task(id="t3", title="Task 3", description="", status=TaskStatus.DONE, assigned_agent="python-pro"),
                    Task(id="t4", title="Task 4", description="", status=TaskStatus.DONE, assigned_agent="backend-architect"),
                    Task(id="t5", title="Task 5", description="", status=TaskStatus.TODO, assigned_agent="devops-troubleshooter"),
                ],
                risks=[]
            )
        ]

    @patch('analytics_engine.FileProjectRepository')
    def test_generate_executive_dashboard(self, MockProjectRepository):
        """Test that the executive dashboard generates correct metrics from mock projects."""

        # 1. Setup Mock
        mock_repo_instance = MockProjectRepository.return_value
        mock_repo_instance.list_projects.return_value = self._create_mock_projects()

        # 2. Initialize the engine (this will use the mocked repository)
        analytics_engine = AnalyticsEngine()

        # 3. Call the method to be tested
        dashboard_data = analytics_engine.generate_executive_dashboard()

        # 4. Assertions

        # System Overview
        overview = dashboard_data['system_overview']
        self.assertEqual(overview['total_projects'], 2)
        self.assertEqual(overview['total_tasks'], 5)
        self.assertEqual(overview['total_agents'], 4)

        # Performance KPIs
        kpis = dashboard_data['performance_kpis']
        self.assertAlmostEqual(kpis['task_completion_rate'], 60.0) # 3 of 5 tasks are DONE

        tasks_by_status = kpis['tasks_by_status']
        self.assertEqual(tasks_by_status[TaskStatus.DONE], 3)
        self.assertEqual(tasks_by_status[TaskStatus.IN_PROGRESS], 1)
        self.assertEqual(tasks_by_status[TaskStatus.TODO], 1)
        self.assertEqual(tasks_by_status[TaskStatus.ARCHIVED], 0)

        # Top Performing Agents
        top_agents = kpis['top_performing_agents']
        self.assertEqual(len(top_agents), 4)

        # python-pro should be first (2/2 completed -> 100%)
        self.assertEqual(top_agents[0]['agent'], 'python-pro')
        self.assertEqual(top_agents[0]['completed'], 2)
        self.assertEqual(top_agents[0]['total'], 2)
        self.assertAlmostEqual(top_agents[0]['success_rate'], 100.0)

        # backend-architect should be second (1/1 completed -> 100%)
        self.assertEqual(top_agents[1]['agent'], 'backend-architect')
        self.assertAlmostEqual(top_agents[1]['success_rate'], 100.0)

        # The other two have 0% completion
        self.assertEqual(top_agents[2]['agent'], 'frontend-developer')
        self.assertAlmostEqual(top_agents[2]['success_rate'], 0.0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
