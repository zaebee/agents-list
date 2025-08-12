#!/usr/bin/env python3
"""
Business-Driven PM Agent Gateway - AI Project Manager Core Experience

Enhanced PM Gateway that translates business goals into comprehensive project plans,
providing intelligent orchestration with business context awareness.

Key Features:
- Business goal to technical task translation
- ROI and business metric tracking
- Comprehensive project roadmap generation
- Business risk assessment
- Executive-level project planning
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pm_agent_gateway import (
    PMAgentGateway,
    TaskComplexity,
)


class ProjectScale(Enum):
    """Project scale based on business impact."""

    FEATURE = 1  # Single feature or small enhancement
    INITIATIVE = 2  # Multi-feature project with business goals
    STRATEGIC = 3  # Large strategic project affecting business direction
    TRANSFORMATION = 4  # Company-wide transformation initiative


class BusinessMetric(Enum):
    """Business metrics for project tracking."""

    REVENUE = "revenue"
    ARR = "arr"  # Annual Recurring Revenue
    MRR = "mrr"  # Monthly Recurring Revenue
    USERS = "users"
    CONVERSION = "conversion_rate"
    RETENTION = "retention_rate"
    COST_SAVINGS = "cost_savings"
    TIME_TO_MARKET = "time_to_market"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    MARKET_SHARE = "market_share"


@dataclass
class BusinessObjective:
    """Business objective with measurable goals."""

    metric: BusinessMetric
    target_value: float
    current_value: Optional[float] = None
    timeline_months: int = 12
    confidence_level: float = 0.8  # 0-1 scale


@dataclass
class BusinessContext:
    """Business context for project planning."""

    business_goals: List[str]
    target_market: Optional[str] = None
    competitive_landscape: List[str] = None
    budget_range: Optional[Tuple[int, int]] = None  # (min, max) in USD
    timeline_constraints: Optional[str] = None
    success_metrics: List[BusinessObjective] = None
    stakeholders: List[str] = None
    compliance_requirements: List[str] = None


@dataclass
class ProjectPlan:
    """Comprehensive project plan with business alignment."""

    project_name: str
    business_context: BusinessContext
    technical_phases: List[Dict]
    total_estimated_hours: float
    estimated_cost: Optional[float] = None
    roi_projection: Optional[Dict] = None
    risk_assessment: Dict = None
    success_criteria: List[str] = None
    milestones: List[Dict] = None
    resource_requirements: Dict = None


class BusinessPMGateway(PMAgentGateway):
    """Enhanced PM Gateway with business intelligence and strategic planning."""

    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path)

        # Business-to-technical mapping patterns
        self.business_patterns = {
            "marketplace": {
                "keywords": ["marketplace", "b2b", "b2c", "platform", "multi-sided"],
                "essential_features": [
                    "user_management",
                    "payment_processing",
                    "search",
                    "messaging",
                    "reviews",
                ],
                "typical_timeline": 6,  # months
                "complexity": ProjectScale.STRATEGIC,
            },
            "saas_product": {
                "keywords": ["saas", "subscription", "cloud", "software-as-a-service"],
                "essential_features": [
                    "authentication",
                    "billing",
                    "analytics",
                    "api",
                    "integrations",
                ],
                "typical_timeline": 4,
                "complexity": ProjectScale.INITIATIVE,
            },
            "mobile_app": {
                "keywords": [
                    "mobile",
                    "app",
                    "ios",
                    "android",
                    "react native",
                    "flutter",
                ],
                "essential_features": [
                    "ui_design",
                    "authentication",
                    "offline_sync",
                    "push_notifications",
                ],
                "typical_timeline": 3,
                "complexity": ProjectScale.INITIATIVE,
            },
            "analytics_platform": {
                "keywords": [
                    "analytics",
                    "dashboard",
                    "reporting",
                    "metrics",
                    "insights",
                ],
                "essential_features": [
                    "data_collection",
                    "visualization",
                    "reporting",
                    "real_time",
                ],
                "typical_timeline": 4,
                "complexity": ProjectScale.INITIATIVE,
            },
            "ai_integration": {
                "keywords": [
                    "ai",
                    "ml",
                    "machine learning",
                    "llm",
                    "artificial intelligence",
                ],
                "essential_features": [
                    "model_integration",
                    "training",
                    "inference",
                    "monitoring",
                ],
                "typical_timeline": 5,
                "complexity": ProjectScale.STRATEGIC,
            },
        }

        # Business metric targets and effort estimation
        self.metric_patterns = {
            BusinessMetric.REVENUE: {"typical_effort_months": 6, "risk_factor": 1.2},
            BusinessMetric.ARR: {"typical_effort_months": 8, "risk_factor": 1.3},
            BusinessMetric.USERS: {"typical_effort_months": 4, "risk_factor": 1.1},
            BusinessMetric.CONVERSION: {"typical_effort_months": 3, "risk_factor": 1.0},
            BusinessMetric.RETENTION: {"typical_effort_months": 5, "risk_factor": 1.1},
        }

        # Enhanced workflow templates for business projects
        self.business_workflows = {
            "marketplace_launch": [
                {
                    "phase": "Market Research & Strategy",
                    "agent": "business-analyst",
                    "duration_hours": 40,
                },
                {
                    "phase": "Technical Architecture",
                    "agent": "backend-architect",
                    "duration_hours": 32,
                },
                {
                    "phase": "User Experience Design",
                    "agent": "ui-ux-designer",
                    "duration_hours": 48,
                },
                {
                    "phase": "Core Platform Development",
                    "agent": "backend-architect",
                    "duration_hours": 160,
                },
                {
                    "phase": "Frontend Development",
                    "agent": "frontend-developer",
                    "duration_hours": 120,
                },
                {
                    "phase": "Payment Integration",
                    "agent": "payment-integration",
                    "duration_hours": 40,
                },
                {
                    "phase": "Security Implementation",
                    "agent": "security-auditor",
                    "duration_hours": 32,
                },
                {
                    "phase": "Testing & QA",
                    "agent": "test-automator",
                    "duration_hours": 48,
                },
                {
                    "phase": "Deployment & Launch",
                    "agent": "deployment-engineer",
                    "duration_hours": 24,
                },
                {
                    "phase": "Analytics & Monitoring",
                    "agent": "business-analyst",
                    "duration_hours": 16,
                },
            ],
            "saas_product_development": [
                {
                    "phase": "Product Strategy",
                    "agent": "business-analyst",
                    "duration_hours": 24,
                },
                {
                    "phase": "Technical Planning",
                    "agent": "backend-architect",
                    "duration_hours": 16,
                },
                {
                    "phase": "MVP Development",
                    "agent": "frontend-developer",
                    "duration_hours": 80,
                },
                {
                    "phase": "Authentication & Security",
                    "agent": "security-auditor",
                    "duration_hours": 24,
                },
                {
                    "phase": "Billing Integration",
                    "agent": "payment-integration",
                    "duration_hours": 32,
                },
                {
                    "phase": "Analytics Implementation",
                    "agent": "data-engineer",
                    "duration_hours": 24,
                },
                {
                    "phase": "Testing & Validation",
                    "agent": "test-automator",
                    "duration_hours": 32,
                },
                {
                    "phase": "Launch & Marketing",
                    "agent": "content-marketer",
                    "duration_hours": 16,
                },
            ],
        }

    def parse_business_context(self, description: str) -> BusinessContext:
        """Extract business context from project description."""
        text = description.lower()

        # Extract business goals
        business_goals = []
        goal_patterns = [
            r"(\$\d+[kmb]?(?:\.\d+)?)\s*(?:arr|revenue|sales)",
            r"(\d+(?:,\d{3})*)\s*(?:users|customers|subscribers)",
            r"(\d+)%\s*(?:conversion|retention|growth)",
            r"(\d+)\s*months?\s*(?:timeline|launch|delivery)",
        ]

        for pattern in goal_patterns:
            matches = re.findall(pattern, text)
            business_goals.extend(matches)

        # Extract target market
        market_indicators = [
            "b2b",
            "b2c",
            "enterprise",
            "small business",
            "startup",
            "consumer",
        ]
        target_market = None
        for indicator in market_indicators:
            if indicator in text:
                target_market = indicator
                break

        # Extract competitive information
        competitive_keywords = [
            "competitor",
            "alternative",
            "market leader",
            "disruption",
        ]
        competitive_landscape = []
        for keyword in competitive_keywords:
            if keyword in text:
                competitive_landscape.append(f"Consider {keyword} analysis")

        # Extract compliance requirements
        compliance_keywords = [
            "gdpr",
            "hipaa",
            "soc2",
            "pci",
            "compliance",
            "regulation",
        ]
        compliance_requirements = []
        for keyword in compliance_keywords:
            if keyword in text:
                compliance_requirements.append(keyword.upper())

        # Parse success metrics
        success_metrics = []
        if "revenue" in text or "$" in text:
            revenue_match = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*([kmb]?)", text)
            if revenue_match:
                value = float(revenue_match.group(1).replace(",", ""))
                multiplier = {"k": 1000, "m": 1000000, "b": 1000000000}.get(
                    revenue_match.group(2).lower(), 1
                )
                success_metrics.append(
                    BusinessObjective(
                        metric=BusinessMetric.REVENUE,
                        target_value=value * multiplier,
                        timeline_months=12,
                    )
                )

        return BusinessContext(
            business_goals=business_goals,
            target_market=target_market,
            competitive_landscape=competitive_landscape,
            compliance_requirements=compliance_requirements,
            success_metrics=success_metrics,
        )

    def identify_project_type(
        self, title: str, description: str
    ) -> Tuple[str, ProjectScale]:
        """Identify project type and scale from description."""
        text = f"{title} {description}".lower()

        # Match against business patterns
        for project_type, pattern in self.business_patterns.items():
            if any(keyword in text for keyword in pattern["keywords"]):
                return project_type, pattern["complexity"]

        # Fallback to complexity-based scale
        complexity = super().analyze_task(title, description).complexity
        scale_map = {
            TaskComplexity.SIMPLE: ProjectScale.FEATURE,
            TaskComplexity.MODERATE: ProjectScale.FEATURE,
            TaskComplexity.COMPLEX: ProjectScale.INITIATIVE,
            TaskComplexity.EPIC: ProjectScale.STRATEGIC,
        }

        return "custom_project", scale_map[complexity]

    def generate_project_phases(
        self, project_type: str, business_context: BusinessContext
    ) -> List[Dict]:
        """Generate comprehensive project phases based on type and business context."""

        # Get base workflow
        if project_type in ["marketplace", "marketplace_launch"]:
            base_workflow = self.business_workflows["marketplace_launch"]
        elif project_type in ["saas", "saas_product"]:
            base_workflow = self.business_workflows["saas_product_development"]
        else:
            # Create custom workflow based on business context
            base_workflow = [
                {
                    "phase": "Business Analysis & Planning",
                    "agent": "business-analyst",
                    "duration_hours": 24,
                },
                {
                    "phase": "Technical Architecture",
                    "agent": "backend-architect",
                    "duration_hours": 32,
                },
                {
                    "phase": "Implementation",
                    "agent": "frontend-developer",
                    "duration_hours": 80,
                },
                {
                    "phase": "Testing & Quality Assurance",
                    "agent": "test-automator",
                    "duration_hours": 32,
                },
                {
                    "phase": "Deployment & Launch",
                    "agent": "deployment-engineer",
                    "duration_hours": 16,
                },
            ]

        # Enhance workflow based on business context
        enhanced_phases = []
        for phase in base_workflow:
            enhanced_phase = phase.copy()

            # Add compliance phases if needed
            if (
                business_context.compliance_requirements
                and "security" in phase["phase"].lower()
            ):
                enhanced_phase["duration_hours"] *= 1.5  # Extra time for compliance
                enhanced_phase["compliance_focus"] = (
                    business_context.compliance_requirements
                )

            # Add business metric tracking
            if (
                business_context.success_metrics
                and "analytics" in phase["phase"].lower()
            ):
                enhanced_phase["business_tracking"] = [
                    metric.metric.value for metric in business_context.success_metrics
                ]

            enhanced_phases.append(enhanced_phase)

        # Add business-specific phases
        if business_context.competitive_landscape:
            enhanced_phases.insert(
                1,
                {
                    "phase": "Competitive Analysis",
                    "agent": "business-analyst",
                    "duration_hours": 16,
                    "focus": "Market positioning and differentiation",
                },
            )

        return enhanced_phases

    def calculate_roi_projection(
        self, business_context: BusinessContext, total_cost: float
    ) -> Dict:
        """Calculate ROI projection based on business metrics."""
        if not business_context.success_metrics:
            return {"message": "No business metrics provided for ROI calculation"}

        projections = {}

        for metric in business_context.success_metrics:
            if metric.metric == BusinessMetric.REVENUE:
                # Simple ROI calculation
                annual_revenue = metric.target_value
                roi_ratio = (
                    (annual_revenue - total_cost) / total_cost if total_cost > 0 else 0
                )
                projections["revenue_roi"] = {
                    "investment": total_cost,
                    "projected_annual_revenue": annual_revenue,
                    "roi_percentage": roi_ratio * 100,
                    "payback_months": (total_cost / (annual_revenue / 12))
                    if annual_revenue > 0
                    else 0,
                    "confidence": metric.confidence_level,
                }

            elif metric.metric == BusinessMetric.ARR:
                monthly_arr = metric.target_value / 12
                payback_months = (total_cost / monthly_arr) if monthly_arr > 0 else 0
                projections["arr_roi"] = {
                    "investment": total_cost,
                    "projected_arr": metric.target_value,
                    "monthly_arr": monthly_arr,
                    "payback_months": payback_months,
                    "confidence": metric.confidence_level,
                }

        return projections

    def assess_business_risks(
        self, business_context: BusinessContext, project_type: str
    ) -> Dict:
        """Comprehensive business risk assessment."""
        risks = {
            "market_risks": [],
            "technical_risks": [],
            "financial_risks": [],
            "operational_risks": [],
            "risk_score": 0.0,  # 0-1 scale
        }

        # Market risks
        if business_context.competitive_landscape:
            risks["market_risks"].append("Competitive market with established players")

        if business_context.target_market == "enterprise":
            risks["market_risks"].append("Enterprise sales cycles can be lengthy")
            risks["operational_risks"].append("Enterprise compliance requirements")

        # Technical risks based on project type
        technical_risk_map = {
            "marketplace": [
                "Two-sided market dynamics",
                "Scalability challenges",
                "Payment processing complexity",
            ],
            "saas_product": [
                "Multi-tenancy complexity",
                "Data security requirements",
                "Integration challenges",
            ],
            "ai_integration": [
                "Model accuracy uncertainties",
                "Data quality dependencies",
                "Regulatory compliance",
            ],
        }

        if project_type in technical_risk_map:
            risks["technical_risks"].extend(technical_risk_map[project_type])

        # Financial risks
        if business_context.success_metrics:
            for metric in business_context.success_metrics:
                if metric.confidence_level < 0.7:
                    risks["financial_risks"].append(
                        f"Low confidence in {metric.metric.value} projections"
                    )

        # Calculate overall risk score
        risk_factors = (
            len(risks["market_risks"])
            + len(risks["technical_risks"])
            + len(risks["financial_risks"])
        )
        risks["risk_score"] = min(risk_factors * 0.1, 1.0)

        return risks

    def create_business_project_plan(self, title: str, description: str) -> ProjectPlan:
        """Create comprehensive business-driven project plan."""

        print(f"🎯 AI Project Manager analyzing business goal: '{title}'")
        print("=" * 60)

        # Parse business context
        business_context = self.parse_business_context(description)
        print("📊 Business Context Identified:")
        print(f"   Target Market: {business_context.target_market or 'Not specified'}")
        print(f"   Business Goals: {len(business_context.business_goals)} identified")
        if business_context.compliance_requirements:
            print(
                f"   Compliance: {', '.join(business_context.compliance_requirements)}"
            )

        # Identify project type and scale
        project_type, project_scale = self.identify_project_type(title, description)
        print(f"   Project Type: {project_type.replace('_', ' ').title()}")
        print(f"   Project Scale: {project_scale.name}")

        # Generate comprehensive project phases
        technical_phases = self.generate_project_phases(project_type, business_context)
        total_hours = sum(phase["duration_hours"] for phase in technical_phases)

        print("\n🔄 Project Roadmap Generated:")
        print(f"   Total Phases: {len(technical_phases)}")
        print(
            f"   Estimated Effort: {total_hours} hours ({total_hours / 40:.1f} person-weeks)"
        )

        # Calculate costs (assuming $150/hour blended rate)
        estimated_cost = total_hours * 150

        # Business risk assessment
        risk_assessment = self.assess_business_risks(business_context, project_type)

        # ROI projection
        roi_projection = self.calculate_roi_projection(business_context, estimated_cost)

        # Generate milestones
        milestones = []
        cumulative_hours = 0
        for i, phase in enumerate(technical_phases):
            cumulative_hours += phase["duration_hours"]
            milestone_week = int(cumulative_hours / 40)
            milestones.append(
                {
                    "name": f"Phase {i + 1} Complete: {phase['phase']}",
                    "week": milestone_week,
                    "deliverables": [f"{phase['phase']} deliverable"],
                    "success_criteria": f"{phase['phase']} meets quality standards",
                }
            )

        # Create comprehensive project plan
        project_plan = ProjectPlan(
            project_name=title,
            business_context=business_context,
            technical_phases=technical_phases,
            total_estimated_hours=total_hours,
            estimated_cost=estimated_cost,
            roi_projection=roi_projection,
            risk_assessment=risk_assessment,
            success_criteria=[
                "All technical phases completed successfully",
                "Business metrics targets achieved",
                "Quality standards met",
                "Project delivered on time and budget",
            ],
            milestones=milestones,
            resource_requirements={
                "team_size": max(
                    2, len(set(phase["agent"] for phase in technical_phases))
                ),
                "timeline_weeks": int(total_hours / 40),
                "budget_range": (int(estimated_cost * 0.8), int(estimated_cost * 1.2)),
            },
        )

        # Display comprehensive analysis
        self._display_project_analysis(project_plan)

        return project_plan

    def _display_project_analysis(self, plan: ProjectPlan):
        """Display comprehensive project analysis."""
        print("\n📋 Comprehensive Project Analysis:")
        print("   📊 Financial Overview:")
        print(f"      Estimated Cost: ${plan.estimated_cost:,.0f}")
        print(
            f"      Budget Range: ${plan.resource_requirements['budget_range'][0]:,.0f} - ${plan.resource_requirements['budget_range'][1]:,.0f}"
        )

        if plan.roi_projection and "revenue_roi" in plan.roi_projection:
            roi = plan.roi_projection["revenue_roi"]
            print(f"      Projected ROI: {roi['roi_percentage']:.0f}%")
            print(f"      Payback Period: {roi['payback_months']:.1f} months")

        print("\n   ⚠️  Risk Assessment:")
        print(f"      Overall Risk Score: {plan.risk_assessment['risk_score']:.1f}/1.0")
        if plan.risk_assessment["market_risks"]:
            print(
                f"      Market Risks: {len(plan.risk_assessment['market_risks'])} identified"
            )
        if plan.risk_assessment["technical_risks"]:
            print(
                f"      Technical Risks: {len(plan.risk_assessment['technical_risks'])} identified"
            )

        print("\n   🎯 Key Milestones:")
        for milestone in plan.milestones[:3]:  # Show first 3 milestones
            print(f"      Week {milestone['week']}: {milestone['name']}")

        print("\n   👥 Resource Requirements:")
        print(f"      Team Size: {plan.resource_requirements['team_size']} specialists")
        print(f"      Timeline: {plan.resource_requirements['timeline_weeks']} weeks")

        print("\n💡 AI Project Manager Recommendation:")
        if plan.risk_assessment["risk_score"] < 0.3:
            print("   ✅ Low risk project - proceed with confidence")
        elif plan.risk_assessment["risk_score"] < 0.6:
            print("   ⚠️  Moderate risk - implement risk mitigation strategies")
        else:
            print(
                "   🚨 High risk project - consider phased approach or risk reduction"
            )


def main():
    """CLI interface for Business PM Gateway."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Business PM Gateway - AI Project Manager for Business Goals"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Business plan command
    plan_parser = subparsers.add_parser(
        "plan", help="Create comprehensive business project plan"
    )
    plan_parser.add_argument(
        "--title", required=True, help="Business goal or project title"
    )
    plan_parser.add_argument(
        "--description",
        required=True,
        help="Detailed business description with goals and context",
    )

    # Quick analysis command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Quick business goal analysis"
    )
    analyze_parser.add_argument("--goal", required=True, help="Business goal statement")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        gateway = BusinessPMGateway()

        if args.command == "plan":
            project_plan = gateway.create_business_project_plan(
                args.title, args.description
            )
            print("\n🎯 Project plan generated successfully!")
            print("📄 Full project details available in generated plan object")

        elif args.command == "analyze":
            # Quick analysis using existing analyze_task method
            analysis = gateway.analyze_task(args.goal, "")
            print("\n🎯 Quick Business Analysis:")
            print(f"   Complexity: {analysis.complexity.name}")
            print(f"   Estimated Effort: {analysis.estimated_hours} hours")
            print(f"   Recommended Agents: {', '.join(analysis.required_agents[:3])}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
