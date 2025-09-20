#!/usr/bin/env python3
"""
Perfect21 Phase Manager - Claude Hooks的5阶段执行管理器
自动引导Claude Code按5个阶段执行任务，每阶段并行多Agent
"""

import json
import os
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ExecutionPhase(Enum):
    """执行阶段枚举"""
    ANALYSIS = "analysis"      # 需求分析
    DESIGN = "design"          # 架构设计
    IMPLEMENTATION = "impl"    # 实现开发
    TESTING = "testing"        # 测试验证
    DEPLOYMENT = "deploy"      # 部署上线

class PhaseManager:
    """5阶段执行管理器"""

    def __init__(self):
        self.phase_config = {
            ExecutionPhase.ANALYSIS: {
                "name": "需求分析",
                "agents": [
                    "requirements-analyst",
                    "business-analyst",
                    "project-manager"
                ],
                "min_agents": 3,
                "execution_mode": "parallel",
                "prompts": {
                    "requirements-analyst": "分析用户需求，创建详细的需求规格说明，包括功能需求、非功能需求、用户故事和验收标准",
                    "business-analyst": "分析业务流程，识别业务价值，创建业务案例，评估ROI和风险",
                    "project-manager": "创建项目计划，定义里程碑，分配资源，识别依赖关系和风险"
                },
                "sync_point": "requirements_review",
                "git_operations": []
            },
            ExecutionPhase.DESIGN: {
                "name": "架构设计",
                "agents": [
                    "api-designer",
                    "backend-architect",
                    "database-specialist",
                    "frontend-specialist"
                ],
                "min_agents": 4,
                "execution_mode": "parallel",
                "prompts": {
                    "api-designer": "设计REST API或GraphQL schema，定义端点、请求/响应格式、认证方案",
                    "backend-architect": "设计后端架构，选择技术栈，定义服务边界，设计数据流",
                    "database-specialist": "设计数据库schema，定义表结构、关系、索引、优化策略",
                    "frontend-specialist": "设计前端架构，组件结构，状态管理，UI/UX方案"
                },
                "sync_point": "design_review",
                "git_operations": ["create_feature_branch", "init_project_structure"]
            },
            ExecutionPhase.IMPLEMENTATION: {
                "name": "实现开发",
                "agents": [
                    "fullstack-engineer",
                    "backend-architect",
                    "frontend-specialist",
                    "database-specialist",
                    "test-engineer"
                ],
                "min_agents": 5,
                "execution_mode": "parallel",
                "prompts": {
                    "fullstack-engineer": "实现核心功能，编写前后端代码，确保代码质量和最佳实践",
                    "backend-architect": "实现后端服务，API端点，业务逻辑，数据访问层",
                    "frontend-specialist": "实现前端组件，页面，交互逻辑，响应式设计",
                    "database-specialist": "创建数据库迁移脚本，优化查询，实现数据访问模式",
                    "test-engineer": "编写单元测试，集成测试，准备测试数据和测试场景"
                },
                "sync_point": "code_review",
                "git_operations": ["commit_changes", "run_pre_commit_hooks"]
            },
            ExecutionPhase.TESTING: {
                "name": "测试验证",
                "agents": [
                    "test-engineer",
                    "e2e-test-specialist",
                    "performance-tester",
                    "security-auditor"
                ],
                "min_agents": 4,
                "execution_mode": "parallel",
                "prompts": {
                    "test-engineer": "执行完整测试套件，验证功能正确性，测试覆盖率分析",
                    "e2e-test-specialist": "执行端到端测试，验证用户工作流，测试集成点",
                    "performance-tester": "执行性能测试，负载测试，识别性能瓶颈",
                    "security-auditor": "执行安全审计，漏洞扫描，验证安全最佳实践"
                },
                "sync_point": "quality_gate",
                "git_operations": ["run_tests", "generate_coverage_report"]
            },
            ExecutionPhase.DEPLOYMENT: {
                "name": "部署上线",
                "agents": [
                    "devops-engineer",
                    "monitoring-specialist",
                    "technical-writer"
                ],
                "min_agents": 3,
                "execution_mode": "sequential",  # 部署阶段顺序执行
                "prompts": {
                    "devops-engineer": "准备部署配置，CI/CD管道，容器化，环境配置",
                    "monitoring-specialist": "设置监控告警，日志收集，性能指标，健康检查",
                    "technical-writer": "更新文档，API文档，部署指南，用户手册"
                },
                "sync_point": "deployment_verification",
                "git_operations": ["tag_release", "merge_to_main"]
            }
        }

        # 状态管理
        self.current_phase = None
        self.phase_history = []
        self.context_pool = {}
        self.state_file = "/home/xx/dev/Perfect21/.perfect21/phase_state.json"
        self.load_state()

    def detect_task_type(self, user_request: str) -> bool:
        """检测是否需要进入5阶段执行"""
        # 编程任务关键词
        programming_keywords = [
            "实现", "开发", "创建", "构建", "编写", "设计",
            "implement", "develop", "create", "build", "write", "design",
            "api", "功能", "系统", "服务", "应用", "组件",
            "feature", "system", "service", "application", "component"
        ]

        request_lower = user_request.lower()
        return any(keyword in request_lower for keyword in programming_keywords)

    def should_start_phases(self, tool_name: str, params: dict) -> bool:
        """判断是否应该开始5阶段执行"""
        # 如果已在阶段中，继续执行
        if self.current_phase:
            return False

        # 检测Task工具调用
        if tool_name == "Task":
            task_desc = params.get("prompt", "")
            return self.detect_task_type(task_desc)

        return False

    def get_current_phase_config(self) -> dict:
        """获取当前阶段配置"""
        if not self.current_phase:
            self.current_phase = ExecutionPhase.ANALYSIS
        return self.phase_config[self.current_phase]

    def get_phase_agents(self, phase: ExecutionPhase) -> List[str]:
        """获取阶段所需的agents"""
        return self.phase_config[phase]["agents"]

    def generate_phase_instructions(self, phase: ExecutionPhase, context: dict) -> dict:
        """生成阶段执行指令"""
        config = self.phase_config[phase]

        # 生成agent调用指令
        agent_calls = []
        for agent in config["agents"]:
            prompt = config["prompts"].get(agent, f"执行{config['name']}相关任务")

            # 添加上下文信息
            if context:
                prompt += f"\n\n基于之前的分析结果:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

            agent_calls.append({
                "agent": agent,
                "prompt": prompt,
                "execution_mode": config["execution_mode"]
            })

        return {
            "phase": phase.value,
            "phase_name": config["name"],
            "agents_to_call": agent_calls,
            "min_agents": config["min_agents"],
            "sync_point": config["sync_point"],
            "git_operations": config["git_operations"]
        }

    def validate_agent_execution(self, agents_used: List[str]) -> Tuple[bool, List[str]]:
        """验证agent执行是否符合当前阶段要求"""
        if not self.current_phase:
            return False, ["未进入阶段执行模式"]

        config = self.phase_config[self.current_phase]
        errors = []

        # 检查agent数量
        if len(agents_used) < config["min_agents"]:
            errors.append(f"阶段{config['name']}需要至少{config['min_agents']}个agents，实际只有{len(agents_used)}个")

        # 检查必需的agents
        required_agents = set(config["agents"][:config["min_agents"]])
        used_agents = set(agents_used)
        missing = required_agents - used_agents

        if missing:
            errors.append(f"缺少必需的agents: {', '.join(missing)}")

        return len(errors) == 0, errors

    def advance_to_next_phase(self) -> Optional[ExecutionPhase]:
        """前进到下一阶段"""
        phase_order = [
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.DESIGN,
            ExecutionPhase.IMPLEMENTATION,
            ExecutionPhase.TESTING,
            ExecutionPhase.DEPLOYMENT
        ]

        if not self.current_phase:
            self.current_phase = ExecutionPhase.ANALYSIS
            return self.current_phase

        current_idx = phase_order.index(self.current_phase)
        if current_idx < len(phase_order) - 1:
            self.current_phase = phase_order[current_idx + 1]
            self.save_state()
            return self.current_phase

        return None

    def save_phase_results(self, phase: ExecutionPhase, results: dict):
        """保存阶段结果"""
        self.context_pool[phase.value] = {
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        self.phase_history.append({
            "phase": phase.value,
            "completed_at": datetime.now().isoformat(),
            "results_summary": len(results)
        })
        self.save_state()

    def get_context_for_phase(self, phase: ExecutionPhase) -> dict:
        """获取阶段所需的上下文"""
        context = {}

        # 获取前序阶段的结果
        phase_order = [
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.DESIGN,
            ExecutionPhase.IMPLEMENTATION,
            ExecutionPhase.TESTING
        ]

        current_idx = phase_order.index(phase) if phase in phase_order else -1

        # 收集之前所有阶段的结果
        for i in range(current_idx):
            prev_phase = phase_order[i]
            if prev_phase.value in self.context_pool:
                context[prev_phase.value] = self.context_pool[prev_phase.value]

        return context

    def reset_phases(self):
        """重置阶段状态"""
        self.current_phase = None
        self.phase_history = []
        self.context_pool = {}
        self.save_state()

    def save_state(self):
        """保存状态到文件"""
        state = {
            "current_phase": self.current_phase.value if self.current_phase else None,
            "phase_history": self.phase_history,
            "context_pool": self.context_pool
        }

        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_state(self):
        """从文件加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                phase_value = state.get("current_phase")
                if phase_value:
                    self.current_phase = ExecutionPhase(phase_value)
                else:
                    self.current_phase = None

                self.phase_history = state.get("phase_history", [])
                self.context_pool = state.get("context_pool", {})
            except Exception as e:
                print(f"加载状态失败: {e}")
                self.reset_phases()

    def generate_phase_summary(self) -> str:
        """生成阶段执行摘要"""
        if not self.phase_history:
            return "尚未执行任何阶段"

        summary = "📊 **阶段执行摘要**\n\n"
        for item in self.phase_history:
            phase_name = self.phase_config[ExecutionPhase(item["phase"])]["name"]
            summary += f"✅ **{phase_name}** - 完成于 {item['completed_at']}\n"

        if self.current_phase:
            current_name = self.phase_config[self.current_phase]["name"]
            summary += f"\n🔄 **当前阶段**: {current_name}\n"

        return summary


# 单例实例
_phase_manager = None

def get_phase_manager() -> PhaseManager:
    """获取阶段管理器单例"""
    global _phase_manager
    if _phase_manager is None:
        _phase_manager = PhaseManager()
    return _phase_manager