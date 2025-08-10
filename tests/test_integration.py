import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'our-crm-ai'))

from analytics_engine import AnalyticsEngine
from models import Project, Task, Risk, TaskStatus

class TestIntegration(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.projects_file = "projects_test.json"
        self.config_file = "config_test.json"

        # Create a dummy config file
        with open(self.config_file, 'w') as f:
            json.dump({
                "ai_owner_sticker": {"id": "s1", "states": {"python-pro": "st1"}}
            }, f)

        # Ensure the projects file is clean before each test
        if os.path.exists(self.projects_file):
            os.remove(self.projects_file)

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.projects_file):
            os.remove(self.projects_file)
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def _get_mock_gateway_output(self):
        """Returns a fixed output for the PMAgentGateway mock."""
        return {
            'type': 'complex_task',
            'original_task': {'title': 'Test Project', 'description': 'A test project.'},
            'analysis': {
                'risk_factors': ['High complexity']
            },
            'subtasks': [
                {'title': 'Subtask 1', 'agent': 'python-pro', 'depends_on': None},
                {'title': 'Subtask 2', 'agent': 'frontend-developer', 'depends_on': 'Subtask 1'},
            ]
        }

    @patch.dict(os.environ, {'YOUGILE_API_KEY': 'DUMMY_KEY'}, clear=True)
    def test_end_to_end_flow(self):
        """Test the full flow from CLI command to analytics."""

        # --- Part 1: Test the CLI command and project creation ---

        # Use a side effect to mock the repository and gateway inside the patched environment
        def run_cli_with_mocks(*args, **kwargs):
            # Import the module here, after the environment is patched
            import crm_enhanced

            with patch('crm_enhanced.PMAgentGateway') as MockGateway, \
                 patch('crm_enhanced.FileProjectRepository') as MockProjectRepository:

                # Configure mocks
                mock_gateway_instance = MockGateway.return_value
                mock_gateway_instance.create_managed_task.return_value = self._get_mock_gateway_output()

                # Configure the repo mock to use the test file
                mock_repo_instance = MockProjectRepository.return_value

                # This is a bit of a hack to make the file-based repo testable
                # without actually writing files in the main test flow.
                # We'll simulate the save and then load from the object.
                saved_projects = {}
                def side_effect_create(project_req):
                    p = Project(**project_req.dict())
                    mock_repo_instance.projects[p.id] = p
                    saved_projects[p.id] = p
                    return p

                def side_effect_add_task(project_id, task):
                    saved_projects[project_id].tasks.append(task)
                    return saved_projects[project_id]

                def side_effect_add_risk(project_id, risk):
                    saved_projects[project_id].risks.append(risk)
                    return saved_projects[project_id]

                mock_repo_instance.projects = {}
                mock_repo_instance.create_project.side_effect = side_effect_create
                mock_repo_instance.add_task_to_project.side_effect = side_effect_add_task
                mock_repo_instance.add_risk_to_project.side_effect = side_effect_add_risk

                # Mock the config loading
                with patch('crm_enhanced.load_config') as mock_load_config:
                    with open(self.config_file, 'r') as f:
                        mock_load_config.return_value = json.load(f)

                    # Run the main function with patched argv
                    with patch('sys.argv', ['crm_enhanced.py', 'pm', '--title', 'Test Project', '--description', 'A test project.']):
                        crm_enhanced.main()

                return saved_projects

        # Run the CLI and get the projects that would have been saved
        saved_projects_dict = run_cli_with_mocks()

        self.assertEqual(len(saved_projects_dict), 1)
        project_id = list(saved_projects_dict.keys())[0]
        project = saved_projects_dict[project_id]

        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(len(project.tasks), 2)
        self.assertEqual(len(project.risks), 1)
        self.assertEqual(project.risks[0].description, 'High complexity')

        task1 = project.tasks[0]
        task2 = project.tasks[1]
        self.assertEqual(task1.title, 'Subtask 1')
        self.assertEqual(task2.title, 'Subtask 2')
        self.assertEqual(len(task2.metadata.dependencies), 1)
        self.assertEqual(task2.metadata.dependencies[0], task1.id)

        # --- Part 2: Test the Analytics Engine ---

        # Patch the repo used by the analytics engine to use our test file
        with patch('analytics_engine.FileProjectRepository') as MockAnalyticsRepo:
            mock_analytics_repo_instance = MockAnalyticsRepo.return_value
            mock_analytics_repo_instance.list_projects.return_value = list(saved_projects_dict.values())

            # We also need to patch the config loading in the engine
            with patch('analytics_engine.open') as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = "{}"
                analytics_engine = AnalyticsEngine()
                dashboard = analytics_engine.generate_executive_dashboard()

        # Assert analytics data is correct
        self.assertEqual(dashboard['system_overview']['total_projects'], 1)
        self.assertEqual(dashboard['system_overview']['total_tasks'], 2)
        self.assertEqual(dashboard['performance_kpis']['task_completion_rate'], 0.0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
