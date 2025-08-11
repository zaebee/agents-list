#!/usr/bin/env python3
"""
Performance Optimizer - Advanced performance optimization and benchmarking system.

This module provides:
1. Real-time performance monitoring and analysis
2. Agent-specific optimization strategies
3. A/B testing framework for agent improvements
4. Resource optimization and scaling
5. Performance benchmarking and comparison
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import defaultdict, deque
import uuid
import sqlite3
import psutil
import resource

# Import system components


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""

    RESPONSE_TIME = "response_time"
    ACCURACY = "accuracy"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    THROUGHPUT = "throughput"
    USER_SATISFACTION = "user_satisfaction"
    COLLABORATION_EFFICIENCY = "collaboration_efficiency"


class PerformanceThreshold(Enum):
    """Performance threshold levels."""

    EXCELLENT = 0.9
    GOOD = 0.75
    ACCEPTABLE = 0.6
    POOR = 0.4
    CRITICAL = 0.2


class OptimizationTechnique(Enum):
    """Available optimization techniques."""

    PROMPT_OPTIMIZATION = "prompt_optimization"
    CONTEXT_PRUNING = "context_pruning"
    CACHING = "caching"
    LOAD_BALANCING = "load_balancing"
    MODEL_QUANTIZATION = "model_quantization"
    PARALLEL_PROCESSING = "parallel_processing"
    MEMORY_OPTIMIZATION = "memory_optimization"
    BATCHING = "batching"


@dataclass
class PerformanceBenchmark:
    """Performance benchmark data structure."""

    benchmark_id: str
    agent_name: str
    test_scenario: str
    baseline_metrics: Dict[str, float]
    optimized_metrics: Dict[str, float]
    improvement_percentage: Dict[str, float]
    optimization_techniques: List[OptimizationTechnique]
    test_date: datetime
    test_duration: float
    resource_usage: Dict[str, float]
    notes: str


@dataclass
class ABTestExperiment:
    """A/B test experiment for agent optimization."""

    experiment_id: str
    agent_name: str
    test_name: str
    control_version: str
    treatment_version: str
    control_metrics: Dict[str, List[float]]
    treatment_metrics: Dict[str, List[float]]
    sample_size: int
    confidence_level: float
    statistical_significance: bool
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    results: Dict[str, Any]


class PerformanceMonitor:
    """Real-time performance monitoring and alerting."""

    def __init__(self, alert_thresholds: Dict[str, float] = None):
        """Initialize performance monitor."""
        self.alert_thresholds = alert_thresholds or {
            "response_time": 5.0,  # seconds
            "accuracy": 0.7,  # minimum acceptable accuracy
            "memory_usage": 0.8,  # 80% memory usage
            "cpu_usage": 0.9,  # 90% CPU usage
        }

        self.monitoring_active = False
        self.performance_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.alert_callbacks = []
        self.monitoring_thread = None
        self.resource_monitor = ResourceMonitor()

    def start_monitoring(self, interval: float = 1.0):
        """Start real-time performance monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval,), daemon=True
        )
        self.monitoring_thread.start()
        logging.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logging.info("Performance monitoring stopped")

    def _monitoring_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self.resource_monitor.get_system_metrics()
                self._process_system_metrics(system_metrics)

                # Check for alerts
                self._check_alerts(system_metrics)

                time.sleep(interval)

            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

    def _process_system_metrics(self, metrics: Dict[str, float]):
        """Process and store system metrics."""
        timestamp = datetime.now()

        for metric_name, value in metrics.items():
            self.performance_buffer[metric_name].append(
                {"timestamp": timestamp, "value": value}
            )

    def _check_alerts(self, metrics: Dict[str, float]):
        """Check metrics against alert thresholds."""
        for metric_name, value in metrics.items():
            threshold = self.alert_thresholds.get(metric_name)
            if threshold is None:
                continue

            # Check if threshold is exceeded (different logic for different metrics)
            alert_triggered = False

            if metric_name in ["memory_usage", "cpu_usage", "response_time"]:
                alert_triggered = value > threshold
            elif metric_name in ["accuracy", "user_satisfaction"]:
                alert_triggered = value < threshold

            if alert_triggered:
                alert_data = {
                    "metric": metric_name,
                    "current_value": value,
                    "threshold": threshold,
                    "timestamp": datetime.now(),
                    "severity": self._calculate_alert_severity(
                        metric_name, value, threshold
                    ),
                }

                self._trigger_alert(alert_data)

    def _calculate_alert_severity(
        self, metric_name: str, value: float, threshold: float
    ) -> str:
        """Calculate alert severity based on how much threshold is exceeded."""
        if metric_name in ["memory_usage", "cpu_usage", "response_time"]:
            ratio = value / threshold
        else:  # accuracy, satisfaction metrics (lower is worse)
            ratio = threshold / value if value > 0 else float("inf")

        if ratio >= 2.0:
            return "critical"
        elif ratio >= 1.5:
            return "high"
        elif ratio >= 1.2:
            return "medium"
        else:
            return "low"

    def _trigger_alert(self, alert_data: Dict):
        """Trigger alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logging.error(f"Alert callback failed: {e}")

    def register_alert_callback(self, callback: Callable[[Dict], None]):
        """Register callback for performance alerts."""
        self.alert_callbacks.append(callback)

    def get_performance_summary(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Get performance summary for specified time window."""
        if time_window is None:
            time_window = timedelta(hours=1)

        cutoff_time = datetime.now() - time_window
        summary = {}

        for metric_name, buffer in self.performance_buffer.items():
            recent_data = [
                entry for entry in buffer if entry["timestamp"] >= cutoff_time
            ]

            if recent_data:
                values = [entry["value"] for entry in recent_data]
                summary[metric_name] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "sample_count": len(values),
                }

        return summary


class ResourceMonitor:
    """System resource monitoring."""

    def __init__(self):
        """Initialize resource monitor."""
        self.baseline_memory = psutil.virtual_memory().used

    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_usage = memory.percent / 100.0

        # CPU metrics
        cpu_usage = psutil.cpu_percent() / 100.0

        # Process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info().rss
        process_cpu = process.cpu_percent() / 100.0

        return {
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "process_memory_mb": process_memory / (1024 * 1024),
            "process_cpu_usage": process_cpu,
            "load_average": psutil.getloadavg()[0]
            if hasattr(psutil, "getloadavg")
            else 0.0,
        }

    def get_resource_limits(self) -> Dict[str, int]:
        """Get current resource limits."""
        return {
            "memory_limit": resource.getrlimit(resource.RLIMIT_AS)[0],
            "cpu_time_limit": resource.getrlimit(resource.RLIMIT_CPU)[0],
            "file_descriptor_limit": resource.getrlimit(resource.RLIMIT_NOFILE)[0],
        }


class AgentOptimizer:
    """Core agent optimization engine."""

    def __init__(self, db_path: str = "performance_optimization.db"):
        """Initialize agent optimizer."""
        self.db_path = db_path
        self.optimization_strategies = {}
        self.benchmark_results = {}
        self.ab_tests = {}
        self.setup_database()
        self.load_optimization_strategies()

    def setup_database(self):
        """Setup optimization database."""
        with sqlite3.connect(self.db_path) as conn:
            # Benchmarks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_benchmarks (
                    benchmark_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    test_scenario TEXT,
                    baseline_metrics TEXT,  -- JSON
                    optimized_metrics TEXT, -- JSON
                    improvement_percentage TEXT, -- JSON
                    optimization_techniques TEXT, -- JSON
                    test_date TEXT,
                    test_duration REAL,
                    resource_usage TEXT, -- JSON
                    notes TEXT
                )
            """)

            # A/B Tests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    test_name TEXT,
                    control_version TEXT,
                    treatment_version TEXT,
                    control_metrics TEXT,  -- JSON
                    treatment_metrics TEXT, -- JSON
                    sample_size INTEGER,
                    confidence_level REAL,
                    statistical_significance INTEGER,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT,
                    results TEXT  -- JSON
                )
            """)

            # Optimization history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS optimization_history (
                    optimization_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    strategy TEXT,
                    technique TEXT,
                    before_metrics TEXT, -- JSON
                    after_metrics TEXT,  -- JSON
                    success INTEGER,
                    timestamp TEXT,
                    notes TEXT
                )
            """)

    def load_optimization_strategies(self):
        """Load optimization strategies for different agent types."""
        self.optimization_strategies = {
            # Programming language agents
            "python-pro": {
                OptimizationStrategy.RESPONSE_TIME: [
                    OptimizationTechnique.CACHING,
                    OptimizationTechnique.CONTEXT_PRUNING,
                    OptimizationTechnique.PROMPT_OPTIMIZATION,
                ],
                OptimizationStrategy.ACCURACY: [
                    OptimizationTechnique.PROMPT_OPTIMIZATION,
                    OptimizationTechnique.CONTEXT_PRUNING,
                ],
            },
            "frontend-developer": {
                OptimizationStrategy.THROUGHPUT: [
                    OptimizationTechnique.BATCHING,
                    OptimizationTechnique.PARALLEL_PROCESSING,
                    OptimizationTechnique.CACHING,
                ]
            },
            "database-optimizer": {
                OptimizationStrategy.RESOURCE_EFFICIENCY: [
                    OptimizationTechnique.MEMORY_OPTIMIZATION,
                    OptimizationTechnique.CONTEXT_PRUNING,
                ]
            },
            # Default strategies for all agents
            "*": {
                OptimizationStrategy.RESPONSE_TIME: [
                    OptimizationTechnique.CACHING,
                    OptimizationTechnique.CONTEXT_PRUNING,
                ],
                OptimizationStrategy.RESOURCE_EFFICIENCY: [
                    OptimizationTechnique.MEMORY_OPTIMIZATION,
                    OptimizationTechnique.BATCHING,
                ],
            },
        }

    def optimize_agent(
        self,
        agent_name: str,
        strategy: OptimizationStrategy,
        current_metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """Optimize an agent using specified strategy."""

        logging.info(
            f"Starting optimization for {agent_name} with strategy {strategy.value}"
        )

        # Get applicable optimization techniques
        techniques = self._get_optimization_techniques(agent_name, strategy)

        optimization_results = {
            "agent_name": agent_name,
            "strategy": strategy.value,
            "techniques_applied": [],
            "before_metrics": current_metrics.copy(),
            "after_metrics": {},
            "improvements": {},
            "optimization_success": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Apply optimization techniques
        best_metrics = current_metrics.copy()

        for technique in techniques:
            logging.info(f"Applying {technique.value} to {agent_name}")

            try:
                # Apply optimization technique
                optimized_metrics = self._apply_optimization_technique(
                    agent_name, technique, best_metrics
                )

                # Check if optimization improved performance
                improvement = self._calculate_improvement(
                    best_metrics, optimized_metrics, strategy
                )

                if improvement > 0:
                    best_metrics = optimized_metrics
                    optimization_results["techniques_applied"].append(
                        {
                            "technique": technique.value,
                            "improvement": improvement,
                            "metrics": optimized_metrics.copy(),
                        }
                    )

                    logging.info(
                        f"{technique.value} improved {strategy.value} by {improvement:.2%}"
                    )

            except Exception as e:
                logging.error(f"Failed to apply {technique.value} to {agent_name}: {e}")

        optimization_results["after_metrics"] = best_metrics
        optimization_results["improvements"] = self._calculate_all_improvements(
            current_metrics, best_metrics
        )
        optimization_results["optimization_success"] = (
            len(optimization_results["techniques_applied"]) > 0
        )

        # Store optimization history
        self._store_optimization_history(optimization_results)

        return optimization_results

    def _get_optimization_techniques(
        self, agent_name: str, strategy: OptimizationStrategy
    ) -> List[OptimizationTechnique]:
        """Get applicable optimization techniques for agent and strategy."""

        # Try agent-specific strategies first
        if agent_name in self.optimization_strategies:
            strategies = self.optimization_strategies[agent_name]
            if strategy in strategies:
                return strategies[strategy]

        # Fall back to default strategies
        default_strategies = self.optimization_strategies.get("*", {})
        return default_strategies.get(strategy, [])

    def _apply_optimization_technique(
        self,
        agent_name: str,
        technique: OptimizationTechnique,
        current_metrics: Dict[str, float],
    ) -> Dict[str, float]:
        """Apply specific optimization technique to agent."""

        # Simulate optimization effects (in real implementation, this would apply actual optimizations)
        optimized_metrics = current_metrics.copy()

        if technique == OptimizationTechnique.CACHING:
            # Caching improves response time
            optimized_metrics["response_time"] = (
                current_metrics.get("response_time", 2.0) * 0.6
            )

        elif technique == OptimizationTechnique.CONTEXT_PRUNING:
            # Context pruning improves response time and resource efficiency
            optimized_metrics["response_time"] = (
                current_metrics.get("response_time", 2.0) * 0.8
            )
            optimized_metrics["memory_usage"] = (
                current_metrics.get("memory_usage", 0.5) * 0.7
            )

        elif technique == OptimizationTechnique.PROMPT_OPTIMIZATION:
            # Prompt optimization improves accuracy and response time
            optimized_metrics["accuracy"] = min(
                current_metrics.get("accuracy", 0.7) * 1.1, 1.0
            )
            optimized_metrics["response_time"] = (
                current_metrics.get("response_time", 2.0) * 0.9
            )

        elif technique == OptimizationTechnique.BATCHING:
            # Batching improves throughput
            optimized_metrics["throughput"] = (
                current_metrics.get("throughput", 10.0) * 1.3
            )

        elif technique == OptimizationTechnique.PARALLEL_PROCESSING:
            # Parallel processing improves throughput and response time
            optimized_metrics["throughput"] = (
                current_metrics.get("throughput", 10.0) * 1.5
            )
            optimized_metrics["response_time"] = (
                current_metrics.get("response_time", 2.0) * 0.7
            )

        elif technique == OptimizationTechnique.MEMORY_OPTIMIZATION:
            # Memory optimization reduces resource usage
            optimized_metrics["memory_usage"] = (
                current_metrics.get("memory_usage", 0.5) * 0.6
            )

        # Add small random variation to simulate real-world conditions
        import random

        for metric in optimized_metrics:
            if isinstance(optimized_metrics[metric], (int, float)):
                variation = random.uniform(0.95, 1.05)
                optimized_metrics[metric] *= variation

        return optimized_metrics

    def _calculate_improvement(
        self,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
        strategy: OptimizationStrategy,
    ) -> float:
        """Calculate improvement for specific optimization strategy."""

        strategy_metrics = {
            OptimizationStrategy.RESPONSE_TIME: ["response_time"],
            OptimizationStrategy.ACCURACY: ["accuracy", "task_success_rate"],
            OptimizationStrategy.RESOURCE_EFFICIENCY: ["memory_usage", "cpu_usage"],
            OptimizationStrategy.THROUGHPUT: ["throughput"],
            OptimizationStrategy.USER_SATISFACTION: ["user_satisfaction"],
            OptimizationStrategy.COLLABORATION_EFFICIENCY: ["collaboration_score"],
        }

        relevant_metrics = strategy_metrics.get(strategy, [])
        if not relevant_metrics:
            return 0.0

        improvements = []

        for metric in relevant_metrics:
            before_value = before_metrics.get(metric, 0.0)
            after_value = after_metrics.get(metric, 0.0)

            if before_value > 0:
                if metric in ["memory_usage", "cpu_usage", "response_time"]:
                    # Lower is better for these metrics
                    improvement = (before_value - after_value) / before_value
                else:
                    # Higher is better for these metrics
                    improvement = (after_value - before_value) / before_value

                improvements.append(improvement)

        return statistics.mean(improvements) if improvements else 0.0

    def _calculate_all_improvements(
        self, before_metrics: Dict[str, float], after_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate improvements for all metrics."""
        improvements = {}

        for metric in before_metrics:
            if metric in after_metrics:
                before_value = before_metrics[metric]
                after_value = after_metrics[metric]

                if before_value != 0:
                    improvements[metric] = (after_value - before_value) / before_value

        return improvements

    def _store_optimization_history(self, optimization_results: Dict[str, Any]):
        """Store optimization results in database."""
        optimization_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO optimization_history 
                (optimization_id, agent_name, strategy, technique, before_metrics, 
                 after_metrics, success, timestamp, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    optimization_id,
                    optimization_results["agent_name"],
                    optimization_results["strategy"],
                    json.dumps(
                        [
                            t["technique"]
                            for t in optimization_results["techniques_applied"]
                        ]
                    ),
                    json.dumps(optimization_results["before_metrics"]),
                    json.dumps(optimization_results["after_metrics"]),
                    int(optimization_results["optimization_success"]),
                    optimization_results["timestamp"],
                    f"Applied {len(optimization_results['techniques_applied'])} techniques",
                ),
            )

    def run_performance_benchmark(
        self, agent_name: str, test_scenarios: List[Dict]
    ) -> PerformanceBenchmark:
        """Run comprehensive performance benchmark for an agent."""

        benchmark_id = str(uuid.uuid4())
        start_time = time.time()

        logging.info(f"Running performance benchmark for {agent_name}")

        # Collect baseline metrics
        baseline_metrics = self._collect_baseline_metrics(agent_name, test_scenarios)

        # Apply optimization strategies
        optimized_metrics = {}
        applied_techniques = []

        for strategy in [
            OptimizationStrategy.RESPONSE_TIME,
            OptimizationStrategy.ACCURACY,
        ]:
            optimization_result = self.optimize_agent(
                agent_name, strategy, baseline_metrics
            )

            if optimization_result["optimization_success"]:
                optimized_metrics.update(optimization_result["after_metrics"])
                applied_techniques.extend(
                    [
                        OptimizationTechnique(t["technique"])
                        for t in optimization_result["techniques_applied"]
                    ]
                )

        # Use baseline if no optimizations were successful
        if not optimized_metrics:
            optimized_metrics = baseline_metrics.copy()

        # Calculate improvements
        improvement_percentage = {}
        for metric in baseline_metrics:
            if metric in optimized_metrics:
                baseline_val = baseline_metrics[metric]
                optimized_val = optimized_metrics[metric]

                if baseline_val != 0:
                    improvement_percentage[metric] = (
                        (optimized_val - baseline_val) / baseline_val
                    ) * 100

        # Collect resource usage data
        resource_monitor = ResourceMonitor()
        resource_usage = resource_monitor.get_system_metrics()

        test_duration = time.time() - start_time

        benchmark = PerformanceBenchmark(
            benchmark_id=benchmark_id,
            agent_name=agent_name,
            test_scenario=f"{len(test_scenarios)} test scenarios",
            baseline_metrics=baseline_metrics,
            optimized_metrics=optimized_metrics,
            improvement_percentage=improvement_percentage,
            optimization_techniques=applied_techniques,
            test_date=datetime.now(),
            test_duration=test_duration,
            resource_usage=resource_usage,
            notes=f"Benchmark with {len(applied_techniques)} optimization techniques",
        )

        # Store benchmark results
        self._store_benchmark_results(benchmark)

        return benchmark

    def _collect_baseline_metrics(
        self, agent_name: str, test_scenarios: List[Dict]
    ) -> Dict[str, float]:
        """Collect baseline performance metrics for an agent."""

        # Simulate baseline metrics collection (in real implementation, this would run actual tests)
        import random

        baseline_metrics = {
            "response_time": random.uniform(1.0, 3.0),
            "accuracy": random.uniform(0.6, 0.8),
            "throughput": random.uniform(8.0, 15.0),
            "memory_usage": random.uniform(0.3, 0.7),
            "cpu_usage": random.uniform(0.2, 0.6),
            "user_satisfaction": random.uniform(0.6, 0.8),
            "task_success_rate": random.uniform(0.7, 0.9),
        }

        # Add agent-specific variations
        if "database" in agent_name:
            baseline_metrics["memory_usage"] *= 1.2  # Database agents use more memory
        elif "frontend" in agent_name:
            baseline_metrics["response_time"] *= (
                0.8  # Frontend agents are typically faster
            )

        return baseline_metrics

    def _store_benchmark_results(self, benchmark: PerformanceBenchmark):
        """Store benchmark results in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_benchmarks
                (benchmark_id, agent_name, test_scenario, baseline_metrics, optimized_metrics,
                 improvement_percentage, optimization_techniques, test_date, test_duration,
                 resource_usage, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    benchmark.benchmark_id,
                    benchmark.agent_name,
                    benchmark.test_scenario,
                    json.dumps(benchmark.baseline_metrics),
                    json.dumps(benchmark.optimized_metrics),
                    json.dumps(benchmark.improvement_percentage),
                    json.dumps(
                        [tech.value for tech in benchmark.optimization_techniques]
                    ),
                    benchmark.test_date.isoformat(),
                    benchmark.test_duration,
                    json.dumps(benchmark.resource_usage),
                    benchmark.notes,
                ),
            )

    def start_ab_test(
        self,
        agent_name: str,
        test_name: str,
        control_version: str,
        treatment_version: str,
        sample_size: int = 100,
        confidence_level: float = 0.95,
    ) -> str:
        """Start an A/B test experiment for agent optimization."""

        experiment_id = str(uuid.uuid4())

        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            agent_name=agent_name,
            test_name=test_name,
            control_version=control_version,
            treatment_version=treatment_version,
            control_metrics=defaultdict(list),
            treatment_metrics=defaultdict(list),
            sample_size=sample_size,
            confidence_level=confidence_level,
            statistical_significance=False,
            start_date=datetime.now(),
            end_date=None,
            status="running",
            results={},
        )

        self.ab_tests[experiment_id] = experiment

        logging.info(
            f"Started A/B test {experiment_id} for {agent_name}: {control_version} vs {treatment_version}"
        )

        return experiment_id

    def add_ab_test_data(
        self, experiment_id: str, version: str, metrics: Dict[str, float]
    ):
        """Add data point to A/B test experiment."""
        if experiment_id not in self.ab_tests:
            raise ValueError(f"A/B test experiment {experiment_id} not found")

        experiment = self.ab_tests[experiment_id]

        if version == experiment.control_version:
            target_metrics = experiment.control_metrics
        elif version == experiment.treatment_version:
            target_metrics = experiment.treatment_metrics
        else:
            raise ValueError(
                f"Unknown version {version} for experiment {experiment_id}"
            )

        # Add metrics to the appropriate group
        for metric_name, value in metrics.items():
            target_metrics[metric_name].append(value)

        # Check if we have enough data for analysis
        control_samples = (
            len(list(experiment.control_metrics.values())[0])
            if experiment.control_metrics
            else 0
        )
        treatment_samples = (
            len(list(experiment.treatment_metrics.values())[0])
            if experiment.treatment_metrics
            else 0
        )

        if (
            control_samples >= experiment.sample_size
            and treatment_samples >= experiment.sample_size
        ):
            self._analyze_ab_test(experiment_id)

    def _analyze_ab_test(self, experiment_id: str):
        """Analyze A/B test results for statistical significance."""
        experiment = self.ab_tests[experiment_id]

        results = {}

        # Analyze each metric
        for metric_name in set(experiment.control_metrics.keys()) | set(
            experiment.treatment_metrics.keys()
        ):
            control_values = experiment.control_metrics.get(metric_name, [])
            treatment_values = experiment.treatment_metrics.get(metric_name, [])

            if len(control_values) < 10 or len(treatment_values) < 10:
                continue  # Need minimum sample size for meaningful analysis

            # Calculate basic statistics
            control_mean = statistics.mean(control_values)
            treatment_mean = statistics.mean(treatment_values)

            control_std = (
                statistics.stdev(control_values) if len(control_values) > 1 else 0
            )
            treatment_std = (
                statistics.stdev(treatment_values) if len(treatment_values) > 1 else 0
            )

            # Calculate effect size
            improvement = (
                (treatment_mean - control_mean) / control_mean
                if control_mean != 0
                else 0
            )

            # Simplified significance test (in real implementation, use proper statistical tests)
            significance_threshold = 0.05  # 5% significance level

            # Simple t-test approximation
            pooled_std = ((control_std**2 + treatment_std**2) / 2) ** 0.5
            if pooled_std > 0:
                t_stat = abs(treatment_mean - control_mean) / (
                    pooled_std
                    * ((1 / len(control_values) + 1 / len(treatment_values)) ** 0.5)
                )
                # Simplified p-value calculation
                significant = t_stat > 2.0  # Rough approximation for p < 0.05
            else:
                significant = False

            results[metric_name] = {
                "control_mean": control_mean,
                "treatment_mean": treatment_mean,
                "improvement": improvement,
                "significant": significant,
                "control_samples": len(control_values),
                "treatment_samples": len(treatment_values),
            }

        # Update experiment with results
        experiment.results = results
        experiment.end_date = datetime.now()
        experiment.status = "completed"

        # Check overall significance
        significant_metrics = [
            r for r in results.values() if r["significant"] and r["improvement"] > 0
        ]
        experiment.statistical_significance = len(significant_metrics) > 0

        # Store results in database
        self._store_ab_test_results(experiment)

        logging.info(
            f"A/B test {experiment_id} completed: {len(significant_metrics)} significant improvements"
        )

    def _store_ab_test_results(self, experiment: ABTestExperiment):
        """Store A/B test results in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ab_test_experiments
                (experiment_id, agent_name, test_name, control_version, treatment_version,
                 control_metrics, treatment_metrics, sample_size, confidence_level,
                 statistical_significance, start_date, end_date, status, results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    experiment.experiment_id,
                    experiment.agent_name,
                    experiment.test_name,
                    experiment.control_version,
                    experiment.treatment_version,
                    json.dumps(
                        {k: list(v) for k, v in experiment.control_metrics.items()}
                    ),
                    json.dumps(
                        {k: list(v) for k, v in experiment.treatment_metrics.items()}
                    ),
                    experiment.sample_size,
                    experiment.confidence_level,
                    int(experiment.statistical_significance),
                    experiment.start_date.isoformat(),
                    experiment.end_date.isoformat() if experiment.end_date else None,
                    experiment.status,
                    json.dumps(experiment.results),
                ),
            )

    def get_optimization_recommendations(
        self, agent_name: str, current_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Get optimization recommendations for an agent."""
        recommendations = []

        # Analyze current performance vs thresholds
        performance_issues = []

        for metric, value in current_metrics.items():
            if metric == "response_time" and value > 3.0:
                performance_issues.append(
                    {
                        "metric": metric,
                        "current": value,
                        "issue": "slow_response",
                        "severity": "high" if value > 5.0 else "medium",
                    }
                )
            elif metric == "accuracy" and value < 0.7:
                performance_issues.append(
                    {
                        "metric": metric,
                        "current": value,
                        "issue": "low_accuracy",
                        "severity": "high" if value < 0.5 else "medium",
                    }
                )
            elif metric in ["memory_usage", "cpu_usage"] and value > 0.8:
                performance_issues.append(
                    {
                        "metric": metric,
                        "current": value,
                        "issue": "high_resource_usage",
                        "severity": "high" if value > 0.9 else "medium",
                    }
                )

        # Generate recommendations based on issues
        for issue in performance_issues:
            metric = issue["metric"]

            if issue["issue"] == "slow_response":
                recommendations.append(
                    {
                        "strategy": OptimizationStrategy.RESPONSE_TIME.value,
                        "techniques": [
                            OptimizationTechnique.CACHING.value,
                            OptimizationTechnique.CONTEXT_PRUNING.value,
                        ],
                        "expected_improvement": "30-50% response time reduction",
                        "priority": issue["severity"],
                        "description": "Implement caching and context optimization to reduce response time",
                    }
                )

            elif issue["issue"] == "low_accuracy":
                recommendations.append(
                    {
                        "strategy": OptimizationStrategy.ACCURACY.value,
                        "techniques": [OptimizationTechnique.PROMPT_OPTIMIZATION.value],
                        "expected_improvement": "10-20% accuracy increase",
                        "priority": issue["severity"],
                        "description": "Optimize prompts and context to improve accuracy",
                    }
                )

            elif issue["issue"] == "high_resource_usage":
                recommendations.append(
                    {
                        "strategy": OptimizationStrategy.RESOURCE_EFFICIENCY.value,
                        "techniques": [
                            OptimizationTechnique.MEMORY_OPTIMIZATION.value,
                            OptimizationTechnique.CONTEXT_PRUNING.value,
                        ],
                        "expected_improvement": "20-40% resource usage reduction",
                        "priority": issue["severity"],
                        "description": "Implement memory optimization and context pruning",
                    }
                )

        return recommendations


def main():
    """CLI interface for performance optimizer."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Optimizer")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Optimize command
    optimize_parser = subparsers.add_parser(
        "optimize", help="Optimize agent performance"
    )
    optimize_parser.add_argument("--agent", required=True, help="Agent name")
    optimize_parser.add_argument(
        "--strategy",
        choices=[s.value for s in OptimizationStrategy],
        required=True,
        help="Optimization strategy",
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Run performance benchmark"
    )
    benchmark_parser.add_argument("--agent", required=True, help="Agent name")

    # Monitor command
    monitor_parser = subparsers.add_parser(
        "monitor", help="Start performance monitoring"
    )
    monitor_parser.add_argument(
        "--interval", type=float, default=1.0, help="Monitoring interval in seconds"
    )

    # AB test commands
    ab_start_parser = subparsers.add_parser("ab-start", help="Start A/B test")
    ab_start_parser.add_argument("--agent", required=True, help="Agent name")
    ab_start_parser.add_argument("--test-name", required=True, help="Test name")
    ab_start_parser.add_argument("--control", required=True, help="Control version")
    ab_start_parser.add_argument("--treatment", required=True, help="Treatment version")

    # Recommendations command
    rec_parser = subparsers.add_parser(
        "recommendations", help="Get optimization recommendations"
    )
    rec_parser.add_argument("--agent", required=True, help="Agent name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Initialize optimizer
    optimizer = AgentOptimizer()

    try:
        if args.command == "optimize":
            # Mock current metrics for demo
            current_metrics = {
                "response_time": 2.5,
                "accuracy": 0.75,
                "memory_usage": 0.6,
                "throughput": 12.0,
            }

            strategy = OptimizationStrategy(args.strategy)
            results = optimizer.optimize_agent(args.agent, strategy, current_metrics)

            print(f"\n🎯 Optimization Results for {args.agent}:")
            print(f"Strategy: {strategy.value}")
            print(f"Success: {results['optimization_success']}")
            print(f"Techniques applied: {len(results['techniques_applied'])}")

            if results["techniques_applied"]:
                print("\nImprovements:")
                for improvement in results["improvements"].items():
                    metric, change = improvement
                    print(f"  {metric}: {change:+.2%}")

        elif args.command == "benchmark":
            test_scenarios = [{"scenario": "basic_task"}, {"scenario": "complex_task"}]
            benchmark = optimizer.run_performance_benchmark(args.agent, test_scenarios)

            print(f"\n📊 Benchmark Results for {args.agent}:")
            print(f"Test Duration: {benchmark.test_duration:.2f}s")
            print(f"Techniques Applied: {len(benchmark.optimization_techniques)}")

            print("\nPerformance Improvements:")
            for metric, improvement in benchmark.improvement_percentage.items():
                print(f"  {metric}: {improvement:+.2f}%")

        elif args.command == "monitor":
            monitor = PerformanceMonitor()

            # Register alert callback
            def alert_handler(alert_data):
                print(
                    f"🚨 ALERT: {alert_data['metric']} = {alert_data['current_value']:.2f} "
                    f"(threshold: {alert_data['threshold']}) - {alert_data['severity']} severity"
                )

            monitor.register_alert_callback(alert_handler)

            print(f"Starting performance monitoring (interval: {args.interval}s)")
            print("Press Ctrl+C to stop...")

            monitor.start_monitoring(args.interval)

            try:
                while True:
                    time.sleep(10)
                    summary = monitor.get_performance_summary()
                    if summary:
                        print("\nCurrent metrics:")
                        for metric, stats in summary.items():
                            print(
                                f"  {metric}: {stats['current']:.2f} (avg: {stats['average']:.2f})"
                            )
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
            finally:
                monitor.stop_monitoring()

        elif args.command == "ab-start":
            experiment_id = optimizer.start_ab_test(
                args.agent, args.test_name, args.control, args.treatment
            )
            print(f"✅ Started A/B test: {experiment_id}")

        elif args.command == "recommendations":
            # Mock current metrics
            current_metrics = {
                "response_time": 4.2,  # Slow
                "accuracy": 0.65,  # Low
                "memory_usage": 0.85,  # High
            }

            recommendations = optimizer.get_optimization_recommendations(
                args.agent, current_metrics
            )

            print(f"\n💡 Optimization Recommendations for {args.agent}:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['description']}")
                print(f"   Strategy: {rec['strategy']}")
                print(f"   Techniques: {', '.join(rec['techniques'])}")
                print(f"   Expected: {rec['expected_improvement']}")
                print(f"   Priority: {rec['priority']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Performance optimizer error: {e}")


if __name__ == "__main__":
    main()
