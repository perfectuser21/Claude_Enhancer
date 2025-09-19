#!/usr/bin/env python3
"""
Perfect21 质量门引擎
===================

统一管理和执行所有质量门检查
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from .models import GateResult, GateStatus, GateSeverity, QualityGateConfig
from .code_quality_gate import CodeQualityGate
from .security_gate import SecurityGate
from .performance_gate import PerformanceGate
from .architecture_gate import ArchitectureGate
from .coverage_gate import CoverageGate


class QualityGateEngine:
    """质量门引擎"""

    def __init__(self, project_root: str, config: Optional[QualityGateConfig] = None):
        self.project_root = Path(project_root)
        self.config = config or QualityGateConfig()
        self.logger = logging.getLogger(__name__)

        # 初始化各个质量门
        self.gates = {
            'code_quality': CodeQualityGate(project_root, self.config),
            'security': SecurityGate(project_root, self.config),
            'performance': PerformanceGate(project_root, self.config),
            'architecture': ArchitectureGate(project_root, self.config),
            'coverage': CoverageGate(project_root, self.config)
        }

        # 执行历史
        self.history_file = self.project_root / ".perfect21" / "quality_gate_history.json"
        self.history_file.parent.mkdir(exist_ok=True)

    async def run_all_gates(self, context: str = "commit") -> Dict[str, GateResult]:
        """运行所有质量门"""
        self.logger.info(f"开始执行质量门检查 - 上下文: {context}")
        start_time = time.time()

        results = {}

        if self.config.parallel_execution:
            # 并行执行
            tasks = []
            for gate_name, gate in self.gates.items():
                if self._should_run_gate(gate_name, context):
                    task = asyncio.create_task(
                        self._run_single_gate(gate_name, gate, context)
                    )
                    tasks.append((gate_name, task))

            for gate_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=self.config.timeout_seconds)
                    results[gate_name] = result

                    if self.config.fail_fast and result.status == GateStatus.FAILED:
                        self.logger.warning(f"质量门失败 (fail_fast): {gate_name}")
                        # 取消其他任务
                        for _, other_task in tasks:
                            if not other_task.done():
                                other_task.cancel()
                        break

                except asyncio.TimeoutError:
                    results[gate_name] = GateResult(
                        gate_name=gate_name,
                        status=GateStatus.FAILED,
                        severity=GateSeverity.HIGH,
                        score=0.0,
                        message="执行超时",
                        details={"timeout": self.config.timeout_seconds},
                        violations=[{"type": "timeout", "message": "质量门执行超时"}],
                        suggestions=["增加超时时间", "优化检查逻辑"],
                        execution_time=self.config.timeout_seconds,
                        timestamp=datetime.now().isoformat(),
                        metadata={"context": context}
                    )
        else:
            # 串行执行
            for gate_name, gate in self.gates.items():
                if self._should_run_gate(gate_name, context):
                    result = await self._run_single_gate(gate_name, gate, context)
                    results[gate_name] = result

                    if self.config.fail_fast and result.status == GateStatus.FAILED:
                        self.logger.warning(f"质量门失败 (fail_fast): {gate_name}")
                        break

        # 计算总体结果
        overall_result = self._calculate_overall_result(results)
        results['overall'] = overall_result

        # 保存执行历史
        execution_time = time.time() - start_time
        await self._save_execution_history(results, context, execution_time)

        self.logger.info(f"质量门检查完成 - 总耗时: {execution_time:.2f}s")
        return results

    async def _run_single_gate(self, gate_name: str, gate, context: str) -> GateResult:
        """运行单个质量门"""
        try:
            self.logger.info(f"执行质量门: {gate_name}")
            result = await gate.check(context)
            self.logger.info(f"质量门完成: {gate_name} - {result.status.value}")
            return result
        except Exception as e:
            self.logger.error(f"质量门执行失败: {gate_name} - {str(e)}")
            return GateResult(
                gate_name=gate_name,
                status=GateStatus.FAILED,
                severity=GateSeverity.HIGH,
                score=0.0,
                message=f"执行异常: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                violations=[{"type": "execution_error", "message": str(e)}],
                suggestions=["检查质量门配置", "查看详细错误日志"],
                execution_time=0.0,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

    def _should_run_gate(self, gate_name: str, context: str) -> bool:
        """判断是否应该运行特定质量门"""
        # 根据上下文决定运行哪些质量门
        gate_contexts = {
            'code_quality': ['commit', 'merge', 'release', 'all'],
            'security': ['commit', 'merge', 'release', 'all'],
            'performance': ['merge', 'release', 'performance_test', 'all'],
            'architecture': ['merge', 'release', 'refactor', 'all'],
            'coverage': ['commit', 'merge', 'release', 'all']
        }

        return context in gate_contexts.get(gate_name, ['all'])

    def _calculate_overall_result(self, results: Dict[str, GateResult]) -> GateResult:
        """计算总体结果"""
        if not results:
            return GateResult(
                gate_name="overall",
                status=GateStatus.SKIPPED,
                severity=GateSeverity.INFO,
                score=0.0,
                message="无质量门执行",
                details={},
                violations=[],
                suggestions=[],
                execution_time=0.0,
                timestamp=datetime.now().isoformat(),
                metadata={}
            )

        # 计算总体状态
        statuses = [r.status for r in results.values()]
        if GateStatus.FAILED in statuses:
            overall_status = GateStatus.FAILED
            overall_severity = GateSeverity.HIGH
        elif GateStatus.BLOCKED in statuses:
            overall_status = GateStatus.BLOCKED
            overall_severity = GateSeverity.HIGH
        elif GateStatus.WARNING in statuses:
            overall_status = GateStatus.WARNING
            overall_severity = GateSeverity.MEDIUM
        else:
            overall_status = GateStatus.PASSED
            overall_severity = GateSeverity.INFO

        # 计算平均分数
        scores = [r.score for r in results.values()]
        average_score = sum(scores) / len(scores) if scores else 0.0

        # 收集违规和建议
        all_violations = []
        all_suggestions = []
        for result in results.values():
            all_violations.extend(result.violations)
            all_suggestions.extend(result.suggestions)

        # 统计信息
        details = {
            "total_gates": len(results),
            "passed": len([r for r in results.values() if r.status == GateStatus.PASSED]),
            "failed": len([r for r in results.values() if r.status == GateStatus.FAILED]),
            "warnings": len([r for r in results.values() if r.status == GateStatus.WARNING]),
            "blocked": len([r for r in results.values() if r.status == GateStatus.BLOCKED]),
            "skipped": len([r for r in results.values() if r.status == GateStatus.SKIPPED]),
            "average_score": round(average_score, 2),
            "individual_scores": {name: r.score for name, r in results.items()}
        }

        return GateResult(
            gate_name="overall",
            status=overall_status,
            severity=overall_severity,
            score=average_score,
            message=self._generate_overall_message(details, overall_status),
            details=details,
            violations=all_violations,
            suggestions=list(set(all_suggestions)),  # 去重
            execution_time=sum(r.execution_time for r in results.values()),
            timestamp=datetime.now().isoformat(),
            metadata={"gates_executed": list(results.keys())}
        )

    def _generate_overall_message(self, details: Dict[str, Any], status: GateStatus) -> str:
        """生成总体消息"""
        total = details["total_gates"]
        passed = details["passed"]
        failed = details["failed"]
        score = details["average_score"]

        if status == GateStatus.PASSED:
            return f"所有质量门检查通过 ({passed}/{total}) - 平均分数: {score:.1f}"
        elif status == GateStatus.FAILED:
            return f"质量门检查失败 ({failed}/{total}个失败) - 平均分数: {score:.1f}"
        elif status == GateStatus.WARNING:
            return f"质量门检查有警告 ({passed}/{total}个通过) - 平均分数: {score:.1f}"
        else:
            return f"质量门检查状态: {status.value} - 平均分数: {score:.1f}"

    async def _save_execution_history(self, results: Dict[str, GateResult], context: str, execution_time: float):
        """保存执行历史"""
        try:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "execution_time": execution_time,
                "results": {name: asdict(result) for name, result in results.items()},
                "summary": {
                    "total_gates": len(results) - 1,  # 排除overall
                    "passed": len([r for r in results.values() if r.status == GateStatus.PASSED and r.gate_name != 'overall']),
                    "failed": len([r for r in results.values() if r.status == GateStatus.FAILED and r.gate_name != 'overall']),
                    "average_score": results.get('overall', GateResult("", GateStatus.SKIPPED, GateSeverity.INFO, 0, "", {}, [], [], 0, "", {})).score
                }
            }

            # 读取现有历史
            history = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    history = []

            # 添加新记录
            history.append(history_entry)

            # 只保留最近100条记录
            history = history[-100:]

            # 保存历史
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存执行历史失败: {str(e)}")

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        try:
            if not self.history_file.exists():
                return []

            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            return history[-limit:] if limit > 0 else history
        except Exception as e:
            self.logger.error(f"读取执行历史失败: {str(e)}")
            return []

    def get_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """获取质量趋势"""
        try:
            history = self.get_execution_history(limit=0)  # 获取所有历史

            # 过滤最近N天的数据
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_history = [
                h for h in history
                if datetime.fromisoformat(h['timestamp']) > cutoff_date
            ]

            if not recent_history:
                return {"message": "无最近数据"}

            # 计算趋势
            trends = {
                "total_executions": len(recent_history),
                "average_score_trend": [],
                "pass_rate_trend": [],
                "gate_performance": {},
                "common_violations": {},
                "improvement_suggestions": []
            }

            # 按天分组计算趋势
            daily_data = {}
            for entry in recent_history:
                date = datetime.fromisoformat(entry['timestamp']).date().isoformat()
                if date not in daily_data:
                    daily_data[date] = []
                daily_data[date].append(entry)

            # 计算每日平均分数和通过率
            for date in sorted(daily_data.keys()):
                entries = daily_data[date]
                avg_score = sum(e['summary']['average_score'] for e in entries) / len(entries)
                pass_rate = sum(1 for e in entries if e['summary']['failed'] == 0) / len(entries) * 100

                trends["average_score_trend"].append({"date": date, "score": round(avg_score, 2)})
                trends["pass_rate_trend"].append({"date": date, "pass_rate": round(pass_rate, 2)})

            # 分析各质量门性能
            for gate_name in ['code_quality', 'security', 'performance', 'architecture', 'coverage']:
                gate_scores = []
                for entry in recent_history:
                    if gate_name in entry['results']:
                        gate_scores.append(entry['results'][gate_name]['score'])

                if gate_scores:
                    trends["gate_performance"][gate_name] = {
                        "average_score": round(sum(gate_scores) / len(gate_scores), 2),
                        "min_score": min(gate_scores),
                        "max_score": max(gate_scores),
                        "executions": len(gate_scores)
                    }

            # 分析常见违规
            violation_counts = {}
            for entry in recent_history:
                for result in entry['results'].values():
                    for violation in result.get('violations', []):
                        vtype = violation.get('type', 'unknown')
                        violation_counts[vtype] = violation_counts.get(vtype, 0) + 1

            trends["common_violations"] = dict(sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:10])

            # 生成改进建议
            if trends["gate_performance"]:
                lowest_gate = min(trends["gate_performance"].items(), key=lambda x: x[1]['average_score'])
                trends["improvement_suggestions"].append(f"重点改进 {lowest_gate[0]} (平均分数: {lowest_gate[1]['average_score']})")

            if trends["common_violations"]:
                top_violation = list(trends["common_violations"].keys())[0]
                trends["improvement_suggestions"].append(f"重点解决 {top_violation} 类型的违规")

            return trends

        except Exception as e:
            self.logger.error(f"计算质量趋势失败: {str(e)}")
            return {"error": str(e)}

    async def run_quick_check(self) -> Dict[str, Any]:
        """运行快速检查"""
        quick_gates = ['code_quality', 'security']
        results = {}

        for gate_name in quick_gates:
            if gate_name in self.gates:
                result = await self._run_single_gate(gate_name, self.gates[gate_name], "quick")
                results[gate_name] = result

        overall = self._calculate_overall_result(results)
        results['overall'] = overall

        return {
            "status": overall.status.value,
            "score": overall.score,
            "message": overall.message,
            "details": results
        }

    def generate_report(self, results: Dict[str, GateResult]) -> str:
        """生成质量门报告"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("Perfect21 质量门检查报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        # 总体结果
        overall = results.get('overall')
        if overall:
            report_lines.append(f"🎯 总体结果: {overall.status.value.upper()}")
            report_lines.append(f"📊 平均分数: {overall.score:.1f}/100")
            report_lines.append(f"⏱️ 执行时间: {overall.execution_time:.2f}秒")
            report_lines.append("")

        # 各质量门详情
        for gate_name, result in results.items():
            if gate_name == 'overall':
                continue

            status_emoji = {
                GateStatus.PASSED: "✅",
                GateStatus.FAILED: "❌",
                GateStatus.WARNING: "⚠️",
                GateStatus.BLOCKED: "🚫",
                GateStatus.SKIPPED: "⏭️"
            }

            report_lines.append(f"{status_emoji.get(result.status, '❓')} {gate_name.upper()}")
            report_lines.append(f"   状态: {result.status.value}")
            report_lines.append(f"   分数: {result.score:.1f}/100")
            report_lines.append(f"   消息: {result.message}")

            if result.violations:
                report_lines.append(f"   违规数量: {len(result.violations)}")
                for violation in result.violations[:3]:  # 只显示前3个
                    report_lines.append(f"     - {violation.get('message', str(violation))}")
                if len(result.violations) > 3:
                    report_lines.append(f"     ... 还有 {len(result.violations) - 3} 个违规")

            if result.suggestions:
                report_lines.append(f"   建议: {result.suggestions[0]}")

            report_lines.append("")

        # 改进建议
        if overall and overall.suggestions:
            report_lines.append("🔧 改进建议:")
            for suggestion in overall.suggestions[:5]:  # 最多5个建议
                report_lines.append(f"   • {suggestion}")
            report_lines.append("")

        report_lines.append("=" * 60)
        return "\n".join(report_lines)