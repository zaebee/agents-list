#!/usr/bin/env python3
"""
Backlog Analyzer - Intelligent analysis and prioritization of CRM tasks.

This module analyzes the current AI-CRM backlog and provides strategic recommendations
for task prioritization, resource allocation, and implementation roadmap.
"""

from dataclasses import dataclass
from enum import Enum

from pm_agent_gateway import PMAgentGateway


class BusinessValue(Enum):
    """Business value assessment levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ImplementationEffort(Enum):
    """Implementation effort levels."""

    TRIVIAL = 1  # < 1 day
    EASY = 2  # 1-3 days
    MODERATE = 3  # 1 week
    COMPLEX = 4  # 2+ weeks


@dataclass
class BacklogTask:
    """Backlog task with analysis metadata."""

    title: str
    description: str
    current_owner: str
    status: str
    business_value: BusinessValue
    effort: ImplementationEffort
    priority_score: float
    dependencies: list[str]
    strategic_impact: str


class BacklogAnalyzer:
    """Intelligent backlog analysis and prioritization system."""

    def __init__(self):
        """Initialize the backlog analyzer."""
        self.pm_gateway = PMAgentGateway()

        # Current AI-CRM backlog (from the actual CRM system)
        self.current_backlog = [
            {
                "title": "Brainstorming: Monetization and ROI strategies for AI-CRM",
                "description": "Develop comprehensive business model and revenue strategies",
                "owner": "business-analyst",
                "status": "To Do",
            },
            {
                "title": "DOCS: Create and Save Onboarding Prompt for AI Teammates",
                "description": "Documentation for team member onboarding and agent collaboration",
                "owner": "business-analyst",
                "status": "To Do",
            },
            {
                "title": "Simple Deployment Strategy",
                "description": "Create straightforward deployment approach for the AI-CRM system",
                "owner": "deployment-engineer",
                "status": "To Do",
            },
            {
                "title": "Develop a Minimal Web UI",
                "description": "Build basic web interface for non-CLI users",
                "owner": "frontend-developer",
                "status": "To Do",
            },
            {
                "title": "Feature Implementation: AI Owner Sticker",
                "description": "Complete the AI owner sticker functionality enhancement",
                "owner": "business-analyst",
                "status": "To Do",
            },
            {
                "title": "Jules's Work: AI-CRM Scoping and Implementation",
                "description": "Project scoping and implementation planning",
                "owner": "business-analyst",
                "status": "To Do",
            },
            {
                "title": "Implement PM Agent as Gateway",
                "description": "Complete PM agent orchestration system",
                "owner": "ai-engineer",
                "status": "In Progress",
            },
        ]

        # Business value assessment criteria
        self.value_criteria = {
            "revenue_impact": {"monetization": 4, "deployment": 3, "ui": 2, "docs": 1},
            "user_experience": {"ui": 4, "deployment": 3, "pm_agent": 3, "docs": 2},
            "scalability": {"deployment": 4, "pm_agent": 4, "ui": 2, "monetization": 1},
            "competitive_advantage": {
                "pm_agent": 4,
                "monetization": 3,
                "ui": 2,
                "docs": 1,
            },
        }

    def analyze_task(self, task: dict) -> BacklogTask:
        """Analyze a single backlog task comprehensively."""

        # Use PM Gateway for technical analysis
        pm_analysis = self.pm_gateway.create_managed_task(
            task["title"], task["description"]
        )

        # Assess business value
        business_value = self._assess_business_value(task)

        # Estimate implementation effort
        effort = self._estimate_effort(pm_analysis, task)

        # Calculate priority score (business value / effort ratio)
        priority_score = business_value.value / effort.value

        # Identify dependencies
        dependencies = self._identify_dependencies(task)

        # Assess strategic impact
        strategic_impact = self._assess_strategic_impact(task)

        return BacklogTask(
            title=task["title"],
            description=task["description"],
            current_owner=task["owner"],
            status=task["status"],
            business_value=business_value,
            effort=effort,
            priority_score=priority_score,
            dependencies=dependencies,
            strategic_impact=strategic_impact,
        )

    def _assess_business_value(self, task: dict) -> BusinessValue:
        """Assess business value based on impact categories."""
        title_lower = task["title"].lower()
        description_lower = task["description"].lower()

        value_score = 0

        # Revenue impact
        if "monetization" in title_lower or "revenue" in title_lower:
            value_score += 4
        elif "deployment" in title_lower:
            value_score += 3
        elif "ui" in title_lower or "web" in title_lower:
            value_score += 2

        # User experience impact
        if "ui" in title_lower or "interface" in title_lower:
            value_score += 3
        elif "deployment" in title_lower or "pm agent" in title_lower:
            value_score += 2

        # Strategic importance
        if "pm agent" in title_lower or "gateway" in title_lower:
            value_score += 4  # Core differentiator
        elif "monetization" in title_lower:
            value_score += 3  # Business critical

        # Map score to enum
        if value_score >= 8:
            return BusinessValue.CRITICAL
        elif value_score >= 6:
            return BusinessValue.HIGH
        elif value_score >= 3:
            return BusinessValue.MEDIUM
        else:
            return BusinessValue.LOW

    def _estimate_effort(self, pm_analysis: dict, task: dict) -> ImplementationEffort:
        """Estimate implementation effort."""
        if pm_analysis["type"] == "complex_task":
            estimated_hours = pm_analysis["analysis"]["estimated_hours"]
        else:
            estimated_hours = pm_analysis["analysis"]["estimated_hours"]

        # Convert hours to effort enum
        if estimated_hours >= 80:  # 2+ weeks
            return ImplementationEffort.COMPLEX
        elif estimated_hours >= 40:  # 1 week
            return ImplementationEffort.MODERATE
        elif estimated_hours >= 16:  # 1-3 days
            return ImplementationEffort.EASY
        else:
            return ImplementationEffort.TRIVIAL

    def _identify_dependencies(self, task: dict) -> list[str]:
        """Identify task dependencies."""
        title_lower = task["title"].lower()
        dependencies = []

        if "deployment" in title_lower:
            dependencies.append("Basic functionality must be complete")
        elif "ui" in title_lower or "web" in title_lower:
            dependencies.append("API endpoints must be stable")
        elif "monetization" in title_lower:
            dependencies.append("Core product features completed")

        return dependencies

    def _assess_strategic_impact(self, task: dict) -> str:
        """Assess strategic impact and positioning."""
        title_lower = task["title"].lower()

        if "pm agent" in title_lower or "gateway" in title_lower:
            return "Core differentiator - enables intelligent task orchestration"
        elif "monetization" in title_lower:
            return "Business foundation - required for sustainable growth"
        elif "deployment" in title_lower:
            return "Market access - enables user adoption and scaling"
        elif "ui" in title_lower or "web" in title_lower:
            return "User experience - broadens market appeal beyond CLI users"
        elif "docs" in title_lower or "onboarding" in title_lower:
            return "Team efficiency - improves development velocity"
        else:
            return "Feature enhancement - improves existing capabilities"

    def analyze_full_backlog(self) -> list[BacklogTask]:
        """Analyze entire backlog and return prioritized list."""
        analyzed_tasks = []

        print("🔍 Analyzing current AI-CRM backlog...")
        print("=" * 50)

        for task in self.current_backlog:
            print(f"📋 Analyzing: {task['title']}")
            analyzed_task = self.analyze_task(task)
            analyzed_tasks.append(analyzed_task)

        # Sort by priority score (descending)
        analyzed_tasks.sort(key=lambda x: x.priority_score, reverse=True)

        return analyzed_tasks

    def generate_implementation_roadmap(
        self, analyzed_tasks: list[BacklogTask]
    ) -> dict:
        """Generate strategic implementation roadmap."""

        # Phase 1: Foundation (High value, low effort)
        phase1 = [
            task
            for task in analyzed_tasks
            if task.business_value.value >= 3 and task.effort.value <= 2
        ]

        # Phase 2: Core Features (High value, moderate effort)
        phase2 = [
            task
            for task in analyzed_tasks
            if task.business_value.value >= 3 and task.effort.value == 3
        ]

        # Phase 3: Complex Features (Any value, high effort)
        phase3 = [task for task in analyzed_tasks if task.effort.value >= 4]

        # Phase 4: Polish (Low-medium value, any effort)
        phase4 = [
            task
            for task in analyzed_tasks
            if task.business_value.value <= 2 and task not in phase1 + phase2 + phase3
        ]

        return {
            "phase1_foundation": phase1,
            "phase2_core": phase2,
            "phase3_complex": phase3,
            "phase4_polish": phase4,
            "estimated_timeline": {
                "phase1": "1-2 weeks",
                "phase2": "2-3 weeks",
                "phase3": "4-6 weeks",
                "phase4": "1-2 weeks",
            },
        }

    def print_analysis_report(self):
        """Print comprehensive backlog analysis report."""
        analyzed_tasks = self.analyze_full_backlog()
        roadmap = self.generate_implementation_roadmap(analyzed_tasks)

        print("\n" + "=" * 60)
        print("📊 AI-CRM BACKLOG ANALYSIS REPORT")
        print("=" * 60)

        print(f"\n🎯 PRIORITIZED BACKLOG ({len(analyzed_tasks)} tasks):")
        print("-" * 40)

        for i, task in enumerate(analyzed_tasks, 1):
            print(f"{i}. {task.title}")
            print(f"   👤 Owner: {task.current_owner}")
            print(
                f"   💰 Value: {task.business_value.name} | ⚡ Effort: {task.effort.name}"
            )
            print(f"   📊 Priority Score: {task.priority_score:.2f}")
            print(f"   🎯 Impact: {task.strategic_impact}")
            if task.dependencies:
                print(f"   🔗 Dependencies: {', '.join(task.dependencies)}")
            print()

        print("📅 IMPLEMENTATION ROADMAP:")
        print("-" * 40)

        for phase, tasks in roadmap.items():
            if phase.startswith("phase") and tasks:
                phase_num = phase.split("_")[0].replace("phase", "Phase ")
                phase_name = phase.split("_")[1].title()
                timeline = roadmap["estimated_timeline"][phase.split("_")[0]]

                print(f"\n{phase_num} - {phase_name} ({timeline}):")
                for task in tasks:
                    print(f"  • {task.title} ({task.current_owner})")

        # Strategic recommendations
        print("\n💡 STRATEGIC RECOMMENDATIONS:")
        print("-" * 40)

        critical_tasks = [
            t for t in analyzed_tasks if t.business_value == BusinessValue.CRITICAL
        ]
        if critical_tasks:
            print("🚨 IMMEDIATE FOCUS:")
            for task in critical_tasks[:2]:
                print(f"  • {task.title} - {task.strategic_impact}")

        quick_wins = [
            t for t in analyzed_tasks if t.priority_score > 2 and t.effort.value <= 2
        ]
        if quick_wins:
            print("\n⚡ QUICK WINS:")
            for task in quick_wins[:3]:
                print(f"  • {task.title} (Score: {task.priority_score:.1f})")

        print("\n🎯 RECOMMENDED NEXT ACTIONS:")
        print("1. Complete PM Agent Gateway (already in progress)")
        print("2. Focus on deployment strategy for market access")
        print("3. Build minimal web UI for broader user base")
        print("4. Develop monetization strategy while building")


def main():
    """CLI interface for backlog analysis."""
    analyzer = BacklogAnalyzer()
    analyzer.print_analysis_report()


if __name__ == "__main__":
    main()
