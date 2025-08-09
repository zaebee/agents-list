#!/usr/bin/env python3
"""
Production Dashboard for AI-CRM System
Real-time monitoring dashboard with business and technical metrics.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import aiohttp
from collections import defaultdict, deque
import statistics


@dataclass
class MetricPoint:
    """Time-series metric data point."""
    timestamp: datetime
    value: float
    labels: Optional[Dict[str, str]] = None


class MetricsCollector:
    """Collects and aggregates metrics from various sources."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_store = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 points
        self.business_metrics = defaultdict(float)
        
    async def collect_system_metrics(self) -> Dict:
        """Collect system performance metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/metrics") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to collect system metrics: {e}")
        
        return {}
    
    async def collect_agent_metrics(self) -> Dict:
        """Collect AI agent performance metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/agents/metrics") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to collect agent metrics: {e}")
        
        return {}
    
    async def collect_business_metrics(self) -> Dict:
        """Collect business intelligence metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/business/metrics") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to collect business metrics: {e}")
        
        return {}

    def store_metric(self, name: str, value: float, labels: Optional[Dict] = None):
        """Store a metric point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.metrics_store[name].append(point)

    def get_metric_history(self, name: str, duration_minutes: int = 60) -> List[MetricPoint]:
        """Get metric history for specified duration."""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            point for point in self.metrics_store[name]
            if point.timestamp > cutoff_time
        ]

    def calculate_metric_stats(self, name: str, duration_minutes: int = 60) -> Dict:
        """Calculate statistics for a metric over time period."""
        history = self.get_metric_history(name, duration_minutes)
        
        if not history:
            return {"count": 0}
        
        values = [point.value for point in history]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "latest": values[-1] if values else 0,
            "trend": "increasing" if len(values) > 1 and values[-1] > values[0] else "decreasing"
        }


class ProductionDashboard:
    """Real-time production dashboard for AI-CRM."""
    
    def __init__(self, config_file: str = "monitoring-config.json"):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.collector = MetricsCollector(self.config)
        self.last_update = datetime.now()
        
    def generate_dashboard_html(self, metrics: Dict) -> str:
        """Generate HTML dashboard."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>AI-CRM Production Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5;
        }
        .header { 
            background: #2c3e50; 
            color: white; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .container { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
        }
        .card { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }
        .card h3 { 
            margin-top: 0; 
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }
        .metric { 
            display: flex; 
            justify-content: space-between; 
            margin: 10px 0;
            padding: 8px 0;
        }
        .metric-value { 
            font-weight: bold; 
            color: #27ae60;
        }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }  
        .status-critical { color: #e74c3c; }
        .chart-placeholder { 
            height: 200px; 
            background: #ecf0f1; 
            border-radius: 4px; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            color: #7f8c8d;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .refresh-info {
            font-size: 0.9em;
            color: #bdc3c7;
        }
    </style>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</head>
<body>
    <div class="header">
        <h1>🚀 AI-CRM Production Dashboard</h1>
        <div class="refresh-info">
            Last Updated: {timestamp}<br>
            Auto-refresh: 30s
        </div>
    </div>
    
    <div class="container">
        <div class="card">
            <h3>🏥 System Health</h3>
            <div class="metric">
                <span>Overall Status:</span>
                <span class="metric-value status-{overall_status}">{overall_status_text}</span>
            </div>
            <div class="metric">
                <span>CPU Usage:</span>
                <span class="metric-value">{cpu_usage}%</span>
            </div>
            <div class="metric">
                <span>Memory Usage:</span>
                <span class="metric-value">{memory_usage}%</span>
            </div>
            <div class="metric">
                <span>Disk Usage:</span>
                <span class="metric-value">{disk_usage}%</span>
            </div>
            <div class="metric">
                <span>Uptime:</span>
                <span class="metric-value">{uptime}</span>
            </div>
        </div>
        
        <div class="card">
            <h3>🔧 Service Status</h3>
            {service_status}
        </div>
        
        <div class="card">
            <h3>🤖 Agent Performance</h3>
            <div class="metric">
                <span>Active Agents:</span>
                <span class="metric-value">{active_agents}</span>
            </div>
            <div class="metric">
                <span>Avg Response Time:</span>
                <span class="metric-value">{agent_response_time}ms</span>
            </div>
            <div class="metric">
                <span>Success Rate:</span>
                <span class="metric-value">{agent_success_rate}%</span>
            </div>
            <div class="metric">
                <span>Tasks Processed:</span>
                <span class="metric-value">{tasks_processed}</span>
            </div>
        </div>
        
        <div class="card">
            <h3>📊 Business Metrics</h3>
            <div class="metric">
                <span>Tasks Created Today:</span>
                <span class="metric-value">{tasks_today}</span>
            </div>
            <div class="metric">
                <span>Active Users:</span>
                <span class="metric-value">{active_users}</span>
            </div>
            <div class="metric">
                <span>Completion Rate:</span>
                <span class="metric-value">{completion_rate}%</span>
            </div>
            <div class="metric">
                <span>PM Analysis Usage:</span>
                <span class="metric-value">{pm_usage}</span>
            </div>
        </div>
        
        <div class="card">
            <h3>⚡ Performance Trends</h3>
            <div class="chart-placeholder">
                Response Time Chart (24h)
                <br><small>Chart implementation: Chart.js or D3.js</small>
            </div>
        </div>
        
        <div class="card">
            <h3>📈 Usage Analytics</h3>
            <div class="chart-placeholder">
                Task Creation Trends
                <br><small>Chart implementation: Chart.js or D3.js</small>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>AI-CRM v2.0.0 Production Dashboard | Generated at {timestamp}</p>
        <p>Monitoring {service_count} services with {metric_count} metrics</p>
    </div>
</body>
</html>
        """
        
        return html_template.format(**metrics)

    async def collect_all_metrics(self) -> Dict:
        """Collect all metrics and format for dashboard."""
        # Placeholder data - in real implementation, this would collect from actual services
        current_time = datetime.now()
        
        # System metrics
        system_metrics = {
            "overall_status": "healthy",
            "overall_status_text": "HEALTHY",
            "cpu_usage": 23.5,
            "memory_usage": 67.2,
            "disk_usage": 45.8,
            "uptime": "3 days 4 hours",
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Service status
        services = [
            {"name": "Backend API", "status": "healthy", "response_time": 145},
            {"name": "Frontend UI", "status": "healthy", "response_time": 67},
            {"name": "PM Gateway", "status": "healthy", "response_time": 234},
            {"name": "Database", "status": "healthy", "response_time": 23}
        ]
        
        service_status_html = ""
        for service in services:
            status_class = f"status-{service['status']}"
            service_status_html += f"""
            <div class="metric">
                <span>{service['name']}:</span>
                <span class="metric-value {status_class}">{service['status'].upper()} ({service['response_time']}ms)</span>
            </div>
            """
        
        # Agent performance
        agent_metrics = {
            "active_agents": 59,
            "agent_response_time": 187,
            "agent_success_rate": 94.3,
            "tasks_processed": 1247
        }
        
        # Business metrics  
        business_metrics = {
            "tasks_today": 143,
            "active_users": 28,
            "completion_rate": 87.2,
            "pm_usage": 89
        }
        
        # Combine all metrics
        dashboard_data = {
            **system_metrics,
            **agent_metrics,
            **business_metrics,
            "service_status": service_status_html,
            "service_count": len(services),
            "metric_count": 15
        }
        
        return dashboard_data

    async def generate_dashboard_file(self, output_path: str = "dashboard.html"):
        """Generate dashboard HTML file."""
        metrics = await self.collect_all_metrics()
        html_content = self.generate_dashboard_html(metrics)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Dashboard generated: {output_path}")
        return output_path

    async def start_dashboard_server(self, port: int = 9090):
        """Start simple HTTP server for dashboard."""
        from aiohttp import web
        import aiohttp_cors
        
        app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        async def dashboard_handler(request):
            """Serve dashboard HTML."""
            metrics = await self.collect_all_metrics()
            html_content = self.generate_dashboard_html(metrics)
            return web.Response(text=html_content, content_type='text/html')
        
        async def metrics_api_handler(request):
            """Serve metrics as JSON API."""
            metrics = await self.collect_all_metrics()
            return web.json_response(metrics)
        
        # Routes
        app.router.add_get('/', dashboard_handler)
        app.router.add_get('/dashboard', dashboard_handler) 
        app.router.add_get('/api/metrics', metrics_api_handler)
        
        # Add CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        print(f"Starting dashboard server on http://localhost:{port}")
        print(f"Dashboard: http://localhost:{port}/dashboard")
        print(f"Metrics API: http://localhost:{port}/api/metrics")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()
        
        # Keep server running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour


def main():
    """Run production dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-CRM Production Dashboard")
    parser.add_argument("--port", type=int, default=9090, help="Dashboard server port")
    parser.add_argument("--generate-file", help="Generate static HTML file")
    parser.add_argument("--config", default="monitoring-config.json", help="Config file")
    
    args = parser.parse_args()
    
    dashboard = ProductionDashboard(args.config)
    
    if args.generate_file:
        # Generate static HTML file
        asyncio.run(dashboard.generate_dashboard_file(args.generate_file))
    else:
        # Start dashboard server
        try:
            asyncio.run(dashboard.start_dashboard_server(args.port))
        except KeyboardInterrupt:
            print("\nDashboard server stopped")


if __name__ == "__main__":
    main()