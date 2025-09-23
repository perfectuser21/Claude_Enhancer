#!/usr/bin/env python3
"""
Claude Enhancer 系统性能分析工具
完整测试所有performance相关脚本的执行时间和效率
"""

import os
import time
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
import statistics


class PerformanceAnalyzer:
    def __init__(self, claude_dir="/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = Path(claude_dir)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "test_results": {},
            "summary": {},
            "recommendations": [],
        }

    def get_system_info(self):
        """获取系统信息"""
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpu_info = f.read()
            cpu_count = cpu_info.count("processor")

            with open("/proc/meminfo", "r") as f:
                mem_info = f.read()
            mem_total = (
                int(
                    [line for line in mem_info.split("\n") if "MemTotal" in line][
                        0
                    ].split()[1]
                )
                // 1024
            )

            return {
                "cpu_cores": cpu_count,
                "memory_mb": mem_total,
                "python_version": sys.version,
                "os": os.uname().sysname,
            }
        except Exception as e:
            return {"error": str(e)}

    def measure_execution_time(self, command, description="", runs=3):
        """测量命令执行时间（多次运行取平均值）"""
        times = []
        success_count = 0

        for i in range(runs):
            try:
                start_time = time.perf_counter()
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.claude_dir.parent,
                )
                end_time = time.perf_counter()

                execution_time = end_time - start_time
                times.append(execution_time)

                if result.returncode == 0:
                    success_count += 1

            except subprocess.TimeoutExpired:
                times.append(60.0)  # 超时记为60秒
            except Exception as e:
                print(f"执行错误 {command}: {e}")
                times.append(float("inf"))

        if times:
            avg_time = statistics.mean([t for t in times if t != float("inf")])
            min_time = (
                min([t for t in times if t != float("inf")])
                if any(t != float("inf") for t in times)
                else 0
            )
            max_time = (
                max([t for t in times if t != float("inf")])
                if any(t != float("inf") for t in times)
                else 0
            )
        else:
            avg_time = min_time = max_time = 0

        return {
            "description": description,
            "command": command,
            "runs": runs,
            "success_rate": success_count / runs,
            "avg_time": round(avg_time, 4),
            "min_time": round(min_time, 4),
            "max_time": round(max_time, 4),
            "all_times": [round(t, 4) for t in times],
        }

    def test_cleanup_scripts(self):
        """测试所有cleanup脚本版本"""
        cleanup_scripts = [
            (".claude/scripts/cleanup.sh", "标准清理脚本"),
            (".claude/scripts/performance_optimized_cleanup.sh", "性能优化清理脚本"),
            (".claude/scripts/ultra_optimized_cleanup.sh", "超级优化清理脚本"),
            (".claude/scripts/safe_cleanup.sh", "安全清理脚本"),
        ]

        results = {}
        for script_path, description in cleanup_scripts:
            full_path = self.claude_dir.parent / script_path
            if full_path.exists():
                # 确保脚本可执行
                os.chmod(full_path, 0o755)
                command = f"bash {full_path}"
                results[script_path] = self.measure_execution_time(command, description)
            else:
                results[script_path] = {"error": "文件不存在"}

        return results

    def test_performance_scripts(self):
        """测试性能相关脚本"""
        performance_scripts = [
            (".claude/scripts/performance_benchmark.sh", "性能基准测试"),
            (".claude/scripts/ultra_performance_benchmark.sh", "超级性能基准测试"),
            (".claude/scripts/quick_performance_test.sh", "快速性能测试"),
            (".claude/scripts/performance_comparison.sh", "性能对比测试"),
            (".claude/scripts/performance_monitor.sh", "性能监控脚本"),
        ]

        results = {}
        for script_path, description in performance_scripts:
            full_path = self.claude_dir.parent / script_path
            if full_path.exists():
                os.chmod(full_path, 0o755)
                command = f"bash {full_path}"
                results[script_path] = self.measure_execution_time(command, description)
            else:
                results[script_path] = {"error": "文件不存在"}

        return results

    def test_python_scripts(self):
        """测试Python性能脚本"""
        python_scripts = [
            (".claude/hooks/parallel_execution_optimizer.py", "并行执行优化器"),
            (".claude/hooks/performance_test.py", "性能测试脚本"),
            (".claude/scripts/smart_document_loader.py", "智能文档加载器"),
        ]

        results = {}
        for script_path, description in python_scripts:
            full_path = self.claude_dir.parent / script_path
            if full_path.exists():
                command = f"python3 {full_path} --test"
                results[script_path] = self.measure_execution_time(command, description)
            else:
                results[script_path] = {"error": "文件不存在"}

        return results

    def test_hook_system(self):
        """测试Hook系统响应时间"""
        hook_scripts = [
            (".claude/hooks/smart_agent_selector.sh", "智能Agent选择器"),
            (".claude/hooks/ultra_smart_agent_selector.sh", "超级智能Agent选择器"),
            (".claude/hooks/smart_dispatcher.py", "智能调度器"),
            (".claude/hooks/enforcer.sh", "强制执行器"),
        ]

        results = {}
        for script_path, description in hook_scripts:
            full_path = self.claude_dir.parent / script_path
            if full_path.exists():
                if script_path.endswith(".py"):
                    command = f"python3 {full_path} --dry-run"
                else:
                    os.chmod(full_path, 0o755)
                    command = f"bash {full_path} --test"
                results[script_path] = self.measure_execution_time(
                    command, description, runs=5
                )
            else:
                results[script_path] = {"error": "文件不存在"}

        return results

    def test_system_startup(self):
        """测试系统启动时间"""
        startup_commands = [
            ("source .claude/scripts/load_config.sh", "配置加载"),
            ("bash .claude/install.sh --dry-run", "安装脚本"),
            ("python3 .claude/scripts/config_validator.py", "配置验证"),
        ]

        results = {}
        for command, description in startup_commands:
            results[command] = self.measure_execution_time(command, description)

        return results

    def analyze_file_sizes(self):
        """分析文件大小和数量"""
        file_stats = {
            "total_files": 0,
            "total_size_mb": 0,
            "largest_files": [],
            "file_types": {},
        }

        try:
            for root, dirs, files in os.walk(self.claude_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        size = file_path.stat().st_size
                        file_stats["total_files"] += 1
                        file_stats["total_size_mb"] += size / (1024 * 1024)

                        # 记录最大的文件
                        file_stats["largest_files"].append((str(file_path), size))

                        # 统计文件类型
                        ext = file_path.suffix.lower()
                        if ext in file_stats["file_types"]:
                            file_stats["file_types"][ext] += 1
                        else:
                            file_stats["file_types"][ext] = 1

                    except OSError:
                        continue

            # 排序最大文件
            file_stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
            file_stats["largest_files"] = file_stats["largest_files"][:10]
            file_stats["total_size_mb"] = round(file_stats["total_size_mb"], 2)

        except Exception as e:
            file_stats["error"] = str(e)

        return file_stats

    def generate_recommendations(self):
        """生成性能优化建议"""
        recommendations = []

        # 分析cleanup脚本性能
        cleanup_results = self.results["test_results"].get("cleanup_scripts", {})
        cleanup_times = {}
        for script, result in cleanup_results.items():
            if isinstance(result, dict) and "avg_time" in result:
                cleanup_times[script] = result["avg_time"]

        if cleanup_times:
            fastest = min(cleanup_times, key=cleanup_times.get)
            slowest = max(cleanup_times, key=cleanup_times.get)
            recommendations.append(
                {
                    "category": "Cleanup Scripts",
                    "issue": f"最慢的cleanup脚本: {slowest} ({cleanup_times[slowest]:.4f}s)",
                    "recommendation": f"建议使用最快的脚本: {fastest} ({cleanup_times[fastest]:.4f}s)",
                    "priority": "medium",
                }
            )

        # 分析Hook响应时间
        hook_results = self.results["test_results"].get("hook_system", {})
        slow_hooks = []
        for script, result in hook_results.items():
            if (
                isinstance(result, dict)
                and "avg_time" in result
                and result["avg_time"] > 1.0
            ):
                slow_hooks.append((script, result["avg_time"]))

        if slow_hooks:
            recommendations.append(
                {
                    "category": "Hook System",
                    "issue": f"发现{len(slow_hooks)}个慢速Hook (>1s)",
                    "recommendation": "优化这些Hook的执行逻辑，考虑异步执行",
                    "details": slow_hooks,
                    "priority": "high",
                }
            )

        # 分析文件系统
        file_stats = self.results["test_results"].get("file_analysis", {})
        if file_stats.get("total_size_mb", 0) > 50:
            recommendations.append(
                {
                    "category": "File System",
                    "issue": f"Claude目录大小: {file_stats['total_size_mb']}MB",
                    "recommendation": "清理不必要的文件，压缩大文件",
                    "priority": "low",
                }
            )

        return recommendations

    def run_full_analysis(self):
        """运行完整的性能分析"""
        print("🚀 开始Claude Enhancer性能分析...")
        print("=" * 60)

        # 1. 测试cleanup脚本
        print("📁 测试Cleanup脚本...")
        self.results["test_results"]["cleanup_scripts"] = self.test_cleanup_scripts()

        # 2. 测试性能脚本
        print("⚡ 测试Performance脚本...")
        self.results["test_results"][
            "performance_scripts"
        ] = self.test_performance_scripts()

        # 3. 测试Python脚本
        print("🐍 测试Python脚本...")
        self.results["test_results"]["python_scripts"] = self.test_python_scripts()

        # 4. 测试Hook系统
        print("🔗 测试Hook系统...")
        self.results["test_results"]["hook_system"] = self.test_hook_system()

        # 5. 测试系统启动
        print("🚀 测试系统启动...")
        self.results["test_results"]["system_startup"] = self.test_system_startup()

        # 6. 分析文件系统
        print("📊 分析文件系统...")
        self.results["test_results"]["file_analysis"] = self.analyze_file_sizes()

        # 7. 生成建议
        print("💡 生成优化建议...")
        self.results["recommendations"] = self.generate_recommendations()

        # 8. 计算总结
        self.calculate_summary()

        print("✅ 性能分析完成!")
        return self.results

    def calculate_summary(self):
        """计算总结统计"""
        all_times = []
        script_count = 0
        success_count = 0

        for category, tests in self.results["test_results"].items():
            if category == "file_analysis":
                continue

            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and "avg_time" in result:
                        all_times.append(result["avg_time"])
                        script_count += 1
                        if result.get("success_rate", 0) > 0.5:
                            success_count += 1

        if all_times:
            self.results["summary"] = {
                "total_scripts_tested": script_count,
                "successful_scripts": success_count,
                "success_rate": round(success_count / script_count, 2),
                "avg_execution_time": round(statistics.mean(all_times), 4),
                "fastest_script": round(min(all_times), 4),
                "slowest_script": round(max(all_times), 4),
                "total_test_duration": round(sum(all_times), 2),
            }

    def save_results(self, filename="claude_enhancer_performance_report.json"):
        """保存结果到文件"""
        report_path = self.claude_dir.parent / filename
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"📄 报告已保存到: {report_path}")
        return report_path


def main():
    analyzer = PerformanceAnalyzer()
    results = analyzer.run_full_analysis()
    report_path = analyzer.save_results()

    # 打印简要总结
    print("\n" + "=" * 60)
    print("📊 性能分析总结")
    print("=" * 60)

    summary = results.get("summary", {})
    if summary:
        print(f"测试脚本总数: {summary.get('total_scripts_tested', 0)}")
        print(f"成功率: {summary.get('success_rate', 0) * 100:.1f}%")
        print(f"平均执行时间: {summary.get('avg_execution_time', 0):.4f}s")
        print(f"最快脚本: {summary.get('fastest_script', 0):.4f}s")
        print(f"最慢脚本: {summary.get('slowest_script', 0):.4f}s")

    print(f"\n💡 发现 {len(results.get('recommendations', []))} 个优化建议")

    return report_path


if __name__ == "__main__":
    main()
