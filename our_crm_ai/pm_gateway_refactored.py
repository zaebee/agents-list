#!/usr/bin/env python3
"""
PM Agent Gateway - Refactored Version
Intelligent task routing and agent orchestration system without circular dependencies.

This refactored version:
1. Uses the new models.py for data structures
2. Eliminates circular imports
3. Integrates with the repository pattern
4. Adds persistence layer for workflow state
5. Provides better error handling and logging
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from models import (
    TaskPriority, TaskComplexity, Task, Agent,
    PMAnalysisRequest, PMAnalysisResult
)
from exceptions import (
    PMGatewayError, AnalysisError, WorkflowError, ConfigurationError
)


class WorkflowState:
    """Manages workflow execution state with persistence."""
    
    def __init__(self, storage_path: str = "workflow_state.json"):
        self.storage_path = Path(storage_path)
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self._load_state()
    
    def _load_state(self):
        """Load workflow state from persistence."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.workflows = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Failed to load workflow state: {e}")
                self.workflows = {}
    
    def _save_state(self):
        """Save workflow state to persistence."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.workflows, f, indent=2, default=str)
        except IOError as e:
            logging.warning(f"Failed to save workflow state: {e}")
    
    def create_workflow(self, task_id: str, workflow_data: Dict[str, Any]):
        """Create new workflow state."""
        self.workflows[task_id] = {
            **workflow_data,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        self._save_state()
    
    def update_workflow(self, task_id: str, updates: Dict[str, Any]):
        """Update workflow state."""
        if task_id in self.workflows:
            self.workflows[task_id].update(updates)
            self.workflows[task_id]['updated_at'] = datetime.utcnow().isoformat()
            self._save_state()
    
    def get_workflow(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow state."""
        return self.workflows.get(task_id)
    
    def complete_workflow(self, task_id: str):
        """Mark workflow as completed."""
        self.update_workflow(task_id, {'status': 'completed'})
    
    def cleanup_old_workflows(self, days: int = 30):
        """Clean up workflows older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        to_remove = []
        for task_id, workflow in self.workflows.items():
            created_at = datetime.fromisoformat(workflow.get('created_at', '1970-01-01'))
            if created_at < cutoff_date and workflow.get('status') == 'completed':
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.workflows[task_id]
        
        if to_remove:
            self._save_state()


class TaskAnalyzer:
    """Analyzes tasks for complexity, requirements, and optimal routing."""
    
    def __init__(self, agent_selector_module=None):
        self.agent_selector = agent_selector_module
        self.logger = logging.getLogger("task_analyzer")
        
        # Task complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: ['fix', 'update', 'change', 'add', 'remove', 'configure'],
            TaskComplexity.MODERATE: ['implement', 'create', 'build', 'develop', 'integrate'],
            TaskComplexity.COMPLEX: ['system', 'platform', 'architecture', 'migrate', 'redesign'],
            TaskComplexity.EPIC: ['enterprise', 'complete', 'full-stack', 'end-to-end', 'ecosystem']
        }
        
        # Priority keywords
        self.priority_indicators = {
            TaskPriority.URGENT: ['urgent', 'critical', 'emergency', 'outage', 'down', 'broken'],
            TaskPriority.HIGH: ['security', 'vulnerability', 'breach', 'bug', 'fix', 'production'],
            TaskPriority.MEDIUM: ['feature', 'enhancement', 'improvement', 'optimize'],
            TaskPriority.LOW: ['documentation', 'refactor', 'cleanup', 'research']
        }
    
    def analyze_complexity(self, title: str, description: str) -> TaskComplexity:
        """Analyze task complexity based on content."""
        text = f"{title} {description}".lower()
        
        # Check indicators from most complex to least
        for complexity in [TaskComplexity.EPIC, TaskComplexity.COMPLEX, 
                          TaskComplexity.MODERATE, TaskComplexity.SIMPLE]:
            indicators = self.complexity_indicators[complexity]
            if any(indicator in text for indicator in indicators):
                return complexity
        
        return TaskComplexity.MODERATE  # Default
    
    def analyze_priority(self, title: str, description: str) -> TaskPriority:
        """Analyze task priority based on content."""
        text = f"{title} {description}".lower()
        
        # Check indicators from highest to lowest priority
        for priority in [TaskPriority.URGENT, TaskPriority.HIGH, 
                        TaskPriority.MEDIUM, TaskPriority.LOW]:
            indicators = self.priority_indicators[priority]
            if any(indicator in text for indicator in indicators):
                return priority
        
        return TaskPriority.MEDIUM  # Default
    
    def estimate_effort(self, complexity: TaskComplexity) -> float:
        """Estimate effort hours based on complexity."""
        effort_map = {
            TaskComplexity.SIMPLE: 2.0,
            TaskComplexity.MODERATE: 8.0,
            TaskComplexity.COMPLEX: 32.0,
            TaskComplexity.EPIC: 80.0
        }
        return effort_map[complexity]
    
    def identify_risk_factors(self, title: str, description: str) -> List[str]:
        """Identify potential risk factors."""
        text = f"{title} {description}".lower()
        risks = []
        
        risk_patterns = {
            'legacy': 'Legacy system integration risk',
            'migration': 'Data migration and consistency risks',
            'security': 'Security compliance requirements',
            'performance': 'Performance and scalability concerns',
            'database': 'Database schema and data integrity risks',
            'external api': 'External service dependency risks',
            'real-time': 'Real-time processing complexity'
        }
        
        for pattern, risk_description in risk_patterns.items():
            if pattern in text:
                risks.append(risk_description)
        
        return risks
    
    def generate_success_criteria(self, title: str, description: str) -> List[str]:
        """Generate success criteria based on task content."""
        criteria = ['Task completed successfully', 'Quality standards met']
        text = f"{title} {description}".lower()
        
        if 'test' in text:
            criteria.append('All tests passing')
        if 'deploy' in text:
            criteria.append('Successfully deployed to production')
        if 'performance' in text:
            criteria.append('Performance benchmarks met')
        if 'security' in text:
            criteria.append('Security requirements validated')
        if 'ui' in text or 'interface' in text:
            criteria.append('User interface requirements satisfied')
        if 'api' in text:
            criteria.append('API functionality verified')
        
        return criteria
    
    def suggest_required_agents(self, title: str, description: str) -> List[str]:
        """Suggest required agents using agent selector."""
        if not self.agent_selector:
            return ['general-purpose']
        
        try:
            combined_text = f"{title} {description}"
            suggestions = self.agent_selector.suggest_agents(combined_text, max_suggestions=5)
            return [s['agent'] for s in suggestions[:3]] if suggestions else ['general-purpose']
        except Exception as e:
            self.logger.warning(f"Agent suggestion failed: {e}")
            return ['general-purpose']


class WorkflowEngine:
    """Manages workflow templates and execution."""
    
    def __init__(self):
        self.logger = logging.getLogger("workflow_engine")
        
        # Configurable workflow templates
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
            ],
            'bug_fix': [
                {'step': 'investigation', 'agent': 'debugger', 'duration_hours': 2},
                {'step': 'fix_implementation', 'agent': 'auto', 'duration_hours': 4},
                {'step': 'testing', 'agent': 'test-automator', 'duration_hours': 2},
                {'step': 'deployment', 'agent': 'devops-troubleshooter', 'duration_hours': 1}
            ],
            'documentation': [
                {'step': 'content_creation', 'agent': 'docs-architect', 'duration_hours': 6},
                {'step': 'review', 'agent': 'business-analyst', 'duration_hours': 2},
                {'step': 'publishing', 'agent': 'content-marketer', 'duration_hours': 1}
            ]
        }
    
    def select_workflow_template(self, title: str, description: str, complexity: TaskComplexity) -> str:
        """Select appropriate workflow template."""
        text = f"{title} {description}".lower()
        
        # Pattern matching for workflow selection
        if any(word in text for word in ['data', 'analysis', 'report', 'metrics', 'analytics']):
            return 'data_analysis'
        elif any(word in text for word in ['infrastructure', 'deploy', 'server', 'cloud', 'devops']):
            return 'infrastructure_setup'
        elif any(word in text for word in ['bug', 'fix', 'error', 'issue', 'broken']):
            return 'bug_fix'
        elif any(word in text for word in ['docs', 'documentation', 'guide', 'manual']):
            return 'documentation'
        elif complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]:
            return 'full_stack_feature'
        else:
            return 'full_stack_feature'  # Default
    
    def create_workflow(
        self, 
        title: str, 
        description: str, 
        complexity: TaskComplexity,
        required_agents: List[str]
    ) -> Dict[str, Any]:
        """Create customized workflow based on analysis."""
        
        # Select base template
        template_key = self.select_workflow_template(title, description, complexity)
        base_workflow = self.workflow_templates[template_key].copy()
        
        # Customize workflow steps
        customized_steps = []
        for step in base_workflow:
            custom_step = step.copy()
            
            # Auto-assign agents based on analysis
            if custom_step['agent'] == 'auto':
                if required_agents:
                    custom_step['agent'] = required_agents[0]
                else:
                    custom_step['agent'] = 'general-purpose'
            
            # Adjust duration based on complexity
            complexity_multiplier = {
                TaskComplexity.SIMPLE: 0.5,
                TaskComplexity.MODERATE: 1.0, 
                TaskComplexity.COMPLEX: 1.5,
                TaskComplexity.EPIC: 2.0
            }
            
            custom_step['duration_hours'] *= complexity_multiplier[complexity]
            customized_steps.append(custom_step)
        
        # Calculate total effort and timeline
        total_hours = sum(step['duration_hours'] for step in customized_steps)
        estimated_days = max(1, int(total_hours / 8))  # Assuming 8-hour work days
        
        return {
            'template': template_key,
            'steps': customized_steps,
            'total_hours': total_hours,
            'estimated_days': estimated_days,
            'primary_agent': required_agents[0] if required_agents else 'general-purpose',
            'supporting_agents': required_agents[1:] if len(required_agents) > 1 else []
        }
    
    def decompose_complex_task(
        self, 
        title: str, 
        description: str, 
        workflow: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Break down complex tasks into subtasks based on workflow."""
        subtasks = []
        
        for i, step in enumerate(workflow['steps']):
            subtask_title = f"{title} - {step['step'].replace('_', ' ').title()}"
            subtask_description = f"Phase {i+1}: {step['step'].replace('_', ' ').title()} for: {description}"
            
            subtask = {
                'title': subtask_title,
                'description': subtask_description,
                'agent': step['agent'],
                'estimated_hours': step['duration_hours'],
                'depends_on': subtasks[-1]['title'] if subtasks else None,
                'phase': i + 1
            }
            subtasks.append(subtask)
        
        return subtasks


class PMAgentGatewayRefactored:
    """
    Refactored PM Agent Gateway with improved architecture.
    
    Eliminates circular dependencies and provides better integration
    with the new service-oriented architecture.
    """
    
    def __init__(
        self, 
        config_path: Optional[str] = None,
        storage_path: str = "workflow_state.json",
        agent_selector_module=None
    ):
        """Initialize the refactored PM Agent Gateway."""
        self.logger = logging.getLogger("pm_gateway")
        
        # Initialize components
        self.workflow_state = WorkflowState(storage_path)
        self.task_analyzer = TaskAnalyzer(agent_selector_module)
        self.workflow_engine = WorkflowEngine()
        
        # Load configuration if provided
        self.config = None
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")
    
    async def analyze_task(self, request: PMAnalysisRequest) -> PMAnalysisResult:
        """
        Perform comprehensive task analysis without circular dependencies.
        
        This replaces the original create_managed_task method with a cleaner interface.
        """
        try:
            self.logger.info(f"🎯 Analyzing task: '{request.title}'")
            
            # Analyze task components
            complexity = self.task_analyzer.analyze_complexity(request.title, request.description)
            priority = self.task_analyzer.analyze_priority(request.title, request.description)
            estimated_hours = self.task_analyzer.estimate_effort(complexity)
            required_agents = self.task_analyzer.suggest_required_agents(request.title, request.description)
            risk_factors = self.task_analyzer.identify_risk_factors(request.title, request.description)
            success_criteria = self.task_analyzer.generate_success_criteria(request.title, request.description)
            
            self.logger.info(f"📊 Analysis Results:")
            self.logger.info(f"   Complexity: {complexity.name}")
            self.logger.info(f"   Priority: {priority.name}")
            self.logger.info(f"   Estimated: {estimated_hours} hours")
            self.logger.info(f"   Required agents: {', '.join(required_agents)}")
            
            # Create workflow
            workflow = self.workflow_engine.create_workflow(
                request.title, request.description, complexity, required_agents
            )
            
            # Determine task type and generate subtasks if needed
            task_type = "direct_assignment"
            subtasks = []
            recommended_agent = required_agents[0] if required_agents else 'general-purpose'
            
            if complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]:
                task_type = "complex_task"
                subtasks = self.workflow_engine.decompose_complex_task(
                    request.title, request.description, workflow
                )
                self.logger.info(f"🔄 Complex task - recommending {len(subtasks)} subtasks")
            
            # Generate recommendation
            if task_type == "direct_assignment":
                recommendation = f"Assign to {recommended_agent} - estimated {estimated_hours} hours"
            else:
                recommendation = f"Break into {len(subtasks)} subtasks for better management"
            
            # Store workflow state if complex
            if task_type == "complex_task":
                workflow_data = {
                    'title': request.title,
                    'description': request.description,
                    'workflow': workflow,
                    'subtasks': subtasks,
                    'analysis': {
                        'complexity': complexity.name,
                        'priority': priority.name,
                        'estimated_hours': estimated_hours,
                        'required_agents': required_agents,
                        'risk_factors': risk_factors,
                        'success_criteria': success_criteria
                    }
                }
                # Use a temporary ID since we don't have task ID yet
                temp_id = f"temp_{int(datetime.utcnow().timestamp())}"
                self.workflow_state.create_workflow(temp_id, workflow_data)
            
            return PMAnalysisResult(
                task_type=task_type,
                complexity=complexity,
                priority=priority,
                estimated_hours=estimated_hours,
                required_agents=required_agents,
                recommended_agent=recommended_agent,
                subtasks=subtasks,
                risk_factors=risk_factors,
                success_criteria=success_criteria,
                recommendation=recommendation
            )
            
        except Exception as e:
            self.logger.error(f"Task analysis failed: {e}")
            raise AnalysisError(f"Task analysis failed: {str(e)}", request.title)
    
    def create_managed_task(self, title: str, description: str, auto_assign: bool = True) -> Dict[str, Any]:
        """
        Legacy compatibility method for existing code.
        
        This method provides backward compatibility with the original interface
        while using the new architecture internally.
        """
        try:
            # Create analysis request
            request = PMAnalysisRequest(
                title=title,
                description=description,
                auto_assign=auto_assign
            )
            
            # Use synchronous wrapper for async method
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new event loop for nested async call
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.analyze_task(request))
                        result = future.result(timeout=30)
                else:
                    result = asyncio.run(self.analyze_task(request))
            except RuntimeError:
                # Fallback for when event loop is not available
                result = asyncio.run(self.analyze_task(request))
            
            # Convert to legacy format
            return {
                'type': result.task_type,
                'priority': result.priority.value,
                'assigned_agent': result.recommended_agent,
                'analysis': {
                    'complexity': result.complexity.name,
                    'estimated_hours': result.estimated_hours,
                    'required_agents': result.required_agents,
                    'risk_factors': result.risk_factors,
                    'success_criteria': result.success_criteria
                },
                'subtasks': result.subtasks,
                'recommendation': result.recommendation,
                'task': {'title': title, 'description': description}
            }
            
        except Exception as e:
            self.logger.error(f"Legacy task creation failed: {e}")
            # Return basic fallback response
            return {
                'type': 'direct_assignment',
                'priority': 'medium',
                'assigned_agent': 'general-purpose',
                'analysis': {
                    'complexity': 'MODERATE',
                    'estimated_hours': 8.0,
                    'required_agents': ['general-purpose'],
                    'risk_factors': [],
                    'success_criteria': ['Task completed successfully']
                },
                'subtasks': [],
                'recommendation': f'Assign to general-purpose - estimated 8 hours',
                'task': {'title': title, 'description': description}
            }
    
    async def monitor_task_progress(self, task_id: str) -> Dict[str, Any]:
        """Monitor task progress with workflow state."""
        workflow = self.workflow_state.get_workflow(task_id)
        
        if not workflow:
            return {
                'task_id': task_id,
                'status': 'not_found',
                'recommendations': ['Task not found in workflow state']
            }
        
        # Basic progress monitoring (would integrate with actual task repository)
        return {
            'task_id': task_id,
            'status': workflow.get('status', 'unknown'),
            'workflow': workflow,
            'recommendations': ['Workflow monitoring active']
        }
    
    def cleanup_old_workflows(self, days: int = 30):
        """Clean up old workflow states."""
        self.workflow_state.cleanup_old_workflows(days)


# Factory function for creating PM Gateway instance
def create_pm_gateway(
    config_path: Optional[str] = None,
    storage_path: str = "workflow_state.json"
) -> PMAgentGatewayRefactored:
    """Create PM Gateway instance with proper dependencies."""
    
    # Try to import agent selector
    agent_selector = None
    try:
        import agent_selector as agent_selector_module
        agent_selector = agent_selector_module
    except ImportError:
        logging.warning("Agent selector module not available")
    
    return PMAgentGatewayRefactored(config_path, storage_path, agent_selector)


# Backward compatibility - create instance that can be imported
def PMAgentGateway(config_path: str = "config.json"):
    """Backward compatibility function."""
    return create_pm_gateway(config_path)