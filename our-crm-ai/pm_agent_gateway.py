#!/usr/bin/env python3
"""
PM Agent Gateway - Intelligent task routing and agent orchestration system.

This module acts as a Project Manager agent that:
1. Analyzes incoming tasks and requirements
2. Determines optimal agent assignment and workflow
3. Coordinates multi-agent tasks with dependencies
4. Monitors progress and handles escalations
5. Provides intelligent task decomposition
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from agent_selector import suggest_agents, AGENT_KEYWORDS
# Import removed to avoid circular imports - will use local validation


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2  
    HIGH = 3
    URGENT = 4


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = 1      # Single agent, < 4 hours
    MODERATE = 2    # 1-2 agents, < 1 day
    COMPLEX = 3     # 2-4 agents, < 1 week
    EPIC = 4        # 4+ agents, > 1 week


@dataclass
class TaskAnalysis:
    """Analysis results for a task."""
    complexity: TaskComplexity
    estimated_hours: float
    required_agents: List[str]
    dependencies: List[str]
    risk_factors: List[str]
    success_criteria: List[str]


@dataclass  
class AgentWorkflow:
    """Workflow definition for multi-agent coordination."""
    task_id: str
    primary_agent: str
    supporting_agents: List[str]
    workflow_steps: List[Dict]
    estimated_completion: str
    dependencies: List[str]


class PMAgentGateway:
    """PM Agent Gateway for intelligent task coordination."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the PM Agent Gateway."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_path)
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Agent specializations for workflow planning
        self.agent_specializations = {
            'frontend-developer': ['ui', 'ux', 'react', 'vue', 'html', 'css'],
            'backend-architect': ['api', 'microservices', 'database', 'architecture'],
            'devops-troubleshooter': ['deployment', 'infrastructure', 'monitoring'],
            'security-auditor': ['authentication', 'authorization', 'vulnerabilities'],
            'database-optimizer': ['queries', 'performance', 'indexing'],
            'ai-engineer': ['llm', 'ml', 'data-processing', 'automation'],
            'business-analyst': ['requirements', 'analysis', 'planning', 'metrics']
        }
        
        # Common task patterns and their workflows
        self.workflow_templates = {
            'full_stack_feature': [
                {'step': 'requirements_analysis', 'agent': 'business-analyst', 'duration_hours': 4},
                {'step': 'api_design', 'agent': 'backend-architect', 'duration_hours': 6}, 
                {'step': 'frontend_design', 'agent': 'frontend-developer', 'duration_hours': 8},
                {'step': 'implementation', 'agent': 'auto', 'duration_hours': 16},
                {'step': 'testing', 'agent': 'test-automator', 'duration_hours': 4},
                {'step': 'security_review', 'agent': 'security-auditor', 'duration_hours': 2},
                {'step': 'deployment', 'agent': 'devops-troubleshooter', 'duration_hours': 3}
            ],
            'data_analysis': [
                {'step': 'data_collection', 'agent': 'data-engineer', 'duration_hours': 6},
                {'step': 'analysis', 'agent': 'data-scientist', 'duration_hours': 8},
                {'step': 'visualization', 'agent': 'business-analyst', 'duration_hours': 4},
                {'step': 'reporting', 'agent': 'docs-architect', 'duration_hours': 3}
            ],
            'infrastructure_setup': [
                {'step': 'architecture_design', 'agent': 'cloud-architect', 'duration_hours': 8},
                {'step': 'infrastructure_code', 'agent': 'terraform-specialist', 'duration_hours': 12},
                {'step': 'deployment', 'agent': 'deployment-engineer', 'duration_hours': 6},
                {'step': 'monitoring', 'agent': 'devops-troubleshooter', 'duration_hours': 4},
                {'step': 'security_hardening', 'agent': 'security-auditor', 'duration_hours': 6}
            ]
        }

    def analyze_task(self, title: str, description: str, context: Dict = None) -> TaskAnalysis:
        """Perform comprehensive task analysis."""
        text = f"{title} {description}".lower()
        
        # Determine complexity based on keywords and scope
        complexity_indicators = {
            'simple': ['fix', 'update', 'change', 'add', 'remove', 'configure'],
            'moderate': ['implement', 'create', 'build', 'develop', 'integrate'],
            'complex': ['system', 'platform', 'architecture', 'migrate', 'redesign'],
            'epic': ['enterprise', 'complete', 'full-stack', 'end-to-end', 'ecosystem']
        }
        
        complexity = TaskComplexity.SIMPLE
        for level, indicators in complexity_indicators.items():
            if any(indicator in text for indicator in indicators):
                complexity = getattr(TaskComplexity, level.upper())
        
        # Get AI agent suggestions
        suggestions = suggest_agents(f"{title} {description}", max_suggestions=5)
        required_agents = [s['agent'] for s in suggestions[:3]] if suggestions else ['general-purpose']
        
        # Estimate hours based on complexity and scope
        base_hours = {
            TaskComplexity.SIMPLE: 2,
            TaskComplexity.MODERATE: 8,
            TaskComplexity.COMPLEX: 32,
            TaskComplexity.EPIC: 80
        }
        
        estimated_hours = base_hours[complexity]
        
        # Identify risk factors
        risk_factors = []
        if 'migration' in text or 'legacy' in text:
            risk_factors.append('Legacy system integration risk')
        if 'security' in text or 'authentication' in text:
            risk_factors.append('Security compliance requirements')
        if 'performance' in text or 'scale' in text:
            risk_factors.append('Performance and scalability concerns')
        if 'database' in text and 'migration' in text:
            risk_factors.append('Data migration and consistency risks')
        
        # Define success criteria based on task type
        success_criteria = ['Task completed successfully', 'Quality standards met']
        if 'test' in text:
            success_criteria.append('All tests passing')
        if 'deploy' in text:
            success_criteria.append('Successfully deployed to production')
        if 'performance' in text:
            success_criteria.append('Performance benchmarks met')
        
        return TaskAnalysis(
            complexity=complexity,
            estimated_hours=estimated_hours,
            required_agents=required_agents,
            dependencies=[],  # Would be extracted from context in real implementation
            risk_factors=risk_factors,
            success_criteria=success_criteria
        )

    def create_workflow(self, task_analysis: TaskAnalysis, title: str, description: str) -> AgentWorkflow:
        """Create optimized workflow for the analyzed task."""
        
        # Determine workflow template based on agents and task type
        text = f"{title} {description}".lower()
        template_key = 'full_stack_feature'  # default
        
        if any(word in text for word in ['data', 'analysis', 'report', 'metrics']):
            template_key = 'data_analysis'
        elif any(word in text for word in ['infrastructure', 'deploy', 'server', 'cloud']):
            template_key = 'infrastructure_setup'
        
        # Get base workflow template
        base_workflow = self.workflow_templates.get(template_key, self.workflow_templates['full_stack_feature'])
        
        # Customize workflow based on analysis
        workflow_steps = []
        for step in base_workflow:
            custom_step = step.copy()
            
            # Auto-assign agents based on analysis
            if custom_step['agent'] == 'auto':
                if task_analysis.required_agents:
                    custom_step['agent'] = task_analysis.required_agents[0]
                else:
                    custom_step['agent'] = 'general-purpose'
            
            # Adjust duration based on complexity
            complexity_multiplier = {
                TaskComplexity.SIMPLE: 0.5,
                TaskComplexity.MODERATE: 1.0, 
                TaskComplexity.COMPLEX: 1.5,
                TaskComplexity.EPIC: 2.0
            }
            
            custom_step['duration_hours'] *= complexity_multiplier[task_analysis.complexity]
            workflow_steps.append(custom_step)
        
        # Calculate estimated completion
        total_hours = sum(step['duration_hours'] for step in workflow_steps)
        days = max(1, int(total_hours / 8))  # Assuming 8-hour work days
        
        return AgentWorkflow(
            task_id="",  # Will be set when task is created
            primary_agent=task_analysis.required_agents[0] if task_analysis.required_agents else 'general-purpose',
            supporting_agents=task_analysis.required_agents[1:] if len(task_analysis.required_agents) > 1 else [],
            workflow_steps=workflow_steps,
            estimated_completion=f"{days} days",
            dependencies=task_analysis.dependencies
        )

    def decompose_complex_task(self, title: str, description: str) -> List[Dict]:
        """Break down complex tasks into manageable subtasks."""
        analysis = self.analyze_task(title, description)
        
        if analysis.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
            return [{'title': title, 'description': description, 'agent': analysis.required_agents[0]}]
        
        # For complex tasks, create subtasks based on workflow
        workflow = self.create_workflow(analysis, title, description)
        subtasks = []
        
        for i, step in enumerate(workflow.workflow_steps):
            subtask_title = f"{title} - {step['step'].replace('_', ' ').title()}"
            subtask_description = f"Phase {i+1}: {step['step'].replace('_', ' ').title()} for: {description}"
            
            subtasks.append({
                'title': subtask_title,
                'description': subtask_description,
                'agent': step['agent'],
                'estimated_hours': step['duration_hours'],
                'depends_on': subtasks[-1]['title'] if subtasks else None
            })
        
        return subtasks

    def recommend_task_priority(self, title: str, description: str, context: Dict = None) -> TaskPriority:
        """Analyze and recommend task priority."""
        text = f"{title} {description}".lower()
        
        # Urgent indicators
        if any(word in text for word in ['urgent', 'critical', 'emergency', 'outage', 'down', 'broken']):
            return TaskPriority.URGENT
        
        # High priority indicators  
        if any(word in text for word in ['security', 'vulnerability', 'breach', 'bug', 'fix', 'production']):
            return TaskPriority.HIGH
        
        # Medium priority indicators
        if any(word in text for word in ['feature', 'enhancement', 'improvement', 'optimize']):
            return TaskPriority.MEDIUM
        
        # Default to low priority
        return TaskPriority.LOW

    def create_managed_task(self, title: str, description: str, auto_assign: bool = True) -> Dict:
        """Create a task with full PM analysis and workflow planning."""
        
        print(f"🎯 PM Agent analyzing task: '{title}'")
        
        # Perform comprehensive analysis
        analysis = self.analyze_task(title, description)
        workflow = self.create_workflow(analysis, title, description)
        priority = self.recommend_task_priority(title, description)
        
        print(f"📊 Analysis Results:")
        print(f"   Complexity: {analysis.complexity.name}")
        print(f"   Estimated: {analysis.estimated_hours} hours")
        print(f"   Priority: {priority.name}")
        print(f"   Required agents: {', '.join(analysis.required_agents)}")
        
        if analysis.risk_factors:
            print(f"   ⚠️  Risk factors: {', '.join(analysis.risk_factors)}")
        
        # Check if task should be decomposed
        if analysis.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]:
            print(f"🔄 Complex task detected - recommending decomposition")
            subtasks = self.decompose_complex_task(title, description)
            
            print(f"📋 Suggested subtasks ({len(subtasks)}):")
            for i, subtask in enumerate(subtasks, 1):
                print(f"   {i}. {subtask['title']} → {subtask['agent']}")
            
            return {
                'type': 'complex_task',
                'original_task': {'title': title, 'description': description},
                'analysis': asdict(analysis),
                'workflow': asdict(workflow),
                'priority': priority.name,
                'subtasks': subtasks,
                'recommendation': 'Break this task into subtasks for better management'
            }
        
        # For simple/moderate tasks, provide direct assignment recommendation
        assigned_agent = analysis.required_agents[0] if analysis.required_agents else 'general-purpose'
        
        print(f"✅ Recommended assignment: {assigned_agent}")
        print(f"🎯 Success criteria: {', '.join(analysis.success_criteria)}")
        
        return {
            'type': 'direct_assignment',
            'task': {'title': title, 'description': description},
            'analysis': asdict(analysis),
            'workflow': asdict(workflow), 
            'priority': priority.name,
            'assigned_agent': assigned_agent,
            'recommendation': f'Assign to {assigned_agent} - estimated {analysis.estimated_hours} hours'
        }

    def monitor_task_progress(self, task_id: str) -> Dict:
        """Monitor and analyze task progress (placeholder for future API integration)."""
        # Basic validation without circular import
        if not task_id or len(task_id) < 8:
            return {'error': 'Invalid task ID format'}
        
        # Placeholder implementation - would integrate with actual CRM API
        progress_analysis = {
            'task_id': task_id,
            'current_status': 'Unknown',
            'title': 'Task monitoring not yet implemented',
            'assigned_agent': 'Unknown',
            'progress_score': 0.5,
            'recommendations': ['Task monitoring feature coming soon']
        }
        
        return progress_analysis

    def _calculate_progress_score(self, column_name: str) -> float:
        """Calculate progress score based on task status."""
        progress_map = {
            'To Do': 0.0,
            'In Progress': 0.5,
            'Done': 1.0
        }
        return progress_map.get(column_name, 0.0)


def main():
    """CLI interface for PM Agent Gateway."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PM Agent Gateway - Intelligent task coordination")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a task and provide recommendations')
    analyze_parser.add_argument('--title', required=True, help='Task title')
    analyze_parser.add_argument('--description', required=True, help='Task description')
    analyze_parser.add_argument('--auto-assign', action='store_true', help='Auto-assign to recommended agent')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor task progress')
    monitor_parser.add_argument('task_id', help='Task ID to monitor')
    
    # Decompose command
    decompose_parser = subparsers.add_parser('decompose', help='Break down complex task into subtasks')
    decompose_parser.add_argument('--title', required=True, help='Task title')
    decompose_parser.add_argument('--description', required=True, help='Task description')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        pm_gateway = PMAgentGateway()
        
        if args.command == 'analyze':
            result = pm_gateway.create_managed_task(args.title, args.description, args.auto_assign)
            print(f"\n🎯 PM Agent Recommendation:")
            print(f"Type: {result['type']}")
            print(f"Priority: {result['priority']}")
            print(f"Recommendation: {result['recommendation']}")
            
        elif args.command == 'monitor':
            result = pm_gateway.monitor_task_progress(args.task_id)
            if 'error' in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📊 Task Progress Analysis:")
                print(f"Status: {result['current_status']}")
                print(f"Progress: {result['progress_score']*100:.0f}%")
                if result['recommendations']:
                    print(f"Recommendations: {', '.join(result['recommendations'])}")
        
        elif args.command == 'decompose':
            subtasks = pm_gateway.decompose_complex_task(args.title, args.description)
            print(f"\n🔄 Task Decomposition:")
            print(f"Original: {args.title}")
            print(f"Subtasks ({len(subtasks)}):")
            for i, subtask in enumerate(subtasks, 1):
                print(f"  {i}. {subtask['title']}")
                print(f"     → {subtask['agent']} ({subtask['estimated_hours']} hours)")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()