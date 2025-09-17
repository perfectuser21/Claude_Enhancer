#!/usr/bin/env python3
"""
Phase Executor - 阶段执行器
生成Claude Code需要执行的并行Agent调用指令
现在集成了执行监督系统
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

# 导入执行监督系统
from features.execution_supervisor import (
    ExecutionSupervisor,
    WorkflowGuardian,
    SmartReminder,
    ExecutionMonitor
)

logger = logging.getLogger("PhaseExecutor")

class ExecutionPhase(Enum):
    """执行阶段定义"""
    ANALYSIS = "analysis"          # 需求分析
    DESIGN = "design"              # 架构设计
    IMPLEMENTATION = "implementation"  # 代码实现
    TESTING = "testing"            # 测试验证
    DEPLOYMENT = "deployment"      # 部署发布

class PhaseExecutor:
    """
    阶段执行器 - 生成Claude Code需要执行的指令

    重要原则：
    1. 只生成指令，实际执行由Claude Code完成
    2. 确保每个阶段的agents并行执行
    3. 提供阶段间的数据传递机制
    4. 集成Git操作到合适的时机
    """

    def __init__(self):
        self.phase_configs = self._init_phase_configs()
        self.current_phase = None
        self.phase_results = {}

        # 初始化监督系统
        self.supervisor = ExecutionSupervisor()
        self.guardian = WorkflowGuardian()
        self.reminder = SmartReminder()
        self.monitor = ExecutionMonitor()

        logger.info("PhaseExecutor初始化完成 - 监督系统已集成")

    def _init_phase_configs(self) -> Dict[ExecutionPhase, Dict]:
        """初始化阶段配置"""
        return {
            ExecutionPhase.ANALYSIS: {
                'name': '需求分析阶段',
                'agents': ['project-manager', 'business-analyst', 'technical-writer'],
                'parallel': True,
                'git_operations': None,
                'sync_point': 'requirement_consensus',
                'description': '分析需求，理解业务目标，制定开发计划'
            },
            ExecutionPhase.DESIGN: {
                'name': '架构设计阶段',
                'agents': ['api-designer', 'backend-architect', 'database-specialist'],
                'parallel': True,
                'git_operations': ['create_feature_branch', 'commit_design_docs'],
                'sync_point': 'architecture_review',
                'description': '设计系统架构，API接口，数据库结构'
            },
            ExecutionPhase.IMPLEMENTATION: {
                'name': '代码实现阶段',
                'agents': ['backend-architect', 'frontend-specialist', 'test-engineer'],
                'parallel': True,
                'git_operations': ['commit_code', 'pre_commit_hook'],
                'sync_point': 'code_review',
                'description': '实现功能代码，编写测试用例'
            },
            ExecutionPhase.TESTING: {
                'name': '测试验证阶段',
                'agents': ['test-engineer', 'security-auditor', 'performance-engineer'],
                'parallel': True,
                'git_operations': ['run_tests', 'pre_push_hook'],
                'sync_point': 'quality_gate',
                'description': '运行测试，安全审计，性能测试'
            },
            ExecutionPhase.DEPLOYMENT: {
                'name': '部署发布阶段',
                'agents': ['devops-engineer', 'deployment-manager', 'monitoring-specialist'],
                'parallel': False,  # 部署阶段需要顺序执行
                'git_operations': ['merge_to_main', 'create_tag'],
                'sync_point': 'deployment_ready',
                'description': '部署到生产环境，监控系统状态'
            }
        }

    def generate_phase_instructions(self, phase: ExecutionPhase, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成阶段执行指令（现在带监督功能）

        返回Claude Code需要执行的指令，包括：
        1. 需要并行调用的agents列表
        2. Git操作指令
        3. 同步点检查要求
        4. 执行监督和提醒
        """
        if phase not in self.phase_configs:
            return {
                'success': False,
                'error': f'未知的执行阶段: {phase}'
            }

        # 开始监控
        self.monitor.start_phase_monitoring(phase.value)

        # 获取执行提醒
        reminder = self.supervisor.before_phase(phase.value, context)
        smart_tip = self.reminder.get_phase_reminder(phase.value, context or {})

        # 生成检查清单
        checklist = self.guardian.generate_execution_checklist(phase.value)
        formatted_checklist = self.guardian.format_checklist(checklist)

        config = self.phase_configs[phase]
        self.current_phase = phase

        # 构建并行执行指令
        instructions = {
            'phase': phase.value,
            'phase_name': config['name'],
            'description': config['description'],
            'agents_to_call': config['agents'],
            'execution_mode': 'parallel' if config['parallel'] else 'sequential',
            'sync_point': config['sync_point'],
            'git_operations': config['git_operations'] or [],
            'context': context or {}
        }

        # 生成Claude Code执行指令文本
        agent_calls = []
        for agent in config['agents']:
            agent_calls.append(f"Task(subagent_type='{agent}', prompt='...')")

        # 添加监督提醒到指令中
        instructions['supervision'] = {
            'reminder': reminder,
            'smart_tip': smart_tip,
            'checklist': formatted_checklist
        }

        # 检查执行计划
        plan_check = self.supervisor.check_execution_plan(phase.value, config['agents'])
        if not plan_check['approved']:
            instructions['warning'] = plan_check.get('warning', '')

        instructions['claude_code_instruction'] = f"""
{reminder}

{formatted_checklist}

请执行{config['name']}：

1. {'并行' if config['parallel'] else '顺序'}调用以下agents：
{chr(10).join(['   - ' + call for call in agent_calls])}

2. Git操作：
{chr(10).join(['   - ' + op for op in (config['git_operations'] or ['无'])]) if config['git_operations'] else '   无Git操作'}

3. 同步点：{config['sync_point']}
   完成后请验证所有agents的输出是否满足{config['sync_point']}要求

{smart_tip}

重要：
- {'这些agents必须在同一个消息中并行调用' if config['parallel'] else '请按顺序执行这些agents'}
- 收集所有输出后进行汇总
- 基于汇总结果生成下一阶段的任务
"""

        logger.info(f"生成{phase.value}阶段执行指令，包含{len(config['agents'])}个agents")

        return {
            'success': True,
            'instructions': instructions,
            'message': f"已生成{config['name']}的执行指令"
        }

    def get_parallel_agents(self, phase: ExecutionPhase) -> List[str]:
        """获取该阶段需要并行执行的agents"""
        if phase not in self.phase_configs:
            return []

        config = self.phase_configs[phase]
        if config['parallel']:
            return config['agents']
        return []

    def should_trigger_git_hook(self, phase: ExecutionPhase, git_status: Dict) -> bool:
        """判断是否需要触发Git Hook"""
        if phase not in self.phase_configs:
            return False

        config = self.phase_configs[phase]
        git_ops = config.get('git_operations', [])

        # 根据阶段和Git状态判断
        if phase == ExecutionPhase.IMPLEMENTATION:
            return 'pre_commit_hook' in git_ops and git_status.get('has_staged_changes', False)
        elif phase == ExecutionPhase.TESTING:
            return 'pre_push_hook' in git_ops
        elif phase == ExecutionPhase.DEPLOYMENT:
            return 'merge_to_main' in git_ops

        return False

    def get_phase_summary_prompt(self, phase: ExecutionPhase, agent_results: List[Dict]) -> str:
        """生成阶段汇总提示"""
        config = self.phase_configs.get(phase)
        if not config:
            return ""

        return f"""
请汇总{config['name']}的执行结果：

已完成的agents：
{chr(10).join([f"- {r.get('agent', 'unknown')}: {r.get('status', 'unknown')}" for r in agent_results])}

汇总要求：
1. 提取各agent输出的关键信息
2. 识别共同点和分歧
3. 生成结构化的阶段总结
4. 基于总结生成下一阶段的TODO列表

同步点验证：{config['sync_point']}
请确保所有必要的{config['sync_point']}条件已满足。
"""

    def record_phase_result(self, phase: ExecutionPhase, result: Dict) -> None:
        """记录阶段执行结果（带监督验证）"""
        self.phase_results[phase.value] = result

        # 验证执行质量
        validation = self.guardian.validate_execution(phase.value, result)
        quality_gate = self.guardian.enforce_quality_gate(phase.value, validation)

        # 记录执行历史
        self.supervisor.record_execution(phase.value, result)

        # 学习执行模式
        self.reminder.learn_from_execution(phase.value, result)

        # 结束监控
        monitor_report = self.monitor.end_phase_monitoring(phase.value, result.get('success', True))

        # 检测退化
        degradation_warning = self.supervisor.detect_degradation(phase.value, result)
        if degradation_warning:
            logger.warning(degradation_warning)

        logger.info(f"记录{phase.value}阶段执行结果 - 质量级别: {validation.get('quality_level')}")

    def get_next_phase(self, current_phase: ExecutionPhase) -> Optional[ExecutionPhase]:
        """获取下一个执行阶段"""
        phase_order = [
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.DESIGN,
            ExecutionPhase.IMPLEMENTATION,
            ExecutionPhase.TESTING,
            ExecutionPhase.DEPLOYMENT
        ]

        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass

        return None

    def validate_phase_transition(self, from_phase: ExecutionPhase, to_phase: ExecutionPhase) -> Dict[str, Any]:
        """验证阶段转换是否合法"""
        next_phase = self.get_next_phase(from_phase)

        if next_phase != to_phase:
            return {
                'valid': False,
                'message': f'不能从{from_phase.value}直接跳转到{to_phase.value}'
            }

        # 检查前置阶段是否完成
        if from_phase.value not in self.phase_results:
            return {
                'valid': False,
                'message': f'{from_phase.value}阶段尚未完成'
            }

        return {
            'valid': True,
            'message': f'可以从{from_phase.value}转换到{to_phase.value}'
        }