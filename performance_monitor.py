#!/usr/bin/env python3
"""
Claude Enhancer 5.0 实时性能监控脚本
"""

import time
import psutil
import json
from pathlib import Path
from datetime import datetime
import sys

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.metrics = []

    def collect_metrics(self):
        """收集性能指标"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metric = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / 1024**3,
            'disk_percent': disk.used / disk.total * 100,
            'uptime': time.time() - self.start_time
        }

        self.metrics.append(metric)
        return metric

    def display_metrics(self, metric):
        """显示性能指标"""
        print(f"\r🚀 Claude Enhancer 5.0 性能监控")
        print(f"⏱️  运行时间: {metric['uptime']:.1f}s")
        print(f"💾 CPU使用率: {metric['cpu_percent']:.1f}%")
        print(f"🧠 内存使用率: {metric['memory_percent']:.1f}%")
        print(f"💿 磁盘使用率: {metric['disk_percent']:.1f}%")
        print("─" * 50)

    def save_metrics(self, filename="performance_metrics.json"):
        """保存性能指标到文件"""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        print(f"📊 性能数据已保存到: {filename}")

    def run_continuous_monitoring(self, duration=300):
        """持续监控指定时间（秒）"""
        end_time = time.time() + duration

        try:
            while time.time() < end_time:
                metric = self.collect_metrics()
                self.display_metrics(metric)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n📊 监控已停止")
        finally:
            self.save_metrics()

if __name__ == "__main__":
    monitor = PerformanceMonitor()

    if len(sys.argv) > 1:
        duration = int(sys.argv[1])
    else:
        duration = 300  # 默认5分钟

    print(f"🚀 开始性能监控 ({duration}秒)...")
    monitor.run_continuous_monitoring(duration)
