#!/usr/bin/env python3
"""
Business Analytics CLI - Command Line Business Intelligence

Provides business analytics and insights through CLI interface without
web dependencies. Focused on executive reporting and project analytics.

Key Features:
- Executive metrics dashboard in CLI format
- Project health monitoring
- ROI analytics and tracking
- Agent performance with business context
- Predictive insights for project success
"""

import argparse
from datetime import datetime
import sqlite3
import uuid

from analytics_engine import AnalyticsEngine
from business_pm_gateway import BusinessPMGateway, ProjectPlan


class BusinessAnalyticsCLI:
    """CLI-based business analytics and reporting system."""

    def __init__(self, db_path: str = "business_analytics.db"):
        self.db_path = db_path
        self.business_gateway = BusinessPMGateway()
        self.analytics_engine = AnalyticsEngine()
        self._init_database()

    def _init_database(self):
        """Initialize analytics database for storing business metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Projects table for business project tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS business_projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    business_goal TEXT,
                    target_revenue REAL,
                    estimated_cost REAL,
                    actual_cost REAL DEFAULT 0,
                    projected_roi REAL,
                    actual_roi REAL DEFAULT 0,
                    start_date TEXT,
                    target_completion TEXT,
                    actual_completion TEXT,
                    status TEXT DEFAULT 'planning',
                    risk_score REAL,
                    team_size INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Project phases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_phases (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    phase_name TEXT,
                    assigned_agent TEXT,
                    estimated_hours REAL,
                    actual_hours REAL DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    start_date TEXT,
                    completion_date TEXT,
                    business_impact TEXT,
                    FOREIGN KEY (project_id) REFERENCES business_projects (id)
                )
            """)

            # Business metrics tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    target_value REAL,
                    measurement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence_level REAL,
                    FOREIGN KEY (project_id) REFERENCES business_projects (id)
                )
            """)

            conn.commit()

    def store_project_plan(self, project_plan: ProjectPlan) -> str:
        """Store a business project plan in the analytics database."""
        project_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Extract business metrics
            target_revenue = 0
            projected_roi = 0
            if (
                project_plan.roi_projection
                and "revenue_roi" in project_plan.roi_projection
            ):
                roi_data = project_plan.roi_projection["revenue_roi"]
                target_revenue = roi_data.get("projected_annual_revenue", 0)
                projected_roi = roi_data.get("roi_percentage", 0)

            # Store main project
            cursor.execute(
                """
                INSERT INTO business_projects (
                    id, name, business_goal, target_revenue, estimated_cost,
                    projected_roi, start_date, risk_score, team_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    project_id,
                    project_plan.project_name,
                    ", ".join(project_plan.business_context.business_goals)
                    if project_plan.business_context.business_goals
                    else "Not specified",
                    target_revenue,
                    project_plan.estimated_cost,
                    projected_roi,
                    datetime.now().isoformat(),
                    project_plan.risk_assessment.get("risk_score", 0),
                    project_plan.resource_requirements.get("team_size", 1),
                ),
            )

            # Store project phases
            for phase in project_plan.technical_phases:
                phase_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO project_phases (
                        id, project_id, phase_name, assigned_agent, estimated_hours
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        phase_id,
                        project_id,
                        phase["phase"],
                        phase["agent"],
                        phase["duration_hours"],
                    ),
                )

            # Store business metrics if available
            if project_plan.business_context.success_metrics:
                for metric in project_plan.business_context.success_metrics:
                    cursor.execute(
                        """
                        INSERT INTO business_metrics (
                            project_id, metric_name, target_value, confidence_level
                        ) VALUES (?, ?, ?, ?)
                    """,
                        (
                            project_id,
                            metric.metric.value,
                            metric.target_value,
                            metric.confidence_level,
                        ),
                    )

            conn.commit()

        return project_id

    def show_executive_dashboard(self):
        """Display executive-level dashboard."""
        print("🎯 AI Project Manager - Executive Dashboard")
        print("=" * 60)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Overall metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(estimated_cost) as total_investment,
                    SUM(target_revenue) as projected_revenue,
                    AVG(projected_roi) as avg_roi,
                    AVG(risk_score) as avg_risk_score
                FROM business_projects 
                WHERE status != 'cancelled'
            """)
            metrics = cursor.fetchone()

            print("📊 Portfolio Overview:")
            print(f"   Total Projects: {metrics['total_projects']}")
            print(f"   Total Investment: ${(metrics['total_investment'] or 0):,.0f}")
            print(f"   Projected Revenue: ${(metrics['projected_revenue'] or 0):,.0f}")
            print(f"   Average ROI: {(metrics['avg_roi'] or 0):.1f}%")
            print(f"   Average Risk Score: {(metrics['avg_risk_score'] or 0):.2f}")
            print()

            # Project status breakdown
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM business_projects 
                GROUP BY status
            """)
            status_data = cursor.fetchall()

            print("📋 Project Status Breakdown:")
            for row in status_data:
                print(f"   {row['status'].title()}: {row['count']} projects")
            print()

            # Recent projects with performance
            cursor.execute("""
                SELECT 
                    p.name,
                    p.target_revenue,
                    p.estimated_cost,
                    p.projected_roi,
                    p.risk_score,
                    p.status,
                    COUNT(ph.id) as total_phases,
                    SUM(CASE WHEN ph.status = 'completed' THEN 1 ELSE 0 END) as completed_phases
                FROM business_projects p
                LEFT JOIN project_phases ph ON p.id = ph.project_id
                GROUP BY p.id
                ORDER BY p.created_at DESC
                LIMIT 5
            """)
            recent_projects = cursor.fetchall()

            print("🏗️  Recent Projects:")
            for project in recent_projects:
                completion_pct = 0
                if project["total_phases"] > 0:
                    completion_pct = (
                        project["completed_phases"] / project["total_phases"]
                    ) * 100

                print(f"   📁 {project['name']}")
                print(f"      Status: {project['status'].title()}")
                print(
                    f"      Completion: {completion_pct:.0f}% ({project['completed_phases']}/{project['total_phases']} phases)"
                )
                print(f"      Investment: ${(project['estimated_cost'] or 0):,.0f}")
                print(f"      Projected ROI: {(project['projected_roi'] or 0):.1f}%")
                print(f"      Risk Score: {(project['risk_score'] or 0):.2f}")
                print()

    def show_project_health(self):
        """Display project health analytics."""
        print("💊 Project Health Monitor")
        print("=" * 50)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Projects at risk
            cursor.execute("""
                SELECT name, risk_score, status, projected_roi, estimated_cost
                FROM business_projects 
                WHERE risk_score > 0.5 AND status IN ('planning', 'in_progress')
                ORDER BY risk_score DESC
            """)
            high_risk = cursor.fetchall()

            if high_risk:
                print("🚨 High Risk Projects:")
                for project in high_risk:
                    risk_level = (
                        "🔴 Critical" if project["risk_score"] > 0.8 else "⚠️  High Risk"
                    )
                    print(f"   {risk_level}: {project['name']}")
                    print(f"      Risk Score: {project['risk_score']:.2f}")
                    print(f"      Status: {project['status'].title()}")
                    print(
                        f"      Investment at Risk: ${(project['estimated_cost'] or 0):,.0f}"
                    )
                    print()
            else:
                print("✅ No high-risk projects identified")
                print()

            # Timeline analysis
            cursor.execute("""
                SELECT 
                    p.name,
                    COUNT(ph.id) as total_phases,
                    SUM(ph.estimated_hours) as estimated_hours,
                    SUM(ph.actual_hours) as actual_hours,
                    SUM(CASE WHEN ph.status = 'completed' THEN 1 ELSE 0 END) as completed_phases
                FROM business_projects p
                LEFT JOIN project_phases ph ON p.id = ph.project_id
                WHERE p.status = 'in_progress'
                GROUP BY p.id
            """)
            active_projects = cursor.fetchall()

            if active_projects:
                print("📈 Active Project Health:")
                for project in active_projects:
                    if project["total_phases"] > 0:
                        completion_rate = (
                            project["completed_phases"] / project["total_phases"]
                        )

                        # Calculate efficiency
                        efficiency = 1.0
                        if project["actual_hours"] and project["estimated_hours"]:
                            efficiency = min(
                                project["estimated_hours"] / project["actual_hours"],
                                1.0,
                            )

                        # Health score
                        health_score = (completion_rate * 0.6 + efficiency * 0.4) * 100

                        health_status = (
                            "🟢 Excellent"
                            if health_score > 85
                            else "🟡 Good"
                            if health_score > 70
                            else "🟠 Warning"
                            if health_score > 50
                            else "🔴 Critical"
                        )

                        print(f"   {health_status}: {project['name']}")
                        print(f"      Health Score: {health_score:.1f}%")
                        print(
                            f"      Progress: {project['completed_phases']}/{project['total_phases']} phases"
                        )
                        if project["actual_hours"]:
                            print(
                                f"      Hours: {project['actual_hours']:.0f}/{project['estimated_hours']:.0f}"
                            )
                        print()
            else:
                print("📝 No active projects to monitor")

    def show_roi_analysis(self):
        """Display ROI analytics."""
        print("💰 ROI Analysis & Financial Performance")
        print("=" * 60)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ROI projections
            cursor.execute("""
                SELECT 
                    name,
                    estimated_cost,
                    actual_cost,
                    target_revenue,
                    projected_roi,
                    actual_roi,
                    status,
                    risk_score
                FROM business_projects
                WHERE target_revenue > 0
                ORDER BY projected_roi DESC
            """)
            roi_data = cursor.fetchall()

            if roi_data:
                # Portfolio metrics
                total_investment = sum(p["estimated_cost"] or 0 for p in roi_data)
                total_projected_return = sum(p["target_revenue"] or 0 for p in roi_data)

                if total_investment > 0:
                    portfolio_roi = (
                        (total_projected_return - total_investment) / total_investment
                    ) * 100
                else:
                    portfolio_roi = 0

                print("📊 Portfolio Financial Summary:")
                print(f"   Total Investment: ${total_investment:,.0f}")
                print(f"   Projected Returns: ${total_projected_return:,.0f}")
                print(f"   Portfolio ROI: {portfolio_roi:.1f}%")
                print(f"   Number of Projects: {len(roi_data)}")
                print()

                print("💹 Project ROI Ranking:")
                for i, project in enumerate(roi_data[:10], 1):  # Top 10
                    risk_indicator = (
                        "🔴"
                        if project["risk_score"] > 0.7
                        else "🟡"
                        if project["risk_score"] > 0.4
                        else "🟢"
                    )
                    print(f"   {i:2d}. {project['name'][:40]}")
                    print(
                        f"       ROI: {(project['projected_roi'] or 0):.1f}% | Investment: ${(project['estimated_cost'] or 0):,.0f}"
                    )
                    print(
                        f"       Status: {project['status'].title()} | Risk: {risk_indicator} {(project['risk_score'] or 0):.2f}"
                    )
                    print()

                # Risk-adjusted analysis
                print("⚖️  Risk-Adjusted Returns:")
                risk_adjusted = []
                for project in roi_data:
                    if project["projected_roi"] and project["risk_score"]:
                        adjusted_roi = project["projected_roi"] * (
                            1 - project["risk_score"]
                        )
                        risk_adjusted.append(
                            {
                                "name": project["name"],
                                "original_roi": project["projected_roi"],
                                "risk_score": project["risk_score"],
                                "adjusted_roi": adjusted_roi,
                                "investment": project["estimated_cost"],
                            }
                        )

                risk_adjusted.sort(key=lambda x: x["adjusted_roi"], reverse=True)

                for i, project in enumerate(risk_adjusted[:5], 1):
                    print(f"   {i}. {project['name'][:40]}")
                    print(
                        f"      Original ROI: {project['original_roi']:.1f}% → Risk-Adjusted: {project['adjusted_roi']:.1f}%"
                    )
                    print(
                        f"      Risk Impact: -{(project['original_roi'] - project['adjusted_roi']):.1f}%"
                    )
                    print()

            else:
                print("📈 No financial data available yet")
                print("💡 Create projects with revenue targets to see ROI analysis")

    def create_sample_data(self):
        """Create sample data for demonstration."""
        print("📝 Creating sample business data...")

        # Sample project plans
        sample_projects = [
            {
                "title": "B2B Marketplace Platform",
                "description": "Business Goal: $2M ARR, Mid-market B2B procurement, React/Node.js, 6 months timeline",
            },
            {
                "title": "AI Analytics Dashboard",
                "description": "Business Goal: $500K revenue, 5K users, Real-time analytics, 4 months timeline",
            },
            {
                "title": "Mobile Customer Portal",
                "description": "Business Goal: $300K savings, 15K users, React Native, 3 months timeline",
            },
        ]

        for project in sample_projects:
            try:
                plan = self.business_gateway.create_business_project_plan(
                    project["title"], project["description"]
                )
                project_id = self.store_project_plan(plan)
                print(f"   ✅ Created: {project['title']} (ID: {project_id[:8]}...)")
            except Exception as e:
                print(f"   ❌ Failed to create {project['title']}: {e}")

        print("🎉 Sample data created successfully!")
        print("💡 Use other commands to explore the analytics")


def main():
    """CLI interface for business analytics."""
    parser = argparse.ArgumentParser(
        description="Business Analytics CLI - AI Project Manager Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s dashboard           # Show executive dashboard
  %(prog)s health             # Show project health monitor  
  %(prog)s roi                # Show ROI analysis
  %(prog)s create-sample      # Create sample data for demo
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Show executive-level business dashboard"
    )

    # Health command
    health_parser = subparsers.add_parser(
        "health", help="Show project health analytics"
    )

    # ROI command
    roi_parser = subparsers.add_parser(
        "roi", help="Show ROI analysis and financial performance"
    )

    # Sample data command
    sample_parser = subparsers.add_parser(
        "create-sample", help="Create sample data for demonstration"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        analytics_cli = BusinessAnalyticsCLI()

        if args.command == "dashboard":
            analytics_cli.show_executive_dashboard()
        elif args.command == "health":
            analytics_cli.show_project_health()
        elif args.command == "roi":
            analytics_cli.show_roi_analysis()
        elif args.command == "create-sample":
            analytics_cli.create_sample_data()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
