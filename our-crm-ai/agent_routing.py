#!/usr/bin/env python3
"""
Context-Aware Agent Routing
Advanced agent routing system with workload balancing, context awareness, and intelligent scheduling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from models import Agent, TaskPriority, TaskComplexity, AgentSuggestion
from exceptions import AgentError, AgentUnavailableError
from repositories import AgentRepository


class RoutingStrategy(Enum):
    """Agent routing strategies."""

    BEST_MATCH = "best_match"  # Best capability match regardless of load
    LOAD_BALANCED = "load_balanced"  # Balance workload across agents
    PRIORITY_AWARE = "priority_aware"  # Consider task priority in routing
    CONTEXT_AWARE = "context_aware"  # Full context-aware routing
    ROUND_ROBIN = "round_robin"  # Simple round-robin distribution


@dataclass
class RoutingContext:
    """Context information for agent routing decisions."""

    task_priority: TaskPriority
    task_complexity: TaskComplexity
    estimated_hours: float
    deadline: Optional[datetime] = None
    required_skills: List[str] = None
    team_preferences: Dict[str, Any] = None
    previous_agent: Optional[str] = None  # For related tasks
    user_preferences: Dict[str, float] = None  # User-specific agent preferences

    def __post_init__(self):
        if self.required_skills is None:
            self.required_skills = []
        if self.team_preferences is None:
            self.team_preferences = {}
        if self.user_preferences is None:
            self.user_preferences = {}


@dataclass
class RoutingScore:
    """Comprehensive routing score for an agent."""

    agent_name: str
    capability_score: float
    workload_score: float
    availability_score: float
    context_score: float
    priority_bonus: float
    composite_score: float
    reasoning: str


class WorkloadBalancer:
    """Manages agent workload balancing and capacity planning."""

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repo = agent_repository
        self.logger = logging.getLogger("workload_balancer")

        # Workload weights for different task complexities
        self.complexity_weights = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MODERATE: 2.0,
            TaskComplexity.COMPLEX: 4.0,
            TaskComplexity.EPIC: 8.0,
        }

        # Priority urgency factors
        self.priority_factors = {
            TaskPriority.LOW: 0.8,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.5,
            TaskPriority.URGENT: 2.0,
        }

    async def calculate_workload_score(
        self, agent: Agent, context: RoutingContext
    ) -> float:
        """Calculate workload-based routing score (higher is better)."""
        try:
            # Base workload score (inversely related to current load)
            if agent.current_workload >= agent.max_concurrent_tasks:
                return 0.0  # Agent is at capacity

            # Calculate capacity utilization
            utilization = agent.current_workload / agent.max_concurrent_tasks

            # Score decreases as utilization increases
            base_score = 1.0 - utilization

            # Adjust for task complexity
            complexity_weight = self.complexity_weights.get(
                context.task_complexity, 2.0
            )

            # Check if agent can handle the additional workload
            weighted_workload = agent.current_workload + (complexity_weight * 0.5)
            if weighted_workload > agent.max_concurrent_tasks:
                return base_score * 0.3  # Heavily penalize overloading

            # Bonus for agents with very low workload
            if utilization < 0.3:
                base_score *= 1.2

            return max(0.0, min(1.0, base_score))

        except Exception as e:
            self.logger.warning(
                f"Failed to calculate workload score for {agent.name}: {e}"
            )
            return 0.5  # Neutral score on error

    async def get_balanced_agents(
        self,
        candidate_agents: List[Agent],
        context: RoutingContext,
        max_agents: int = 3,
    ) -> List[Tuple[Agent, float]]:
        """Get agents balanced by workload with scores."""
        agent_scores = []

        for agent in candidate_agents:
            if not agent.is_available:
                continue

            workload_score = await self.calculate_workload_score(agent, context)
            if workload_score > 0.1:  # Only include agents with reasonable capacity
                agent_scores.append((agent, workload_score))

        # Sort by workload score (best capacity first)
        agent_scores.sort(key=lambda x: x[1], reverse=True)

        return agent_scores[:max_agents]

    async def predict_completion_time(
        self, agent: Agent, context: RoutingContext
    ) -> datetime:
        """Predict when agent can complete the task."""
        try:
            # Base completion time from agent's average
            base_hours = agent.average_response_time_hours

            # Adjust for task complexity
            complexity_multiplier = self.complexity_weights.get(
                context.task_complexity, 2.0
            )
            estimated_hours = base_hours * complexity_multiplier

            # Adjust for current workload (more work = longer delays)
            workload_delay = agent.current_workload * 0.5  # Half hour delay per task
            total_hours = estimated_hours + workload_delay

            # Factor in priority
            priority_factor = self.priority_factors.get(context.task_priority, 1.0)
            if priority_factor > 1.0:
                # High priority tasks get expedited
                total_hours /= priority_factor

            completion_time = datetime.utcnow() + timedelta(hours=total_hours)
            return completion_time

        except Exception as e:
            self.logger.warning(f"Failed to predict completion time: {e}")
            # Fallback to simple estimate
            return datetime.utcnow() + timedelta(hours=context.estimated_hours)


class ContextAnalyzer:
    """Analyzes routing context for intelligent agent selection."""

    def __init__(self):
        self.logger = logging.getLogger("context_analyzer")

        # Skill affinity matrix (which agents work well together)
        self.skill_affinities = {
            "frontend-developer": ["ui-ux-designer", "backend-architect"],
            "backend-architect": ["database-optimizer", "security-auditor"],
            "devops-troubleshooter": ["cloud-architect", "network-engineer"],
            "data-scientist": ["ai-engineer", "data-engineer"],
            "security-auditor": ["backend-architect", "network-engineer"],
        }

        # Task type patterns
        self.task_patterns = {
            "bug_fix": ["debugger", "test-automator"],
            "new_feature": [
                "business-analyst",
                "backend-architect",
                "frontend-developer",
            ],
            "infrastructure": [
                "cloud-architect",
                "devops-troubleshooter",
                "network-engineer",
            ],
            "data_analysis": ["data-scientist", "business-analyst"],
            "security_review": ["security-auditor", "code-reviewer"],
        }

    def analyze_task_context(self, task_description: str) -> Dict[str, Any]:
        """Analyze task context to extract routing insights."""
        context_insights = {
            "task_type": self._classify_task_type(task_description),
            "urgency_indicators": self._extract_urgency_indicators(task_description),
            "collaboration_needs": self._assess_collaboration_needs(task_description),
            "technical_complexity": self._assess_technical_complexity(task_description),
        }

        return context_insights

    def _classify_task_type(self, description: str) -> str:
        """Classify the type of task based on content."""
        desc_lower = description.lower()

        # Check for specific patterns
        if any(word in desc_lower for word in ["bug", "fix", "error", "broken"]):
            return "bug_fix"
        elif any(
            word in desc_lower for word in ["feature", "implement", "add", "create"]
        ):
            return "new_feature"
        elif any(
            word in desc_lower
            for word in ["deploy", "infrastructure", "server", "cloud"]
        ):
            return "infrastructure"
        elif any(
            word in desc_lower for word in ["data", "analysis", "report", "metrics"]
        ):
            return "data_analysis"
        elif any(word in desc_lower for word in ["security", "audit", "vulnerability"]):
            return "security_review"
        else:
            return "general"

    def _extract_urgency_indicators(self, description: str) -> List[str]:
        """Extract urgency indicators from task description."""
        desc_lower = description.lower()
        indicators = []

        urgency_keywords = {
            "critical": 3,
            "urgent": 3,
            "asap": 3,
            "immediately": 3,
            "production down": 3,
            "high priority": 2,
            "important": 2,
            "soon": 1,
            "when possible": -1,
        }

        for keyword, weight in urgency_keywords.items():
            if keyword in desc_lower:
                indicators.append(f"{keyword} (weight: {weight})")

        return indicators

    def _assess_collaboration_needs(self, description: str) -> Dict[str, Any]:
        """Assess if task requires collaboration between agents."""
        desc_lower = description.lower()

        collaboration_indicators = {
            "full_stack": any(
                word in desc_lower for word in ["full stack", "end-to-end", "complete"]
            ),
            "cross_functional": any(
                word in desc_lower for word in ["frontend and backend", "ui and api"]
            ),
            "review_needed": any(
                word in desc_lower for word in ["review", "approve", "validate"]
            ),
            "integration": any(
                word in desc_lower for word in ["integrate", "connect", "sync"]
            ),
        }

        return {k: v for k, v in collaboration_indicators.items() if v}

    def _assess_technical_complexity(self, description: str) -> Dict[str, int]:
        """Assess technical complexity indicators."""
        desc_lower = description.lower()

        complexity_indicators = {}

        # Technical depth indicators
        if any(
            word in desc_lower
            for word in ["architecture", "design pattern", "scalable"]
        ):
            complexity_indicators["architectural"] = 3

        if any(
            word in desc_lower for word in ["algorithm", "optimization", "performance"]
        ):
            complexity_indicators["algorithmic"] = 2

        if any(word in desc_lower for word in ["integration", "api", "third-party"]):
            complexity_indicators["integration"] = 2

        if any(word in desc_lower for word in ["database", "schema", "migration"]):
            complexity_indicators["data"] = 2

        return complexity_indicators

    def calculate_context_score(
        self, agent_name: str, context: RoutingContext, task_insights: Dict[str, Any]
    ) -> float:
        """Calculate context-aware score for agent."""
        score = 0.5  # Base neutral score

        # Task type affinity
        task_type = task_insights.get("task_type", "general")
        if task_type in self.task_patterns:
            preferred_agents = self.task_patterns[task_type]
            if agent_name in preferred_agents:
                score += 0.3

        # Skill affinity with previous agent
        if context.previous_agent and context.previous_agent in self.skill_affinities:
            if agent_name in self.skill_affinities[context.previous_agent]:
                score += 0.2

        # User preferences
        if context.user_preferences and agent_name in context.user_preferences:
            preference_score = context.user_preferences[agent_name]
            score += (preference_score - 0.5) * 0.2  # -0.1 to +0.1 adjustment

        # Urgency match
        urgency_indicators = task_insights.get("urgency_indicators", [])
        if urgency_indicators and context.task_priority in [
            TaskPriority.HIGH,
            TaskPriority.URGENT,
        ]:
            score += 0.1

        return max(0.0, min(1.0, score))


class SmartAgentRouter:
    """
    Smart agent routing system with multiple strategies and context awareness.
    """

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repo = agent_repository
        self.workload_balancer = WorkloadBalancer(agent_repository)
        self.context_analyzer = ContextAnalyzer()
        self.logger = logging.getLogger("smart_agent_router")

        # Round robin state
        self._round_robin_index = {}

    async def route_task(
        self,
        agent_suggestions: List[AgentSuggestion],
        context: RoutingContext,
        strategy: RoutingStrategy = RoutingStrategy.CONTEXT_AWARE,
        task_description: str = "",
    ) -> Tuple[str, RoutingScore]:
        """
        Route task to optimal agent using specified strategy.

        Returns:
            Tuple of (agent_name, routing_score)
        """
        try:
            if not agent_suggestions:
                raise AgentError("No agent suggestions provided for routing")

            # Get agent details
            agents = []
            for suggestion in agent_suggestions:
                agent = await self.agent_repo.get_agent(suggestion.agent_name)
                if agent and agent.is_available:
                    agents.append((agent, suggestion))

            if not agents:
                raise AgentUnavailableError("No available agents found")

            # Route based on strategy
            if strategy == RoutingStrategy.BEST_MATCH:
                return await self._route_best_match(agents, context)
            elif strategy == RoutingStrategy.LOAD_BALANCED:
                return await self._route_load_balanced(agents, context)
            elif strategy == RoutingStrategy.PRIORITY_AWARE:
                return await self._route_priority_aware(
                    agents, context, task_description
                )
            elif strategy == RoutingStrategy.CONTEXT_AWARE:
                return await self._route_context_aware(
                    agents, context, task_description
                )
            elif strategy == RoutingStrategy.ROUND_ROBIN:
                return await self._route_round_robin(agents)
            else:
                # Default to context-aware
                return await self._route_context_aware(
                    agents, context, task_description
                )

        except Exception as e:
            self.logger.error(f"Agent routing failed: {e}")
            raise AgentError(f"Agent routing failed: {str(e)}")

    async def _route_best_match(
        self, agents: List[Tuple[Agent, AgentSuggestion]], context: RoutingContext
    ) -> Tuple[str, RoutingScore]:
        """Route to agent with best capability match."""
        best_agent = None
        best_score = 0.0

        for agent, suggestion in agents:
            if suggestion.confidence > best_score:
                best_score = suggestion.confidence
                best_agent = (agent, suggestion)

        if not best_agent:
            raise AgentError("No suitable agent found")

        agent, suggestion = best_agent

        routing_score = RoutingScore(
            agent_name=agent.name,
            capability_score=suggestion.confidence / 100.0,
            workload_score=1.0,  # Not considered in this strategy
            availability_score=1.0 if agent.is_available else 0.0,
            context_score=1.0,  # Not considered
            priority_bonus=0.0,
            composite_score=suggestion.confidence / 100.0,
            reasoning="Best capability match",
        )

        return agent.name, routing_score

    async def _route_load_balanced(
        self, agents: List[Tuple[Agent, AgentSuggestion]], context: RoutingContext
    ) -> Tuple[str, RoutingScore]:
        """Route to agent with best workload balance."""
        agent_list = [agent for agent, _ in agents]
        balanced_agents = await self.workload_balancer.get_balanced_agents(
            agent_list, context, max_agents=len(agent_list)
        )

        if not balanced_agents:
            raise AgentUnavailableError("No agents with available capacity")

        best_agent, workload_score = balanced_agents[0]

        routing_score = RoutingScore(
            agent_name=best_agent.name,
            capability_score=0.5,  # Average capability assumed
            workload_score=workload_score,
            availability_score=1.0 if best_agent.is_available else 0.0,
            context_score=0.5,  # Not considered
            priority_bonus=0.0,
            composite_score=workload_score,
            reasoning="Best workload balance",
        )

        return best_agent.name, routing_score

    async def _route_priority_aware(
        self,
        agents: List[Tuple[Agent, AgentSuggestion]],
        context: RoutingContext,
        task_description: str,
    ) -> Tuple[str, RoutingScore]:
        """Route considering task priority and urgency."""
        best_agent = None
        best_score = 0.0

        # Priority multipliers
        priority_multiplier = {
            TaskPriority.LOW: 0.8,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.3,
            TaskPriority.URGENT: 1.6,
        }.get(context.task_priority, 1.0)

        for agent, suggestion in agents:
            # Base score from capability
            capability_score = suggestion.confidence / 100.0

            # Workload penalty (urgent tasks prefer less loaded agents)
            workload_score = await self.workload_balancer.calculate_workload_score(
                agent, context
            )

            # Combine scores with priority weighting
            if context.task_priority in [TaskPriority.HIGH, TaskPriority.URGENT]:
                # For high priority, heavily weight workload
                composite_score = (
                    capability_score * 0.4 + workload_score * 0.6
                ) * priority_multiplier
            else:
                # For lower priority, balance capability and workload
                composite_score = (
                    capability_score * 0.7 + workload_score * 0.3
                ) * priority_multiplier

            if composite_score > best_score:
                best_score = composite_score
                best_agent = (agent, suggestion, capability_score, workload_score)

        if not best_agent:
            raise AgentError("No suitable agent found")

        agent, suggestion, cap_score, work_score = best_agent

        routing_score = RoutingScore(
            agent_name=agent.name,
            capability_score=cap_score,
            workload_score=work_score,
            availability_score=1.0 if agent.is_available else 0.0,
            context_score=0.5,
            priority_bonus=(priority_multiplier - 1.0) * 0.5,
            composite_score=best_score,
            reasoning=f"Priority-aware routing (priority: {context.task_priority.value})",
        )

        return agent.name, routing_score

    async def _route_context_aware(
        self,
        agents: List[Tuple[Agent, AgentSuggestion]],
        context: RoutingContext,
        task_description: str,
    ) -> Tuple[str, RoutingScore]:
        """Full context-aware routing with all factors."""
        task_insights = self.context_analyzer.analyze_task_context(task_description)

        best_agent = None
        best_score = 0.0

        for agent, suggestion in agents:
            # Component scores
            capability_score = suggestion.confidence / 100.0
            workload_score = await self.workload_balancer.calculate_workload_score(
                agent, context
            )
            availability_score = 1.0 if agent.is_available else 0.0
            context_score = self.context_analyzer.calculate_context_score(
                agent.name, context, task_insights
            )

            # Priority bonus
            priority_bonus = {
                TaskPriority.LOW: 0.0,
                TaskPriority.MEDIUM: 0.05,
                TaskPriority.HIGH: 0.1,
                TaskPriority.URGENT: 0.2,
            }.get(context.task_priority, 0.0)

            # Deadline urgency
            deadline_factor = 1.0
            if context.deadline:
                hours_until_deadline = (
                    context.deadline - datetime.utcnow()
                ).total_seconds() / 3600
                if hours_until_deadline < 24:  # Less than 24 hours
                    deadline_factor = 1.3
                elif hours_until_deadline < 8:  # Less than 8 hours
                    deadline_factor = 1.6

            # Composite score with weighted factors
            composite_score = (
                capability_score * 0.3
                + workload_score * 0.25
                + availability_score * 0.2
                + context_score * 0.25
            ) + priority_bonus

            composite_score *= deadline_factor

            if composite_score > best_score and availability_score > 0:
                best_score = composite_score
                best_agent = (
                    agent,
                    suggestion,
                    capability_score,
                    workload_score,
                    availability_score,
                    context_score,
                    priority_bonus,
                )

        if not best_agent:
            raise AgentError("No suitable agent found")

        agent, suggestion, cap_score, work_score, avail_score, ctx_score, pri_bonus = (
            best_agent
        )

        # Generate detailed reasoning
        reasoning_parts = [
            f"Capability: {cap_score:.2f}",
            f"Workload: {work_score:.2f}",
            f"Context: {ctx_score:.2f}",
        ]

        if pri_bonus > 0:
            reasoning_parts.append(f"Priority bonus: {pri_bonus:.2f}")

        task_type = task_insights.get("task_type", "general")
        if task_type != "general":
            reasoning_parts.append(f"Task type: {task_type}")

        routing_score = RoutingScore(
            agent_name=agent.name,
            capability_score=cap_score,
            workload_score=work_score,
            availability_score=avail_score,
            context_score=ctx_score,
            priority_bonus=pri_bonus,
            composite_score=best_score,
            reasoning="; ".join(reasoning_parts),
        )

        return agent.name, routing_score

    async def _route_round_robin(
        self, agents: List[Tuple[Agent, AgentSuggestion]]
    ) -> Tuple[str, RoutingScore]:
        """Simple round-robin routing."""
        available_agents = [agent for agent, _ in agents if agent.is_available]

        if not available_agents:
            raise AgentUnavailableError("No available agents")

        # Get or initialize round robin index for this agent set
        agent_names = [agent.name for agent in available_agents]
        agent_key = "|".join(sorted(agent_names))

        if agent_key not in self._round_robin_index:
            self._round_robin_index[agent_key] = 0

        # Select next agent in round robin
        selected_agent = available_agents[self._round_robin_index[agent_key]]

        # Update index for next selection
        self._round_robin_index[agent_key] = (
            self._round_robin_index[agent_key] + 1
        ) % len(available_agents)

        routing_score = RoutingScore(
            agent_name=selected_agent.name,
            capability_score=0.5,
            workload_score=0.5,
            availability_score=1.0,
            context_score=0.5,
            priority_bonus=0.0,
            composite_score=0.5,
            reasoning="Round-robin selection",
        )

        return selected_agent.name, routing_score

    async def get_routing_recommendations(
        self,
        agent_suggestions: List[AgentSuggestion],
        context: RoutingContext,
        task_description: str = "",
    ) -> List[Tuple[str, RoutingScore]]:
        """Get routing recommendations with scores for all strategies."""
        recommendations = []

        strategies = [
            RoutingStrategy.CONTEXT_AWARE,
            RoutingStrategy.PRIORITY_AWARE,
            RoutingStrategy.LOAD_BALANCED,
            RoutingStrategy.BEST_MATCH,
        ]

        for strategy in strategies:
            try:
                agent_name, score = await self.route_task(
                    agent_suggestions, context, strategy, task_description
                )
                recommendations.append((f"{strategy.value}: {agent_name}", score))
            except Exception as e:
                self.logger.warning(
                    f"Failed to get recommendation for {strategy.value}: {e}"
                )

        return recommendations


# Factory function
def create_smart_router(agent_repository: AgentRepository) -> SmartAgentRouter:
    """Create smart agent router instance."""
    return SmartAgentRouter(agent_repository)
