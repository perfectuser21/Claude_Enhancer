#!/usr/bin/env python3
"""
Perfect21 实时性能监控脚本
展示系统实时性能状况和优化效果
"""

import os
import sys
import time
import psutil
import json
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

class RealTimePerformanceMonitor:
    """实时性能监控器"""

    def __init__(self):
        self.start_time = time.time()
        self.baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        self.history = []

    def collect_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_memory = psutil.virtual_memory()

        # Perfect21特定指标
        perfect21_metrics = {}
        try:
            from modules.performance_optimizer import get_performance_optimizer
            optimizer = get_performance_optimizer()
            perfect21_metrics = optimizer.get_comprehensive_metrics()
        except Exception as e:
            perfect21_metrics = {'error': str(e)}

        return {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'uptime': time.time() - self.start_time,
            'system': {
                'cpu_percent': cpu_percent,
                'cpu_cores': psutil.cpu_count(logical=False),
                'memory_percent': system_memory.percent,
                'memory_available_gb': system_memory.available / 1024 / 1024 / 1024,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            },
            'process': {
                'memory_rss_mb': memory_info.rss / 1024 / 1024,
                'memory_vms_mb': memory_info.vms / 1024 / 1024,
                'memory_growth_mb': (memory_info.rss / 1024 / 1024) - self.baseline_memory,
                'num_threads': process.num_threads(),
                'cpu_times': process.cpu_times()._asdict(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0
            },
            'perfect21': perfect21_metrics
        }

    def display_dashboard(self, metrics: Dict[str, Any]):
        """显示性能仪表板"""
        # 清屏
        os.system('clear' if os.name == 'posix' else 'cls')

        print("🚀 Perfect21 实时性能监控")
        print("=" * 80)
        print(f"时间: {metrics['timestamp']} | 运行时间: {metrics['uptime']:.1f}秒")
        print()

        # 系统指标
        sys_metrics = metrics['system']
        print("🖥️  系统性能:")
        print(f"  CPU使用率: {sys_metrics['cpu_percent']:5.1f}% | 核心数: {sys_metrics['cpu_cores']}")
        print(f"  内存使用: {sys_metrics['memory_percent']:5.1f}% | 可用: {sys_metrics['memory_available_gb']:.1f}GB")
        if sys_metrics['load_average'][0] > 0:
            print(f"  负载均值: {sys_metrics['load_average'][0]:.2f} {sys_metrics['load_average'][1]:.2f} {sys_metrics['load_average'][2]:.2f}")

        # 进程指标
        proc_metrics = metrics['process']
        print()
        print("🔧 进程性能:")
        print(f"  RSS内存: {proc_metrics['memory_rss_mb']:6.1f}MB | 增长: {proc_metrics['memory_growth_mb']:+6.1f}MB")
        print(f"  VMS内存: {proc_metrics['memory_vms_mb']:6.1f}MB | 线程数: {proc_metrics['num_threads']}")
        print(f"  文件描述符: {proc_metrics['num_fds']}")

        # Perfect21指标
        p21_metrics = metrics['perfect21']
        print()
        print("⚡ Perfect21优化器:")
        if 'error' in p21_metrics:
            print(f"  ❌ 优化器未运行: {p21_metrics['error']}")
        else:
            if 'thread_pool' in p21_metrics:
                tp = p21_metrics['thread_pool']
                print(f"  线程池: {tp.get('current_workers', 0)}个工作线程")
                print(f"  平均CPU: {tp.get('avg_cpu_usage', 0):.1f}% | 内存: {tp.get('avg_memory_usage', 0):.1f}%")

            if 'cache' in p21_metrics:
                cache = p21_metrics['cache']
                print(f"  缓存命中率: {cache.get('hit_rate', 0):.1f}% | L1: {cache.get('l1_size', 0)} L2: {cache.get('l2_size', 0)}")

            if 'memory' in p21_metrics:
                mem = p21_metrics['memory']
                threshold_status = "⚠️ 超阈值" if mem.get('threshold_exceeded', False) else "✅ 正常"
                print(f"  内存状态: {threshold_status}")

        # 性能评级
        performance_grade = self.calculate_performance_grade(metrics)
        grade_color = self.get_grade_color(performance_grade)
        print()
        print(f"📊 性能评级: {grade_color}{performance_grade}📊")

        # 历史趋势（最近10个数据点）
        if len(self.history) > 1:
            print()
            print("📈 性能趋势 (最近10个点):")
            recent_history = self.history[-10:]
            cpu_trend = [m['system']['cpu_percent'] for m in recent_history]
            memory_trend = [m['process']['memory_rss_mb'] for m in recent_history]

            print(f"  CPU:    {self.format_trend(cpu_trend, '%')}")
            print(f"  内存:   {self.format_trend(memory_trend, 'MB')}")

        print()
        print("按 Ctrl+C 退出监控")
        print("=" * 80)

    def format_trend(self, values: list, unit: str) -> str:
        """格式化趋势数据"""
        if len(values) < 2:
            return "数据不足"

        trend_chars = []
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                trend_chars.append('↗')
            elif values[i] < values[i-1]:
                trend_chars.append('↘')
            else:
                trend_chars.append('→')

        latest = values[-1]
        trend_str = ''.join(trend_chars[-8:])  # 最近8个变化

        return f"{latest:6.1f}{unit} {trend_str}"

    def calculate_performance_grade(self, metrics: Dict[str, Any]) -> str:
        """计算性能评级"""
        score = 100

        # CPU使用率评分
        cpu_usage = metrics['system']['cpu_percent']
        if cpu_usage > 80:
            score -= 30
        elif cpu_usage > 60:
            score -= 15
        elif cpu_usage > 40:
            score -= 5

        # 内存使用率评分
        memory_usage = metrics['system']['memory_percent']
        if memory_usage > 90:
            score -= 25
        elif memory_usage > 80:
            score -= 15
        elif memory_usage > 70:
            score -= 5

        # 进程内存增长评分
        memory_growth = metrics['process']['memory_growth_mb']
        if memory_growth > 100:
            score -= 20
        elif memory_growth > 50:
            score -= 10

        # 返回等级
        if score >= 90:
            return "A+ (优秀)"
        elif score >= 80:
            return "A  (良好)"
        elif score >= 70:
            return "B  (中等)"
        elif score >= 60:
            return "C  (及格)"
        else:
            return "D  (需改进)"

    def get_grade_color(self, grade: str) -> str:
        """获取等级颜色"""
        if "A+" in grade:
            return "🟢 "
        elif "A" in grade:
            return "🔵 "
        elif "B" in grade:
            return "🟡 "
        elif "C" in grade:
            return "🟠 "
        else:
            return "🔴 "

    def save_metrics_log(self, metrics: Dict[str, Any]):
        """保存指标日志"""
        log_file = f"performance_log_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                json.dump(metrics, f, default=str)
                f.write('\n')
        except Exception as e:
            print(f"保存日志失败: {e}")

    def run_monitor(self, interval: float = 2.0, save_log: bool = False):
        """运行实时监控"""
        print("🚀 启动Perfect21实时性能监控...")
        print(f"监控间隔: {interval}秒")
        if save_log:
            print("📝 性能日志将保存到文件")
        print("按 Ctrl+C 停止监控")
        print()

        try:
            while True:
                # 收集指标
                metrics = self.collect_metrics()
                self.history.append(metrics)

                # 保持历史记录在合理大小
                if len(self.history) > 100:
                    self.history = self.history[-100:]

                # 显示仪表板
                self.display_dashboard(metrics)

                # 保存日志
                if save_log:
                    self.save_metrics_log(metrics)

                # 等待下一次采集
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 性能监控已停止")
            print(f"📊 总运行时间: {time.time() - self.start_time:.1f}秒")
            print(f"📈 收集了 {len(self.history)} 个数据点")

            # 显示性能汇总
            if self.history:
                self.show_performance_summary()

    def show_performance_summary(self):
        """显示性能汇总"""
        print("\n📊 性能汇总报告:")
        print("=" * 50)

        cpu_values = [m['system']['cpu_percent'] for m in self.history]
        memory_values = [m['process']['memory_rss_mb'] for m in self.history]

        print(f"CPU使用率:")
        print(f"  平均: {sum(cpu_values)/len(cpu_values):.1f}%")
        print(f"  最高: {max(cpu_values):.1f}%")
        print(f"  最低: {min(cpu_values):.1f}%")

        print(f"进程内存:")
        print(f"  平均: {sum(memory_values)/len(memory_values):.1f}MB")
        print(f"  峰值: {max(memory_values):.1f}MB")
        print(f"  最低: {min(memory_values):.1f}MB")

        # 稳定性分析
        cpu_variance = sum((x - sum(cpu_values)/len(cpu_values))**2 for x in cpu_values) / len(cpu_values)
        stability = "稳定" if cpu_variance < 100 else "波动较大"
        print(f"系统稳定性: {stability} (方差: {cpu_variance:.1f})")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Perfect21实时性能监控')
    parser.add_argument('--interval', '-i', type=float, default=2.0, help='监控间隔(秒)')
    parser.add_argument('--save-log', '-s', action='store_true', help='保存性能日志')
    parser.add_argument('--duration', '-d', type=int, help='监控持续时间(秒)')

    args = parser.parse_args()

    monitor = RealTimePerformanceMonitor()

    if args.duration:
        print(f"监控将在{args.duration}秒后自动停止")
        import threading
        timer = threading.Timer(args.duration, lambda: os._exit(0))
        timer.start()

    monitor.run_monitor(interval=args.interval, save_log=args.save_log)