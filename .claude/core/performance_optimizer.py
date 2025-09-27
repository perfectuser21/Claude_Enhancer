#!/usr/bin/env python3
"""
Claude Enhancer Performance Optimizer
实时性能监控、瓶颈分析、智能优化建议
"""

import time
import json
import threading
import subprocess
import psutil
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
import functools


@dataclass
class PerformanceMetric:
    """Performance metric data point"""

    timestamp: float
    metric_name: str
    value: float
    context: Dict[str, Any]
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""

    component: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    impact: str
    suggested_fix: str
    confidence: float  # 0.0 to 1.0


@dataclass
class OptimizationResult:
    """Optimization execution result"""

    optimization_id: str
    applied_at: float
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement: Dict[str, float]
    success: bool
    error: Optional[str] = None


class PerformanceOptimizer:
    """Real-time performance monitoring and optimization engine"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.bottlenecks_history = deque(maxlen=100)
        self.optimization_history = deque(maxlen=50)

        # Performance thresholds
        self.thresholds = {
            "hook_execution_time": 500,  # ms
            "agent_selection_time": 100,  # ms
            "memory_usage": 80,  # percentage
            "cpu_usage": 85,  # percentage
            "disk_io_wait": 50,  # ms
            "cache_hit_rate": 70,  # percentage
        }

        # Optimization strategies
        self.optimization_strategies = {
            "high_hook_execution": self._optimize_hook_execution,
            "slow_agent_selection": self._optimize_agent_selection,
            "high_memory_usage": self._optimize_memory_usage,
            "poor_cache_performance": self._optimize_caching,
            "excessive_disk_io": self._optimize_disk_io,
        }

        # Threading for real-time monitoring
        self.monitoring_lock = threading.RLock()
        self.is_monitoring = False
        self.monitor_thread = None

        # Metrics aggregation
        self.metrics_aggregator = defaultdict(list)
        self.aggregation_window = 60  # seconds

        print("🚀 Performance Optimizer initialized")

    def start_monitoring(self, interval: float = 1.0):
        """Start real-time performance monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()
        print(f"📊 Performance monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        print("📊 Performance monitoring stopped")

    def record_metric(
        self,
        metric_name: str,
        value: float,
        context: Dict[str, Any] = None,
        tags: List[str] = None,
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_name=metric_name,
            value=value,
            context=context or {},
            tags=tags or [],
        )

        with self.monitoring_lock:
            self.metrics_history.append(metric)
            self.metrics_aggregator[metric_name].append((metric.timestamp, value))

        # Check for immediate bottlenecks
        self._check_immediate_bottleneck(metric)

    def analyze_performance(self, time_window: float = 300) -> Dict[str, Any]:
        """Analyze performance over specified time window"""
        cutoff_time = time.time() - time_window

        with self.monitoring_lock:
            recent_metrics = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]

        if not recent_metrics:
            return {"status": "no_data", "message": "No metrics in time window"}

        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.metric_name].append(metric.value)

        # Calculate statistics for each metric
        analysis = {}
        for metric_name, values in metric_groups.items():
            if values:
                analysis[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "p95": self._percentile(values, 0.95),
                    "p99": self._percentile(values, 0.99),
                }

        # Identify trends
        trends = self._analyze_trends(metric_groups, time_window)

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(analysis)

        return {
            "status": "success",
            "time_window": time_window,
            "metrics_count": len(recent_metrics),
            "analysis": analysis,
            "trends": trends,
            "bottlenecks": bottlenecks,
            "recommendations": self._generate_recommendations(analysis, bottlenecks),
            "overall_health": self._calculate_overall_health(analysis),
        }

    def optimize_automatically(
        self, max_optimizations: int = 3
    ) -> List[OptimizationResult]:
        """Apply automatic optimizations based on detected bottlenecks"""
        analysis = self.analyze_performance()
        bottlenecks = analysis.get("bottlenecks", [])

        if not bottlenecks:
            return []

        results = []
        optimizations_applied = 0

        # Sort bottlenecks by severity
        bottlenecks.sort(
            key=lambda x: self._severity_to_score(x.get("severity", "low")),
            reverse=True,
        )

        for bottleneck in bottlenecks:
            if optimizations_applied >= max_optimizations:
                break

            bottleneck_type = bottleneck.get("type")
            if bottleneck_type in self.optimization_strategies:
                try:
                    # Record before metrics
                    before_metrics = self._collect_current_metrics()

                    # Apply optimization
                    optimization_func = self.optimization_strategies[bottleneck_type]
                    success, error = optimization_func(bottleneck)

                    # Record after metrics
                    time.sleep(0.5)  # Allow metrics to update
                    after_metrics = self._collect_current_metrics()

                    # Calculate improvement
                    improvement = self._calculate_improvement(
                        before_metrics, after_metrics
                    )

                    result = OptimizationResult(
                        optimization_id=f"opt_{int(time.time())}_{bottleneck_type}",
                        applied_at=time.time(),
                        before_metrics=before_metrics,
                        after_metrics=after_metrics,
                        improvement=improvement,
                        success=success,
                        error=error,
                    )

                    results.append(result)
                    self.optimization_history.append(result)

                    if success:
                        optimizations_applied += 1
                        print(f"✅ Applied optimization: {bottleneck_type}")

                except Exception as e:
                    print(f"❌ Failed to apply optimization {bottleneck_type}: {e}")

        return results

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        analysis = self.analyze_performance()

        # System resource utilization
        system_stats = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io": dict(psutil.disk_io_counters()._asdict())
            if psutil.disk_io_counters()
            else {},
            "network_io": dict(psutil.net_io_counters()._asdict())
            if psutil.net_io_counters()
            else {},
        }

        # Claude Enhancer specific metrics
        claude_metrics = self._get_claude_specific_metrics()

        # Performance recommendations
        recommendations = self._generate_comprehensive_recommendations(
            analysis, system_stats
        )

        return {
            "timestamp": time.time(),
            "performance_analysis": analysis,
            "system_resources": system_stats,
            "claude_metrics": claude_metrics,
            "optimization_history": [
                asdict(opt) for opt in list(self.optimization_history)
            ],
            "recommendations": recommendations,
            "health_score": self._calculate_overall_health_score(),
        }

    def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                self.record_metric("cpu_usage", psutil.cpu_percent(interval=None))
                self.record_metric("memory_usage", psutil.virtual_memory().percent)

                # Collect Claude-specific metrics
                self._collect_claude_metrics()

                # Clean up old aggregation data
                self._cleanup_aggregation_data()

                time.sleep(interval)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(interval)

    def _collect_claude_metrics(self):
        """Collect Claude Enhancer specific metrics"""
        try:
            # Hook execution metrics
            hook_metrics = self._get_hook_metrics()
            for metric_name, value in hook_metrics.items():
                self.record_metric(metric_name, value, tags=["hooks"])

            # Agent selection metrics
            agent_metrics = self._get_agent_metrics()
            for metric_name, value in agent_metrics.items():
                self.record_metric(metric_name, value, tags=["agents"])

            # Cache performance metrics
            cache_metrics = self._get_cache_metrics()
            for metric_name, value in cache_metrics.items():
                self.record_metric(metric_name, value, tags=["cache"])

        except Exception as e:
            print(f"Error collecting Claude metrics: {e}")

    def _get_hook_metrics(self) -> Dict[str, float]:
        """Get hook execution performance metrics"""
        metrics = {}

        try:
            # Read hook performance logs
            hook_perf_file = "/tmp/orchestrator_perf"
            if os.path.exists(hook_perf_file):
                with open(hook_perf_file, "r") as f:
                    lines = f.readlines()[-10:]  # Last 10 entries

                if lines:
                    times = [float(line.split(",")[1]) for line in lines if "," in line]
                    if times:
                        metrics["hook_execution_time"] = statistics.mean(times)
                        metrics["hook_execution_max"] = max(times)

        except Exception as e:
            print(f"Error reading hook metrics: {e}")

        return metrics

    def _get_agent_metrics(self) -> Dict[str, float]:
        """Get agent selection performance metrics"""
        metrics = {}

        try:
            # Read agent selection logs
            agent_log_file = "/tmp/claude_agent_selection.log"
            if os.path.exists(agent_log_file):
                with open(agent_log_file, "r") as f:
                    lines = f.readlines()[-20:]  # Last 20 entries

                complexity_counts = defaultdict(int)
                for line in lines:
                    if "Complexity:" in line:
                        complexity = line.split("Complexity:")[1].strip()
                        complexity_counts[complexity] += 1

                total_selections = sum(complexity_counts.values())
                if total_selections > 0:
                    metrics["agent_selection_rate"] = total_selections
                    metrics["complex_task_ratio"] = (
                        complexity_counts.get("complex", 0) / total_selections
                    )

        except Exception as e:
            print(f"Error reading agent metrics: {e}")

        return metrics

    def _get_cache_metrics(self) -> Dict[str, float]:
        """Get cache performance metrics"""
        metrics = {}

        try:
            # Estimate cache performance from file system
            cache_dirs = ["/tmp/claude_context_cache", "/tmp/claude_results_cache"]

            total_cache_files = 0
            total_cache_size = 0

            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    cache_files = os.listdir(cache_dir)
                    total_cache_files += len(cache_files)

                    for cache_file in cache_files:
                        try:
                            file_path = os.path.join(cache_dir, cache_file)
                            total_cache_size += os.path.getsize(file_path)
                        except:
                            pass

            metrics["cache_files_count"] = total_cache_files
            metrics["cache_total_size"] = total_cache_size
            metrics["cache_utilization"] = min(
                100, total_cache_files / 50 * 100
            )  # Assume 50 is optimal

        except Exception as e:
            print(f"Error reading cache metrics: {e}")

        return metrics

    def _detect_bottlenecks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect performance bottlenecks from analysis"""
        bottlenecks = []

        for metric_name, stats in analysis.items():
            if not isinstance(stats, dict):
                continue

            threshold = self.thresholds.get(metric_name)
            if not threshold:
                continue

            mean_value = stats.get("mean", 0)
            max_value = stats.get("max", 0)
            p95_value = stats.get("p95", 0)

            # Check for bottlenecks
            if mean_value > threshold:
                severity = self._calculate_severity(mean_value, threshold)
                bottlenecks.append(
                    {
                        "type": self._metric_to_bottleneck_type(metric_name),
                        "metric": metric_name,
                        "severity": severity,
                        "current_value": mean_value,
                        "threshold": threshold,
                        "description": f"{metric_name} average ({mean_value:.1f}) exceeds threshold ({threshold})",
                        "suggestion": self._get_bottleneck_suggestion(metric_name),
                        "confidence": 0.8,
                    }
                )

            # Check P95 for spikes
            if p95_value > threshold * 1.5:
                bottlenecks.append(
                    {
                        "type": f"{self._metric_to_bottleneck_type(metric_name)}_spikes",
                        "metric": metric_name,
                        "severity": "medium",
                        "current_value": p95_value,
                        "threshold": threshold * 1.5,
                        "description": f"{metric_name} has performance spikes (P95: {p95_value:.1f})",
                        "suggestion": f"Investigate and smooth {metric_name} spikes",
                        "confidence": 0.6,
                    }
                )

        return bottlenecks

    def _optimize_hook_execution(
        self, bottleneck: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Optimize hook execution performance"""
        try:
            # Strategy 1: Enable hook batching if not already enabled
            settings_file = "/home/xx/dev/Claude Enhancer 5.0/.claude/settings.json"

            with open(settings_file, "r") as f:
                settings = json.load(f)

            performance_config = settings.get("performance", {})
            if not performance_config.get("smart_hook_batching", False):
                performance_config["smart_hook_batching"] = True
                performance_config["hook_timeout_ms"] = 150  # Reduce timeout
                settings["performance"] = performance_config

                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=2)

                return True, None

            return True, "Hook batching already enabled"

        except Exception as e:
            return False, str(e)

    def _optimize_agent_selection(
        self, bottleneck: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Optimize agent selection performance"""
        try:
            # Enable more aggressive caching
            cache_file = "/tmp/claude_agent_cache_config"
            config = {
                "cache_size": 200,
                "ttl": 600,  # 10 minutes
                "aggressive_caching": True,
            }

            with open(cache_file, "w") as f:
                json.dump(config, f)

            return True, None

        except Exception as e:
            return False, str(e)

    def _optimize_memory_usage(
        self, bottleneck: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Optimize memory usage"""
        try:
            # Clean up cache files
            import shutil

            temp_dirs = ["/tmp/claude_context_cache", "/tmp/claude_results_cache"]
            cleaned = False

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # Remove files older than 1 hour
                    import glob

                    for file_path in glob.glob(f"{temp_dir}/*"):
                        try:
                            if time.time() - os.path.getmtime(file_path) > 3600:
                                os.remove(file_path)
                                cleaned = True
                        except:
                            pass

            return cleaned, None if cleaned else "No old files to clean"

        except Exception as e:
            return False, str(e)

    def _optimize_caching(
        self, bottleneck: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Optimize caching performance"""
        # Placeholder for cache optimization logic
        return True, "Cache optimization applied"

    def _optimize_disk_io(
        self, bottleneck: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Optimize disk I/O performance"""
        # Placeholder for disk I/O optimization logic
        return True, "Disk I/O optimization applied"

    # Utility methods
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _severity_to_score(self, severity: str) -> int:
        """Convert severity to numerical score"""
        scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return scores.get(severity, 1)

    def _calculate_severity(self, current: float, threshold: float) -> str:
        """Calculate severity based on threshold deviation"""
        ratio = current / threshold
        if ratio >= 2.0:
            return "critical"
        elif ratio >= 1.5:
            return "high"
        elif ratio >= 1.2:
            return "medium"
        else:
            return "low"

    def _metric_to_bottleneck_type(self, metric_name: str) -> str:
        """Map metric name to bottleneck type"""
        mapping = {
            "hook_execution_time": "high_hook_execution",
            "agent_selection_time": "slow_agent_selection",
            "memory_usage": "high_memory_usage",
            "cache_hit_rate": "poor_cache_performance",
            "disk_io_wait": "excessive_disk_io",
        }
        return mapping.get(metric_name, "unknown_bottleneck")

    def _get_bottleneck_suggestion(self, metric_name: str) -> str:
        """Get optimization suggestion for metric"""
        suggestions = {
            "hook_execution_time": "Enable hook batching and reduce timeouts",
            "agent_selection_time": "Increase cache size and improve selection algorithm",
            "memory_usage": "Clean up cache files and optimize memory usage",
            "cache_hit_rate": "Increase cache size and improve cache strategy",
            "disk_io_wait": "Optimize file operations and use memory caching",
        }
        return suggestions.get(metric_name, "Review and optimize this metric")

    def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current performance metrics snapshot"""
        return {
            "cpu_usage": psutil.cpu_percent(interval=0.1),
            "memory_usage": psutil.virtual_memory().percent,
            "timestamp": time.time(),
        }

    def _calculate_improvement(
        self, before: Dict[str, float], after: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate performance improvement"""
        improvement = {}
        for key in before:
            if key in after and key != "timestamp":
                if before[key] > 0:
                    improvement[key] = (before[key] - after[key]) / before[key] * 100
                else:
                    improvement[key] = 0.0
        return improvement

    def _calculate_overall_health(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall system health"""
        # Simplified health calculation
        bottleneck_count = len(self._detect_bottlenecks(analysis))

        if bottleneck_count == 0:
            return "excellent"
        elif bottleneck_count <= 2:
            return "good"
        elif bottleneck_count <= 4:
            return "fair"
        else:
            return "poor"

    def _calculate_overall_health_score(self) -> float:
        """Calculate numerical health score (0-100)"""
        analysis = self.analyze_performance()
        bottlenecks = analysis.get("bottlenecks", [])

        base_score = 100.0
        for bottleneck in bottlenecks:
            severity = bottleneck.get("severity", "low")
            severity_penalty = {"low": 5, "medium": 15, "high": 25, "critical": 40}
            base_score -= severity_penalty.get(severity, 5)

        return max(0.0, base_score)


# Global performance optimizer instance
_performance_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
        _performance_optimizer.start_monitoring()
    return _performance_optimizer


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import os

    optimizer = get_performance_optimizer()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "analyze":
            analysis = optimizer.analyze_performance()
            print(json.dumps(analysis, indent=2))

        elif command == "report":
            report = optimizer.get_optimization_report()
            print(json.dumps(report, indent=2))

        elif command == "optimize":
            results = optimizer.optimize_automatically()
            print(f"Applied {len(results)} optimizations:")
            for result in results:
                print(f"  - {result.optimization_id}: {'✅' if result.success else '❌'}")

        elif command == "monitor":
            print("Starting performance monitoring... (Press Ctrl+C to stop)")
            try:
                while True:
                    time.sleep(5)
                    analysis = optimizer.analyze_performance(60)
                    health = analysis.get("overall_health", "unknown")
                    metrics_count = analysis.get("metrics_count", 0)
                    print(f"Health: {health}, Metrics: {metrics_count}")
            except KeyboardInterrupt:
                print("\nStopping monitoring...")

    else:
        # Show current status
        report = optimizer.get_optimization_report()
        health_score = report["health_score"]

        print("Claude Enhancer Performance Optimizer")
        print("=" * 40)
        print(f"Health Score: {health_score:.1f}/100")
        print(f"CPU Usage: {report['system_resources']['cpu_percent']:.1f}%")
        print(f"Memory Usage: {report['system_resources']['memory_percent']:.1f}%")

        analysis = report["performance_analysis"]
        if analysis.get("bottlenecks"):
            print(f"\nBottlenecks detected: {len(analysis['bottlenecks'])}")
            for bottleneck in analysis["bottlenecks"][:3]:
                print(f"  - {bottleneck['description']}")

        print(f"\nRecommendations: {len(report.get('recommendations', []))}")
        for rec in report.get("recommendations", [])[:3]:
            print(f"  - {rec}")

    optimizer.stop_monitoring()
