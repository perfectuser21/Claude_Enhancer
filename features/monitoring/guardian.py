#!/usr/bin/env python3
"""
Workflow Guardian - 工作流守护者
确保工作流执行符合Perfect21的质量标准
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("WorkflowGuardian")

class QualityLevel(Enum):
    """质量级别"""
    EXCELLENT = "excellent"   # 优秀：完全并行
    GOOD = "good"             # 良好：大部分并行
    ACCEPTABLE = "acceptable" # 可接受：部分并行
    POOR = "poor"            # 差：大部分串行
    FAILED = "failed"        # 失败：完全串行

class WorkflowGuardian:
    """
    工作流守护者 - 守护Perfect21的执行质量

    主要功能：
    1. 定义执行规则
    2. 生成检查清单
    3. 验证执行质量
    4. 强制质量门
    """

    def __init__(self):
        self.rules = {
            'min_parallel_agents': 2,       # 最少并行agent数
            'require_sync_point': True,     # 必须有同步点
            'enforce_git_hooks': True,      # 强制Git Hook
            'require_summary': True,        # 必须有汇总
            'require_todo_generation': True, # 必须生成TODO
            'max_sequential_operations': 3  # 最多连续串行操作数
        }

        self.quality_thresholds = {
            QualityLevel.EXCELLENT: 0.9,  # 90%以上并行
            QualityLevel.GOOD: 0.7,       # 70%以上并行
            QualityLevel.ACCEPTABLE: 0.5, # 50%以上并行
            QualityLevel.POOR: 0.3,       # 30%以上并行
            QualityLevel.FAILED: 0        # 完全串行
        }

        self.checklist_status = {}
        self.violations = []

        logger.info("WorkflowGuardian初始化 - 质量守护已启动")

    def generate_execution_checklist(self, phase: str) -> List[Dict[str, Any]]:
        """
        生成执行检查清单

        Args:
            phase: 阶段名称

        Returns:
            检查清单项列表
        """
        checklist = [
            {
                'id': 'parallel_agents',
                'description': f"并行调用至少{self.rules['min_parallel_agents']}个agents",
                'required': True,
                'phase': phase
            },
            {
                'id': 'wait_completion',
                'description': "等待所有agents完成执行",
                'required': True,
                'phase': phase
            },
            {
                'id': 'sync_point',
                'description': "执行同步点检查",
                'required': self.rules['require_sync_point'],
                'phase': phase
            },
            {
                'id': 'result_summary',
                'description': "汇总所有agents的结果",
                'required': self.rules['require_summary'],
                'phase': phase
            },
            {
                'id': 'todo_generation',
                'description': "生成下一阶段TODO",
                'required': self.rules['require_todo_generation'],
                'phase': phase
            },
            {
                'id': 'git_operations',
                'description': "执行必要的Git操作",
                'required': phase in ['design', 'implementation', 'deployment'],
                'phase': phase
            },
            {
                'id': 'quality_check',
                'description': "通过质量检查",
                'required': True,
                'phase': phase
            }
        ]

        # 初始化检查状态
        for item in checklist:
            key = f"{phase}_{item['id']}"
            self.checklist_status[key] = {
                'checked': False,
                'timestamp': None,
                'result': None
            }

        return checklist

    def format_checklist(self, checklist: List[Dict[str, Any]]) -> str:
        """
        格式化检查清单为可读格式
        """
        formatted = """
📋 执行检查清单
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for i, item in enumerate(checklist, 1):
            status = self._get_check_status(item['phase'], item['id'])
            checkbox = "✅" if status['checked'] else "☐"
            required = "【必需】" if item['required'] else "【可选】"

            formatted += f"{checkbox} {i}. {item['description']} {required}\n"

        formatted += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        return formatted

    def validate_execution(self, phase: str, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证执行是否符合规则

        Args:
            phase: 阶段名称
            execution_data: 执行数据

        Returns:
            验证结果
        """
        violations = []
        warnings = []

        # 检查并行agent数量
        agent_count = execution_data.get('agent_count', 0)
        if agent_count < self.rules['min_parallel_agents']:
            violations.append(f"并行agent数量不足：{agent_count} < {self.rules['min_parallel_agents']}")

        # 检查同步点
        if self.rules['require_sync_point'] and not execution_data.get('sync_point_executed'):
            violations.append("未执行同步点检查")

        # 检查汇总
        if self.rules['require_summary'] and not execution_data.get('summary_generated'):
            violations.append("未生成结果汇总")

        # 检查TODO生成
        if self.rules['require_todo_generation'] and not execution_data.get('todos_generated'):
            warnings.append("未生成下阶段TODO")

        # 检查串行操作
        sequential_count = execution_data.get('sequential_operations', 0)
        if sequential_count > self.rules['max_sequential_operations']:
            violations.append(f"串行操作过多：{sequential_count} > {self.rules['max_sequential_operations']}")

        # 计算质量级别
        quality_level = self._calculate_quality_level(execution_data)

        # 记录违规
        if violations:
            self.violations.extend(violations)

        result = {
            'phase': phase,
            'valid': len(violations) == 0,
            'quality_level': quality_level,
            'violations': violations,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }

        if not result['valid']:
            result['enforcement_action'] = self._get_enforcement_action(violations)

        logger.info(f"{phase}阶段验证结果：{quality_level.value}，违规数：{len(violations)}")

        return result

    def enforce_quality_gate(self, phase: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        强制执行质量门

        Args:
            phase: 阶段名称
            validation_result: 验证结果

        Returns:
            质量门结果
        """
        quality_level = validation_result['quality_level']
        violations = validation_result.get('violations', [])

        # 质量门判定
        if quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]:
            gate_result = 'PASSED'
            action = None
        elif quality_level == QualityLevel.ACCEPTABLE:
            gate_result = 'PASSED_WITH_WARNING'
            action = 'IMPROVEMENT_REQUIRED'
        else:
            gate_result = 'FAILED'
            action = 'MUST_RETRY'

        result = {
            'phase': phase,
            'gate_result': gate_result,
            'quality_level': quality_level.value,
            'required_action': action,
            'message': self._generate_gate_message(gate_result, quality_level, violations)
        }

        if gate_result == 'FAILED':
            result['retry_guidance'] = self._generate_retry_guidance(phase, violations)

        logger.info(f"{phase}阶段质量门结果：{gate_result}")

        return result

    def mark_check_completed(self, phase: str, check_id: str, result: bool = True) -> None:
        """
        标记检查项完成

        Args:
            phase: 阶段名称
            check_id: 检查项ID
            result: 检查结果
        """
        key = f"{phase}_{check_id}"
        if key in self.checklist_status:
            self.checklist_status[key] = {
                'checked': True,
                'timestamp': datetime.now().isoformat(),
                'result': result
            }
            logger.debug(f"标记检查项完成：{key} = {result}")

    def get_guardian_report(self) -> Dict[str, Any]:
        """
        获取守护者报告
        """
        # 统计检查完成情况
        total_checks = len(self.checklist_status)
        completed_checks = sum(1 for status in self.checklist_status.values() if status['checked'])
        passed_checks = sum(1 for status in self.checklist_status.values()
                          if status['checked'] and status['result'])

        report = {
            'total_checks': total_checks,
            'completed_checks': completed_checks,
            'passed_checks': passed_checks,
            'completion_rate': (completed_checks / total_checks * 100) if total_checks > 0 else 0,
            'pass_rate': (passed_checks / completed_checks * 100) if completed_checks > 0 else 0,
            'total_violations': len(self.violations),
            'recent_violations': self.violations[-5:],  # 最近5个违规
            'rules': self.rules
        }

        return report

    def _get_check_status(self, phase: str, check_id: str) -> Dict[str, Any]:
        """获取检查项状态"""
        key = f"{phase}_{check_id}"
        return self.checklist_status.get(key, {
            'checked': False,
            'timestamp': None,
            'result': None
        })

    def _calculate_quality_level(self, execution_data: Dict[str, Any]) -> QualityLevel:
        """计算质量级别"""
        total_operations = execution_data.get('total_operations', 1)
        parallel_operations = execution_data.get('parallel_operations', 0)

        if total_operations == 0:
            return QualityLevel.FAILED

        parallel_ratio = parallel_operations / total_operations

        for level, threshold in self.quality_thresholds.items():
            if parallel_ratio >= threshold:
                return level

        return QualityLevel.FAILED

    def _get_enforcement_action(self, violations: List[str]) -> str:
        """获取强制执行动作"""
        if len(violations) >= 3:
            return "BLOCK_EXECUTION"  # 阻止执行
        elif len(violations) >= 2:
            return "REQUIRE_APPROVAL"  # 需要批准
        else:
            return "WARNING_ONLY"      # 仅警告

    def _generate_gate_message(self, gate_result: str, quality_level: QualityLevel,
                               violations: List[str]) -> str:
        """生成质量门消息"""
        if gate_result == 'PASSED':
            return f"✅ 质量门通过 - 质量级别：{quality_level.value}"
        elif gate_result == 'PASSED_WITH_WARNING':
            return f"⚠️ 质量门通过（有警告）- 质量级别：{quality_level.value}"
        else:
            violation_list = '\n'.join([f"  • {v}" for v in violations])
            return f"""
❌ 质量门失败 - 质量级别：{quality_level.value}

违规项：
{violation_list}

必须修复这些问题才能继续！
"""

    def _generate_retry_guidance(self, phase: str, violations: List[str]) -> str:
        """生成重试指导"""
        guidance = f"""
🔄 {phase}阶段重试指导
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

需要修复的问题：
"""
        for i, violation in enumerate(violations, 1):
            guidance += f"{i}. {violation}\n"
            guidance += f"   修复建议：{self._get_fix_suggestion(violation)}\n\n"

        guidance += """
执行步骤：
1. 停止当前执行
2. 按照修复建议调整
3. 重新执行该阶段
4. 确保所有检查项通过
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return guidance

    def _get_fix_suggestion(self, violation: str) -> str:
        """获取修复建议"""
        if "并行agent数量不足" in violation:
            return "增加更多agents到执行计划"
        elif "未执行同步点" in violation:
            return "在所有agents完成后添加同步点检查"
        elif "未生成结果汇总" in violation:
            return "收集并汇总所有agents的输出"
        elif "串行操作过多" in violation:
            return "将串行操作改为并行执行"
        else:
            return "参考Perfect21最佳实践进行修复"