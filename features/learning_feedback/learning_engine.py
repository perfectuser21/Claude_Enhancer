#!/usr/bin/env python3
"""
Perfect21 学习引擎
==================

核心学习引擎，从执行结果中提取知识并持续改进决策
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class ExecutionStatus(Enum):
    """执行状态"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class TaskComplexity(Enum):
    """任务复杂度"""
    TRIVIAL = "trivial"       # 1-2分
    SIMPLE = "simple"         # 3-4分
    MODERATE = "moderate"     # 5-6分
    COMPLEX = "complex"       # 7-8分
    EXPERT = "expert"         # 9-10分

@dataclass
class ExecutionMetrics:
    """执行指标"""
    start_time: str
    end_time: str
    duration_seconds: float
    agents_used: List[str]
    parallel_execution: bool
    token_usage: int
    success_rate: float
    error_count: int
    warning_count: int

@dataclass
class TaskContext:
    """任务上下文"""
    task_description: str
    task_type: str
    complexity: TaskComplexity
    workspace_id: Optional[str]
    template_used: Optional[str]
    git_branch: str
    project_state: Dict[str, Any]

@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    task_context: TaskContext
    execution_metrics: ExecutionMetrics
    status: ExecutionStatus
    output_summary: str
    errors: List[str]
    warnings: List[str]
    agent_performance: Dict[str, float]
    quality_score: float
    user_satisfaction: Optional[float]

@dataclass
class LearningData:
    """学习数据"""
    pattern_id: str
    pattern_type: str
    context_features: Dict[str, Any]
    outcome_metrics: Dict[str, float]
    success_factors: List[str]
    failure_factors: List[str]
    improvement_suggestions: List[str]
    confidence_score: float
    last_updated: str

class LearningEngine:
    """学习引擎"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.learning_dir = self.project_root / ".perfect21" / "learning"
        self.execution_history_file = self.learning_dir / "execution_history.json"
        self.learning_patterns_file = self.learning_dir / "learning_patterns.json"
        self.knowledge_base_file = self.learning_dir / "knowledge_base.json"

        self._ensure_directories()
        self._load_data()

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _ensure_directories(self):
        """确保目录结构存在"""
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self):
        """加载学习数据"""
        # 执行历史
        if self.execution_history_file.exists():
            with open(self.execution_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                self.execution_history = [
                    self._dict_to_execution_result(data)
                    for data in history_data
                ]
        else:
            self.execution_history = []

        # 学习模式
        if self.learning_patterns_file.exists():
            with open(self.learning_patterns_file, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
                self.learning_patterns = [
                    self._dict_to_learning_data(data)
                    for data in patterns_data
                ]
        else:
            self.learning_patterns = []

        # 知识库
        if self.knowledge_base_file.exists():
            with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = {
                "best_practices": {},
                "anti_patterns": {},
                "agent_preferences": {},
                "template_effectiveness": {},
                "complexity_estimations": {},
                "performance_baselines": {}
            }

    def _save_data(self):
        """保存学习数据"""
        # 执行历史
        history_data = [self._execution_result_to_dict(result) for result in self.execution_history]
        with open(self.execution_history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

        # 学习模式
        patterns_data = [self._learning_data_to_dict(pattern) for pattern in self.learning_patterns]
        with open(self.learning_patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)

        # 知识库
        with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

    def _dict_to_execution_result(self, data: Dict) -> ExecutionResult:
        """将字典转换为ExecutionResult对象"""
        return ExecutionResult(
            execution_id=data['execution_id'],
            task_context=TaskContext(**data['task_context']),
            execution_metrics=ExecutionMetrics(**data['execution_metrics']),
            status=ExecutionStatus(data['status']),
            output_summary=data['output_summary'],
            errors=data['errors'],
            warnings=data['warnings'],
            agent_performance=data['agent_performance'],
            quality_score=data['quality_score'],
            user_satisfaction=data.get('user_satisfaction')
        )

    def _execution_result_to_dict(self, result: ExecutionResult) -> Dict:
        """将ExecutionResult对象转换为字典"""
        return {
            'execution_id': result.execution_id,
            'task_context': asdict(result.task_context),
            'execution_metrics': asdict(result.execution_metrics),
            'status': result.status.value,
            'output_summary': result.output_summary,
            'errors': result.errors,
            'warnings': result.warnings,
            'agent_performance': result.agent_performance,
            'quality_score': result.quality_score,
            'user_satisfaction': result.user_satisfaction
        }

    def _dict_to_learning_data(self, data: Dict) -> LearningData:
        """将字典转换为LearningData对象"""
        return LearningData(**data)

    def _learning_data_to_dict(self, learning_data: LearningData) -> Dict:
        """将LearningData对象转换为字典"""
        return asdict(learning_data)

    def record_execution(self, execution_result: ExecutionResult):
        """记录执行结果"""
        self.execution_history.append(execution_result)

        # 保持历史记录在合理范围内（最多1000条）
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        # 触发学习过程
        self._learn_from_execution(execution_result)

        # 保存数据
        self._save_data()

        self.logger.info(f"记录执行结果: {execution_result.execution_id}")

    def _learn_from_execution(self, execution_result: ExecutionResult):
        """从执行结果中学习"""

        # 1. 更新Agent性能统计
        self._update_agent_performance(execution_result)

        # 2. 更新复杂度估算
        self._update_complexity_estimation(execution_result)

        # 3. 识别最佳实践和反模式
        self._identify_patterns(execution_result)

        # 4. 更新模板效果评估
        self._update_template_effectiveness(execution_result)

        # 5. 建立性能基线
        self._update_performance_baselines(execution_result)

    def _update_agent_performance(self, execution_result: ExecutionResult):
        """更新Agent性能统计"""
        if "agent_preferences" not in self.knowledge_base:
            self.knowledge_base["agent_preferences"] = {}

        for agent, performance in execution_result.agent_performance.items():
            if agent not in self.knowledge_base["agent_preferences"]:
                self.knowledge_base["agent_preferences"][agent] = {
                    "total_uses": 0,
                    "avg_performance": 0.0,
                    "success_rate": 0.0,
                    "preferred_tasks": [],
                    "performance_history": []
                }

            agent_stats = self.knowledge_base["agent_preferences"][agent]
            agent_stats["total_uses"] += 1

            # 更新平均性能
            prev_avg = agent_stats["avg_performance"]
            new_avg = (prev_avg * (agent_stats["total_uses"] - 1) + performance) / agent_stats["total_uses"]
            agent_stats["avg_performance"] = new_avg

            # 更新成功率
            is_success = execution_result.status == ExecutionStatus.SUCCESS
            prev_success_rate = agent_stats["success_rate"]
            new_success_rate = (prev_success_rate * (agent_stats["total_uses"] - 1) + (1.0 if is_success else 0.0)) / agent_stats["total_uses"]
            agent_stats["success_rate"] = new_success_rate

            # 记录性能历史（最多保留50条）
            agent_stats["performance_history"].append({
                "timestamp": execution_result.execution_metrics.start_time,
                "performance": performance,
                "task_type": execution_result.task_context.task_type,
                "complexity": execution_result.task_context.complexity.value
            })

            if len(agent_stats["performance_history"]) > 50:
                agent_stats["performance_history"] = agent_stats["performance_history"][-50:]

    def _update_complexity_estimation(self, execution_result: ExecutionResult):
        """更新复杂度估算模型"""
        if "complexity_estimations" not in self.knowledge_base:
            self.knowledge_base["complexity_estimations"] = {}

        task_type = execution_result.task_context.task_type
        complexity = execution_result.task_context.complexity.value
        duration = execution_result.execution_metrics.duration_seconds

        if task_type not in self.knowledge_base["complexity_estimations"]:
            self.knowledge_base["complexity_estimations"][task_type] = {}

        if complexity not in self.knowledge_base["complexity_estimations"][task_type]:
            self.knowledge_base["complexity_estimations"][task_type][complexity] = {
                "avg_duration": 0.0,
                "sample_count": 0,
                "success_rate": 0.0,
                "typical_agents": set(),
                "duration_history": []
            }

        comp_stats = self.knowledge_base["complexity_estimations"][task_type][complexity]
        comp_stats["sample_count"] += 1

        # 更新平均持续时间
        prev_avg = comp_stats["avg_duration"]
        new_avg = (prev_avg * (comp_stats["sample_count"] - 1) + duration) / comp_stats["sample_count"]
        comp_stats["avg_duration"] = new_avg

        # 更新成功率
        is_success = execution_result.status == ExecutionStatus.SUCCESS
        prev_success_rate = comp_stats["success_rate"]
        new_success_rate = (prev_success_rate * (comp_stats["sample_count"] - 1) + (1.0 if is_success else 0.0)) / comp_stats["sample_count"]
        comp_stats["success_rate"] = new_success_rate

        # 更新典型Agents
        comp_stats["typical_agents"].update(execution_result.execution_metrics.agents_used)
        comp_stats["typical_agents"] = list(comp_stats["typical_agents"])  # 转换为list以便JSON序列化

        # 记录持续时间历史
        comp_stats["duration_history"].append(duration)
        if len(comp_stats["duration_history"]) > 20:
            comp_stats["duration_history"] = comp_stats["duration_history"][-20:]

    def _identify_patterns(self, execution_result: ExecutionResult):
        """识别最佳实践和反模式"""

        # 成功模式识别
        if execution_result.status == ExecutionStatus.SUCCESS and execution_result.quality_score > 0.8:
            pattern_key = f"{execution_result.task_context.task_type}_{execution_result.task_context.complexity.value}"

            if "best_practices" not in self.knowledge_base:
                self.knowledge_base["best_practices"] = {}

            if pattern_key not in self.knowledge_base["best_practices"]:
                self.knowledge_base["best_practices"][pattern_key] = []

            best_practice = {
                "agents_used": execution_result.execution_metrics.agents_used,
                "parallel_execution": execution_result.execution_metrics.parallel_execution,
                "template_used": execution_result.task_context.template_used,
                "duration": execution_result.execution_metrics.duration_seconds,
                "quality_score": execution_result.quality_score,
                "success_factors": self._extract_success_factors(execution_result),
                "timestamp": execution_result.execution_metrics.start_time
            }

            self.knowledge_base["best_practices"][pattern_key].append(best_practice)

            # 保持最多10个最佳实践
            if len(self.knowledge_base["best_practices"][pattern_key]) > 10:
                # 按质量分数排序，保留最好的
                self.knowledge_base["best_practices"][pattern_key].sort(
                    key=lambda x: x["quality_score"], reverse=True
                )
                self.knowledge_base["best_practices"][pattern_key] = self.knowledge_base["best_practices"][pattern_key][:10]

        # 反模式识别
        elif execution_result.status == ExecutionStatus.FAILURE or execution_result.quality_score < 0.3:
            pattern_key = f"{execution_result.task_context.task_type}_{execution_result.task_context.complexity.value}"

            if "anti_patterns" not in self.knowledge_base:
                self.knowledge_base["anti_patterns"] = {}

            if pattern_key not in self.knowledge_base["anti_patterns"]:
                self.knowledge_base["anti_patterns"][pattern_key] = []

            anti_pattern = {
                "agents_used": execution_result.execution_metrics.agents_used,
                "parallel_execution": execution_result.execution_metrics.parallel_execution,
                "template_used": execution_result.task_context.template_used,
                "errors": execution_result.errors,
                "failure_factors": self._extract_failure_factors(execution_result),
                "timestamp": execution_result.execution_metrics.start_time
            }

            self.knowledge_base["anti_patterns"][pattern_key].append(anti_pattern)

            # 保持最多5个反模式
            if len(self.knowledge_base["anti_patterns"][pattern_key]) > 5:
                self.knowledge_base["anti_patterns"][pattern_key] = self.knowledge_base["anti_patterns"][pattern_key][-5:]

    def _extract_success_factors(self, execution_result: ExecutionResult) -> List[str]:
        """提取成功因素"""
        factors = []

        if execution_result.execution_metrics.parallel_execution:
            factors.append("parallel_execution")

        if execution_result.execution_metrics.duration_seconds < 300:  # 5分钟内
            factors.append("fast_execution")

        if execution_result.execution_metrics.error_count == 0:
            factors.append("error_free")

        if len(execution_result.execution_metrics.agents_used) <= 3:
            factors.append("focused_agent_usage")

        if execution_result.task_context.template_used:
            factors.append("template_guided")

        if execution_result.execution_metrics.success_rate > 0.9:
            factors.append("high_success_rate")

        return factors

    def _extract_failure_factors(self, execution_result: ExecutionResult) -> List[str]:
        """提取失败因素"""
        factors = []

        if execution_result.execution_metrics.duration_seconds > 1800:  # 30分钟以上
            factors.append("slow_execution")

        if execution_result.execution_metrics.error_count > 5:
            factors.append("high_error_rate")

        if len(execution_result.execution_metrics.agents_used) > 8:
            factors.append("too_many_agents")

        if "timeout" in str(execution_result.errors).lower():
            factors.append("timeout_issues")

        if "conflict" in str(execution_result.errors).lower():
            factors.append("conflict_issues")

        if not execution_result.execution_metrics.parallel_execution and execution_result.task_context.complexity != TaskComplexity.TRIVIAL:
            factors.append("serial_execution_for_complex_task")

        return factors

    def _update_template_effectiveness(self, execution_result: ExecutionResult):
        """更新模板效果评估"""
        template = execution_result.task_context.template_used
        if not template:
            return

        if "template_effectiveness" not in self.knowledge_base:
            self.knowledge_base["template_effectiveness"] = {}

        if template not in self.knowledge_base["template_effectiveness"]:
            self.knowledge_base["template_effectiveness"][template] = {
                "usage_count": 0,
                "avg_quality_score": 0.0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "suitable_task_types": set(),
                "effectiveness_history": []
            }

        template_stats = self.knowledge_base["template_effectiveness"][template]
        template_stats["usage_count"] += 1

        # 更新平均质量分数
        prev_quality = template_stats["avg_quality_score"]
        new_quality = (prev_quality * (template_stats["usage_count"] - 1) + execution_result.quality_score) / template_stats["usage_count"]
        template_stats["avg_quality_score"] = new_quality

        # 更新成功率
        is_success = execution_result.status == ExecutionStatus.SUCCESS
        prev_success_rate = template_stats["success_rate"]
        new_success_rate = (prev_success_rate * (template_stats["usage_count"] - 1) + (1.0 if is_success else 0.0)) / template_stats["usage_count"]
        template_stats["success_rate"] = new_success_rate

        # 更新平均持续时间
        prev_duration = template_stats["avg_duration"]
        new_duration = (prev_duration * (template_stats["usage_count"] - 1) + execution_result.execution_metrics.duration_seconds) / template_stats["usage_count"]
        template_stats["avg_duration"] = new_duration

        # 更新适用任务类型
        template_stats["suitable_task_types"].add(execution_result.task_context.task_type)
        template_stats["suitable_task_types"] = list(template_stats["suitable_task_types"])  # 转换为list

        # 记录效果历史
        template_stats["effectiveness_history"].append({
            "timestamp": execution_result.execution_metrics.start_time,
            "quality_score": execution_result.quality_score,
            "task_type": execution_result.task_context.task_type,
            "success": is_success
        })

        if len(template_stats["effectiveness_history"]) > 30:
            template_stats["effectiveness_history"] = template_stats["effectiveness_history"][-30:]

    def _update_performance_baselines(self, execution_result: ExecutionResult):
        """更新性能基线"""
        if "performance_baselines" not in self.knowledge_base:
            self.knowledge_base["performance_baselines"] = {}

        baseline_key = f"{execution_result.task_context.task_type}_{execution_result.task_context.complexity.value}"

        if baseline_key not in self.knowledge_base["performance_baselines"]:
            self.knowledge_base["performance_baselines"][baseline_key] = {
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "avg_duration": 0.0,
                "min_quality": 1.0,
                "max_quality": 0.0,
                "avg_quality": 0.0,
                "sample_count": 0,
                "last_updated": ""
            }

        baseline = self.knowledge_base["performance_baselines"][baseline_key]
        baseline["sample_count"] += 1

        duration = execution_result.execution_metrics.duration_seconds
        quality = execution_result.quality_score

        # 更新持续时间统计
        baseline["min_duration"] = min(baseline["min_duration"], duration)
        baseline["max_duration"] = max(baseline["max_duration"], duration)
        prev_avg_duration = baseline["avg_duration"]
        baseline["avg_duration"] = (prev_avg_duration * (baseline["sample_count"] - 1) + duration) / baseline["sample_count"]

        # 更新质量统计
        baseline["min_quality"] = min(baseline["min_quality"], quality)
        baseline["max_quality"] = max(baseline["max_quality"], quality)
        prev_avg_quality = baseline["avg_quality"]
        baseline["avg_quality"] = (prev_avg_quality * (baseline["sample_count"] - 1) + quality) / baseline["sample_count"]

        baseline["last_updated"] = execution_result.execution_metrics.start_time

    def get_recommendations(self, task_description: str, task_type: str, complexity: TaskComplexity) -> Dict[str, Any]:
        """获取基于学习的推荐"""

        pattern_key = f"{task_type}_{complexity.value}"

        recommendations = {
            "recommended_agents": [],
            "recommended_template": None,
            "recommended_parallel": True,
            "expected_duration": 0,
            "success_probability": 0.5,
            "quality_expectation": 0.7,
            "risk_factors": [],
            "best_practices": [],
            "warnings": []
        }

        # 基于最佳实践的推荐
        if pattern_key in self.knowledge_base.get("best_practices", {}):
            best_practices = self.knowledge_base["best_practices"][pattern_key]
            if best_practices:
                # 选择质量分数最高的实践
                best_practice = max(best_practices, key=lambda x: x["quality_score"])

                recommendations["recommended_agents"] = best_practice["agents_used"]
                recommendations["recommended_template"] = best_practice["template_used"]
                recommendations["recommended_parallel"] = best_practice["parallel_execution"]
                recommendations["quality_expectation"] = best_practice["quality_score"]
                recommendations["best_practices"] = best_practice["success_factors"]

        # 基于Agent性能的推荐
        agent_prefs = self.knowledge_base.get("agent_preferences", {})
        suitable_agents = []
        for agent, stats in agent_prefs.items():
            if stats["success_rate"] > 0.7 and stats["avg_performance"] > 0.6:
                # 检查Agent是否适合当前任务类型
                suitable_for_task = any(
                    history["task_type"] == task_type
                    for history in stats["performance_history"][-10:]
                )
                if suitable_for_task:
                    suitable_agents.append((agent, stats["avg_performance"]))

        # 按性能排序
        suitable_agents.sort(key=lambda x: x[1], reverse=True)

        if not recommendations["recommended_agents"] and suitable_agents:
            recommendations["recommended_agents"] = [agent for agent, _ in suitable_agents[:5]]

        # 基于复杂度估算的时间预测
        if pattern_key in self.knowledge_base.get("complexity_estimations", {}):
            complexity_stats = self.knowledge_base["complexity_estimations"][task_type].get(complexity.value, {})
            if complexity_stats:
                recommendations["expected_duration"] = complexity_stats.get("avg_duration", 0)
                recommendations["success_probability"] = complexity_stats.get("success_rate", 0.5)

        # 基于模板效果的推荐
        template_effectiveness = self.knowledge_base.get("template_effectiveness", {})
        suitable_templates = []
        for template, stats in template_effectiveness.items():
            if (task_type in stats.get("suitable_task_types", []) and
                stats["success_rate"] > 0.7 and stats["avg_quality_score"] > 0.6):
                suitable_templates.append((template, stats["avg_quality_score"]))

        if suitable_templates and not recommendations["recommended_template"]:
            suitable_templates.sort(key=lambda x: x[1], reverse=True)
            recommendations["recommended_template"] = suitable_templates[0][0]

        # 识别风险因素
        if pattern_key in self.knowledge_base.get("anti_patterns", {}):
            anti_patterns = self.knowledge_base["anti_patterns"][pattern_key]
            for anti_pattern in anti_patterns[-3:]:  # 最近3个反模式
                recommendations["risk_factors"].extend(anti_pattern["failure_factors"])

                # 基于反模式添加警告
                if "timeout_issues" in anti_pattern["failure_factors"]:
                    recommendations["warnings"].append("任务可能超时，建议设置更长的超时时间")
                if "too_many_agents" in anti_pattern["failure_factors"]:
                    recommendations["warnings"].append("避免使用过多agents，专注核心功能")
                if "conflict_issues" in anti_pattern["failure_factors"]:
                    recommendations["warnings"].append("注意工作空间冲突，建议使用独立工作空间")

        # 去重风险因素
        recommendations["risk_factors"] = list(set(recommendations["risk_factors"]))

        return recommendations

    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习摘要"""

        total_executions = len(self.execution_history)
        if total_executions == 0:
            return {"message": "暂无学习数据"}

        # 最近30天的执行
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_executions = [
            exec_result for exec_result in self.execution_history
            if datetime.fromisoformat(exec_result.execution_metrics.start_time.replace('Z', '+00:00')) > recent_cutoff
        ]

        success_count = len([e for e in recent_executions if e.status == ExecutionStatus.SUCCESS])
        success_rate = success_count / len(recent_executions) if recent_executions else 0

        avg_quality = sum(e.quality_score for e in recent_executions) / len(recent_executions) if recent_executions else 0
        avg_duration = sum(e.execution_metrics.duration_seconds for e in recent_executions) / len(recent_executions) if recent_executions else 0

        # 最常用的agents
        agent_usage = {}
        for exec_result in recent_executions:
            for agent in exec_result.execution_metrics.agents_used:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1

        top_agents = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:5]

        # 学习模式统计
        pattern_count = len(self.learning_patterns)
        best_practices_count = sum(len(practices) for practices in self.knowledge_base.get("best_practices", {}).values())
        anti_patterns_count = sum(len(patterns) for patterns in self.knowledge_base.get("anti_patterns", {}).values())

        return {
            "总执行次数": total_executions,
            "最近30天执行": len(recent_executions),
            "最近成功率": f"{success_rate:.1%}",
            "平均质量分数": f"{avg_quality:.2f}",
            "平均执行时间": f"{avg_duration:.1f}秒",
            "最常用agents": [f"{agent}({count}次)" for agent, count in top_agents],
            "学习模式数量": pattern_count,
            "最佳实践数量": best_practices_count,
            "反模式数量": anti_patterns_count,
            "知识库大小": len(self.knowledge_base),
            "最后更新": datetime.now().isoformat()
        }

    def export_knowledge(self, export_path: str) -> bool:
        """导出知识库"""
        try:
            export_data = {
                "execution_history": [self._execution_result_to_dict(result) for result in self.execution_history[-100:]],  # 最近100条
                "learning_patterns": [self._learning_data_to_dict(pattern) for pattern in self.learning_patterns],
                "knowledge_base": self.knowledge_base,
                "export_timestamp": datetime.now().isoformat(),
                "total_executions": len(self.execution_history)
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"知识库已导出到: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"导出知识库失败: {e}")
            return False

    def import_knowledge(self, import_path: str) -> bool:
        """导入知识库"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # 合并执行历史
            imported_history = [self._dict_to_execution_result(data) for data in import_data.get("execution_history", [])]
            self.execution_history.extend(imported_history)

            # 合并学习模式
            imported_patterns = [self._dict_to_learning_data(data) for data in import_data.get("learning_patterns", [])]
            self.learning_patterns.extend(imported_patterns)

            # 合并知识库
            imported_kb = import_data.get("knowledge_base", {})
            for key, value in imported_kb.items():
                if key not in self.knowledge_base:
                    self.knowledge_base[key] = value
                elif isinstance(value, dict):
                    self.knowledge_base[key].update(value)

            self._save_data()
            self.logger.info(f"知识库已从 {import_path} 导入")
            return True

        except Exception as e:
            self.logger.error(f"导入知识库失败: {e}")
            return False