import json
from datetime import datetime
from typing import Dict, List


class AnalyticsEngine:
    """
    Comprehensive analytics engine for AI-CRM system
    Handles metrics collection, processing, and reporting
    """

    def __init__(self, config_path: str = "config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)

        self.metrics = {
            "task_completion": {},
            "agent_performance": {},
            "user_engagement": {},
            "workflow_efficiency": {},
            "cross_platform_insights": {},
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
        completed_tasks = len([task for task in tasks if task["status"] == "completed"])

        completion_rate = (
            (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        )

        avg_task_duration = (
            sum(task["duration"] for task in tasks) / total_tasks
            if total_tasks > 0
            else 0
        )

        self.metrics["task_completion"] = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "avg_task_duration": avg_task_duration,
            "timestamp": datetime.now().isoformat(),
        }

        return self.metrics["task_completion"]

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
            agent_name = log["agent_name"]
            if agent_name not in agent_metrics:
                agent_metrics[agent_name] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "success_rate": 0,
                    "avg_response_time": 0,
                }

            agent_metrics[agent_name]["total_tasks"] += 1
            if log["status"] == "completed":
                agent_metrics[agent_name]["completed_tasks"] += 1

        for agent, metrics in agent_metrics.items():
            metrics["success_rate"] = (
                (metrics["completed_tasks"] / metrics["total_tasks"]) * 100
                if metrics["total_tasks"] > 0
                else 0
            )

        self.metrics["agent_performance"] = agent_metrics
        return self.metrics["agent_performance"]

    def generate_executive_dashboard(self) -> Dict:
        """
        Generate high-level executive dashboard

        Returns:
            Dict: Executive-level business metrics
        """
        executive_dashboard = {
            "system_overview": {
                "total_agents": len(self.config.get("agents", [])),
                "active_integrations": len(self.config.get("integrations", [])),
                "system_health": self._calculate_system_health(),
            },
            "performance_kpis": {
                "task_completion_rate": self.metrics["task_completion"].get(
                    "completion_rate", 0
                ),
                "top_performing_agents": self._get_top_performing_agents(),
                "workflow_efficiency": self._calculate_workflow_efficiency(),
            },
            "business_insights": {
                "trending_tasks": self._identify_trending_tasks(),
                "potential_optimizations": self._recommend_optimizations(),
            },
            "timestamp": datetime.now().isoformat(),
        }

        return executive_dashboard

    def _calculate_system_health(self) -> float:
        """Internal method to calculate overall system health"""
        # Placeholder implementation
        return 85.5  # percentage

    def _get_top_performing_agents(self, top_n: int = 5) -> List[Dict]:
        """Get top N performing agents"""
        performance_data = self.metrics["agent_performance"]
        return sorted(
            [{"agent": k, **v} for k, v in performance_data.items()],
            key=lambda x: x["success_rate"],
            reverse=True,
        )[:top_n]

    def _calculate_workflow_efficiency(self) -> float:
        """Calculate overall workflow efficiency"""
        # Placeholder implementation
        return 78.5  # percentage

    def _identify_trending_tasks(self) -> List[Dict]:
        """Identify most frequent or critical tasks"""
        # Placeholder implementation
        return [
            {"task_type": "Customer Onboarding", "frequency": 42},
            {"task_type": "Support Ticket Resolution", "frequency": 35},
        ]

    def _recommend_optimizations(self) -> List[str]:
        """Generate optimization recommendations"""
        # Placeholder implementation
        return [
            "Reduce agent context switching time",
            "Optimize high-complexity task routing",
            "Enhance cross-platform integration efficiency",
        ]

    def track_business_metric(
        self, project_id: str, metric_name: str, value: float, target: float
    ) -> Dict:
        """Track business metrics for projects."""
        metric_data = {
            "project_id": project_id,
            "metric_name": metric_name,
            "current_value": value,
            "target_value": target,
            "achievement_percentage": (value / target * 100) if target > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "status": "on_track" if value >= target * 0.8 else "at_risk",
        }

        # In a real implementation, this would store to database
        self.metrics.setdefault("business_tracking", []).append(metric_data)

        return metric_data

    def calculate_project_health_score(self, project_data: Dict) -> Dict:
        """Calculate comprehensive project health score."""
        health_factors = {
            "timeline": 0.3,
            "budget": 0.25,
            "quality": 0.2,
            "team_performance": 0.15,
            "stakeholder_satisfaction": 0.1,
        }

        scores = {}

        # Timeline score (completion rate vs time elapsed)
        if project_data.get("phases_completed") and project_data.get("total_phases"):
            completion_rate = (
                project_data["phases_completed"] / project_data["total_phases"]
            )
            # Simplified timeline score
            scores["timeline"] = min(completion_rate * 100, 100)
        else:
            scores["timeline"] = 50

        # Budget score (actual vs estimated)
        if project_data.get("actual_cost") and project_data.get("estimated_cost"):
            budget_efficiency = (
                project_data["estimated_cost"] / project_data["actual_cost"]
            )
            scores["budget"] = min(budget_efficiency * 100, 100)
        else:
            scores["budget"] = 75

        # Default scores for other factors
        scores["quality"] = project_data.get("quality_score", 80)
        scores["team_performance"] = project_data.get("team_performance", 75)
        scores["stakeholder_satisfaction"] = project_data.get(
            "stakeholder_satisfaction", 80
        )

        # Calculate weighted health score
        health_score = sum(
            scores[factor] * weight for factor, weight in health_factors.items()
        )

        return {
            "overall_health_score": round(health_score, 1),
            "factor_scores": scores,
            "health_status": "excellent"
            if health_score > 85
            else "good"
            if health_score > 70
            else "warning"
            if health_score > 50
            else "critical",
            "recommendations": self._generate_health_recommendations(scores),
        }

    def _generate_health_recommendations(self, scores: Dict) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []

        if scores["timeline"] < 70:
            recommendations.append(
                "Consider task prioritization and resource reallocation"
            )
        if scores["budget"] < 70:
            recommendations.append(
                "Review budget allocation and cost optimization opportunities"
            )
        if scores["quality"] < 70:
            recommendations.append("Implement additional quality assurance measures")
        if scores["team_performance"] < 70:
            recommendations.append(
                "Provide additional support and training for team members"
            )
        if scores["stakeholder_satisfaction"] < 70:
            recommendations.append("Increase stakeholder communication and engagement")

        return recommendations

    def generate_predictive_insights(self, project_data: Dict) -> Dict:
        """Generate predictive insights for project success."""
        # Simplified predictive model
        risk_factors = []
        success_probability = 0.8  # Base probability

        # Analyze risk factors
        if project_data.get("risk_score", 0) > 0.6:
            risk_factors.append("High technical risk identified")
            success_probability *= 0.8

        if project_data.get("team_size", 0) < 2:
            risk_factors.append("Small team size may impact delivery")
            success_probability *= 0.9

        if project_data.get("timeline_weeks", 0) > 26:
            risk_factors.append("Extended timeline increases uncertainty")
            success_probability *= 0.85

        # Generate recommendations
        recommendations = []
        if success_probability < 0.7:
            recommendations.append("Consider phased delivery approach")
            recommendations.append("Implement additional risk mitigation strategies")
        if success_probability < 0.5:
            recommendations.append("Recommend project scope reduction")

        return {
            "success_probability": round(success_probability * 100, 1),
            "confidence_level": "high"
            if success_probability > 0.8
            else "medium"
            if success_probability > 0.6
            else "low",
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "key_metrics_to_monitor": [
                "timeline_adherence",
                "budget_utilization",
                "quality_metrics",
            ],
        }


def initialize_analytics(config_path: str = "config.json") -> AnalyticsEngine:
    """
    Initialize and configure the analytics engine

    Args:
        config_path (str): Path to configuration file

    Returns:
        AnalyticsEngine: Configured analytics engine
    """
    return AnalyticsEngine(config_path)
