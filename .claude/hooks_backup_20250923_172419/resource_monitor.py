#!/usr/bin/env python3
"""
Resource Monitor for Claude Enhancer
Monitors and optimizes system resource usage
"""

import os
import sys
import time
import psutil
import threading
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import signal
from dataclasses import dataclass
from collections import deque

@dataclass
class ResourceSnapshot:
    """Resource usage snapshot"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    io_read: int
    io_write: int
    open_files: int
    threads: int

class ResourceMonitor:
    """Monitor and optimize system resource usage"""

    def __init__(self, alert_cpu: float = 80.0, alert_memory: float = 85.0):
        self.alert_cpu = alert_cpu
        self.alert_memory = alert_memory

        # Resource history (last 100 snapshots)
        self.history = deque(maxlen=100)

        # Performance tracking
        self.claude_processes = []
        self.hook_processes = []

        # Optimization flags
        self.optimization_enabled = True
        self.auto_cleanup = True

        # Monitor thread
        self.monitor_thread = None
        self.monitoring = False

        # Start monitoring
        self.start_monitoring()

    def start_monitoring(self):
        """Start resource monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="ResourceMonitor"
            )
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Take resource snapshot
                snapshot = self._take_snapshot()
                self.history.append(snapshot)

                # Check for alerts
                self._check_alerts(snapshot)

                # Update process lists
                self._update_process_lists()

                # Auto-optimization
                if self.optimization_enabled:
                    self._auto_optimize()

                time.sleep(5)  # Monitor every 5 seconds

            except Exception:
                pass  # Silent fail to maintain stability

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take current resource snapshot"""
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Current process metrics
            current_process = psutil.Process()
            io_counters = current_process.io_counters()

            return ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory.used / 1024 / 1024,
                memory_percent=memory.percent,
                io_read=io_counters.read_bytes,
                io_write=io_counters.write_bytes,
                open_files=current_process.num_fds() if hasattr(current_process, 'num_fds') else 0,
                threads=current_process.num_threads()
            )
        except:
            # Return empty snapshot on error
            return ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=0, memory_mb=0, memory_percent=0,
                io_read=0, io_write=0, open_files=0, threads=0
            )

    def _check_alerts(self, snapshot: ResourceSnapshot):
        """Check for resource alerts"""
        if snapshot.cpu_percent > self.alert_cpu:
            self._handle_cpu_alert(snapshot)

        if snapshot.memory_percent > self.alert_memory:
            self._handle_memory_alert(snapshot)

        # Check for excessive file handles
        if snapshot.open_files > 1000:
            self._handle_file_alert(snapshot)

    def _handle_cpu_alert(self, snapshot: ResourceSnapshot):
        """Handle high CPU usage"""
    # print(f"⚠️ High CPU usage: {snapshot.cpu_percent:.1f}%", file=sys.stderr)

        # Find CPU-intensive Claude processes
        cpu_hogs = self._find_cpu_intensive_processes()
        if cpu_hogs:
    # print(f"Top CPU consumers: {cpu_hogs}", file=sys.stderr)

    def _handle_memory_alert(self, snapshot: ResourceSnapshot):
        """Handle high memory usage"""
    # print(f"⚠️ High memory usage: {snapshot.memory_percent:.1f}%", file=sys.stderr)

        # Trigger cleanup
        if self.auto_cleanup:
            self._cleanup_resources()

    def _handle_file_alert(self, snapshot: ResourceSnapshot):
        """Handle excessive file handles"""
    # print(f"⚠️ High file handle usage: {snapshot.open_files}", file=sys.stderr)

        # Cleanup temporary files
        self._cleanup_temp_files()

    def _update_process_lists(self):
        """Update lists of Claude-related processes"""
        try:
            self.claude_processes = []
            self.hook_processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()

                    if 'claude' in name or 'claude' in cmdline:
                        self.claude_processes.append(proc)

                    if any(hook in cmdline for hook in ['hook', 'validator', 'dispatcher']):
                        self.hook_processes.append(proc)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass

    def _find_cpu_intensive_processes(self) -> List[str]:
        """Find CPU-intensive processes"""
        cpu_hogs = []

        for proc in self.claude_processes + self.hook_processes:
            try:
                cpu_percent = proc.cpu_percent()
                if cpu_percent > 10:  # More than 10% CPU
                    cpu_hogs.append(f"{proc.info['name']}({proc.pid}): {cpu_percent:.1f}%")
            except:
                continue

        return cpu_hogs[:5]  # Top 5

    def _auto_optimize(self):
        """Perform automatic optimizations"""
        if len(self.history) < 10:
            return

        # Get recent resource usage trend
        recent = list(self.history)[-10:]
        avg_cpu = sum(s.cpu_percent for s in recent) / len(recent)
        avg_memory = sum(s.memory_percent for s in recent) / len(recent)

        # Optimize if consistently high usage
        if avg_cpu > 70 or avg_memory > 75:
            self._optimize_performance()

    def _optimize_performance(self):
        """Optimize system performance"""
        optimizations = []

        # 1. Cleanup temporary files
        cleaned = self._cleanup_temp_files()
        if cleaned > 0:
            optimizations.append(f"Cleaned {cleaned} temp files")

        # 2. Reduce hook process priority
        self._reduce_hook_priority()
        optimizations.append("Reduced hook process priority")

        # 3. Clear system caches
        self._clear_system_caches()
        optimizations.append("Cleared system caches")

        if optimizations:
    # print(f"🔧 Auto-optimization: {', '.join(optimizations)}", file=sys.stderr)

    def _cleanup_resources(self):
        """Cleanup system resources"""
        # Close unused file handles
        self._close_unused_handles()

        # Clear Python caches
        import gc
        gc.collect()

        # Clear temporary files
        self._cleanup_temp_files()

    def _cleanup_temp_files(self) -> int:
        """Cleanup temporary files"""
        temp_dirs = ['/tmp', '/var/tmp']
        claude_patterns = ['claude', 'enhancer', 'hook']

        cleaned_count = 0
        cutoff_time = time.time() - 3600  # 1 hour old

        for temp_dir in temp_dirs:
            try:
                temp_path = Path(temp_dir)
                for file_path in temp_path.glob('*'):
                    if (file_path.is_file() and
                        file_path.stat().st_mtime < cutoff_time and
                        any(pattern in file_path.name.lower() for pattern in claude_patterns)):
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except:
                            continue
            except:
                continue

        return cleaned_count

    def _close_unused_handles(self):
        """Close unused file handles"""
        try:
            current_process = psutil.Process()
            # Force garbage collection to close Python file handles
            import gc
            gc.collect()
        except:
            pass

    def _reduce_hook_priority(self):
        """Reduce priority of hook processes"""
        for proc in self.hook_processes:
            try:
                proc.nice(5)  # Lower priority
            except:
                continue

    def _clear_system_caches(self):
        """Clear system caches"""
        try:
            # Clear page cache (Linux only)
            if os.path.exists('/proc/sys/vm/drop_caches'):
                os.system('echo 1 > /proc/sys/vm/drop_caches 2>/dev/null')
        except:
            pass

    def get_resource_summary(self) -> Dict:
        """Get resource usage summary"""
        if not self.history:
            return {}

        latest = self.history[-1]

        # Calculate averages over last 60 seconds
        recent = [s for s in self.history if (latest.timestamp - s.timestamp) <= 60]

        if not recent:
            recent = [latest]

        avg_cpu = sum(s.cpu_percent for s in recent) / len(recent)
        avg_memory = sum(s.memory_percent for s in recent) / len(recent)

        return {
            'current': {
                'cpu_percent': latest.cpu_percent,
                'memory_percent': latest.memory_percent,
                'memory_mb': latest.memory_mb,
                'open_files': latest.open_files,
                'threads': latest.threads
            },
            'averages_60s': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory
            },
            'processes': {
                'claude_count': len(self.claude_processes),
                'hook_count': len(self.hook_processes)
            },
            'alerts': {
                'cpu_alert': latest.cpu_percent > self.alert_cpu,
                'memory_alert': latest.memory_percent > self.alert_memory,
                'file_alert': latest.open_files > 1000
            }
        }

    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations"""
        recommendations = []
        summary = self.get_resource_summary()

        if not summary:
            return recommendations

        current = summary['current']

        if current['cpu_percent'] > 80:
            recommendations.append("Consider reducing hook frequency or complexity")

        if current['memory_percent'] > 85:
            recommendations.append("Enable aggressive caching cleanup")
            recommendations.append("Reduce buffer sizes in logging")

        if current['open_files'] > 500:
            recommendations.append("Enable automatic file handle cleanup")

        if summary['processes']['hook_count'] > 10:
            recommendations.append("Consolidate hook processes")

        if not recommendations:
            recommendations.append("System performance is optimal")

        return recommendations

# Global monitor instance
_resource_monitor = None

def get_resource_monitor():
    """Get global resource monitor instance"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor

def cleanup_system_resources():
    """Manual resource cleanup"""
    monitor = get_resource_monitor()
    monitor._cleanup_resources()

def get_system_status():
    """Get current system status"""
    monitor = get_resource_monitor()
    return monitor.get_resource_summary()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            status = get_system_status()
    # print(json.dumps(status, indent=2))
        elif command == "cleanup":
            cleanup_system_resources()
    # print("Resources cleaned up")
        elif command == "recommendations":
            monitor = get_resource_monitor()
            recommendations = monitor.get_optimization_recommendations()
            for rec in recommendations:
    # print(f"• {rec}")
        elif command == "monitor":
            # Interactive monitoring mode
            monitor = get_resource_monitor()
            try:
                while True:
                    status = monitor.get_resource_summary()
                    if status:
    # print(f"\rCPU: {status['current']['cpu_percent']:5.1f}% | "
                              f"Memory: {status['current']['memory_percent']:5.1f}% | "
                              f"Files: {status['current']['open_files']:4d} | "
                              f"Threads: {status['current']['threads']:3d}", end='')
                    time.sleep(1)
            except KeyboardInterrupt:
    # print("\nMonitoring stopped")
    else:
        # Start monitoring in background
        monitor = get_resource_monitor()
    # print("Resource monitoring started")