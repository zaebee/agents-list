#!/usr/bin/env python3
"""
Business Intelligence Dashboard - Real-time Analytics for AI Project Manager

Enhanced dashboard providing business insights, project analytics, and real-time
monitoring for PM-driven projects with executive-level reporting.

Key Features:
- Executive metrics dashboard with KPI tracking
- Real-time project health monitoring
- Agent performance analytics with business impact
- Predictive project success indicators
- ROI tracking and financial analytics
- Risk assessment visualization
"""

from datetime import datetime
import sqlite3
from typing import Any
import uuid

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

from analytics_engine import AnalyticsEngine
from business_pm_gateway import BusinessPMGateway, ProjectPlan
from crm_service import CRMService


class BusinessIntelligenceDashboard:
    """Enhanced analytics dashboard with business intelligence capabilities."""

    def __init__(self, db_path: str = "business_analytics.db"):
        self.db_path = db_path
        self.business_gateway = BusinessPMGateway()
        self.crm_service = CRMService()
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

            # Agent performance with business context
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_business_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT,
                    project_id TEXT,
                    phase_id TEXT,
                    task_completed BOOLEAN,
                    business_value_delivered REAL,
                    time_to_completion REAL,
                    quality_score REAL,
                    stakeholder_satisfaction REAL,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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

    def get_executive_dashboard(self) -> dict[str, Any]:
        """Generate executive-level dashboard data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Overall business metrics
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
            overall_metrics = dict(cursor.fetchone())

            # Project status breakdown
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM business_projects 
                GROUP BY status
            """)
            project_status = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Top performing agents by business value
            cursor.execute("""
                SELECT 
                    agent_name,
                    COUNT(*) as tasks_completed,
                    AVG(business_value_delivered) as avg_business_value,
                    AVG(quality_score) as avg_quality,
                    AVG(stakeholder_satisfaction) as avg_satisfaction
                FROM agent_business_performance 
                WHERE task_completed = 1
                GROUP BY agent_name
                ORDER BY avg_business_value DESC
                LIMIT 5
            """)
            top_agents = [dict(row) for row in cursor.fetchall()]

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
                LIMIT 10
            """)
            recent_projects = [dict(row) for row in cursor.fetchall()]

            # Calculate completion percentages
            for project in recent_projects:
                if project["total_phases"] > 0:
                    project["completion_percentage"] = (
                        project["completed_phases"] / project["total_phases"]
                    ) * 100
                else:
                    project["completion_percentage"] = 0

        return {
            "overall_metrics": overall_metrics,
            "project_status_breakdown": project_status,
            "top_performing_agents": top_agents,
            "recent_projects": recent_projects,
            "generated_at": datetime.now().isoformat(),
        }

    def get_project_health_analytics(self) -> dict[str, Any]:
        """Get real-time project health analytics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Projects at risk
            cursor.execute("""
                SELECT name, risk_score, status, projected_roi, estimated_cost
                FROM business_projects 
                WHERE risk_score > 0.6 AND status IN ('planning', 'in_progress')
                ORDER BY risk_score DESC
            """)
            high_risk_projects = [dict(row) for row in cursor.fetchall()]

            # Timeline analysis
            cursor.execute("""
                SELECT 
                    p.name,
                    p.target_completion,
                    COUNT(ph.id) as total_phases,
                    SUM(ph.estimated_hours) as estimated_hours,
                    SUM(ph.actual_hours) as actual_hours,
                    SUM(CASE WHEN ph.status = 'completed' THEN 1 ELSE 0 END) as completed_phases
                FROM business_projects p
                LEFT JOIN project_phases ph ON p.id = ph.project_id
                WHERE p.status = 'in_progress'
                GROUP BY p.id
            """)
            timeline_analysis = [dict(row) for row in cursor.fetchall()]

            # Calculate health scores
            for project in timeline_analysis:
                if project["total_phases"] > 0:
                    completion_rate = (
                        project["completed_phases"] / project["total_phases"]
                    )

                    # Simple health score calculation
                    if project["actual_hours"] and project["estimated_hours"]:
                        efficiency = min(
                            project["estimated_hours"] / project["actual_hours"], 1.0
                        )
                    else:
                        efficiency = 1.0

                    project["health_score"] = (
                        completion_rate * 0.6 + efficiency * 0.4
                    ) * 100
                else:
                    project["health_score"] = 0

            # Budget analysis
            cursor.execute("""
                SELECT 
                    SUM(estimated_cost) as total_budget,
                    SUM(actual_cost) as total_spent,
                    COUNT(*) as active_projects
                FROM business_projects 
                WHERE status IN ('planning', 'in_progress')
            """)
            budget_data = dict(cursor.fetchone())

            if budget_data["total_budget"]:
                budget_data["budget_utilization"] = (
                    budget_data["total_spent"] / budget_data["total_budget"]
                ) * 100
            else:
                budget_data["budget_utilization"] = 0

        return {
            "high_risk_projects": high_risk_projects,
            "timeline_analysis": timeline_analysis,
            "budget_analysis": budget_data,
            "health_summary": {
                "projects_on_track": len(
                    [p for p in timeline_analysis if p["health_score"] > 70]
                ),
                "projects_at_risk": len(
                    [p for p in timeline_analysis if p["health_score"] < 50]
                ),
                "average_health_score": sum(
                    p["health_score"] for p in timeline_analysis
                )
                / len(timeline_analysis)
                if timeline_analysis
                else 0,
            },
        }

    def get_roi_analytics(self) -> dict[str, Any]:
        """Calculate and return ROI analytics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ROI projections vs actuals
            cursor.execute("""
                SELECT 
                    name,
                    estimated_cost,
                    actual_cost,
                    target_revenue,
                    projected_roi,
                    actual_roi,
                    status
                FROM business_projects
                WHERE target_revenue > 0
                ORDER BY projected_roi DESC
            """)
            roi_analysis = [dict(row) for row in cursor.fetchall()]

            # Portfolio performance
            total_investment = sum(p["estimated_cost"] or 0 for p in roi_analysis)
            total_projected_return = sum(p["target_revenue"] or 0 for p in roi_analysis)
            portfolio_roi = (
                ((total_projected_return - total_investment) / total_investment * 100)
                if total_investment > 0
                else 0
            )

            # Risk-adjusted returns
            cursor.execute("""
                SELECT 
                    projected_roi,
                    risk_score,
                    estimated_cost
                FROM business_projects
                WHERE projected_roi > 0 AND risk_score > 0
            """)
            risk_return_data = [dict(row) for row in cursor.fetchall()]

            risk_adjusted_returns = []
            for project in risk_return_data:
                risk_adjusted_roi = project["projected_roi"] * (
                    1 - project["risk_score"]
                )
                risk_adjusted_returns.append(
                    {
                        "original_roi": project["projected_roi"],
                        "risk_score": project["risk_score"],
                        "risk_adjusted_roi": risk_adjusted_roi,
                        "investment": project["estimated_cost"],
                    }
                )

        return {
            "project_roi_analysis": roi_analysis,
            "portfolio_metrics": {
                "total_investment": total_investment,
                "projected_returns": total_projected_return,
                "portfolio_roi": portfolio_roi,
                "project_count": len(roi_analysis),
            },
            "risk_adjusted_analysis": risk_adjusted_returns,
        }


def create_dashboard_app():
    """Create Flask app for business intelligence dashboard."""
    app = Flask(__name__)
    CORS(app)

    dashboard = BusinessIntelligenceDashboard()

    # HTML template for dashboard
    DASHBOARD_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Project Manager - Business Intelligence Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .metric-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2.5em; font-weight: bold; color: #667eea; margin: 10px 0; }
            .metric-label { color: #666; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
            .chart-container { background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .project-list { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .project-item { padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
            .project-item:last-child { border-bottom: none; }
            .status-badge { padding: 5px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; }
            .status-planning { background: #fff3cd; color: #856404; }
            .status-in-progress { background: #d4edda; color: #155724; }
            .status-completed { background: #d1ecf1; color: #0c5460; }
            .health-score { font-weight: bold; }
            .health-good { color: #28a745; }
            .health-warning { color: #ffc107; }
            .health-danger { color: #dc3545; }
            .refresh-btn { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 AI Project Manager</h1>
            <p>Business Intelligence Dashboard</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
        </div>
        
        <div class="metrics-grid" id="executive-metrics">
            <!-- Executive metrics will be populated here -->
        </div>
        
        <div class="chart-container">
            <h3>Project Portfolio Overview</h3>
            <canvas id="portfolioChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>ROI Analysis</h3>
            <canvas id="roiChart" width="400" height="200"></canvas>
        </div>
        
        <div class="project-list" id="project-health">
            <!-- Project health data will be populated here -->
        </div>
        
        <script>
            // Load dashboard data
            async function loadDashboard() {
                try {
                    const [execResponse, healthResponse, roiResponse] = await Promise.all([
                        fetch('/api/executive-dashboard'),
                        fetch('/api/project-health'),
                        fetch('/api/roi-analytics')
                    ]);
                    
                    const execData = await execResponse.json();
                    const healthData = await healthResponse.json();
                    const roiData = await roiResponse.json();
                    
                    updateExecutiveMetrics(execData);
                    updatePortfolioChart(execData);
                    updateROIChart(roiData);
                    updateProjectHealth(healthData);
                    
                } catch (error) {
                    console.error('Error loading dashboard:', error);
                }
            }
            
            function updateExecutiveMetrics(data) {
                const metrics = data.overall_metrics;
                const container = document.getElementById('executive-metrics');
                
                container.innerHTML = `
                    <div class="metric-card">
                        <div class="metric-label">Total Projects</div>
                        <div class="metric-value">${metrics.total_projects || 0}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Investment</div>
                        <div class="metric-value">$${Math.round((metrics.total_investment || 0) / 1000)}K</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Projected Revenue</div>
                        <div class="metric-value">$${Math.round((metrics.projected_revenue || 0) / 1000)}K</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Average ROI</div>
                        <div class="metric-value">${Math.round(metrics.avg_roi || 0)}%</div>
                    </div>
                `;
            }
            
            function updatePortfolioChart(data) {
                const ctx = document.getElementById('portfolioChart').getContext('2d');
                const statusData = data.project_status_breakdown;
                
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(statusData),
                        datasets: [{
                            data: Object.values(statusData),
                            backgroundColor: ['#667eea', '#28a745', '#ffc107', '#dc3545']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            }
            
            function updateROIChart(data) {
                const ctx = document.getElementById('roiChart').getContext('2d');
                const projects = data.project_roi_analysis.slice(0, 10);
                
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: projects.map(p => p.name.substring(0, 20) + '...'),
                        datasets: [{
                            label: 'Projected ROI %',
                            data: projects.map(p => p.projected_roi),
                            backgroundColor: '#667eea'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            }
            
            function updateProjectHealth(data) {
                const container = document.getElementById('project-health');
                const projects = data.timeline_analysis;
                
                let html = '<div style="padding: 20px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;"><h3>Project Health Monitor</h3></div>';
                
                projects.forEach(project => {
                    const healthClass = project.health_score > 70 ? 'health-good' : 
                                      project.health_score > 50 ? 'health-warning' : 'health-danger';
                    
                    html += `
                        <div class="project-item">
                            <div>
                                <strong>${project.name}</strong>
                                <div style="font-size: 0.9em; color: #666;">
                                    ${project.completed_phases}/${project.total_phases} phases completed
                                </div>
                            </div>
                            <div class="health-score ${healthClass}">
                                ${Math.round(project.health_score)}% Health
                            </div>
                        </div>
                    `;
                });
                
                container.innerHTML = html;
            }
            
            // Load dashboard on page load
            loadDashboard();
            
            // Auto-refresh every 5 minutes
            setInterval(loadDashboard, 300000);
        </script>
    </body>
    </html>
    """

    @app.route("/")
    def dashboard_home():
        """Main dashboard page."""
        return render_template_string(DASHBOARD_TEMPLATE)

    @app.route("/api/executive-dashboard")
    def get_executive_dashboard():
        """Get executive dashboard data."""
        return jsonify(dashboard.get_executive_dashboard())

    @app.route("/api/project-health")
    def get_project_health():
        """Get project health analytics."""
        return jsonify(dashboard.get_project_health_analytics())

    @app.route("/api/roi-analytics")
    def get_roi_analytics():
        """Get ROI analytics data."""
        return jsonify(dashboard.get_roi_analytics())

    @app.route("/api/store-project", methods=["POST"])
    def store_project():
        """Store a new project plan."""
        try:
            data = request.json
            # This would integrate with BusinessPMGateway to create ProjectPlan object
            # For now, return success
            return jsonify(
                {"status": "success", "message": "Project stored successfully"}
            )
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return app


def main():
    """Run the business intelligence dashboard."""
    app = create_dashboard_app()
    print("🎯 Starting AI Project Manager - Business Intelligence Dashboard")
    print("📊 Dashboard available at: http://localhost:5001")
    print("📈 API endpoints:")
    print("   - /api/executive-dashboard")
    print("   - /api/project-health")
    print("   - /api/roi-analytics")

    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()
