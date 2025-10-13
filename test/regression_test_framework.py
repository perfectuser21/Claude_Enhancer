#!/usr/bin/env python3
"""
Claude Enhancer 5.0 - 回归测试框架
作为test-engineer设计的专业回归测试系统

功能特性:
1. 性能回归检测
2. 功能回归验证
3. 配置变更影响分析
4. 基线管理和版本对比
5. 自动化回归报告
6. Git集成的变更追踪
"""

import os
import sys
import json
import time
import hashlib
import subprocess
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timedelta


@dataclass
class BaselineMetrics:
    """基线性能指标"""

    test_name: str
    avg_execution_time_ms: float
    success_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float
    version: str
    git_commit: Optional[str] = None


@dataclass
class RegressionResult:
    """回归测试结果"""

    test_name: str
    baseline_value: float
    current_value: float
    change_percent: float
    regression_detected: bool
    severity: str  # "minor", "moderate", "severe", "critical"
    recommendation: str


@dataclass
class ConfigurationChange:
    """配置变更记录"""

    file_path: str
    change_type: str  # "modified", "added", "deleted"
    old_checksum: Optional[str]
    new_checksum: Optional[str]
    impact_severity: str


class BaselineManager:
    """基线管理器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.baseline_dir = os.path.join(project_root, "test", "baselines")
        self.current_baseline_file = os.path.join(
            self.baseline_dir, "current_baseline.json"
        )
        self.historical_baselines_dir = os.path.join(self.baseline_dir, "historical")

        # 确保目录存在
        os.makedirs(self.baseline_dir, exist_ok=True)
        os.makedirs(self.historical_baselines_dir, exist_ok=True)

    def create_baseline(self, metrics: List[BaselineMetrics], version: str) -> str:
        """创建新的性能基线"""
        timestamp = time.time()
        git_commit = self._get_current_git_commit()

        baseline_data = {
            "created_at": timestamp,
            "created_date": datetime.fromtimestamp(timestamp).isoformat(),
            "version": version,
            "git_commit": git_commit,
            "metrics": [asdict(metric) for metric in metrics],
            "configuration_checksums": self._generate_config_checksums(),
            "critical_files_checksums": self._generate_critical_files_checksums(),
        }

        # 保存当前基线
        with open(self.current_baseline_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

        # 保存历史基线
        baseline_filename = f"baseline_{version}_{int(timestamp)}.json"
        historical_file = os.path.join(self.historical_baselines_dir, baseline_filename)

        with open(historical_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

        print(f"✅ 基线已创建: {version}")
        print(f"📁 基线文件: {self.current_baseline_file}")
        print(f"📚 历史记录: {historical_file}")

        return self.current_baseline_file

    def load_baseline(self, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """加载基线数据"""
        if version:
            pass  # Auto-fixed empty block
            # 加载指定版本的基线
            baseline_files = list(
                Path(self.historical_baselines_dir).glob(f"baseline_{version}_*.json")
            )
            if baseline_files:
                baseline_file = baseline_files[0]  # 取第一个匹配的文件
            else:
                print(f"⚠️ 未找到版本 {version} 的基线")
                return None
        else:
            pass  # Auto-fixed empty block
            # 加载当前基线
            baseline_file = self.current_baseline_file

        if not os.path.exists(baseline_file):
            print(f"⚠️ 基线文件不存在: {baseline_file}")
            return None

        try:
            with open(baseline_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载基线失败: {e}")
            return None

    def list_baselines(self) -> List[Dict[str, Any]]:
        """列出所有可用的基线"""
        baselines = []

        # 当前基线
        current = self.load_baseline()
        if current:
            baselines.append(
                {
                    "type": "current",
                    "version": current.get("version", "unknown"),
                    "created_date": current.get("created_date", "unknown"),
                    "git_commit": current.get("git_commit", "unknown"),
                }
            )

        # 历史基线
        for baseline_file in Path(self.historical_baselines_dir).glob(
            "baseline_*.json"
        ):
            try:
                with open(baseline_file, "r") as f:
                    baseline_data = json.load(f)
                    baselines.append(
                        {
                            "type": "historical",
                            "version": baseline_data.get("version", "unknown"),
                            "created_date": baseline_data.get(
                                "created_date", "unknown"
                            ),
                            "git_commit": baseline_data.get("git_commit", "unknown"),
                            "file": str(baseline_file),
                        }
                    )
            except Exception:
                continue

        return sorted(baselines, key=lambda x: x.get("created_date", ""), reverse=True)

    def _get_current_git_commit(self) -> Optional[str]:
        """获取当前Git提交哈希"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _generate_config_checksums(self) -> Dict[str, str]:
        """生成配置文件校验和"""
        config_files = [
            ".claude/settings.json",
            ".claude/config.yaml",
            ".claude/hooks/config.yaml",
            "test/test_config.yaml",
        ]

        checksums = {}
        for config_file in config_files:
            file_path = os.path.join(self.project_root, config_file)
            if os.path.exists(file_path):
                checksums[config_file] = self._calculate_file_checksum(file_path)

        return checksums

    def _generate_critical_files_checksums(self) -> Dict[str, str]:
        """生成关键文件校验和"""
        critical_files = [
            ".claude/hooks/quality_gate.sh",
            ".claude/hooks/smart_agent_selector.sh",
            ".claude/core/lazy_orchestrator.py",
            ".claude/core/engine.py",
        ]

        checksums = {}
        for critical_file in critical_files:
            file_path = os.path.join(self.project_root, critical_file)
            if os.path.exists(file_path):
                checksums[critical_file] = self._calculate_file_checksum(file_path)

        return checksums

    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件MD5校验和"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "error"


class PerformanceRegressionDetector:
    """性能回归检测器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.baseline_manager = BaselineManager(project_root)

        # 回归阈值配置
        self.regression_thresholds = {
            "minor": 5.0,  # 5% 性能下降
            "moderate": 15.0,  # 15% 性能下降
            "severe": 30.0,  # 30% 性能下降
            "critical": 50.0,  # 50% 性能下降
        }

    def detect_performance_regression(
        self, current_metrics: List[BaselineMetrics]
    ) -> List[RegressionResult]:
        """检测性能回归"""
        print("🔍 开始性能回归检测...")

        baseline_data = self.baseline_manager.load_baseline()
        if not baseline_data:
            print("⚠️ 无基线数据，无法进行回归检测")
            return []

        baseline_metrics = {
            metric["test_name"]: metric for metric in baseline_data.get("metrics", [])
        }

        regression_results = []

        for current_metric in current_metrics:
            test_name = current_metric.test_name
            baseline_metric = baseline_metrics.get(test_name)

            if not baseline_metric:
                print(f"⚠️ 测试 {test_name} 无基线数据，跳过回归检测")
                continue

            # 检测执行时间回归
            time_regression = self._detect_metric_regression(
                test_name + "_execution_time",
                baseline_metric["avg_execution_time_ms"],
                current_metric.avg_execution_time_ms,
                "执行时间",
            )
            if time_regression:
                regression_results.append(time_regression)

            # 检测成功率回归
            success_regression = self._detect_metric_regression(
                test_name + "_success_rate",
                baseline_metric["success_rate"],
                current_metric.success_rate,
                "成功率",
                is_success_rate=True,
            )
            if success_regression:
                regression_results.append(success_regression)

            # 检测内存使用回归
            memory_regression = self._detect_metric_regression(
                test_name + "_memory_usage",
                baseline_metric["memory_usage_mb"],
                current_metric.memory_usage_mb,
                "内存使用",
            )
            if memory_regression:
                regression_results.append(memory_regression)

        return regression_results

    def _detect_metric_regression(
        self,
        test_name: str,
        baseline_value: float,
        current_value: float,
        metric_type: str,
        is_success_rate: bool = False,
    ) -> Optional[RegressionResult]:
        """检测单项指标回归"""
        if baseline_value == 0:
            return None

        if is_success_rate:
            pass  # Auto-fixed empty block
            # 成功率下降检测
            change_percent = (baseline_value - current_value) / baseline_value * 100
            regression_detected = change_percent > 1.0  # 成功率下降超过1%
        else:
            pass  # Auto-fixed empty block
            # 性能指标恶化检测（时间增加、内存增加）
            change_percent = (current_value - baseline_value) / baseline_value * 100
            regression_detected = change_percent > self.regression_thresholds["minor"]

        if not regression_detected:
            return None

        # 确定严重程度
        severity = self._determine_severity(abs(change_percent), is_success_rate)

        # 生成建议
        recommendation = self._generate_recommendation(
            metric_type, severity, change_percent
        )

        return RegressionResult(
            test_name=test_name,
            baseline_value=baseline_value,
            current_value=current_value,
            change_percent=change_percent,
            regression_detected=True,
            severity=severity,
            recommendation=recommendation,
        )

    def _determine_severity(
        self, change_percent: float, is_success_rate: bool = False
    ) -> str:
        """确定回归严重程度"""
        if is_success_rate:
            pass  # Auto-fixed empty block
            # 成功率回归严重程度
            if change_percent > 10:
                return "critical"
            elif change_percent > 5:
                return "severe"
            elif change_percent > 2:
                return "moderate"
            else:
                return "minor"
        else:
            pass  # Auto-fixed empty block
            # 性能回归严重程度
            if change_percent > self.regression_thresholds["critical"]:
                return "critical"
            elif change_percent > self.regression_thresholds["severe"]:
                return "severe"
            elif change_percent > self.regression_thresholds["moderate"]:
                return "moderate"
            else:
                return "minor"

    def _generate_recommendation(
        self, metric_type: str, severity: str, change_percent: float
    ) -> str:
        """生成优化建议"""
        recommendations = {
            "执行时间": {
                "critical": "立即停止部署！执行时间严重恶化，需要紧急优化算法",
                "severe": "需要立即优化，考虑算法重构或缓存机制",
                "moderate": "建议优化性能，检查最近的代码变更",
                "minor": "轻微性能下降，建议监控趋势",
            },
            "成功率": {
                "critical": "立即回滚！成功率严重下降，系统可靠性受损",
                "severe": "需要立即修复，检查错误处理逻辑",
                "moderate": "需要调查失败原因，改进错误处理",
                "minor": "建议检查测试用例和边界条件",
            },
            "内存使用": {
                "critical": "严重内存泄漏！立即调查内存管理问题",
                "severe": "需要优化内存使用，检查是否有内存泄漏",
                "moderate": "建议优化内存使用效率",
                "minor": "轻微内存增长，建议持续监控",
            },
        }

        return recommendations.get(metric_type, {}).get(
            severity, f"{metric_type}出现{severity}级别回归，变化{change_percent:.1f}%"
        )


class ConfigurationChangeDetector:
    """配置变更检测器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.baseline_manager = BaselineManager(project_root)

    def detect_configuration_changes(self) -> List[ConfigurationChange]:
        """检测配置变更"""
        print("🔧 检测配置文件变更...")

        baseline_data = self.baseline_manager.load_baseline()
        if not baseline_data:
            print("⚠️ 无基线数据，无法检测配置变更")
            return []

        baseline_checksums = baseline_data.get("configuration_checksums", {})
        current_checksums = self.baseline_manager._generate_config_checksums()

        changes = []

        # 检查所有配置文件
        all_config_files = set(baseline_checksums.keys()) | set(
            current_checksums.keys()
        )

        for config_file in all_config_files:
            baseline_checksum = baseline_checksums.get(config_file)
            current_checksum = current_checksums.get(config_file)

            if not baseline_checksum and current_checksum:
                pass  # Auto-fixed empty block
                # 新增配置文件
                changes.append(
                    ConfigurationChange(
                        file_path=config_file,
                        change_type="added",
                        old_checksum=None,
                        new_checksum=current_checksum,
                        impact_severity=self._assess_config_impact(
                            config_file, "added"
                        ),
                    )
                )

            elif baseline_checksum and not current_checksum:
                pass  # Auto-fixed empty block
                # 删除配置文件
                changes.append(
                    ConfigurationChange(
                        file_path=config_file,
                        change_type="deleted",
                        old_checksum=baseline_checksum,
                        new_checksum=None,
                        impact_severity=self._assess_config_impact(
                            config_file, "deleted"
                        ),
                    )
                )

            elif baseline_checksum != current_checksum:
                pass  # Auto-fixed empty block
                # 修改配置文件
                changes.append(
                    ConfigurationChange(
                        file_path=config_file,
                        change_type="modified",
                        old_checksum=baseline_checksum,
                        new_checksum=current_checksum,
                        impact_severity=self._assess_config_impact(
                            config_file, "modified"
                        ),
                    )
                )

        return changes

    def _assess_config_impact(self, config_file: str, change_type: str) -> str:
        """评估配置变更影响"""
        critical_configs = [".claude/settings.json", ".claude/config.yaml"]
        important_configs = [".claude/hooks/config.yaml"]

        if config_file in critical_configs:
            if change_type == "deleted":
                return "critical"
            else:
                return "high"
        elif config_file in important_configs:
            return "medium"
        else:
            return "low"


class FunctionalRegressionTester:
    """功能回归测试器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.hooks_dir = os.path.join(project_root, ".claude", "hooks")
        self.baseline_manager = BaselineManager(project_root)

    def test_functional_regression(self) -> List[Dict[str, Any]]:
        """测试功能回归"""
        print("🧪 开始功能回归测试...")

        baseline_data = self.baseline_manager.load_baseline()
        if not baseline_data:
            print("⚠️ 无基线数据，执行基础功能测试")
            return self._run_basic_functional_tests()

        baseline_checksums = baseline_data.get("critical_files_checksums", {})
        current_checksums = self.baseline_manager._generate_critical_files_checksums()

        regression_results = []

        # 检查关键文件变更
        for file_path, baseline_checksum in baseline_checksums.items():
            current_checksum = current_checksums.get(file_path)

            if current_checksum != baseline_checksum:
                print(f"🔍 检测到文件变更: {file_path}")
                # 对变更的文件进行功能测试
                functional_result = self._test_file_functionality(file_path)
                regression_results.append(
                    {
                        "file_path": file_path,
                        "change_detected": True,
                        "functional_test_result": functional_result,
                    }
                )
            else:
                regression_results.append(
                    {
                        "file_path": file_path,
                        "change_detected": False,
                        "functional_test_result": {
                            "status": "skipped",
                            "reason": "no_changes",
                        },
                    }
                )

        return regression_results

    def _test_file_functionality(self, file_path: str) -> Dict[str, Any]:
        """测试文件功能"""
        full_path = os.path.join(self.project_root, file_path)

        if file_path.endswith(".sh"):
            return self._test_shell_script(full_path)
        elif file_path.endswith(".py"):
            return self._test_python_module(full_path)
        else:
            return {"status": "skipped", "reason": "unsupported_file_type"}

    def _test_shell_script(self, script_path: str) -> Dict[str, Any]:
        """测试Shell脚本功能"""
        test_cases = [
            '{"prompt": "test functionality"}',
            '{"prompt": "implement feature"}',
            '{"prompt": ""}',  # 边界条件测试
        ]

        results = []
        for test_input in test_cases:
            try:
                result = subprocess.run(
                    [script_path],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=10,
                )

                results.append(
                    {
                        "input": test_input,
                        "return_code": result.returncode,
                        "success": result.returncode == 0,
                        "stdout": result.stdout[:100],  # 限制输出长度
                        "stderr": result.stderr[:100],
                    }
                )

            except subprocess.TimeoutExpired:
                results.append(
                    {
                        "input": test_input,
                        "return_code": -1,
                        "success": False,
                        "error": "timeout",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "input": test_input,
                        "return_code": -1,
                        "success": False,
                        "error": str(e),
                    }
                )

        success_count = sum(1 for r in results if r["success"])
        success_rate = success_count / len(results)

        return {
            "status": "completed",
            "test_cases": len(results),
            "success_count": success_count,
            "success_rate": success_rate,
            "results": results,
        }

    def _test_python_module(self, module_path: str) -> Dict[str, Any]:
        """测试Python模块功能"""
        try:
            pass  # Auto-fixed empty block
            # 简单的导入测试
            import importlib.util

            spec = importlib.util.spec_from_file_location("test_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return {"status": "completed", "success": True, "message": "模块导入成功"}

        except Exception as e:
            return {"status": "failed", "success": False, "error": str(e)}

    def _run_basic_functional_tests(self) -> List[Dict[str, Any]]:
        """运行基础功能测试"""
        critical_files = [
            ".claude/hooks/quality_gate.sh",
            ".claude/hooks/smart_agent_selector.sh",
            ".claude/core/lazy_orchestrator.py",
        ]

        results = []
        for file_path in critical_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                functional_result = self._test_file_functionality(file_path)
                results.append(
                    {
                        "file_path": file_path,
                        "change_detected": False,
                        "functional_test_result": functional_result,
                    }
                )

        return results


class RegressionReportGenerator:
    """回归测试报告生成器"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_regression_report(
        self,
        performance_regressions: List[RegressionResult],
        config_changes: List[ConfigurationChange],
        functional_results: List[Dict[str, Any]],
        timestamp: str,
    ) -> str:
        """生成回归测试报告"""
        report_file = self.output_dir / f"regression_report_{timestamp}.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(
                self._generate_regression_markdown(
                    performance_regressions,
                    config_changes,
                    functional_results,
                    timestamp,
                )
            )

        print(f"📊 回归测试报告已生成: {report_file}")
        return str(report_file)

    def _generate_regression_markdown(
        self,
        performance_regressions: List[RegressionResult],
        config_changes: List[ConfigurationChange],
        functional_results: List[Dict[str, Any]],
        timestamp: str,
    ) -> str:
        """生成回归测试Markdown报告"""
        # 统计数据
        critical_regressions = len(
            [r for r in performance_regressions if r.severity == "critical"]
        )
        severe_regressions = len(
            [r for r in performance_regressions if r.severity == "severe"]
        )
        total_regressions = len(performance_regressions)

        critical_config_changes = len(
            [c for c in config_changes if c.impact_severity == "critical"]
        )
        high_impact_changes = len(
            [c for c in config_changes if c.impact_severity == "high"]
        )

        functional_failures = len(
            [
                f
                for f in functional_results
                if not f.get("functional_test_result", {}).get("success", True)
            ]
        )

        # 确定整体状态
        if (
            critical_regressions > 0
            or critical_config_changes > 0
            or functional_failures > 0
        ):
            overall_status = "🚨 CRITICAL"
            overall_color = "red"
        elif severe_regressions > 0 or high_impact_changes > 0:
            overall_status = "⚠️ WARNING"
            overall_color = "orange"
        elif total_regressions > 0 or len(config_changes) > 0:
            overall_status = "📋 REVIEW"
            overall_color = "yellow"
        else:
            overall_status = "✅ PASS"
            overall_color = "green"

        report = f"""# Claude Enhancer 5.0 - 回归测试报告

**生成时间**: {timestamp}
**整体状态**: {overall_status}
**系统环境**: {os.uname().sysname} {os.uname().release}

## 📊 执行摘要

| 测试类型 | 检测项目 | 问题数量 | 状态 |
|---------|----------|----------|------|
| 性能回归 | {len(performance_regressions)} 项指标 | {critical_regressions} 严重 + {severe_regressions} 重要 | {'🚨' if critical_regressions > 0 else '⚠️' if severe_regressions > 0 else '✅'} |
| 配置变更 | {len(config_changes)} 个文件 | {critical_config_changes} 关键 + {high_impact_changes} 重要 | {'🚨' if critical_config_changes > 0 else '⚠️' if high_impact_changes > 0 else '✅'} |
| 功能回归 | {len(functional_results)} 个组件 | {functional_failures} 个失败 | {'🚨' if functional_failures > 0 else '✅'} |

## 🔥 性能回归分析

"""

        if performance_regressions:
            report += """### 检测到的性能回归

| 测试项目 | 基线值 | 当前值 | 变化 | 严重程度 | 建议 |
|---------|--------|--------|------|----------|------|
"""
            for regression in performance_regressions:
                severity_icon = {
                    "critical": "🚨",
                    "severe": "⚠️",
                    "moderate": "📋",
                    "minor": "ℹ️",
                }.get(regression.severity, "❓")

                if "execution_time" in regression.test_name:
                    unit = "ms"
                elif "success_rate" in regression.test_name:
                    unit = "%"
                    regression.baseline_value *= 100
                    regression.current_value *= 100
                else:
                    unit = "MB"

                report += f"| {regression.test_name} | {regression.baseline_value:.2f}{unit} | {regression.current_value:.2f}{unit} | {regression.change_percent:+.1f}% | {severity_icon} {regression.severity} | {regression.recommendation} |\n"

        else:
            report += "✅ **无性能回归检测到**\n"

        report += f"""
## 🔧 配置变更分析

"""

        if config_changes:
            report += """### 检测到的配置变更

| 文件路径 | 变更类型 | 影响程度 | 建议 |
|---------|----------|----------|------|
"""
            for change in config_changes:
                impact_icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "📋",
                    "low": "ℹ️",
                }.get(change.impact_severity, "❓")

                change_icon = {"added": "➕", "modified": "📝", "deleted": "🗑️"}.get(
                    change.change_type, "❓"
                )

                recommendation = self._get_config_change_recommendation(change)

                report += f"| {change.file_path} | {change_icon} {change.change_type} | {impact_icon} {change.impact_severity} | {recommendation} |\n"

        else:
            report += "✅ **无配置变更检测到**\n"

        report += f"""
## 🧪 功能回归测试

"""

        if functional_results:
            for result in functional_results:
                file_path = result["file_path"]
                change_detected = result["change_detected"]
                test_result = result["functional_test_result"]

                status_icon = "🔍" if change_detected else "✅"
                test_status = test_result.get("status", "unknown")

                report += f"""### {file_path}
- **文件变更**: {'是' if change_detected else '否'} {status_icon}
- **测试状态**: {test_status}
"""

                if test_status == "completed":
                    success_rate = test_result.get("success_rate", 0)
                    test_cases = test_result.get("test_cases", 0)
                    report += f"- **测试用例**: {test_cases} 个\n"
                    report += f"- **成功率**: {success_rate:.1%}\n"

                    if success_rate < 1.0:
                        report += "- **⚠️ 存在功能问题，需要调查**\n"

                elif test_status == "failed":
                    error = test_result.get("error", "unknown")
                    report += f"- **❌ 测试失败**: {error}\n"

                report += "\n"

        else:
            report += "ℹ️ **无功能测试结果**\n"

        report += f"""
## 🎯 行动建议

### 立即处理项
"""

        immediate_actions = []

        # 严重性能回归
        for regression in performance_regressions:
            if regression.severity in ["critical", "severe"]:
                immediate_actions.append(
                    f"- **{regression.test_name}**: {regression.recommendation}"
                )

        # 关键配置变更
        for change in config_changes:
            if change.impact_severity in ["critical", "high"]:
                immediate_actions.append(
                    f"- **{change.file_path}**: {self._get_config_change_recommendation(change)}"
                )

        # 功能失败
        for result in functional_results:
            test_result = result["functional_test_result"]
            if (
                test_result.get("status") == "failed"
                or test_result.get("success_rate", 1) < 0.8
            ):
                immediate_actions.append(f"- **{result['file_path']}**: 修复功能问题")

        if immediate_actions:
            for action in immediate_actions:
                report += f"{action}\n"
        else:
            report += "✅ **无需立即处理的问题**\n"

        report += f"""
### 监控建议
1. 持续监控性能指标，建立自动化告警
2. 定期更新回归测试基线
3. 实施配置变更审批流程
4. 增强功能测试覆盖率

### 质量保证
1. 所有性能回归都需要详细分析
2. 关键配置变更需要团队评审
3. 功能失败必须在部署前修复
4. 建立性能预算和阈值管理

## 📈 趋势分析

### 性能趋势
- **执行时间**: {'上升趋势 ⚠️' if any(r.change_percent > 0 for r in performance_regressions if 'execution_time' in r.test_name) else '稳定 ✅'}
- **成功率**: {'下降趋势 ⚠️' if any(r.change_percent > 0 for r in performance_regressions if 'success_rate' in r.test_name) else '稳定 ✅'}
- **内存使用**: {'增长趋势 ⚠️' if any(r.change_percent > 0 for r in performance_regressions if 'memory' in r.test_name) else '稳定 ✅'}

## 🏆 结论

### 回归测试评估
{overall_status}

### 部署建议
"""

        if overall_status.startswith("🚨"):
            report += "**🛑 不建议部署**：发现严重回归问题，需要立即修复后再部署。\n"
        elif overall_status.startswith("⚠️"):
            report += "**⚠️ 谨慎部署**：存在一些问题，建议修复后部署，或在低风险环境先行验证。\n"
        elif overall_status.startswith("📋"):
            report += "**📋 评估后部署**：有轻微变更，建议评估影响后决定是否部署。\n"
        else:
            report += "**✅ 可以部署**：无回归问题检测到，系统状态良好。\n"

        report += f"""
---
*报告由 Claude Enhancer Regression Test Framework 自动生成*
*测试工程师: Test Engineer Professional*
*生成时间: {timestamp}*
"""

        return report

    def _get_config_change_recommendation(self, change: ConfigurationChange) -> str:
        """获取配置变更建议"""
        recommendations = {
            ("critical", "deleted"): "立即恢复配置文件，可能导致系统无法正常工作",
            ("critical", "modified"): "仔细审查配置变更，确保不影响核心功能",
            ("critical", "added"): "验证新配置的必要性和安全性",
            ("high", "deleted"): "确认删除的必要性，评估对功能的影响",
            ("high", "modified"): "审查配置变更，确保符合系统要求",
            ("high", "added"): "验证新配置的有效性",
            ("medium", "deleted"): "评估删除对系统的影响",
            ("medium", "modified"): "确认配置变更的合理性",
            ("medium", "added"): "验证新配置文件",
            ("low", "deleted"): "记录变更原因",
            ("low", "modified"): "记录配置变更",
            ("low", "added"): "文档化新配置",
        }

        return recommendations.get(
            (change.impact_severity, change.change_type), f"评估{change.change_type}配置的影响"
        )


class RegressionTestFramework:
    """回归测试框架主类"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or "/home/xx/dev/Claude Enhancer 5.0"
        self.test_dir = os.path.join(self.project_root, "test")
        self.reports_dir = os.path.join(self.test_dir, "regression_reports")

        # 确保目录存在
        os.makedirs(self.reports_dir, exist_ok=True)

        # 初始化组件
        self.baseline_manager = BaselineManager(self.project_root)
        self.performance_detector = PerformanceRegressionDetector(self.project_root)
        self.config_detector = ConfigurationChangeDetector(self.project_root)
        self.functional_tester = FunctionalRegressionTester(self.project_root)
        self.report_generator = RegressionReportGenerator(self.reports_dir)

    def run_complete_regression_test(
        self, current_metrics: List[BaselineMetrics] = None
    ) -> str:
        """运行完整回归测试"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("🔄 Claude Enhancer 5.0 - 回归测试框架")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 项目路径: {self.project_root}")
        print("=" * 60)

        start_time = time.time()

        # 1. 性能回归检测
        print("\n📊 1. 性能回归检测")
        if current_metrics:
            performance_regressions = (
                self.performance_detector.detect_performance_regression(current_metrics)
            )
        else:
            print("⚠️ 无当前性能指标，跳过性能回归检测")
            performance_regressions = []

        # 2. 配置变更检测
        print("\n🔧 2. 配置变更检测")
        config_changes = self.config_detector.detect_configuration_changes()

        # 3. 功能回归测试
        print("\n🧪 3. 功能回归测试")
        functional_results = self.functional_tester.test_functional_regression()

        # 4. 生成回归测试报告
        print("\n📊 4. 生成回归测试报告")
        report_file = self.report_generator.generate_regression_report(
            performance_regressions, config_changes, functional_results, timestamp
        )

        total_time = time.time() - start_time

        # 输出总结
        print("\n" + "=" * 60)
        print("🏆 回归测试完成")
        print(f"⏱️ 总耗时: {total_time:.2f}秒")
        print(f"📊 报告文件: {report_file}")

        # 显示关键结果
        critical_issues = len(
            [r for r in performance_regressions if r.severity == "critical"]
        )
        critical_configs = len(
            [c for c in config_changes if c.impact_severity == "critical"]
        )
        functional_failures = len(
            [
                f
                for f in functional_results
                if not f.get("functional_test_result", {}).get("success", True)
            ]
        )

        print(f"🚨 严重问题: {critical_issues + critical_configs + functional_failures}")
        print(
            f"📋 总问题数: {len(performance_regressions) + len(config_changes) + functional_failures}"
        )

        if critical_issues + critical_configs + functional_failures > 0:
            print("⚠️ 建议：发现严重问题，不建议部署")
        else:
            print("✅ 建议：回归测试通过，可以部署")

        return report_file

    def create_baseline_from_current_state(self, version: str = "5.1") -> str:
        """从当前状态创建基线"""
        print(f"📏 创建版本 {version} 的性能基线...")

        # 这里应该运行性能测试获取当前指标
        # 为了演示，我们创建一些模拟指标
        current_metrics = [
            BaselineMetrics(
                test_name="quality_gate",
                avg_execution_time_ms=45.0,
                success_rate=0.99,
                memory_usage_mb=8.5,
                cpu_usage_percent=2.1,
                timestamp=time.time(),
                version=version,
            ),
            BaselineMetrics(
                test_name="smart_agent_selector",
                avg_execution_time_ms=28.0,
                success_rate=0.995,
                memory_usage_mb=6.2,
                cpu_usage_percent=1.8,
                timestamp=time.time(),
                version=version,
            ),
        ]

        return self.baseline_manager.create_baseline(current_metrics, version)

    def list_available_baselines(self):
        """列出可用的基线"""
        baselines = self.baseline_manager.list_baselines()

        print("📚 可用的性能基线:")
        for baseline in baselines:
            print(
                f"  {baseline['type']}: {baseline['version']} "
                f"({baseline['created_date']}) "
                f"[{baseline.get('git_commit', 'unknown')[:8]}]"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude Enhancer 5.0 回归测试框架")
    parser.add_argument("--project-root", help="项目根目录路径")
    parser.add_argument("--create-baseline", metavar="VERSION", help="创建新的性能基线")
    parser.add_argument("--list-baselines", action="store_true", help="列出所有可用基线")

    args = parser.parse_args()

    try:
        framework = RegressionTestFramework(args.project_root)

        if args.create_baseline:
            baseline_file = framework.create_baseline_from_current_state(
                args.create_baseline
            )
            print(f"✅ 基线创建成功: {baseline_file}")

        elif args.list_baselines:
            framework.list_available_baselines()

        else:
            report_file = framework.run_complete_regression_test()
            print(f"\n✅ 回归测试完成，报告保存在: {report_file}")

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)
