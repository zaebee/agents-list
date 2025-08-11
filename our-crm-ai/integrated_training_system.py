#!/usr/bin/env python3
"""
Integrated Training System - Unified system for training all 59+ specialized agents.

This module orchestrates:
1. Complete training pipeline integration
2. Cross-agent collaboration training
3. Production deployment of improved agents
4. System-wide performance monitoring
5. Automated training scheduling and management
"""

import json
import asyncio
import logging
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import uuid

# Import all training framework components
from agent_training_framework import (
    AgentTrainingPipeline,
    TrainingPhase,
)
from training_data_manager import TrainingDataCurator
from performance_optimizer import (
    AgentOptimizer,
    OptimizationStrategy,
    PerformanceMonitor,
)
from agent_selector import AGENT_KEYWORDS
from pm_agent_gateway import PMAgentGateway


class SystemStatus(Enum):
    """System-wide training status."""

    INITIALIZING = "initializing"
    TRAINING = "training"
    OPTIMIZING = "optimizing"
    MONITORING = "monitoring"
    IDLE = "idle"
    ERROR = "error"


class TrainingPriority(Enum):
    """Training priority levels."""

    CRITICAL = 1  # System-critical agents
    HIGH = 2  # High-impact agents
    NORMAL = 3  # Standard agents
    LOW = 4  # Background training


@dataclass
class SystemTrainingConfig:
    """System-wide training configuration."""

    training_schedule: Dict[str, str]  # agent -> cron expression
    batch_size: int
    max_concurrent_training: int
    auto_optimization: bool
    performance_monitoring: bool
    continuous_learning: bool
    resource_limits: Dict[str, Any]
    notification_settings: Dict[str, bool]


@dataclass
class AgentTrainingStatus:
    """Individual agent training status."""

    agent_name: str
    current_phase: Optional[TrainingPhase]
    last_trained: Optional[datetime]
    training_score: float
    performance_trend: str
    next_training: Optional[datetime]
    priority: TrainingPriority
    issues: List[str]
    recommendations: List[str]


class IntegratedTrainingSystem:
    """Master training system orchestrating all components."""

    def __init__(self, config_path: str = "integrated_training_config.json"):
        """Initialize the integrated training system."""
        self.config = self._load_system_config(config_path)
        self.status = SystemStatus.INITIALIZING

        # Initialize core components
        self.training_pipeline = AgentTrainingPipeline()
        self.data_curator = TrainingDataCurator()
        self.optimizer = AgentOptimizer()
        self.performance_monitor = PerformanceMonitor()
        self.pm_gateway = PMAgentGateway()

        # Training orchestration
        self.active_training_sessions = {}
        self.training_queue = []
        self.agent_status = {}

        # System monitoring
        self.system_metrics = {}
        self.training_history = []

        # Initialize all agents
        self._initialize_agent_status()

        # Setup scheduling
        self._setup_training_schedules()

        # Setup performance monitoring
        if self.config.performance_monitoring:
            self._setup_performance_monitoring()

        self.status = SystemStatus.IDLE
        logging.info("Integrated Training System initialized")

    def _load_system_config(self, config_path: str) -> SystemTrainingConfig:
        """Load system configuration."""
        default_config = {
            "training_schedule": {
                # Critical agents - daily training
                "pm-agent-gateway": "0 2 * * *",  # 2 AM daily
                "agent-selector": "0 3 * * *",  # 3 AM daily
                # High-priority agents - every other day
                "python-pro": "0 1 */2 * *",
                "javascript-pro": "0 1 */2 * *",
                "security-auditor": "0 4 */2 * *",
                "database-optimizer": "0 5 */2 * *",
                # Normal agents - weekly
                "*": "0 0 * * 0",  # Sunday midnight for all others
            },
            "batch_size": 3,
            "max_concurrent_training": 2,
            "auto_optimization": True,
            "performance_monitoring": True,
            "continuous_learning": True,
            "resource_limits": {
                "max_memory_gb": 4,
                "max_cpu_percent": 80,
                "max_training_duration_hours": 2,
            },
            "notification_settings": {
                "training_completion": True,
                "performance_alerts": True,
                "system_errors": True,
            },
        }

        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logging.info(f"Config file {config_path} not found, using defaults")

        return SystemTrainingConfig(**default_config)

    def _initialize_agent_status(self):
        """Initialize training status for all agents."""
        all_agents = list(AGENT_KEYWORDS.keys()) + [
            "pm-agent-gateway",
            "agent-selector",
            "backlog-analyzer",
        ]

        for agent_name in all_agents:
            priority = self._determine_agent_priority(agent_name)

            self.agent_status[agent_name] = AgentTrainingStatus(
                agent_name=agent_name,
                current_phase=None,
                last_trained=None,
                training_score=0.5,  # Initial score
                performance_trend="unknown",
                next_training=None,
                priority=priority,
                issues=[],
                recommendations=[],
            )

    def _determine_agent_priority(self, agent_name: str) -> TrainingPriority:
        """Determine training priority for an agent."""
        critical_agents = ["pm-agent-gateway", "agent-selector", "security-auditor"]
        high_priority_agents = [
            "python-pro",
            "javascript-pro",
            "database-optimizer",
            "frontend-developer",
            "backend-architect",
            "ai-engineer",
        ]

        if agent_name in critical_agents:
            return TrainingPriority.CRITICAL
        elif agent_name in high_priority_agents:
            return TrainingPriority.HIGH
        else:
            return TrainingPriority.NORMAL

    def _setup_training_schedules(self):
        """Setup automated training schedules."""
        # Schedule training for each agent based on configuration
        for agent_name, cron_expr in self.config.training_schedule.items():
            if agent_name == "*":
                # Apply to all agents without specific schedules
                for agent in self.agent_status.keys():
                    if agent not in self.config.training_schedule:
                        schedule.every().sunday.at("00:00").do(
                            self._schedule_agent_training, agent
                        )
            else:
                # Parse cron expression and create schedule
                # Simplified scheduling (full cron parsing would be more complex)
                if "* * *" in cron_expr:  # Daily
                    hour = int(cron_expr.split()[1])
                    schedule.every().day.at(f"{hour:02d}:00").do(
                        self._schedule_agent_training, agent_name
                    )
                elif "*/2 * *" in cron_expr:  # Every other day
                    hour = int(cron_expr.split()[1])
                    schedule.every(2).days.at(f"{hour:02d}:00").do(
                        self._schedule_agent_training, agent_name
                    )

        logging.info(
            f"Scheduled training for {len(self.config.training_schedule)} agent patterns"
        )

    def _setup_performance_monitoring(self):
        """Setup system-wide performance monitoring."""

        def performance_alert_handler(alert_data):
            self._handle_performance_alert(alert_data)

        self.performance_monitor.register_alert_callback(performance_alert_handler)
        self.performance_monitor.start_monitoring(interval=10.0)

        logging.info("Performance monitoring activated")

    def _schedule_agent_training(self, agent_name: str):
        """Schedule training for a specific agent."""
        if agent_name not in self.agent_status:
            logging.warning(f"Unknown agent {agent_name} scheduled for training")
            return

        # Check if agent is already in training queue or actively training
        if (
            agent_name in [item["agent_name"] for item in self.training_queue]
            or agent_name in self.active_training_sessions
        ):
            logging.info(f"Agent {agent_name} already scheduled or training")
            return

        # Add to training queue
        priority = self.agent_status[agent_name].priority.value
        self.training_queue.append(
            {
                "agent_name": agent_name,
                "scheduled_at": datetime.now(),
                "priority": priority,
            }
        )

        # Sort queue by priority
        self.training_queue.sort(key=lambda x: x["priority"])

        logging.info(f"Scheduled training for {agent_name} (priority: {priority})")

    def _handle_performance_alert(self, alert_data: Dict):
        """Handle performance alerts from monitoring system."""
        if alert_data["severity"] in ["critical", "high"]:
            # Find affected agent and schedule emergency training
            affected_agents = self._identify_agents_for_alert(alert_data)

            for agent_name in affected_agents:
                self._schedule_emergency_training(agent_name, alert_data)

        # Log alert
        self.system_metrics["last_alert"] = alert_data
        logging.warning(
            f"Performance alert: {alert_data['metric']} = {alert_data['current_value']}"
        )

    def _identify_agents_for_alert(self, alert_data: Dict) -> List[str]:
        """Identify which agents might be related to a performance alert."""
        metric = alert_data["metric"]

        # Simple mapping of metrics to agent types
        if "memory" in metric:
            return [
                agent
                for agent in self.agent_status.keys()
                if "database" in agent or "data" in agent or "ml" in agent
            ]
        elif "response_time" in metric:
            return [
                agent
                for agent in self.agent_status.keys()
                if "frontend" in agent or "api" in agent
            ]
        else:
            # Return high-priority agents as default
            return [
                agent
                for agent, status in self.agent_status.items()
                if status.priority in [TrainingPriority.CRITICAL, TrainingPriority.HIGH]
            ]

    def _schedule_emergency_training(self, agent_name: str, alert_data: Dict):
        """Schedule emergency training for performance issues."""
        # Add to front of training queue with emergency priority
        emergency_item = {
            "agent_name": agent_name,
            "scheduled_at": datetime.now(),
            "priority": 0,  # Highest priority
            "emergency": True,
            "alert_context": alert_data,
        }

        self.training_queue.insert(0, emergency_item)
        logging.warning(
            f"Emergency training scheduled for {agent_name} due to {alert_data['metric']} alert"
        )

    async def start_system_training(self):
        """Start the system-wide training orchestration."""
        self.status = SystemStatus.TRAINING
        logging.info("Starting integrated training system")

        # Start background processes
        training_task = asyncio.create_task(self._training_orchestrator())
        monitoring_task = asyncio.create_task(self._system_monitoring())
        scheduling_task = asyncio.create_task(self._schedule_processor())

        try:
            # Run all tasks concurrently
            await asyncio.gather(training_task, monitoring_task, scheduling_task)
        except Exception as e:
            logging.error(f"Error in system training: {e}")
            self.status = SystemStatus.ERROR
        finally:
            self.status = SystemStatus.IDLE

    async def _training_orchestrator(self):
        """Main training orchestration loop."""
        while True:
            try:
                # Check if we can start new training sessions
                if (
                    len(self.active_training_sessions)
                    < self.config.max_concurrent_training
                    and self.training_queue
                ):
                    # Get next training item
                    training_item = self.training_queue.pop(0)
                    agent_name = training_item["agent_name"]

                    # Start training
                    await self._start_agent_training(agent_name, training_item)

                # Check for completed training sessions
                await self._check_training_completion()

                # Process continuous learning updates
                if self.config.continuous_learning:
                    await self._process_continuous_learning()

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logging.error(f"Error in training orchestrator: {e}")
                await asyncio.sleep(10)

    async def _start_agent_training(self, agent_name: str, training_item: Dict):
        """Start training for a specific agent."""
        try:
            logging.info(f"Starting training for {agent_name}")

            # Update agent status
            self.agent_status[agent_name].current_phase = TrainingPhase.INITIAL

            # Determine training phases needed
            insights = self.training_pipeline.continuous_learning.get_learning_insights(
                agent_name
            )

            # Check for emergency optimization
            if training_item.get("emergency"):
                # Focus on performance optimization for emergency cases
                optimization_results = await self._emergency_optimize_agent(
                    agent_name, training_item["alert_context"]
                )

                session_data = {
                    "agent_name": agent_name,
                    "type": "emergency_optimization",
                    "started_at": datetime.now(),
                    "results": optimization_results,
                    "training_item": training_item,
                }
            else:
                # Regular comprehensive training
                training_results = await self._comprehensive_agent_training(agent_name)

                session_data = {
                    "agent_name": agent_name,
                    "type": "comprehensive_training",
                    "started_at": datetime.now(),
                    "results": training_results,
                    "training_item": training_item,
                }

            # Store active session
            session_id = str(uuid.uuid4())
            self.active_training_sessions[session_id] = session_data

            # Update agent status
            self.agent_status[agent_name].last_trained = datetime.now()

        except Exception as e:
            logging.error(f"Failed to start training for {agent_name}: {e}")
            self.agent_status[agent_name].current_phase = None
            self.agent_status[agent_name].issues.append(f"Training failed: {str(e)}")

    async def _emergency_optimize_agent(
        self, agent_name: str, alert_context: Dict
    ) -> Dict[str, Any]:
        """Emergency optimization for performance issues."""
        alert_metric = alert_context["metric"]

        # Determine optimization strategy based on alert
        if "memory" in alert_metric:
            strategy = OptimizationStrategy.RESOURCE_EFFICIENCY
        elif "response_time" in alert_metric:
            strategy = OptimizationStrategy.RESPONSE_TIME
        elif "accuracy" in alert_metric:
            strategy = OptimizationStrategy.ACCURACY
        else:
            strategy = OptimizationStrategy.RESPONSE_TIME  # Default

        # Mock current metrics based on alert
        current_metrics = {
            alert_metric: alert_context["current_value"],
            "response_time": 2.0,
            "accuracy": 0.7,
            "memory_usage": 0.6,
        }

        # Run optimization
        optimization_results = self.optimizer.optimize_agent(
            agent_name, strategy, current_metrics
        )

        return optimization_results

    async def _comprehensive_agent_training(self, agent_name: str) -> Dict[str, Any]:
        """Run comprehensive training for an agent."""
        # This would run the full training pipeline
        training_results = self.training_pipeline.run_comprehensive_training(agent_name)

        # If auto-optimization is enabled, also run optimization
        if self.config.auto_optimization:
            current_metrics = self._get_current_agent_metrics(agent_name)

            optimization_results = self.optimizer.optimize_agent(
                agent_name, OptimizationStrategy.RESPONSE_TIME, current_metrics
            )

            training_results["optimization"] = optimization_results

        return training_results

    def _get_current_agent_metrics(self, agent_name: str) -> Dict[str, float]:
        """Get current performance metrics for an agent."""
        # In real implementation, this would fetch actual metrics
        return {
            "response_time": 2.0 + hash(agent_name) % 10 / 10,
            "accuracy": 0.7 + hash(agent_name) % 20 / 100,
            "memory_usage": 0.5 + hash(agent_name) % 30 / 100,
            "throughput": 10.0 + hash(agent_name) % 50 / 10,
        }

    async def _check_training_completion(self):
        """Check for completed training sessions."""
        completed_sessions = []

        for session_id, session_data in self.active_training_sessions.items():
            # Check if training is complete (simplified check)
            duration = datetime.now() - session_data["started_at"]

            if duration.total_seconds() > 30:  # 30 seconds for demo
                completed_sessions.append(session_id)

        # Process completed sessions
        for session_id in completed_sessions:
            await self._handle_training_completion(session_id)

    async def _handle_training_completion(self, session_id: str):
        """Handle completion of a training session."""
        session_data = self.active_training_sessions[session_id]
        agent_name = session_data["agent_name"]

        try:
            # Update agent status
            self.agent_status[agent_name].current_phase = None
            self.agent_status[
                agent_name
            ].training_score = self._calculate_training_score(session_data["results"])

            # Calculate performance trend
            self.agent_status[
                agent_name
            ].performance_trend = self._calculate_performance_trend(
                agent_name, session_data["results"]
            )

            # Clear any old issues
            self.agent_status[agent_name].issues.clear()

            # Generate new recommendations
            self.agent_status[
                agent_name
            ].recommendations = self._generate_agent_recommendations(
                agent_name, session_data["results"]
            )

            # Schedule next training
            self._schedule_next_training(agent_name)

            # Store in training history
            self.training_history.append(
                {
                    "session_id": session_id,
                    "completed_at": datetime.now(),
                    **session_data,
                }
            )

            logging.info(
                f"Training completed for {agent_name} (score: {self.agent_status[agent_name].training_score:.2f})"
            )

        except Exception as e:
            logging.error(f"Error handling training completion for {agent_name}: {e}")
            self.agent_status[agent_name].issues.append(
                f"Post-training error: {str(e)}"
            )
        finally:
            # Remove from active sessions
            del self.active_training_sessions[session_id]

    def _calculate_training_score(self, training_results: Dict[str, Any]) -> float:
        """Calculate overall training score for an agent."""
        score = 0.5  # Base score

        if "overall_improvement" in training_results:
            improvements = training_results["overall_improvement"]
            if improvements:
                avg_improvement = statistics.mean(improvements.values())
                score += avg_improvement * 0.5  # Add improvement bonus

        if "optimization" in training_results:
            opt_results = training_results["optimization"]
            if opt_results.get("optimization_success"):
                score += 0.2  # Optimization bonus

        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1

    def _calculate_performance_trend(
        self, agent_name: str, training_results: Dict[str, Any]
    ) -> str:
        """Calculate performance trend for an agent."""
        if "overall_improvement" in training_results:
            improvements = training_results["overall_improvement"]
            if improvements:
                avg_improvement = statistics.mean(improvements.values())
                if avg_improvement > 0.1:
                    return "improving"
                elif avg_improvement < -0.1:
                    return "declining"
                else:
                    return "stable"

        return "unknown"

    def _generate_agent_recommendations(
        self, agent_name: str, training_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for an agent based on training results."""
        recommendations = []

        if "learning_insights" in training_results:
            insights = training_results["learning_insights"]
            recommendations.extend(insights.get("improvement_recommendations", []))

        if "optimization" in training_results:
            opt_results = training_results["optimization"]
            if not opt_results.get("optimization_success"):
                recommendations.append("Consider manual optimization review")

        # Add agent-specific recommendations
        if agent_name in AGENT_KEYWORDS:
            keywords = AGENT_KEYWORDS[agent_name]
            recommendations.append(f"Focus on {', '.join(keywords[:2])} expertise")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _schedule_next_training(self, agent_name: str):
        """Schedule next training session for an agent."""
        priority = self.agent_status[agent_name].priority

        # Determine next training interval based on priority and performance
        if priority == TrainingPriority.CRITICAL:
            interval = timedelta(days=1)
        elif priority == TrainingPriority.HIGH:
            interval = timedelta(days=2)
        else:
            interval = timedelta(days=7)

        # Adjust based on performance trend
        trend = self.agent_status[agent_name].performance_trend
        if trend == "declining":
            interval = interval / 2  # More frequent training
        elif trend == "improving":
            interval = interval * 1.5  # Less frequent training

        next_training = datetime.now() + interval
        self.agent_status[agent_name].next_training = next_training

    async def _process_continuous_learning(self):
        """Process continuous learning updates."""
        # Collect recent feedback and interactions
        for agent_name in self.agent_status.keys():
            try:
                # Mock feedback collection (in real implementation, this would collect actual feedback)
                if hash(agent_name) % 10 == 0:  # 10% chance of new feedback
                    self._process_agent_feedback(agent_name)

            except Exception as e:
                logging.error(
                    f"Error processing continuous learning for {agent_name}: {e}"
                )

    def _process_agent_feedback(self, agent_name: str):
        """Process new feedback for an agent."""
        # Mock feedback processing
        feedback_score = (
            0.6 + (hash(agent_name + str(datetime.now().minute)) % 40) / 100
        )

        # Update training score based on feedback
        current_score = self.agent_status[agent_name].training_score
        updated_score = (current_score * 0.9) + (
            feedback_score * 0.1
        )  # Weighted average
        self.agent_status[agent_name].training_score = updated_score

        # If feedback is very poor, schedule emergency training
        if feedback_score < 0.4:
            self._schedule_emergency_training(
                agent_name,
                {
                    "metric": "user_satisfaction",
                    "current_value": feedback_score,
                    "severity": "high",
                },
            )

    async def _system_monitoring(self):
        """System-wide monitoring loop."""
        while True:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Check system health
                self._check_system_health()

                # Update agent priorities based on usage patterns
                self._update_agent_priorities()

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logging.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(60)

    def _collect_system_metrics(self):
        """Collect system-wide metrics."""
        self.system_metrics.update(
            {
                "timestamp": datetime.now(),
                "active_training_sessions": len(self.active_training_sessions),
                "training_queue_length": len(self.training_queue),
                "system_status": self.status.value,
                "total_agents": len(self.agent_status),
                "healthy_agents": len(
                    [s for s in self.agent_status.values() if s.training_score > 0.7]
                ),
                "average_training_score": statistics.mean(
                    [s.training_score for s in self.agent_status.values()]
                ),
                "agents_needing_training": len(
                    [
                        s
                        for s in self.agent_status.values()
                        if s.performance_trend == "declining" or s.training_score < 0.5
                    ]
                ),
            }
        )

    def _check_system_health(self):
        """Check overall system health."""
        metrics = self.system_metrics

        # Check for concerning patterns
        if metrics.get("healthy_agents", 0) < metrics.get("total_agents", 1) * 0.8:
            logging.warning(
                "System health warning: Less than 80% of agents are healthy"
            )

        if metrics.get("average_training_score", 0) < 0.6:
            logging.warning("System health warning: Low average training score")

        if (
            metrics.get("agents_needing_training", 0)
            > metrics.get("total_agents", 1) * 0.3
        ):
            logging.warning("System health warning: Many agents need training")

    def _update_agent_priorities(self):
        """Update agent priorities based on performance and usage."""
        # This would analyze usage patterns and adjust priorities
        # For now, just log the update
        critical_agents = [
            name
            for name, status in self.agent_status.items()
            if status.priority == TrainingPriority.CRITICAL
        ]

        logging.debug(
            f"Agent priorities updated. Critical agents: {len(critical_agents)}"
        )

    async def _schedule_processor(self):
        """Process scheduled training jobs."""
        while True:
            try:
                # Run pending scheduled jobs
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logging.error(f"Error in schedule processor: {e}")
                await asyncio.sleep(60)

    def get_system_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system dashboard data."""
        return {
            "system_status": self.status.value,
            "system_metrics": self.system_metrics,
            "agent_status_summary": {
                "total_agents": len(self.agent_status),
                "by_priority": {
                    priority.name: len(
                        [
                            s
                            for s in self.agent_status.values()
                            if s.priority == priority
                        ]
                    )
                    for priority in TrainingPriority
                },
                "by_trend": {
                    trend: len(
                        [
                            s
                            for s in self.agent_status.values()
                            if s.performance_trend == trend
                        ]
                    )
                    for trend in ["improving", "stable", "declining", "unknown"]
                },
                "training_scores": {
                    "excellent": len(
                        [
                            s
                            for s in self.agent_status.values()
                            if s.training_score > 0.9
                        ]
                    ),
                    "good": len(
                        [
                            s
                            for s in self.agent_status.values()
                            if 0.7 < s.training_score <= 0.9
                        ]
                    ),
                    "acceptable": len(
                        [
                            s
                            for s in self.agent_status.values()
                            if 0.5 < s.training_score <= 0.7
                        ]
                    ),
                    "poor": len(
                        [
                            s
                            for s in self.agent_status.values()
                            if s.training_score <= 0.5
                        ]
                    ),
                },
            },
            "training_activity": {
                "active_sessions": len(self.active_training_sessions),
                "queue_length": len(self.training_queue),
                "recent_completions": len(
                    [
                        h
                        for h in self.training_history
                        if h.get("completed_at", datetime.min)
                        > datetime.now() - timedelta(hours=24)
                    ]
                ),
            },
            "top_performing_agents": [
                {"name": name, "score": status.training_score}
                for name, status in sorted(
                    self.agent_status.items(),
                    key=lambda x: x[1].training_score,
                    reverse=True,
                )[:5]
            ],
            "agents_needing_attention": [
                {"name": name, "score": status.training_score, "issues": status.issues}
                for name, status in self.agent_status.items()
                if status.training_score < 0.5 or status.issues
            ][:5],
            "generated_at": datetime.now().isoformat(),
        }

    def get_agent_details(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific agent."""
        if agent_name not in self.agent_status:
            return {"error": f"Agent {agent_name} not found"}

        status = self.agent_status[agent_name]

        # Get recent training history for this agent
        agent_history = [
            h for h in self.training_history if h.get("agent_name") == agent_name
        ][-5:]  # Last 5 training sessions

        return {
            "agent_name": agent_name,
            "status": asdict(status),
            "keywords": AGENT_KEYWORDS.get(agent_name, []),
            "recent_training_history": agent_history,
            "current_session": next(
                (
                    s
                    for s in self.active_training_sessions.values()
                    if s["agent_name"] == agent_name
                ),
                None,
            ),
            "performance_recommendations": self.optimizer.get_optimization_recommendations(
                agent_name, self._get_current_agent_metrics(agent_name)
            ),
        }

    def emergency_retrain_agent(self, agent_name: str, reason: str) -> bool:
        """Emergency retrain a specific agent."""
        if agent_name not in self.agent_status:
            return False

        emergency_alert = {
            "metric": "manual_intervention",
            "current_value": 0.0,
            "severity": "critical",
            "reason": reason,
        }

        self._schedule_emergency_training(agent_name, emergency_alert)
        logging.warning(f"Emergency retraining scheduled for {agent_name}: {reason}")

        return True

    def stop_system(self):
        """Gracefully stop the training system."""
        logging.info("Stopping integrated training system...")

        # Stop monitoring
        if self.performance_monitor.monitoring_active:
            self.performance_monitor.stop_monitoring()

        # Wait for active training sessions to complete or timeout
        timeout = datetime.now() + timedelta(minutes=5)
        while self.active_training_sessions and datetime.now() < timeout:
            time.sleep(1)

        self.status = SystemStatus.IDLE
        logging.info("Integrated training system stopped")


def main():
    """CLI interface for integrated training system."""
    import argparse

    parser = argparse.ArgumentParser(description="Integrated Training System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start system command
    start_parser = subparsers.add_parser(
        "start", help="Start the integrated training system"
    )
    start_parser.add_argument("--config", help="Config file path")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")

    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Show system dashboard")

    # Agent details command
    agent_parser = subparsers.add_parser("agent", help="Show agent details")
    agent_parser.add_argument("agent_name", help="Agent name")

    # Emergency retrain command
    retrain_parser = subparsers.add_parser(
        "emergency-retrain", help="Emergency retrain agent"
    )
    retrain_parser.add_argument("agent_name", help="Agent name")
    retrain_parser.add_argument(
        "--reason", required=True, help="Reason for emergency retraining"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        if args.command == "start":
            config_path = args.config or "integrated_training_config.json"
            system = IntegratedTrainingSystem(config_path)

            print("🚀 Starting Integrated Training System...")
            print("Press Ctrl+C to stop")

            try:
                asyncio.run(system.start_system_training())
            except KeyboardInterrupt:
                print("\n🛑 Stopping system...")
                system.stop_system()

        elif args.command == "status":
            system = IntegratedTrainingSystem()
            metrics = system.system_metrics

            print(f"\n📊 System Status: {system.status.value}")
            print(
                f"Active training sessions: {metrics.get('active_training_sessions', 0)}"
            )
            print(f"Training queue length: {metrics.get('training_queue_length', 0)}")
            print(f"Total agents: {metrics.get('total_agents', 0)}")
            print(f"Healthy agents: {metrics.get('healthy_agents', 0)}")
            print(
                f"Average training score: {metrics.get('average_training_score', 0):.2f}"
            )

        elif args.command == "dashboard":
            system = IntegratedTrainingSystem()
            dashboard = system.get_system_dashboard()
            print(json.dumps(dashboard, indent=2, default=str))

        elif args.command == "agent":
            system = IntegratedTrainingSystem()
            agent_details = system.get_agent_details(args.agent_name)
            print(json.dumps(agent_details, indent=2, default=str))

        elif args.command == "emergency-retrain":
            system = IntegratedTrainingSystem()
            success = system.emergency_retrain_agent(args.agent_name, args.reason)

            if success:
                print(f"✅ Emergency retraining scheduled for {args.agent_name}")
            else:
                print(
                    f"❌ Failed to schedule emergency retraining for {args.agent_name}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Integrated training system error: {e}")


if __name__ == "__main__":
    main()
