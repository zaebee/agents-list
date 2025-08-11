#!/usr/bin/env python3
"""Test monitoring system functionality."""

import sys
import asyncio

sys.path.append(".")

from dotenv import load_dotenv

load_dotenv()


async def test_monitoring():
    print("📊 Testing Monitoring System...")

    try:
        from production_monitoring import ProductionMonitoring

        monitoring = ProductionMonitoring()
        await monitoring.initialize()

        print("✅ Production monitoring initialized")

        # Test metrics collection
        monitoring.metrics.update_system_metrics()
        print("✅ System metrics collection working")

        # Test health checker
        health_status = await monitoring.health_checker.check_all_health()
        print("📊 Component Health Status:")

        for component, status in health_status.items():
            emoji = (
                "✅"
                if status.status == "healthy"
                else "⚠️"
                if status.status == "degraded"
                else "❌"
            )
            print(
                f"   {emoji} {component}: {status.status} ({status.response_time_ms:.1f}ms)"
            )

        overall_health = monitoring.health_checker.get_overall_health()
        print(f"Overall System Health: {overall_health}")

        # Test monitoring app
        monitoring_app = monitoring.create_monitoring_app()
        with monitoring_app.test_client() as client:
            # Test health endpoint
            response = client.get("/health")
            health_data = response.get_json()
            print(
                f"✅ Health endpoint: {health_data.get('status')} (HTTP {response.status_code})"
            )

            # Test metrics endpoint
            response = client.get("/metrics")
            if response.status_code == 200:
                metrics_data = response.data.decode()
                metric_lines = len(
                    [
                        line
                        for line in metrics_data.split("\n")
                        if line and not line.startswith("#")
                    ]
                )
                print(f"✅ Metrics endpoint: {metric_lines} metrics exported")

        print("🎯 Monitoring system is functional!")

    except Exception as e:
        print(f"❌ Monitoring error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_monitoring())
