#!/usr/bin/env python3
"""
Configuration Management with Validation
Advanced configuration system with Pydantic validation, environment variables, and multiple sources.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum

from exceptions import ConfigurationError


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StorageBackend(str, Enum):
    """Storage backend types."""
    FILE = "file"
    SQLITE = "sqlite"
    MEMORY = "memory"


class AIProviderConfig(BaseModel):
    """AI provider configuration."""
    provider: str = Field(..., description="AI provider name")
    model: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(None, description="API key (can be from environment)")
    endpoint: Optional[str] = Field(None, description="Custom endpoint URL")
    max_tokens: int = Field(default=4000, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: int = Field(default=30, ge=1, le=300)
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'anthropic', 'azure', 'local']
        if v.lower() not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v.lower()


class YouGileConfig(BaseModel):
    """YouGile integration configuration."""
    api_key: Optional[str] = Field(None, description="YouGile API key (from environment)")
    base_url: str = Field(default="https://yougile.com/api/v2")
    project_id: str = Field(..., description="YouGile project ID")
    board_id: str = Field(..., description="YouGile board ID")
    
    # Column mappings
    columns: Dict[str, str] = Field(default_factory=dict, description="Status column mappings")
    
    # Agent sticker configuration
    ai_owner_sticker: Dict[str, Any] = Field(default_factory=dict, description="AI owner sticker config")
    
    # API settings
    timeout: int = Field(default=30, ge=1, le=120)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    
    @validator('columns')
    def validate_columns(cls, v):
        required_statuses = ['To Do', 'In Progress', 'Done']
        missing = [status for status in required_statuses if status not in v]
        if missing:
            raise ValueError(f'Missing required column mappings: {missing}')
        return v


class AgentConfig(BaseModel):
    """Individual agent configuration."""
    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    keywords: List[str] = Field(default_factory=list, description="Agent keywords")
    max_concurrent_tasks: int = Field(default=5, ge=1, le=20)
    average_response_time_hours: float = Field(default=4.0, ge=0.1, le=72.0)
    is_available: bool = Field(default=True)
    specializations: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list, description="Available tools")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Agent name cannot be empty')
        return v.strip()


class AgentSystemConfig(BaseModel):
    """Agent system configuration."""
    enabled_agents: List[str] = Field(default_factory=list, description="List of enabled agent names")
    agent_configs: Dict[str, AgentConfig] = Field(default_factory=dict)
    default_agent: str = Field(default="general-purpose", description="Default fallback agent")
    
    # Agent selection settings
    enable_semantic_matching: bool = Field(default=True)
    enable_learning_system: bool = Field(default=True)
    max_suggestions: int = Field(default=5, ge=1, le=20)
    
    # Routing settings
    default_routing_strategy: str = Field(default="context_aware")
    workload_balancing: bool = Field(default=True)
    priority_routing: bool = Field(default=True)
    
    @validator('enabled_agents')
    def validate_enabled_agents(cls, v, values):
        if 'agent_configs' in values:
            missing = [agent for agent in v if agent not in values['agent_configs']]
            if missing:
                raise ValueError(f'Enabled agents not found in agent_configs: {missing}')
        return v


class WorkflowConfig(BaseModel):
    """Workflow and persistence configuration."""
    storage_backend: StorageBackend = Field(default=StorageBackend.FILE)
    storage_path: str = Field(default="workflow_storage")
    enable_caching: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    cleanup_days: int = Field(default=30, ge=1, le=365)
    
    # SQLite specific settings
    sqlite_db_path: str = Field(default="workflows.db")
    sqlite_connection_pool_size: int = Field(default=10, ge=1, le=50)
    
    @validator('storage_path')
    def validate_storage_path(cls, v):
        # Ensure path is valid and create directory if needed
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f'Cannot create storage path {v}: {str(e)}')
        return str(path)


class SecurityConfig(BaseModel):
    """Security and encryption configuration."""
    encrypt_sensitive_data: bool = Field(default=True)
    encryption_key_env: str = Field(default="AI_CRM_ENCRYPTION_KEY")
    api_rate_limit_per_minute: int = Field(default=100, ge=1, le=10000)
    enable_request_logging: bool = Field(default=False)
    log_sensitive_data: bool = Field(default=False)
    
    # Session and token settings
    session_timeout_hours: int = Field(default=24, ge=1, le=168)
    token_refresh_threshold_minutes: int = Field(default=30, ge=5, le=120)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_path: Optional[str] = Field(None, description="Log file path (None for console only)")
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=20)
    
    # Component-specific log levels
    component_levels: Dict[str, LogLevel] = Field(default_factory=dict)
    
    @validator('file_path')
    def validate_log_path(cls, v):
        if v:
            log_path = Path(v)
            log_dir = log_path.parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ValueError(f'Cannot create log directory {log_dir}: {str(e)}')
        return v


class PerformanceConfig(BaseModel):
    """Performance and optimization settings."""
    max_concurrent_requests: int = Field(default=10, ge=1, le=100)
    request_timeout_seconds: int = Field(default=60, ge=5, le=300)
    connection_pool_size: int = Field(default=20, ge=1, le=100)
    enable_request_caching: bool = Field(default=True)
    cache_size_mb: int = Field(default=50, ge=1, le=500)
    
    # Agent processing settings
    max_agent_processing_time_minutes: int = Field(default=30, ge=1, le=120)
    agent_health_check_interval_seconds: int = Field(default=300, ge=30, le=3600)


class MainConfig(BaseModel):
    """Main application configuration."""
    # Core components
    ai_provider: AIProviderConfig
    yougile: YouGileConfig
    agents: AgentSystemConfig
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Application metadata
    app_name: str = Field(default="AI-CRM")
    app_version: str = Field(default="2.0.0")
    debug: bool = Field(default=False)
    
    # Feature flags
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "semantic_matching": True,
        "learning_system": True,
        "workflow_persistence": True,
        "agent_routing": True,
        "pm_analysis": True,
        "rich_cli": True
    })
    
    class Config:
        env_prefix = "AI_CRM_"
        case_sensitive = False


class ConfigurationManager:
    """
    Advanced configuration manager with validation, environment variables, and multiple sources.
    """
    
    def __init__(self, config_path: Optional[str] = None, env_prefix: str = "AI_CRM_"):
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self.env_prefix = env_prefix
        self.logger = logging.getLogger("config_manager")
        
        self._config: Optional[MainConfig] = None
        self._env_overrides: Dict[str, Any] = {}
        
    def _load_environment_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        overrides = {}
        
        # Map of environment variable suffixes to config paths
        env_mappings = {
            "YOUGILE_API_KEY": ("yougile", "api_key"),
            "AI_PROVIDER": ("ai_provider", "provider"),
            "AI_MODEL": ("ai_provider", "model"),
            "AI_API_KEY": ("ai_provider", "api_key"),
            "DEBUG": ("debug",),
            "LOG_LEVEL": ("logging", "level"),
            "LOG_FILE": ("logging", "file_path"),
            "STORAGE_BACKEND": ("workflow", "storage_backend"),
            "STORAGE_PATH": ("workflow", "storage_path"),
            "ENABLE_SEMANTIC": ("agents", "enable_semantic_matching"),
            "MAX_CONCURRENT": ("performance", "max_concurrent_requests"),
        }
        
        for env_suffix, config_path in env_mappings.items():
            env_var = f"{self.env_prefix}{env_suffix}"
            value = os.getenv(env_var)
            
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                
                # Set nested configuration
                current = overrides
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                current[config_path[-1]] = converted_value
                self.logger.debug(f"Environment override: {env_var} -> {config_path}")
        
        return overrides
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer values
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float values
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON values (for lists/dicts)
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # String values
        return value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def load_config(self) -> MainConfig:
        """Load and validate configuration from all sources."""
        try:
            # Load base configuration from file
            base_config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    base_config = json.load(f)
                self.logger.info(f"Loaded base configuration from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file {self.config_path} not found, using defaults")
            
            # Load environment overrides
            self._env_overrides = self._load_environment_overrides()
            
            # Merge configurations
            merged_config = self._merge_configs(base_config, self._env_overrides)
            
            # Validate and create configuration object
            self._config = MainConfig(**merged_config)
            
            # Post-validation setup
            self._setup_logging()
            
            self.logger.info("Configuration loaded and validated successfully")
            return self._config
            
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg)
    
    def _setup_logging(self):
        """Configure logging based on configuration."""
        if not self._config:
            return
        
        log_config = self._config.logging
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.level.value))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(log_config.format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_config.file_path:
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_config.file_path,
                    maxBytes=log_config.max_file_size_mb * 1024 * 1024,
                    backupCount=log_config.backup_count
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                self.logger.info(f"Logging to file: {log_config.file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to setup file logging: {e}")
        
        # Set component-specific log levels
        for component, level in log_config.component_levels.items():
            component_logger = logging.getLogger(component)
            component_logger.setLevel(getattr(logging, level.value))
    
    def get_config(self) -> MainConfig:
        """Get the current configuration, loading it if necessary."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self) -> MainConfig:
        """Reload configuration from all sources."""
        self._config = None
        return self.load_config()
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """Save current configuration to file (excluding environment overrides)."""
        if not self._config:
            raise ConfigurationError("No configuration loaded to save")
        
        save_path = Path(config_path) if config_path else self.config_path
        
        try:
            # Convert to dict and remove environment-only values
            config_dict = self._config.dict()
            
            # Remove sensitive data that should only come from environment
            if "yougile" in config_dict and "api_key" in config_dict["yougile"]:
                config_dict["yougile"]["api_key"] = None
            
            if "ai_provider" in config_dict and "api_key" in config_dict["ai_provider"]:
                config_dict["ai_provider"]["api_key"] = None
            
            with open(save_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            self.logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def validate_runtime_config(self) -> Dict[str, Any]:
        """Validate runtime configuration and return status."""
        if not self._config:
            return {"valid": False, "error": "No configuration loaded"}
        
        issues = []
        
        try:
            # Check required environment variables
            if not os.getenv(f"{self.env_prefix}YOUGILE_API_KEY"):
                issues.append("YOUGILE_API_KEY environment variable not set")
            
            ai_provider = self._config.ai_provider.provider
            if ai_provider in ['openai', 'anthropic'] and not self._config.ai_provider.api_key:
                if not os.getenv(f"{self.env_prefix}AI_API_KEY"):
                    issues.append(f"AI_API_KEY environment variable required for {ai_provider}")
            
            # Check file paths exist
            if self._config.logging.file_path:
                log_dir = Path(self._config.logging.file_path).parent
                if not log_dir.exists():
                    issues.append(f"Log directory does not exist: {log_dir}")
            
            # Check storage configuration
            if self._config.workflow.storage_backend == StorageBackend.SQLITE:
                db_path = Path(self._config.workflow.sqlite_db_path)
                if not db_path.parent.exists():
                    issues.append(f"Database directory does not exist: {db_path.parent}")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "config_source": str(self.config_path),
                "env_overrides_count": len(self._env_overrides)
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
    
    def get_effective_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the effective configuration."""
        if not self._config:
            return {"error": "No configuration loaded"}
        
        return {
            "app_name": self._config.app_name,
            "app_version": self._config.app_version,
            "debug": self._config.debug,
            "ai_provider": {
                "provider": self._config.ai_provider.provider,
                "model": self._config.ai_provider.model,
                "has_api_key": bool(self._config.ai_provider.api_key or os.getenv(f"{self.env_prefix}AI_API_KEY"))
            },
            "yougile": {
                "project_id": self._config.yougile.project_id,
                "board_id": self._config.yougile.board_id,
                "has_api_key": bool(os.getenv(f"{self.env_prefix}YOUGILE_API_KEY"))
            },
            "agents": {
                "enabled_count": len(self._config.agents.enabled_agents),
                "semantic_matching": self._config.agents.enable_semantic_matching,
                "learning_system": self._config.agents.enable_learning_system
            },
            "workflow": {
                "storage_backend": self._config.workflow.storage_backend.value,
                "storage_path": self._config.workflow.storage_path,
                "caching_enabled": self._config.workflow.enable_caching
            },
            "features": self._config.features,
            "logging": {
                "level": self._config.logging.level.value,
                "file_logging": bool(self._config.logging.file_path)
            }
        }


# Factory functions and global instance
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager(config_path: Optional[str] = None) -> ConfigurationManager:
    """Get global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None or config_path:
        _config_manager = ConfigurationManager(config_path)
    
    return _config_manager

def load_config(config_path: Optional[str] = None) -> MainConfig:
    """Load configuration using global manager."""
    return get_config_manager(config_path).get_config()

def reload_config() -> MainConfig:
    """Reload configuration using global manager."""
    return get_config_manager().reload_config()