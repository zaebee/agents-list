#!/usr/bin/env python3
"""
Production Health Check System for AI-CRM
Comprehensive monitoring and alerting for production deployments.
"""

import asyncio
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import aiohttp


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result structure."""
    service: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    message: str
    details: Optional[Dict] = None
    
    
@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_connections: int
    active_processes: int
    uptime_seconds: float
    

class ProductionHealthMonitor:
    """Comprehensive production health monitoring system."""
    
    def __init__(self, config_file: str = "monitoring-config.json"):
        """Initialize health monitor with configuration."""
        self.config = self._load_config(config_file)
        self.logger = self._setup_logging()
        self.health_history: List[HealthCheck] = []
        self.alert_thresholds = self.config.get("alert_thresholds", {})
        
    def _load_config(self, config_file: str) -> Dict:
        """Load monitoring configuration."""
        default_config = {
            "endpoints": {
                "backend": "http://localhost:8000/health",
                "frontend": "http://localhost:3000/health",
                "pm_gateway": "http://localhost:8000/pm/health"
            },
            "alert_thresholds": {
                "response_time_ms": 2000,
                "cpu_usage_percent": 80,
                "memory_usage_percent": 85,
                "disk_usage_percent": 90,
                "error_rate_percent": 5
            },
            "check_intervals": {
                "health_checks": 30,    # seconds
                "system_metrics": 60,   # seconds  
                "detailed_analysis": 300 # seconds
            },
            "retention_days": 7,
            "alert_channels": {
                "email": True,
                "slack": False,
                "webhook": False
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            self.logger.info(f"Config file {config_file} not found, using defaults")
            return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Set up comprehensive logging."""
        logger = logging.getLogger("ai_crm_health_monitor")
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler("health-monitor.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger

    async def check_endpoint_health(self, service: str, url: str) -> HealthCheck:
        """Check health of a specific endpoint."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        status = HealthStatus.HEALTHY
                        message = f"{service} is healthy"
                        details = data
                    else:
                        status = HealthStatus.CRITICAL
                        message = f"{service} returned status {response.status}"
                        details = {"status_code": response.status}
                        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.CRITICAL
            message = f"{service} health check timed out"
            details = {"error": "timeout"}
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.CRITICAL  
            message = f"{service} health check failed: {str(e)}"
            details = {"error": str(e)}
        
        return HealthCheck(
            service=service,
            status=status,
            response_time_ms=response_time,
            timestamp=datetime.now(),
            message=message,
            details=details
        )

    def get_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage (root partition)
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Active processes
            processes = len(psutil.pids())
            
            # System uptime
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_connections=connections,
                active_processes=processes,
                uptime_seconds=uptime
            )
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0)

    async def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all configured health checks."""
        checks = {}
        endpoints = self.config.get("endpoints", {})
        
        # Create tasks for parallel execution
        tasks = []
        for service, url in endpoints.items():
            task = self.check_endpoint_health(service, url)
            tasks.append((service, task))
        
        # Execute all health checks in parallel
        for service, task in tasks:
            checks[service] = await task
            
        return checks

    def analyze_health_status(self, checks: Dict[str, HealthCheck], metrics: SystemMetrics) -> Dict:
        """Analyze overall system health and generate alerts."""
        overall_status = HealthStatus.HEALTHY
        alerts = []
        warnings = []
        
        # Check service health
        critical_services = []
        warning_services = []
        
        for service, check in checks.items():
            if check.status == HealthStatus.CRITICAL:
                critical_services.append(service)
                overall_status = HealthStatus.CRITICAL
            elif check.status == HealthStatus.WARNING:
                warning_services.append(service)
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
        
        # Check response times
        slow_services = []
        threshold = self.alert_thresholds.get("response_time_ms", 2000)
        for service, check in checks.items():
            if check.response_time_ms > threshold:
                slow_services.append({
                    "service": service,
                    "response_time": check.response_time_ms,
                    "threshold": threshold
                })
                
        if slow_services and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.WARNING
        
        # Check system metrics
        cpu_threshold = self.alert_thresholds.get("cpu_usage_percent", 80)
        memory_threshold = self.alert_thresholds.get("memory_usage_percent", 85)
        disk_threshold = self.alert_thresholds.get("disk_usage_percent", 90)
        
        if metrics.cpu_usage > cpu_threshold:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
            overall_status = HealthStatus.WARNING
            
        if metrics.memory_usage > memory_threshold:
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
            overall_status = HealthStatus.WARNING
            
        if metrics.disk_usage > disk_threshold:
            alerts.append(f"High disk usage: {metrics.disk_usage:.1f}%")
            if metrics.disk_usage > 95:
                overall_status = HealthStatus.CRITICAL
        
        # Generate alert messages
        if critical_services:
            alerts.append(f"Critical services down: {', '.join(critical_services)}")
            
        if warning_services:
            warnings.append(f"Services with warnings: {', '.join(warning_services)}")
            
        if slow_services:
            service_names = [s["service"] for s in slow_services]
            warnings.append(f"Slow response times: {', '.join(service_names)}")
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "warnings": warnings,
            "critical_services": critical_services,
            "warning_services": warning_services,
            "slow_services": slow_services,
            "system_metrics": asdict(metrics),
            "service_checks": {k: asdict(v) for k, v in checks.items()}
        }

    def generate_health_report(self, analysis: Dict) -> str:
        """Generate human-readable health report."""
        status = analysis["overall_status"]
        timestamp = analysis["timestamp"]
        
        # Status emoji
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "🚨",
            HealthStatus.UNKNOWN: "❓"
        }
        
        report = f"""
🏥 AI-CRM Production Health Report
=====================================
Status: {status_emoji.get(HealthStatus(status), '❓')} {status.upper()}
Time: {timestamp}

"""
        
        # Alerts
        if analysis["alerts"]:
            report += "🚨 ALERTS:\n"
            for alert in analysis["alerts"]:
                report += f"  • {alert}\n"
            report += "\n"
        
        # Warnings  
        if analysis["warnings"]:
            report += "⚠️  WARNINGS:\n"
            for warning in analysis["warnings"]:
                report += f"  • {warning}\n"
            report += "\n"
        
        # System metrics
        metrics = analysis["system_metrics"]
        report += f"""📊 SYSTEM METRICS:
  • CPU Usage: {metrics['cpu_usage']:.1f}%
  • Memory Usage: {metrics['memory_usage']:.1f}%
  • Disk Usage: {metrics['disk_usage']:.1f}%
  • Network Connections: {metrics['network_connections']}
  • Active Processes: {metrics['active_processes']}
  • Uptime: {metrics['uptime_seconds']/3600:.1f} hours

"""
        
        # Service status
        report += "🔧 SERVICE STATUS:\n"
        for service, check_data in analysis["service_checks"].items():
            status_icon = status_emoji.get(HealthStatus(check_data["status"]), "❓")
            response_time = check_data["response_time_ms"]
            report += f"  {status_icon} {service}: {response_time:.0f}ms\n"
        
        return report

    async def send_alerts(self, analysis: Dict):
        """Send alerts through configured channels."""
        if analysis["overall_status"] in [HealthStatus.CRITICAL.value, HealthStatus.WARNING.value]:
            report = self.generate_health_report(analysis)
            
            # Email alerts
            if self.config["alert_channels"].get("email"):
                await self._send_email_alert(report, analysis)
            
            # Slack alerts
            if self.config["alert_channels"].get("slack"):
                await self._send_slack_alert(report, analysis)
                
            # Webhook alerts
            if self.config["alert_channels"].get("webhook"):
                await self._send_webhook_alert(analysis)

    async def _send_email_alert(self, report: str, analysis: Dict):
        """Send email alert (placeholder for SMTP integration)."""
        self.logger.info("Email alert would be sent:")
        self.logger.info(report)

    async def _send_slack_alert(self, report: str, analysis: Dict):
        """Send Slack alert (placeholder for Slack integration)."""
        self.logger.info("Slack alert would be sent:")
        self.logger.info(report)

    async def _send_webhook_alert(self, analysis: Dict):
        """Send webhook alert (placeholder for webhook integration)."""
        self.logger.info("Webhook alert would be sent with data:")
        self.logger.info(json.dumps(analysis, indent=2, default=str))

    def cleanup_old_data(self):
        """Clean up old health check data."""
        retention_days = self.config.get("retention_days", 7)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.health_history = [
            check for check in self.health_history 
            if check.timestamp > cutoff_date
        ]

    async def monitor_loop(self):
        """Main monitoring loop."""
        self.logger.info("Starting AI-CRM production health monitoring...")
        
        while True:
            try:
                # Run health checks
                checks = await self.run_health_checks()
                
                # Get system metrics
                metrics = self.get_system_metrics()
                
                # Analyze health
                analysis = self.analyze_health_status(checks, metrics)
                
                # Log status
                status = analysis["overall_status"]
                self.logger.info(f"Health check complete: {status}")
                
                # Send alerts if needed
                await self.send_alerts(analysis)
                
                # Store results
                for check in checks.values():
                    self.health_history.append(check)
                
                # Clean up old data
                self.cleanup_old_data()
                
                # Print report to console
                if status != HealthStatus.HEALTHY.value:
                    print(self.generate_health_report(analysis))
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
            
            # Wait for next check
            interval = self.config["check_intervals"]["health_checks"]
            await asyncio.sleep(interval)


def main():
    """Run health monitoring system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-CRM Production Health Monitor")
    parser.add_argument("--config", default="monitoring-config.json", 
                       help="Configuration file path")
    parser.add_argument("--once", action="store_true", 
                       help="Run health check once and exit")
    
    args = parser.parse_args()
    
    monitor = ProductionHealthMonitor(args.config)
    
    if args.once:
        # Single health check
        async def single_check():
            checks = await monitor.run_health_checks()
            metrics = monitor.get_system_metrics()
            analysis = monitor.analyze_health_status(checks, metrics)
            report = monitor.generate_health_report(analysis)
            print(report)
            return analysis
        
        result = asyncio.run(single_check())
        exit_code = 0 if result["overall_status"] == HealthStatus.HEALTHY.value else 1
        exit(exit_code)
    else:
        # Continuous monitoring
        asyncio.run(monitor.monitor_loop())


if __name__ == "__main__":
    main()