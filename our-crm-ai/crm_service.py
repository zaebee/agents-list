#!/usr/bin/env python3
"""
AI-CRM Service Layer
Unified business logic service that consolidates functionality from crm_enhanced.py and crm/__init__.py
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from models import (
    Task, TaskStatus, TaskPriority, TaskComplexity,
    TaskCreateRequest, TaskUpdateRequest, TaskResponse, 
    Agent, AgentSuggestion, AgentSuggestionResponse,
    CRMConfiguration, CRMStats, PMAnalysisRequest, PMAnalysisResult,
    TaskMetadata
)
from exceptions import (
    CRMError, TaskError, TaskNotFoundError, TaskValidationError,
    AgentError, AgentNotFoundError, ConfigurationError,
    PMGatewayError, ValidationError
)
from repositories import TaskRepository, AgentRepository, ConfigurationRepository


class CRMService:
    """
    Unified CRM service layer providing high-level business operations.
    Consolidates functionality from both crm_enhanced.py and crm/__init__.py.
    """
    
    def __init__(
        self,
        task_repository: TaskRepository,
        agent_repository: AgentRepository,
        config_repository: ConfigurationRepository,
        logger: Optional[logging.Logger] = None
    ):
        self.task_repo = task_repository
        self.agent_repo = agent_repository
        self.config_repo = config_repository
        self.logger = logger or self._setup_logging()
        
        # PM Gateway integration (will be initialized lazily)
        self._pm_gateway = None
        self._agent_selector = None
    
    def _setup_logging(self) -> logging.Logger:
        """Set up service logging."""
        logger = logging.getLogger("crm_service")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @property
    def pm_gateway(self):
        """Lazy initialization of PM Gateway."""
        if self._pm_gateway is None:
            try:
                from pm_agent_gateway import PMAgentGateway
                self._pm_gateway = PMAgentGateway()
            except ImportError as e:
                self.logger.warning(f"PM Gateway not available: {e}")
                self._pm_gateway = None
        return self._pm_gateway
    
    @property
    def agent_selector(self):
        """Lazy initialization of agent selector."""
        if self._agent_selector is None:
            try:
                import agent_selector
                self._agent_selector = agent_selector
            except ImportError as e:
                self.logger.warning(f"Agent selector not available: {e}")
                self._agent_selector = None
        return self._agent_selector
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        try:
            # Check task repository
            task_healthy = await self.task_repo.health_check()
            health_status["components"]["task_repository"] = {
                "status": "healthy" if task_healthy else "unhealthy"
            }
            
            # Check agent repository
            agent_healthy = await self.agent_repo.health_check()
            health_status["components"]["agent_repository"] = {
                "status": "healthy" if agent_healthy else "unhealthy"
            }
            
            # Check configuration repository
            config_healthy = await self.config_repo.health_check()
            health_status["components"]["configuration"] = {
                "status": "healthy" if config_healthy else "unhealthy"
            }
            
            # Check PM Gateway
            pm_status = "healthy" if self.pm_gateway else "unavailable"
            health_status["components"]["pm_gateway"] = {"status": pm_status}
            
            # Overall status
            all_healthy = all(
                comp["status"] in ["healthy", "unavailable"] 
                for comp in health_status["components"].values()
            )
            health_status["status"] = "healthy" if all_healthy else "degraded"
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def create_task(
        self, 
        task_request: TaskCreateRequest,
        use_pm_analysis: bool = True,
        auto_assign: bool = True
    ) -> TaskResponse:
        """
        Create a new task with intelligent agent assignment and PM analysis.
        Consolidates logic from both crm_enhanced.py create_task and crm/__init__.py create_task.
        """
        try:
            self.logger.info(f"Creating task: '{task_request.title}'")
            
            # Initialize response
            warnings = []
            agent_suggestions = []
            suggested_agent = task_request.assigned_agent
            pm_result = None
            
            # PM Gateway analysis if enabled and available
            if use_pm_analysis and self.pm_gateway and not suggested_agent:
                try:
                    self.logger.info("🎯 Using PM Agent Gateway for intelligent task analysis...")
                    
                    pm_gateway_result = self.pm_gateway.create_managed_task(
                        task_request.title, 
                        task_request.description or "",
                        auto_assign
                    )
                    
                    # Convert PM gateway result to PMAnalysisResult
                    from models import PMAnalysisResult
                    analysis_data = pm_gateway_result.get('analysis', {})
                    
                    # Handle complexity - could be string or enum
                    complexity_value = analysis_data.get('complexity', 'MODERATE')
                    if hasattr(complexity_value, 'name'):
                        complexity_str = complexity_value.name
                    else:
                        complexity_str = str(complexity_value).upper()
                    
                    pm_result = PMAnalysisResult(
                        task_type=pm_gateway_result['type'],
                        complexity=getattr(TaskComplexity, complexity_str),
                        priority=getattr(TaskPriority, pm_gateway_result['priority'].upper()),
                        estimated_hours=analysis_data.get('estimated_hours', 8.0),
                        required_agents=analysis_data.get('required_agents', []),
                        recommended_agent=pm_gateway_result.get('assigned_agent'),
                        subtasks=pm_gateway_result.get('subtasks', []),
                        risk_factors=analysis_data.get('risk_factors', []),
                        success_criteria=analysis_data.get('success_criteria', []),
                        recommendation=pm_gateway_result['recommendation']
                    )
                    
                    if pm_gateway_result['type'] == 'direct_assignment':
                        suggested_agent = pm_gateway_result['assigned_agent']
                        priority = pm_gateway_result['priority']
                        
                        # Update request with PM analysis results
                        if hasattr(TaskPriority, priority.upper()):
                            task_request.priority = getattr(TaskPriority, priority.upper())
                        
                        # Enrich metadata with PM analysis
                        if not task_request.metadata:
                            task_request.metadata = TaskMetadata()
                        
                        task_request.metadata.effort_estimate_hours = analysis_data.get('estimated_hours')
                        task_request.metadata.risk_factors = analysis_data.get('risk_factors', [])
                        task_request.metadata.success_criteria = analysis_data.get('success_criteria', [])
                        
                        self.logger.info(f"💡 PM Recommendation: {suggested_agent}")
                        
                    elif pm_gateway_result['type'] == 'complex_task':
                        warnings.append("Complex task detected - consider breaking into subtasks")
                        subtasks_count = len(pm_gateway_result.get('subtasks', []))
                        self.logger.warning(f"⚠️ Complex task with {subtasks_count} recommended subtasks")
                        
                        # Use primary agent for complex tasks
                        required_agents = analysis_data.get('required_agents', [])
                        if required_agents:
                            suggested_agent = required_agents[0]
                
                except Exception as e:
                    self.logger.warning(f"PM Gateway analysis failed: {e}, falling back to basic selection")
                    warnings.append(f"PM analysis failed: {str(e)}")
            
            # Always collect agent suggestions if agent selector is available
            if auto_assign and self.agent_selector:
                try:
                    self.logger.info("🔍 Using agent selector for suggestions...")
                    
                    combined_text = f"{task_request.title} {task_request.description or ''}"
                    suggestions = self.agent_selector.suggest_agents(combined_text, max_suggestions=3)
                    
                    if suggestions:
                        # Convert agent selector suggestions to AgentSuggestion objects
                        from models import AgentSuggestion
                        for suggestion in suggestions:
                            # Convert confidence from percentage to decimal (0-100 -> 0-1)
                            confidence = suggestion['confidence']
                            if confidence > 1:
                                confidence = confidence / 100.0
                            
                            agent_suggestion = AgentSuggestion(
                                agent_name=suggestion['agent'],
                                confidence=confidence,
                                reasoning=suggestion['reasoning'],
                                matched_keywords=suggestion.get('matched_keywords', [])
                            )
                            agent_suggestions.append(agent_suggestion)
                        
                        # Use as fallback only if no PM suggestion
                        if not suggested_agent:
                            suggested_agent = suggestions[0]['agent']
                            confidence = suggestions[0]['confidence']
                            
                            self.logger.info(f"💡 Basic suggestion: {suggested_agent} ({confidence:.1f}% confidence)")
                    
                except Exception as e:
                    self.logger.warning(f"Agent selection failed: {e}")
                    warnings.append(f"Agent selection failed: {str(e)}")
            
            # Validate suggested agent
            if suggested_agent:
                agent = await self.agent_repo.get_agent(suggested_agent)
                if not agent:
                    warnings.append(f"Suggested agent '{suggested_agent}' not found in configuration")
                    suggested_agent = None
                elif agent.is_overloaded:
                    warnings.append(f"Agent '{suggested_agent}' is at capacity ({agent.workload_percentage:.0f}%)")
                elif not agent.is_available:
                    warnings.append(f"Agent '{suggested_agent}' is currently unavailable")
                    suggested_agent = None
            
            # Update task request with final agent assignment
            if suggested_agent:
                task_request.assigned_agent = suggested_agent
                # Update agent workload
                try:
                    await self.agent_repo.update_agent_workload(suggested_agent, 1)
                except Exception as e:
                    self.logger.warning(f"Failed to update agent workload: {e}")
            
            # Create task
            task = await self.task_repo.create_task(task_request)
            
            self.logger.info(f"✅ Task created successfully with ID: {task.id}")
            
            return TaskResponse(
                task=task,
                success=True,
                message=f"Task created successfully with ID: {task.id}",
                warnings=warnings,
                pm_analysis=pm_result if pm_result else None,
                agent_suggestions=agent_suggestions
            )
            
        except TaskValidationError as e:
            self.logger.error(f"Task validation failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise TaskError(f"Task creation failed: {str(e)}")
    
    async def get_task(self, task_id: str) -> Task:
        """Get task by ID with validation."""
        if not task_id or not isinstance(task_id, str):
            raise ValidationError("Invalid task ID format")
        
        task = await self.task_repo.get_task(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        
        return task
    
    async def update_task(self, task_id: str, task_update: TaskUpdateRequest) -> TaskResponse:
        """Update existing task with agent workload management."""
        try:
            # Get current task
            current_task = await self.get_task(task_id)
            
            # Track agent changes for workload management
            old_agent = current_task.assigned_agent
            new_agent = task_update.assigned_agent
            
            # Validate new agent if specified
            if new_agent:
                agent = await self.agent_repo.get_agent(new_agent)
                if not agent:
                    raise AgentNotFoundError(new_agent)
                if agent.is_overloaded:
                    raise AgentError(f"Agent '{new_agent}' is at capacity")
                if not agent.is_available:
                    raise AgentError(f"Agent '{new_agent}' is unavailable")
            
            # Update task
            updated_task = await self.task_repo.update_task(task_id, task_update)
            
            # Manage agent workloads
            if old_agent != new_agent:
                if old_agent:
                    try:
                        await self.agent_repo.update_agent_workload(old_agent, -1)
                    except Exception as e:
                        self.logger.warning(f"Failed to decrease workload for {old_agent}: {e}")
                
                if new_agent:
                    try:
                        await self.agent_repo.update_agent_workload(new_agent, 1)
                    except Exception as e:
                        self.logger.warning(f"Failed to increase workload for {new_agent}: {e}")
            
            # Track task completion
            if (current_task.status != TaskStatus.DONE and 
                updated_task.status == TaskStatus.DONE and 
                updated_task.assigned_agent):
                
                # Calculate completion time
                creation_time = current_task.created_at or datetime.utcnow()
                completion_time = datetime.utcnow()
                hours_taken = (completion_time - creation_time).total_seconds() / 3600
                
                # Update agent statistics
                try:
                    await self.agent_repo.update_agent_stats(
                        updated_task.assigned_agent, 
                        success=True, 
                        completion_time_hours=hours_taken
                    )
                    # Decrease workload as task is complete
                    await self.agent_repo.update_agent_workload(updated_task.assigned_agent, -1)
                except Exception as e:
                    self.logger.warning(f"Failed to update agent stats: {e}")
            
            return TaskResponse(
                task=updated_task,
                success=True,
                message="Task updated successfully"
            )
            
        except (TaskNotFoundError, AgentNotFoundError, AgentError, TaskValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to update task {task_id}: {e}")
            raise TaskError(f"Task update failed: {str(e)}", task_id)
    
    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        assigned_agent: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """List tasks with optional filters."""
        try:
            tasks = await self.task_repo.list_tasks(status, assigned_agent, limit, offset)
            self.logger.info(f"Retrieved {len(tasks)} tasks")
            return tasks
        except Exception as e:
            self.logger.error(f"Failed to list tasks: {e}")
            raise TaskError(f"Failed to list tasks: {str(e)}")
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task with agent workload cleanup."""
        try:
            # Get task to check for assigned agent
            task = await self.get_task(task_id)
            
            # Delete task
            success = await self.task_repo.delete_task(task_id)
            
            # Clean up agent workload if task was assigned
            if success and task.assigned_agent:
                try:
                    await self.agent_repo.update_agent_workload(task.assigned_agent, -1)
                except Exception as e:
                    self.logger.warning(f"Failed to update agent workload after deletion: {e}")
            
            return success
            
        except TaskNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete task {task_id}: {e}")
            raise TaskError(f"Task deletion failed: {str(e)}", task_id)
    
    async def move_task(self, task_id: str, target_status: TaskStatus) -> TaskResponse:
        """Move task to different status."""
        update_request = TaskUpdateRequest(status=target_status)
        return await self.update_task(task_id, update_request)
    
    async def add_comment(self, task_id: str, message: str) -> bool:
        """Add comment to task."""
        try:
            # Verify task exists
            await self.get_task(task_id)
            
            # Add comment
            success = await self.task_repo.add_comment(task_id, message)
            
            if success:
                self.logger.info(f"Comment added to task {task_id}")
            
            return success
            
        except TaskNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to add comment to task {task_id}: {e}")
            raise TaskError(f"Failed to add comment: {str(e)}", task_id)
    
    async def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """Get task comments."""
        try:
            # Verify task exists
            await self.get_task(task_id)
            
            # Get comments
            comments = await self.task_repo.get_comments(task_id)
            return comments
            
        except TaskNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get comments for task {task_id}: {e}")
            raise TaskError(f"Failed to get comments: {str(e)}", task_id)
    
    async def suggest_agents(self, task_description: str, max_suggestions: int = 5) -> AgentSuggestionResponse:
        """Suggest optimal agents for a task with context-aware ranking."""
        try:
            suggestions = []
            
            # Get basic suggestions from agent selector
            if self.agent_selector:
                basic_suggestions = self.agent_selector.suggest_agents(task_description, max_suggestions * 2)
                
                # Enhance suggestions with workload and availability context
                for suggestion in basic_suggestions:
                    agent_name = suggestion['agent']
                    agent = await self.agent_repo.get_agent(agent_name)
                    
                    if agent:
                        # Calculate workload factor (lower is better)
                        workload_factor = 1.0 + (agent.workload_percentage / 100.0)
                        
                        # Adjust confidence based on availability and workload
                        adjusted_confidence = suggestion['confidence'] / workload_factor
                        
                        if not agent.is_available:
                            adjusted_confidence *= 0.5  # Penalize unavailable agents
                        
                        suggestions.append(AgentSuggestion(
                            agent_name=agent_name,
                            confidence=min(adjusted_confidence, 100.0),
                            reasoning=suggestion['reasoning'],
                            matched_keywords=suggestion['matched_keywords'],
                            workload_factor=workload_factor,
                            availability_status="available" if agent.is_available else "unavailable"
                        ))
            
            # Sort by adjusted confidence
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            suggestions = suggestions[:max_suggestions]
            
            # Generate recommendation
            if suggestions:
                top_suggestion = suggestions[0]
                recommendation = f"Recommended: {top_suggestion.agent_name} ({top_suggestion.confidence:.1f}% confidence)"
            else:
                recommendation = "No specific agent recommendations found"
            
            return AgentSuggestionResponse(
                suggestions=suggestions,
                recommendation=recommendation,
                task_analysis={"description": task_description, "suggestions_count": len(suggestions)}
            )
            
        except Exception as e:
            self.logger.error(f"Agent suggestion failed: {e}")
            raise AgentError(f"Agent suggestion failed: {str(e)}")
    
    async def get_agent_info(self, agent_name: str) -> Agent:
        """Get agent information."""
        agent = await self.agent_repo.get_agent(agent_name)
        if not agent:
            raise AgentNotFoundError(agent_name)
        return agent
    
    async def list_agents(self) -> List[Agent]:
        """List all available agents with current status."""
        try:
            agents = await self.agent_repo.list_agents()
            self.logger.info(f"Retrieved {len(agents)} agents")
            return agents
        except Exception as e:
            self.logger.error(f"Failed to list agents: {e}")
            raise AgentError(f"Failed to list agents: {str(e)}")
    
    async def pm_analyze_task(self, request: PMAnalysisRequest) -> PMAnalysisResult:
        """Analyze task using PM Gateway."""
        if not self.pm_gateway:
            raise PMGatewayError("PM Gateway not available")
        
        try:
            result = self.pm_gateway.create_managed_task(
                request.title, 
                request.description, 
                request.auto_assign
            )
            
            # Convert PM Gateway result to standard format
            analysis = result.get('analysis', {})
            
            return PMAnalysisResult(
                task_type=result['type'],
                complexity=getattr(TaskComplexity, analysis.get('complexity', 'MODERATE').upper()),
                priority=getattr(TaskPriority, result['priority'].upper()),
                estimated_hours=analysis.get('estimated_hours', 8.0),
                required_agents=analysis.get('required_agents', []),
                recommended_agent=result.get('assigned_agent'),
                subtasks=result.get('subtasks', []),
                risk_factors=analysis.get('risk_factors', []),
                success_criteria=analysis.get('success_criteria', []),
                recommendation=result['recommendation']
            )
            
        except Exception as e:
            self.logger.error(f"PM analysis failed: {e}")
            raise PMGatewayError(f"PM analysis failed: {str(e)}")
    
    async def get_system_stats(self) -> CRMStats:
        """Get comprehensive system statistics."""
        try:
            # Get all tasks
            all_tasks = await self.task_repo.list_tasks(limit=10000)
            
            # Calculate basic stats
            total_tasks = len(all_tasks)
            tasks_by_status = {}
            tasks_by_priority = {}
            tasks_by_agent = {}
            completion_times = []
            
            for task in all_tasks:
                # Status distribution
                status = task.status
                tasks_by_status[status] = tasks_by_status.get(status, 0) + 1
                
                # Priority distribution
                priority = task.priority
                tasks_by_priority[priority] = tasks_by_priority.get(priority, 0) + 1
                
                # Agent distribution
                if task.assigned_agent:
                    agent = task.assigned_agent
                    tasks_by_agent[agent] = tasks_by_agent.get(agent, 0) + 1
                
                # Completion time calculation
                if task.status == TaskStatus.DONE and task.created_at and task.completed_at:
                    completion_time = (task.completed_at - task.created_at).total_seconds() / 3600
                    completion_times.append(completion_time)
            
            # Calculate averages
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None
            
            # Calculate success rate (tasks completed vs created)
            completed_tasks = tasks_by_status.get(TaskStatus.DONE, 0)
            success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
            
            # Most active agents
            most_active_agents = sorted(tasks_by_agent.keys(), key=tasks_by_agent.get, reverse=True)[:5]
            
            # System health assessment
            health_data = await self.health_check()
            system_health = health_data["status"]
            
            return CRMStats(
                total_tasks=total_tasks,
                tasks_by_status=tasks_by_status,
                tasks_by_priority=tasks_by_priority,
                tasks_by_agent=tasks_by_agent,
                average_completion_time_hours=avg_completion_time,
                success_rate=success_rate,
                most_active_agents=most_active_agents,
                system_health=system_health
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate system stats: {e}")
            raise CRMError(f"System stats generation failed: {str(e)}")
    
    async def close(self):
        """Clean up service resources."""
        try:
            if hasattr(self.task_repo, 'close'):
                await self.task_repo.close()
        except Exception as e:
            self.logger.warning(f"Error closing task repository: {e}")


# Service factory function
async def create_crm_service(
    api_key: str,
    config_path: str = "config.json"
) -> CRMService:
    """Create CRM service with all dependencies."""
    from repositories import (
        create_task_repository, 
        create_agent_repository, 
        create_configuration_repository
    )
    
    # Create repositories
    config_repo = await create_configuration_repository(config_path)
    config = await config_repo.get_configuration()
    
    task_repo = await create_task_repository(api_key, config)
    agent_repo = await create_agent_repository(config)
    
    # Create service
    service = CRMService(task_repo, agent_repo, config_repo)
    
    return service