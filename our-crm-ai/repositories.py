#!/usr/bin/env python3
"""
AI-CRM Repository Layer
Data access abstraction for YouGile API and local storage.
"""

import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

import httpx  # Modern async HTTP client
import requests  # For backward compatibility
from pydantic import ValidationError

from models import (
    Task, TaskStatus, TaskCreateRequest, TaskUpdateRequest,
    Agent, CRMConfiguration, CRMStats, TaskMetadata
)
from exceptions import (
    APIError, TaskNotFoundError, TaskValidationError, ConfigurationError,
    NetworkError, TimeoutError, AuthenticationError, create_api_exception,
    is_retryable_error, get_retry_delay
)


class BaseRepository(ABC):
    """Abstract base repository interface."""
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check repository health."""
        pass


class TaskRepository(BaseRepository):
    """Repository for task data access."""
    
    @abstractmethod
    async def create_task(self, task_request: TaskCreateRequest) -> Task:
        """Create a new task."""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, task_update: TaskUpdateRequest) -> Task:
        """Update existing task."""
        pass
    
    @abstractmethod
    async def list_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        assigned_agent: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """List tasks with optional filters."""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Delete task."""
        pass
    
    @abstractmethod
    async def move_task(self, task_id: str, target_status: TaskStatus) -> Task:
        """Move task to different status/column."""
        pass
    
    @abstractmethod
    async def add_comment(self, task_id: str, message: str) -> bool:
        """Add comment to task."""
        pass
    
    @abstractmethod
    async def get_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """Get task comments."""
        pass


class AgentRepository(BaseRepository):
    """Repository for agent data access."""
    
    @abstractmethod
    async def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get agent by name."""
        pass
    
    @abstractmethod
    async def list_agents(self) -> List[Agent]:
        """List all available agents."""
        pass
    
    @abstractmethod
    async def update_agent_workload(self, agent_name: str, workload_delta: int) -> Agent:
        """Update agent workload."""
        pass
    
    @abstractmethod
    async def update_agent_stats(self, agent_name: str, success: bool, completion_time_hours: float) -> Agent:
        """Update agent performance statistics."""
        pass


class ConfigurationRepository(BaseRepository):
    """Repository for configuration management."""
    
    @abstractmethod
    async def get_configuration(self) -> CRMConfiguration:
        """Get current configuration."""
        pass
    
    @abstractmethod
    async def update_configuration(self, config: CRMConfiguration) -> bool:
        """Update configuration."""
        pass


class YouGileTaskRepository(TaskRepository):
    """YouGile API implementation of task repository."""
    
    def __init__(
        self, 
        api_key: str, 
        config: CRMConfiguration,
        base_url: str = "https://yougile.com/api-v2",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.config = config
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Synchronous client for backward compatibility
        self.sync_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Async client will be created when needed
        self._async_client: Optional[httpx.AsyncClient] = None
    
    async def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._async_client
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        client = await self._get_async_client()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.request(method, url, json=json_data, params=params)
                
                # Try to parse JSON response
                try:
                    response_data = response.json() if response.content else {}
                except Exception:
                    response_data = {}
                
                if response.status_code == 200 or response.status_code == 201:
                    return response_data
                else:
                    error = create_api_exception(response.status_code, f"API request failed", response_data)
                    if not is_retryable_error(error) or attempt == self.max_retries:
                        raise error
                    
                    delay = get_retry_delay(error, attempt)
                    await asyncio.sleep(delay)
                    
            except httpx.RequestError as e:
                error = NetworkError(f"Network error: {str(e)}", endpoint=endpoint)
                if attempt == self.max_retries:
                    raise error
                
                delay = get_retry_delay(error, attempt)
                await asyncio.sleep(delay)
        
        raise NetworkError(f"Max retries exceeded for {endpoint}")
    
    def _make_sync_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make synchronous HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(
                    method, url, 
                    headers=self.sync_headers,
                    json=json_data,
                    params=params,
                    timeout=self.timeout,
                    verify=True
                )
                
                response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                
                if response.status_code in [200, 201]:
                    return response_data
                else:
                    error = create_api_exception(response.status_code, f"API request failed", response_data)
                    if not is_retryable_error(error) or attempt == self.max_retries:
                        raise error
                    
                    delay = get_retry_delay(error, attempt)
                    time.sleep(delay)
                    
            except requests.exceptions.RequestException as e:
                error = NetworkError(f"Network error: {str(e)}", endpoint=endpoint)
                if attempt == self.max_retries:
                    raise error
                
                delay = get_retry_delay(error, attempt)
                time.sleep(delay)
        
        raise NetworkError(f"Max retries exceeded for {endpoint}")
    
    async def health_check(self) -> bool:
        """Check API health."""
        try:
            # Try to get board info as health check
            await self._make_request("GET", f"/boards/{self.config.board_id}")
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close async HTTP client."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
    
    async def create_task(self, task_request: TaskCreateRequest) -> Task:
        """Create a new task in YouGile."""
        try:
            # Get column ID for To Do status
            todo_column_id = self.config.columns.get("To Do")
            if not todo_column_id:
                raise ConfigurationError("'To Do' column not found in configuration")
            
            # Prepare task data
            task_data = {
                "title": task_request.title,
                "description": task_request.description,
                "columnId": str(todo_column_id)
            }
            
            # Add agent sticker if assigned
            if task_request.assigned_agent:
                ai_owner_config = self.config.ai_owner_sticker
                sticker_id = ai_owner_config.get("id")
                state_id = ai_owner_config.get("states", {}).get(task_request.assigned_agent)
                
                if not sticker_id or not state_id:
                    raise TaskValidationError(f"Agent '{task_request.assigned_agent}' not configured in stickers")
                
                task_data["stickers"] = {sticker_id: state_id}
            
            # Create task via API
            response_data = await self._make_request("POST", "/tasks", task_data)
            task_id = response_data.get("id")
            
            if not task_id:
                raise APIError("Task creation failed - no ID returned")
            
            # Return created task
            return Task(
                id=task_id,
                title=task_request.title,
                description=task_request.description,
                status=TaskStatus.TODO,
                priority=task_request.priority,
                assigned_agent=task_request.assigned_agent,
                column_id=str(todo_column_id),
                board_id=str(self.config.board_id),
                created_at=datetime.utcnow(),
                metadata=task_request.metadata or TaskMetadata()
            )
            
        except ValidationError as e:
            raise TaskValidationError(f"Task validation failed: {str(e)}")
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID from YouGile."""
        try:
            response_data = await self._make_request("GET", f"/tasks/{task_id}")
            return self._convert_api_task_to_model(response_data)
        except APIError as e:
            if e.details.get("status_code") == 404:
                return None
            raise
    
    def _convert_api_task_to_model(self, api_data: Dict[str, Any]) -> Task:
        """Convert YouGile API task data to Task model."""
        # Map column ID to status
        column_id = api_data.get("columnId")
        status = TaskStatus.TODO  # default
        
        for status_name, col_id in self.config.columns.items():
            if str(col_id) == str(column_id):
                if status_name == "In Progress":
                    status = TaskStatus.IN_PROGRESS
                elif status_name == "Done":
                    status = TaskStatus.DONE
                break
        
        # Extract assigned agent from stickers
        assigned_agent = None
        stickers = api_data.get("stickers", {})
        ai_owner_config = self.config.ai_owner_sticker
        
        if ai_owner_config:
            sticker_id = ai_owner_config.get("id")
            if sticker_id and sticker_id in stickers:
                state_id = stickers[sticker_id]
                # Reverse lookup agent name
                for agent_name, agent_state_id in ai_owner_config.get("states", {}).items():
                    if agent_state_id == state_id:
                        assigned_agent = agent_name
                        break
        
        return Task(
            id=api_data.get("id"),
            title=api_data.get("title", ""),
            description=api_data.get("description", ""),
            status=status,
            assigned_agent=assigned_agent,
            column_id=str(column_id) if column_id else None,
            board_id=str(self.config.board_id),
            stickers=stickers,
            created_at=datetime.fromisoformat(api_data["created_at"].replace('Z', '+00:00')) if api_data.get("created_at") else None,
            updated_at=datetime.fromisoformat(api_data["updated_at"].replace('Z', '+00:00')) if api_data.get("updated_at") else None
        )
    
    async def update_task(self, task_id: str, task_update: TaskUpdateRequest) -> Task:
        """Update existing task."""
        # Build update payload
        update_data = {}
        
        if task_update.title is not None:
            update_data["title"] = task_update.title
        
        if task_update.description is not None:
            update_data["description"] = task_update.description
        
        if task_update.status is not None:
            column_id = self.config.columns.get(task_update.status.value)
            if column_id:
                update_data["columnId"] = str(column_id)
        
        if task_update.assigned_agent is not None:
            ai_owner_config = self.config.ai_owner_sticker
            sticker_id = ai_owner_config.get("id")
            state_id = ai_owner_config.get("states", {}).get(task_update.assigned_agent)
            
            if sticker_id and state_id:
                update_data["stickers"] = {sticker_id: state_id}
        
        if not update_data:
            raise TaskValidationError("No valid fields to update")
        
        # Update via API
        await self._make_request("PUT", f"/tasks/{task_id}", update_data)
        
        # Return updated task
        updated_task = await self.get_task(task_id)
        if not updated_task:
            raise TaskNotFoundError(task_id)
        
        return updated_task
    
    async def list_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        assigned_agent: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """List tasks with optional filters."""
        all_tasks = []
        
        # If status filter specified, only check that column
        if status:
            column_id = self.config.columns.get(status.value)
            if column_id:
                params = {"columnId": str(column_id), "limit": min(limit, 1000)}
                response_data = await self._make_request("GET", "/task-list", params=params)
                tasks = response_data.get("content", [])
                
                for task_data in tasks:
                    task = self._convert_api_task_to_model(task_data)
                    if not assigned_agent or task.assigned_agent == assigned_agent:
                        all_tasks.append(task)
        else:
            # Get tasks from all columns
            for column_name, column_id in self.config.columns.items():
                params = {"columnId": str(column_id), "limit": 1000}
                response_data = await self._make_request("GET", "/task-list", params=params)
                tasks = response_data.get("content", [])
                
                for task_data in tasks:
                    task = self._convert_api_task_to_model(task_data)
                    if not assigned_agent or task.assigned_agent == assigned_agent:
                        all_tasks.append(task)
        
        # Apply offset and limit
        return all_tasks[offset:offset + limit]
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task."""
        try:
            await self._make_request("DELETE", f"/tasks/{task_id}")
            return True
        except APIError as e:
            if e.details.get("status_code") == 404:
                raise TaskNotFoundError(task_id)
            raise
    
    async def move_task(self, task_id: str, target_status: TaskStatus) -> Task:
        """Move task to different status/column."""
        update_request = TaskUpdateRequest(status=target_status)
        return await self.update_task(task_id, update_request)
    
    async def add_comment(self, task_id: str, message: str) -> bool:
        """Add comment to task."""
        comment_data = {"text": message}
        await self._make_request("POST", f"/chats/{task_id}/messages", comment_data)
        return True
    
    async def get_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """Get task comments."""
        try:
            response_data = await self._make_request("GET", f"/chats/{task_id}/messages")
            return response_data.get("content", [])
        except APIError as e:
            if e.details.get("status_code") == 404:
                return []
            raise
    
    async def close(self):
        """Close async client."""
        if hasattr(self, '_async_client') and self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()


class InMemoryAgentRepository(AgentRepository):
    """In-memory agent repository with persistence."""
    
    def __init__(self, config: CRMConfiguration):
        self.config = config
        self.agents: Dict[str, Agent] = {}
        self._load_agents_from_config()
    
    def _load_agents_from_config(self):
        """Load agents from configuration."""
        if hasattr(self.config, 'available_agents'):
            self.agents = self.config.available_agents.copy()
        else:
            # Create default agents from config sticker states
            ai_owner_config = self.config.ai_owner_sticker
            if ai_owner_config and "states" in ai_owner_config:
                from agent_selector import AGENT_KEYWORDS
                
                for agent_name in ai_owner_config["states"].keys():
                    keywords = AGENT_KEYWORDS.get(agent_name, [])
                    # Categorize agent
                    category = self._categorize_agent(agent_name)
                    
                    self.agents[agent_name] = Agent(
                        name=agent_name,
                        category=category,
                        keywords=keywords,
                        specializations=keywords[:3]  # Top 3 as specializations
                    )
    
    def _categorize_agent(self, agent_name: str) -> str:
        """Categorize agent based on name."""
        if any(lang in agent_name for lang in ['python', 'javascript', 'java', 'go', 'rust', 'cpp']):
            return "programming"
        elif any(fe in agent_name for fe in ['frontend', 'ui-ux', 'mobile', 'ios']):
            return "frontend_mobile"
        elif any(arch in agent_name for arch in ['architect', 'backend', 'api']):
            return "architecture_backend"
        elif any(infra in agent_name for infra in ['devops', 'cloud', 'deployment']):
            return "infrastructure_devops"
        elif any(data in agent_name for data in ['data', 'ai-', 'ml-']):
            return "data_ai"
        elif any(sec in agent_name for sec in ['security', 'test', 'performance']):
            return "security_quality"
        elif any(doc in agent_name for doc in ['docs', 'content', 'tutorial']):
            return "documentation"
        elif any(biz in agent_name for biz in ['business', 'sales', 'customer']):
            return "business_support"
        else:
            return "specialized"
    
    async def health_check(self) -> bool:
        """Check repository health."""
        return len(self.agents) > 0
    
    async def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get agent by name."""
        return self.agents.get(agent_name)
    
    async def list_agents(self) -> List[Agent]:
        """List all available agents."""
        return list(self.agents.values())
    
    async def update_agent_workload(self, agent_name: str, workload_delta: int) -> Agent:
        """Update agent workload."""
        if agent_name not in self.agents:
            raise AgentError(f"Agent '{agent_name}' not found")
        
        agent = self.agents[agent_name]
        new_workload = max(0, agent.current_workload + workload_delta)
        
        # Create updated agent
        updated_agent = agent.copy(update={"current_workload": new_workload})
        self.agents[agent_name] = updated_agent
        
        return updated_agent
    
    async def update_agent_stats(self, agent_name: str, success: bool, completion_time_hours: float) -> Agent:
        """Update agent performance statistics."""
        if agent_name not in self.agents:
            raise AgentError(f"Agent '{agent_name}' not found")
        
        agent = self.agents[agent_name]
        
        # Simple running average update
        current_success_rate = agent.success_rate
        current_response_time = agent.average_response_time_hours
        
        # Exponential moving average with alpha = 0.1
        alpha = 0.1
        new_success_rate = current_success_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
        new_response_time = current_response_time * (1 - alpha) + completion_time_hours * alpha
        
        updated_agent = agent.copy(update={
            "success_rate": new_success_rate,
            "average_response_time_hours": new_response_time
        })
        
        self.agents[agent_name] = updated_agent
        return updated_agent


class FileConfigurationRepository(ConfigurationRepository):
    """File-based configuration repository."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config_cache: Optional[CRMConfiguration] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
    
    async def health_check(self) -> bool:
        """Check configuration file health."""
        return self.config_path.exists() and self.config_path.is_file()
    
    async def get_configuration(self) -> CRMConfiguration:
        """Get current configuration with caching."""
        now = datetime.utcnow()
        
        # Check cache validity
        if (self._config_cache and self._cache_time and 
            (now - self._cache_time) < self._cache_ttl):
            return self._config_cache
        
        # Load configuration from file
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            # Extract YouGile config from enhanced config format
            if 'yougile' in config_data:
                # New enhanced config format
                yougile_config = config_data['yougile']
                legacy_config_data = {
                    'project_id': yougile_config['project_id'],
                    'board_id': yougile_config['board_id'],
                    'columns': yougile_config['columns'],
                    'ai_owner_sticker': yougile_config['ai_owner_sticker'],
                    'api_base_url': yougile_config.get('base_url', 'https://yougile.com/api-v2'),
                    'default_timeout_seconds': yougile_config.get('timeout', 30),
                    'max_retries': yougile_config.get('retry_attempts', 3),
                    'retry_delay_seconds': yougile_config.get('retry_delay', 1.0)
                }
            else:
                # Legacy config format
                legacy_config_data = config_data
            
            # Validate and create configuration model
            config = CRMConfiguration(**legacy_config_data)
            
            # Update cache
            self._config_cache = config
            self._cache_time = now
            
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {str(e)}")
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
        except IOError as e:
            raise ConfigurationError(f"Failed to read configuration file: {str(e)}")
    
    async def update_configuration(self, config: CRMConfiguration) -> bool:
        """Update configuration file."""
        try:
            # Convert to dict and write to file
            config_dict = config.dict()
            
            # Create backup
            backup_path = self.config_path.with_suffix('.json.backup')
            if self.config_path.exists():
                self.config_path.replace(backup_path)
            
            # Write new configuration
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            # Update cache
            self._config_cache = config
            self._cache_time = datetime.utcnow()
            
            return True
            
        except Exception as e:
            # Restore backup if write failed
            backup_path = self.config_path.with_suffix('.json.backup')
            if backup_path.exists():
                backup_path.replace(self.config_path)
            raise ConfigurationError(f"Failed to update configuration: {str(e)}")


# Repository factory functions
async def create_task_repository(api_key: str, config: CRMConfiguration) -> TaskRepository:
    """Create task repository instance."""
    return YouGileTaskRepository(api_key, config)


async def create_agent_repository(config: CRMConfiguration) -> AgentRepository:
    """Create agent repository instance."""
    return InMemoryAgentRepository(config)


async def create_configuration_repository(config_path: str = "config.json") -> ConfigurationRepository:
    """Create configuration repository instance."""
    return FileConfigurationRepository(config_path)