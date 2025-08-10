import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from repositories import FileProjectRepository
from models import Project, Task, Risk, TaskStatus

class AnalyticsEngine:
    """
    Comprehensive analytics engine for AI-CRM system
    Handles metrics collection, processing, and reporting
    """
    def __init__(self, config_path: str = 'config.json'):
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {} # Handle case where config is not found

        self.project_repo = FileProjectRepository()
        self.projects = self.project_repo.list_projects()
        
        self.metrics = {
            'task_completion': {},
            'agent_performance': {},
            'user_engagement': {},
            'workflow_efficiency': {},
            'cross_platform_insights': {}
        }
        
        self.historical_data = {}
    
    def collect_task_completion_metrics(self, tasks: List[Dict]) -> Dict:
        """
        Analyze task completion rates and performance
        
        Args:
            tasks (List[Dict]): List of completed tasks
        
        Returns:
            Dict: Task completion analytics
        """
        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task['status'] == 'completed'])
        
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        avg_task_duration = sum(task['duration'] for task in tasks) / total_tasks if total_tasks > 0 else 0
        
        self.metrics['task_completion'] = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completion_rate,
            'avg_task_duration': avg_task_duration,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.metrics['task_completion']
    
    def analyze_agent_performance(self, agent_logs: List[Dict]) -> Dict:
        """
        Calculate agent performance metrics
        
        Args:
            agent_logs (List[Dict]): Logs from various agents
        
        Returns:
            Dict: Agent performance analytics
        """
        agent_metrics = {}
        
        for log in agent_logs:
            agent_name = log['agent_name']
            if agent_name not in agent_metrics:
                agent_metrics[agent_name] = {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'success_rate': 0,
                    'avg_response_time': 0
                }
            
            agent_metrics[agent_name]['total_tasks'] += 1
            if log['status'] == 'completed':
                agent_metrics[agent_name]['completed_tasks'] += 1
        
        for agent, metrics in agent_metrics.items():
            metrics['success_rate'] = (metrics['completed_tasks'] / metrics['total_tasks']) * 100 \
                if metrics['total_tasks'] > 0 else 0
        
        self.metrics['agent_performance'] = agent_metrics
        return self.metrics['agent_performance']
    
    def generate_executive_dashboard(self) -> Dict:
        """
        Generate high-level executive dashboard from real project data.
        
        Returns:
            Dict: Executive-level business metrics
        """
        all_tasks = [task for project in self.projects for task in project.tasks]
        total_tasks = len(all_tasks)
        completed_tasks = len([task for task in all_tasks if task.status == TaskStatus.DONE])
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        all_agents = [task.assigned_agent for task in all_tasks if task.assigned_agent]
        unique_agents = set(all_agents)

        executive_dashboard = {
            'system_overview': {
                'total_projects': len(self.projects),
                'total_tasks': total_tasks,
                'total_agents': len(unique_agents),
            },
            'performance_kpis': {
                'task_completion_rate': round(completion_rate, 2),
                'tasks_by_status': self._get_tasks_by_status(all_tasks),
                'top_performing_agents': self._get_top_performing_agents(all_tasks),
            },
            'business_insights': {
                'potential_optimizations': self._recommend_optimizations()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return executive_dashboard

    def _get_tasks_by_status(self, tasks: List[Task]) -> Dict[str, int]:
        """Get a count of tasks for each status."""
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            if task.status.value in status_counts:
                status_counts[task.status.value] += 1
        return status_counts

    def _get_top_performing_agents(self, tasks: List[Task], top_n: int = 5) -> List[Dict]:
        """Get top N performing agents based on completed tasks."""
        agent_performance = {}
        for task in tasks:
            if not task.assigned_agent:
                continue

            agent_name = task.assigned_agent
            if agent_name not in agent_performance:
                agent_performance[agent_name] = {'completed': 0, 'total': 0}

            agent_performance[agent_name]['total'] += 1
            if task.status == TaskStatus.DONE:
                agent_performance[agent_name]['completed'] += 1

        # Calculate success rate
        for agent, stats in agent_performance.items():
            stats['success_rate'] = (stats['completed'] / stats['total']) * 100 if stats['total'] > 0 else 0

        # Sort agents by success rate and then by completed tasks
        sorted_agents = sorted(
            agent_performance.items(),
            key=lambda item: (item[1]['success_rate'], item[1]['completed']),
            reverse=True
        )

        return [
            {'agent': agent, **stats} for agent, stats in sorted_agents
        ][:top_n]
    
    def _calculate_workflow_efficiency(self) -> float:
        """Calculate overall workflow efficiency"""
        # Placeholder implementation
        return 78.5  # percentage
    
    def _identify_trending_tasks(self) -> List[Dict]:
        """Identify most frequent or critical tasks"""
        # Placeholder implementation
        return [
            {'task_type': 'Customer Onboarding', 'frequency': 42},
            {'task_type': 'Support Ticket Resolution', 'frequency': 35}
        ]
    
    def _recommend_optimizations(self) -> List[str]:
        """Generate optimization recommendations"""
        # Placeholder implementation
        return [
            "Reduce agent context switching time",
            "Optimize high-complexity task routing",
            "Enhance cross-platform integration efficiency"
        ]

def initialize_analytics(config_path: str = 'config.json') -> AnalyticsEngine:
    """
    Initialize and configure the analytics engine
    
    Args:
        config_path (str): Path to configuration file
    
    Returns:
        AnalyticsEngine: Configured analytics engine
    """
    return AnalyticsEngine(config_path)