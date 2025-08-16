#!/usr/bin/env python3
"""
Pricing Models and Billing Infrastructure for AI-CRM System

This module implements the tiered pricing structure based on our monetization strategy:
- Free Tier: 9 Haiku agents, 10 tasks/month
- Pro Tier: $49/user/month, 37 Sonnet agents, unlimited tasks
- Enterprise Tier: $199-$499/user/month, all 59 agents + custom features
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class SubscriptionTier(Enum):
    """Subscription tier definitions."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AgentModelType(Enum):
    """Agent model types with different capabilities and costs."""

    HAIKU = "haiku"  # Fast, lightweight for simple tasks
    SONNET = "sonnet"  # Balanced performance and capability
    OPUS = "opus"  # Most capable for complex tasks


@dataclass
class PricingPlan:
    """Pricing plan definition."""

    tier: SubscriptionTier
    name: str
    price_per_month: float
    price_per_year: float  # Usually with discount
    max_tasks_per_month: int | None  # None = unlimited
    available_agents: dict[AgentModelType, int]
    features: list[str]
    target_audience: str
    support_level: str


@dataclass
class UsageMetrics:
    """Track user usage for billing and limits."""

    user_id: str
    subscription_tier: SubscriptionTier
    current_period_start: datetime
    current_period_end: datetime
    tasks_used_this_month: int
    total_tokens_used: int
    cost_breakdown: dict[str, float]
    agent_usage: dict[str, int]


class PricingManager:
    """Manages pricing plans, billing, and usage tracking."""

    def __init__(self):
        self.pricing_plans = self._initialize_pricing_plans()
        self.agent_configurations = self._initialize_agent_configurations()

    def _initialize_pricing_plans(self) -> dict[SubscriptionTier, PricingPlan]:
        """Initialize the three-tier pricing structure."""
        return {
            SubscriptionTier.FREE: PricingPlan(
                tier=SubscriptionTier.FREE,
                name="Free Tier",
                price_per_month=0.0,
                price_per_year=0.0,
                max_tasks_per_month=10,
                available_agents={
                    AgentModelType.HAIKU: 9,
                    AgentModelType.SONNET: 0,
                    AgentModelType.OPUS: 0,
                },
                features=[
                    "Access to 9 Haiku-powered agents",
                    "Basic task creation and management",
                    "Limited to 10 tasks per month",
                    "Community support",
                    "Basic analytics dashboard",
                ],
                target_audience="Individual developers, small teams, evaluation",
                support_level="community",
            ),
            SubscriptionTier.PRO: PricingPlan(
                tier=SubscriptionTier.PRO,
                name="Pro Tier",
                price_per_month=49.0,
                price_per_year=490.0,  # 2 months free
                max_tasks_per_month=None,  # Unlimited
                available_agents={
                    AgentModelType.HAIKU: 9,
                    AgentModelType.SONNET: 37,
                    AgentModelType.OPUS: 0,
                },
                features=[
                    "Full access to 46 agents (9 Haiku + 37 Sonnet)",
                    "Unlimited task creation",
                    "Advanced agent matching and routing",
                    "Priority email support",
                    "API access and webhooks",
                    "Advanced analytics and reporting",
                    "Task automation workflows",
                    "Integration with popular tools",
                ],
                target_audience="Startups, SMBs, development teams",
                support_level="email",
            ),
            SubscriptionTier.ENTERPRISE: PricingPlan(
                tier=SubscriptionTier.ENTERPRISE,
                name="Enterprise Tier",
                price_per_month=299.0,  # Starting price, custom pricing available
                price_per_year=2990.0,  # 2 months free
                max_tasks_per_month=None,  # Unlimited
                available_agents={
                    AgentModelType.HAIKU: 9,
                    AgentModelType.SONNET: 37,
                    AgentModelType.OPUS: 13,
                },
                features=[
                    "Full access to all 59 agents (including 13 Opus-powered)",
                    "Custom agent training and development",
                    "Dedicated customer success manager",
                    "Advanced security features and compliance",
                    "On-premise deployment options",
                    "Single Sign-On (SSO) integration",
                    "Custom integrations and API limits",
                    "24/7 phone and priority support",
                    "Service level agreement (SLA)",
                    "Advanced admin and user management",
                    "White-label options available",
                ],
                target_audience="Large enterprises, regulated industries",
                support_level="dedicated",
            ),
        }

    def _initialize_agent_configurations(self) -> dict[str, dict]:
        """Initialize agent configurations by tier and capability."""
        return {
            "free_tier_agents": [
                # 9 Haiku-powered agents for basic tasks
                "data-scientist",
                "business-analyst",
                "frontend-developer",
                "debugger",
                "test-automator",
                "content-marketer",
                "customer-support",
                "documentation-linter",
                "tutorial-engineer",
            ],
            "pro_tier_agents": [
                # Additional 37 Sonnet-powered agents
                "backend-architect",
                "security-auditor",
                "devops-troubleshooter",
                "performance-engineer",
                "code-reviewer",
                "api-documenter",
                "database-optimizer",
                "cloud-architect",
                "legacy-modernizer",
                "search-specialist",
                "error-detective",
                "mermaid-expert",
                "reference-builder",
                "architect-reviewer",
                "project-scaffolder",
                "test-generator",
                "python-pro",
                "javascript-pro",
                "golang-pro",
                "rust-pro",
                "cpp-pro",
                "java-pro",
                "csharp-pro",
                "typescript-pro",
                "php-pro",
                "scala-pro",
                "elixir-pro",
                "sql-pro",
                "network-engineer",
                "c-pro",
                "mobile-developer",
                "unity-developer",
                "ios-developer",
                "deployment-engineer",
                "terraform-specialist",
                "database-admin",
                "payment-integration",
                "graphql-architect",
            ],
            "enterprise_tier_agents": [
                # Additional 13 Opus-powered agents for complex tasks
                "ai-engineer",
                "ml-engineer",
                "mlops-engineer",
                "data-engineer",
                "quant-analyst",
                "risk-manager",
                "legal-advisor",
                "docs-architect",
                "context-manager",
                "incident-responder",
                "dx-optimizer",
                "sales-automator",
                "prompt-engineer",
            ],
        }

    def get_pricing_plan(self, tier: SubscriptionTier) -> PricingPlan:
        """Get pricing plan for a specific tier."""
        return self.pricing_plans[tier]

    def get_all_pricing_plans(self) -> list[PricingPlan]:
        """Get all available pricing plans."""
        return list(self.pricing_plans.values())

    def calculate_monthly_cost(self, tier: SubscriptionTier, users: int = 1) -> float:
        """Calculate monthly cost for given tier and user count."""
        plan = self.pricing_plans[tier]
        return plan.price_per_month * users

    def calculate_annual_savings(self, tier: SubscriptionTier, users: int = 1) -> float:
        """Calculate savings when paying annually."""
        plan = self.pricing_plans[tier]
        monthly_cost = plan.price_per_month * users * 12
        annual_cost = plan.price_per_year * users
        return monthly_cost - annual_cost

    def check_usage_limits(self, usage: UsageMetrics) -> dict[str, Any]:
        """Check if user is within their subscription limits."""
        plan = self.pricing_plans[usage.subscription_tier]

        result = {
            "within_limits": True,
            "warnings": [],
            "limits_exceeded": [],
            "current_usage": {
                "tasks_this_month": usage.tasks_used_this_month,
                "tasks_limit": plan.max_tasks_per_month,
            },
        }

        # Check task limits
        if plan.max_tasks_per_month is not None:
            if usage.tasks_used_this_month >= plan.max_tasks_per_month:
                result["within_limits"] = False
                result["limits_exceeded"].append(
                    {
                        "type": "monthly_tasks",
                        "current": usage.tasks_used_this_month,
                        "limit": plan.max_tasks_per_month,
                    }
                )
            elif usage.tasks_used_this_month >= plan.max_tasks_per_month * 0.8:
                result["warnings"].append(
                    {
                        "type": "approaching_task_limit",
                        "current": usage.tasks_used_this_month,
                        "limit": plan.max_tasks_per_month,
                        "percentage_used": (
                            usage.tasks_used_this_month / plan.max_tasks_per_month
                        )
                        * 100,
                    }
                )

        return result

    def get_available_agents(self, tier: SubscriptionTier) -> list[str]:
        """Get list of agents available for a subscription tier."""
        available_agents = []

        # Add Haiku agents for all tiers
        if self.pricing_plans[tier].available_agents[AgentModelType.HAIKU] > 0:
            available_agents.extend(self.agent_configurations["free_tier_agents"])

        # Add Sonnet agents for Pro and Enterprise
        if tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
            if self.pricing_plans[tier].available_agents[AgentModelType.SONNET] > 0:
                available_agents.extend(self.agent_configurations["pro_tier_agents"])

        # Add Opus agents for Enterprise only
        if tier == SubscriptionTier.ENTERPRISE:
            if self.pricing_plans[tier].available_agents[AgentModelType.OPUS] > 0:
                available_agents.extend(
                    self.agent_configurations["enterprise_tier_agents"]
                )

        return available_agents

    def get_upgrade_recommendations(self, usage: UsageMetrics) -> list[dict[str, Any]]:
        """Suggest upgrades based on usage patterns."""
        recommendations = []
        current_plan = self.pricing_plans[usage.subscription_tier]

        # Check if user is hitting limits frequently
        if (
            current_plan.max_tasks_per_month is not None
            and usage.tasks_used_this_month >= current_plan.max_tasks_per_month * 0.9
        ):
            if usage.subscription_tier == SubscriptionTier.FREE:
                recommendations.append(
                    {
                        "type": "tier_upgrade",
                        "from_tier": SubscriptionTier.FREE,
                        "to_tier": SubscriptionTier.PRO,
                        "reason": "Task limit approaching",
                        "benefits": [
                            "Unlimited tasks per month",
                            "Access to 37 additional Sonnet-powered agents",
                            "API access and advanced features",
                        ],
                        "cost_increase": self.pricing_plans[
                            SubscriptionTier.PRO
                        ].price_per_month,
                    }
                )

        # Analyze agent usage patterns for Pro users
        if usage.subscription_tier == SubscriptionTier.PRO:
            complex_task_indicators = [
                "ai-engineering",
                "ml-ops",
                "quantitative-analysis",
            ]
            if any(
                indicator in str(usage.agent_usage)
                for indicator in complex_task_indicators
            ):
                recommendations.append(
                    {
                        "type": "tier_upgrade",
                        "from_tier": SubscriptionTier.PRO,
                        "to_tier": SubscriptionTier.ENTERPRISE,
                        "reason": "Complex task requirements detected",
                        "benefits": [
                            "Access to 13 Opus-powered agents",
                            "Custom agent training",
                            "Dedicated support",
                        ],
                        "cost_increase": self.pricing_plans[
                            SubscriptionTier.ENTERPRISE
                        ].price_per_month
                        - self.pricing_plans[SubscriptionTier.PRO].price_per_month,
                    }
                )

        return recommendations

    def generate_billing_summary(self, usage: UsageMetrics) -> dict[str, Any]:
        """Generate billing summary for a user."""
        plan = self.pricing_plans[usage.subscription_tier]

        return {
            "user_id": usage.user_id,
            "subscription_tier": usage.subscription_tier.value,
            "plan_name": plan.name,
            "billing_period": {
                "start": usage.current_period_start.isoformat(),
                "end": usage.current_period_end.isoformat(),
            },
            "costs": {
                "base_subscription": plan.price_per_month,
                "additional_usage": sum(usage.cost_breakdown.values()),
                "total": plan.price_per_month + sum(usage.cost_breakdown.values()),
            },
            "usage_summary": {
                "tasks_completed": usage.tasks_used_this_month,
                "tasks_limit": plan.max_tasks_per_month,
                "tokens_consumed": usage.total_tokens_used,
                "most_used_agents": sorted(
                    usage.agent_usage.items(), key=lambda x: x[1], reverse=True
                )[:5],
            },
            "available_features": plan.features,
            "support_level": plan.support_level,
        }


# Global pricing manager instance
pricing_manager = PricingManager()


def get_pricing_for_api() -> dict[str, Any]:
    """Get pricing information formatted for API responses."""
    plans = pricing_manager.get_all_pricing_plans()

    return {
        "pricing_plans": [
            {
                "tier": plan.tier.value,
                "name": plan.name,
                "pricing": {
                    "monthly": plan.price_per_month,
                    "annual": plan.price_per_year,
                    "annual_savings": pricing_manager.calculate_annual_savings(
                        plan.tier
                    ),
                },
                "limits": {
                    "max_tasks_per_month": plan.max_tasks_per_month,
                    "total_agents": sum(plan.available_agents.values()),
                },
                "agent_breakdown": {
                    "haiku_agents": plan.available_agents[AgentModelType.HAIKU],
                    "sonnet_agents": plan.available_agents[AgentModelType.SONNET],
                    "opus_agents": plan.available_agents[AgentModelType.OPUS],
                },
                "features": plan.features,
                "target_audience": plan.target_audience,
                "support_level": plan.support_level,
            }
            for plan in plans
        ],
        "currency": "USD",
        "billing_cycles": ["monthly", "annual"],
        "free_trial": {"available": True, "duration_days": 14, "tier": "pro"},
    }


if __name__ == "__main__":
    # Demo the pricing system
    pm = PricingManager()

    print("🏷️ AI-CRM Pricing Plans")
    print("=" * 50)

    for plan in pm.get_all_pricing_plans():
        print(f"\n{plan.name} ({plan.tier.value.upper()})")
        print(f"💰 Price: ${plan.price_per_month}/month")
        if plan.price_per_year > 0:
            savings = pm.calculate_annual_savings(plan.tier)
            print(f"💰 Annual: ${plan.price_per_year}/year (Save ${savings})")

        print(f"🤖 Agents: {sum(plan.available_agents.values())} total")
        for model_type, count in plan.available_agents.items():
            if count > 0:
                print(f"   - {count} {model_type.value.capitalize()} agents")

        if plan.max_tasks_per_month:
            print(f"📋 Tasks: {plan.max_tasks_per_month}/month")
        else:
            print("📋 Tasks: Unlimited")

        print(f"🎯 Target: {plan.target_audience}")
        print(f"🛟 Support: {plan.support_level}")

    # Demo usage check
    print("\n🔍 Usage Example")
    print("=" * 30)

    sample_usage = UsageMetrics(
        user_id="user_123",
        subscription_tier=SubscriptionTier.FREE,
        current_period_start=datetime.now(),
        current_period_end=datetime.now() + timedelta(days=30),
        tasks_used_this_month=8,
        total_tokens_used=50000,
        cost_breakdown={"base": 0.0},
        agent_usage={"data-scientist": 5, "business-analyst": 3},
    )

    limits_check = pm.check_usage_limits(sample_usage)
    print(f"Within limits: {limits_check['within_limits']}")
    print(f"Warnings: {len(limits_check['warnings'])}")

    recommendations = pm.get_upgrade_recommendations(sample_usage)
    if recommendations:
        print("\n💡 Upgrade recommendations:")
        for rec in recommendations:
            print(f"   - Upgrade to {rec['to_tier'].value}: {rec['reason']}")
