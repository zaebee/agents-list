"""
AI-CRM Agents Module

Intelligent agent system for task automation, routing, and AI-powered assistance.
"""

# Import key components for easy access
from .routing import RoutingContext, RoutingStrategy, SmartAgentRouter, WorkloadBalancer
from .selector import EnhancedAgentSelector, get_enhanced_selector, suggest_agents

__all__ = [
    # Agent selection
    "EnhancedAgentSelector",
    "get_enhanced_selector",
    "suggest_agents",
    # Agent routing
    "SmartAgentRouter",
    "RoutingStrategy",
    "RoutingContext",
    "WorkloadBalancer",
    # Submodules
    "selector",
    "routing",
    "integration",
    "training",
    "pm",
]
