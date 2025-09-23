#!/usr/bin/env python3
"""
Claude Enhancer Core Orchestrator - Agent协调器
负责协调多个Agent的并行执行，实现4-6-8策略
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
from enum import Enum
import random


class ComplexityLevel(Enum):
    """任务复杂度级别"""

    SIMPLE = "simple"  # 4个Agent
    STANDARD = "standard"  # 6个Agent
    COMPLEX = "complex"  # 8个Agent


class AgentCategory(Enum):
    """Agent分类"""

    BUSINESS = "business"
    CREATIVE = "creative"
    DATA_AI = "data-ai"
    DEVELOPMENT = "development"
    INFRASTRUCTURE = "infrastructure"
    QUALITY = "quality"
    SPECIALIZED = "specialized"


class AgentOrchestrator:
    """
    Agent协调器
    负责选择、组织和协调多个Agent的并行执行
    """

    def __init__(self):
        self.agents_dir = ".claude/agents"
        self.min_agents = 4  # 最少Agent数量
        self.max_agents = 8  # 最多Agent数量
        self.available_agents = self._load_available_agents()

    def _load_available_agents(self) -> Dict[str, List[str]]:
        """加载所有可用的Agent"""
        agents = {}

        # 按类别组织Agent
        agent_categories = {
            "business": [
                "api-designer",
                "business-analyst",
                "product-strategist",
                "project-manager",
                "requirements-analyst",
                "technical-writer",
            ],
            "creative": ["ux-designer"],
            "data-ai": [
                "ai-engineer",
                "analytics-engineer",
                "data-engineer",
                "data-scientist",
                "mlops-engineer",
                "prompt-engineer",
            ],
            "development": [
                "angular-expert",
                "backend-architect",
                "backend-engineer",
                "database-specialist",
                "frontend-specialist",
                "fullstack-engineer",
                "golang-pro",
                "java-enterprise",
                "javascript-pro",
                "nextjs-pro",
                "python-pro",
                "react-pro",
                "rust-pro",
                "typescript-pro",
                "vue-specialist",
            ],
            "infrastructure": [
                "cloud-architect",
                "deployment-manager",
                "devops-engineer",
                "incident-responder",
                "kubernetes-expert",
                "monitoring-specialist",
                "performance-engineer",
            ],
            "quality": [
                "accessibility-auditor",
                "code-reviewer",
                "e2e-test-specialist",
                "performance-tester",
                "security-auditor",
                "test-engineer",
            ],
            "specialized": [
                "agent-generator",
                "blockchain-developer",
                "cleanup-specialist",
                "context-manager",
                "documentation-writer",
                "ecommerce-expert",
                "embedded-engineer",
                "error-detective",
                "fintech-specialist",
                "game-developer",
                "healthcare-dev",
                "mobile-developer",
                "workflow-optimizer",
            ],
        }

        return agent_categories

    def detect_complexity(self, task_description: str) -> ComplexityLevel:
        """检测任务复杂度"""
        description_lower = task_description.lower()

        # 复杂任务关键词
        complex_keywords = [
            "architecture",
            "system design",
            "架构",
            "系统设计",
            "microservices",
            "distributed",
            "migration",
            "迁移",
            "refactor entire",
            "重构整个",
            "performance optimization",
        ]

        # 标准任务关键词
        standard_keywords = [
            "new feature",
            "api",
            "database",
            "新功能",
            "integration",
            "authentication",
            "deployment",
            "部署",
        ]

        # 检测复杂度
        if any(keyword in description_lower for keyword in complex_keywords):
            return ComplexityLevel.COMPLEX
        elif any(keyword in description_lower for keyword in standard_keywords):
            return ComplexityLevel.STANDARD
        else:
            return ComplexityLevel.SIMPLE

    def select_agents(
        self,
        task_description: str,
        complexity: Optional[ComplexityLevel] = None,
        required_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        智能选择Agent组合
        实现4-6-8策略
        """
        # 自动检测复杂度
        if complexity is None:
            complexity = self.detect_complexity(task_description)

        # 确定Agent数量
        agent_count = {
            ComplexityLevel.SIMPLE: 4,
            ComplexityLevel.STANDARD: 6,
            ComplexityLevel.COMPLEX: 8,
        }[complexity]

        # 分析任务特征
        task_features = self._analyze_task_features(task_description)

        # 选择Agent
        selected_agents = []

        # 1. 添加必需的Agent
        if required_agents:
            selected_agents.extend(required_agents[:agent_count])

        # 2. 根据任务特征添加相关Agent
        for feature, agents in task_features.items():
            for agent in agents:
                if agent not in selected_agents and len(selected_agents) < agent_count:
                    selected_agents.append(agent)

        # 3. 补充到所需数量
        if len(selected_agents) < agent_count:
            selected_agents.extend(
                self._get_complementary_agents(
                    selected_agents, agent_count - len(selected_agents)
                )
            )

        return {
            "complexity": complexity.value,
            "agent_count": agent_count,
            "selected_agents": selected_agents[:agent_count],
            "execution_mode": "parallel",
            "estimated_time": self._estimate_time(complexity),
            "rationale": self._generate_rationale(task_description, selected_agents),
        }

    def _analyze_task_features(self, task_description: str) -> Dict[str, List[str]]:
        """分析任务特征，返回推荐的Agent"""
        features = {}
        description_lower = task_description.lower()

        # 前端相关
        if any(
            word in description_lower
            for word in ["frontend", "ui", "react", "vue", "angular", "前端"]
        ):
            features["frontend"] = [
                "frontend-specialist",
                "react-pro",
                "vue-specialist",
                "ux-designer",
            ]

        # 后端相关
        if any(
            word in description_lower
            for word in ["backend", "api", "server", "后端", "接口"]
        ):
            features["backend"] = [
                "backend-architect",
                "backend-engineer",
                "api-designer",
                "database-specialist",
            ]

        # 测试相关
        if any(
            word in description_lower for word in ["test", "testing", "quality", "测试"]
        ):
            features["testing"] = [
                "test-engineer",
                "e2e-test-specialist",
                "performance-tester",
            ]

        # 安全相关
        if any(
            word in description_lower
            for word in ["security", "vulnerability", "安全", "漏洞"]
        ):
            features["security"] = ["security-auditor", "code-reviewer"]

        # 性能相关
        if any(
            word in description_lower
            for word in ["performance", "optimization", "性能", "优化"]
        ):
            features["performance"] = ["performance-engineer", "performance-tester"]

        # 部署相关
        if any(
            word in description_lower
            for word in ["deploy", "deployment", "ci/cd", "部署"]
        ):
            features["deployment"] = [
                "deployment-manager",
                "devops-engineer",
                "kubernetes-expert",
            ]

        # 错误修复
        if any(
            word in description_lower for word in ["bug", "error", "fix", "修复", "错误"]
        ):
            features["debugging"] = [
                "error-detective",
                "incident-responder",
                "test-engineer",
            ]

        return features

    def _get_complementary_agents(self, selected: List[str], count: int) -> List[str]:
        """获取补充的Agent"""
        complementary = []

        # 通用有用的Agent
        useful_agents = [
            "code-reviewer",  # 代码审查总是有用
            "test-engineer",  # 测试总是需要
            "technical-writer",  # 文档很重要
            "workflow-optimizer",  # 优化工作流
            "error-detective",  # 发现潜在问题
        ]

        for agent in useful_agents:
            if agent not in selected and len(complementary) < count:
                complementary.append(agent)

        # 如果还不够，从所有Agent中随机选择
        if len(complementary) < count:
            all_agents = []
            for category_agents in self.available_agents.values():
                all_agents.extend(category_agents)

            available = [
                a for a in all_agents if a not in selected and a not in complementary
            ]
            random.shuffle(available)
            complementary.extend(available[: count - len(complementary)])

        return complementary

    def _estimate_time(self, complexity: ComplexityLevel) -> str:
        """估算执行时间"""
        time_map = {
            ComplexityLevel.SIMPLE: "5-10分钟",
            ComplexityLevel.STANDARD: "15-20分钟",
            ComplexityLevel.COMPLEX: "25-30分钟",
        }
        return time_map[complexity]

    def _generate_rationale(self, task_description: str, agents: List[str]) -> str:
        """生成Agent选择理由"""
        return f"基于任务 '{task_description[:50]}...' 的分析，选择了 {len(agents)} 个专业Agent进行并行协作"

    def validate_agent_count(self, agents: List[str]) -> Dict[str, Any]:
        """验证Agent数量是否符合要求"""
        count = len(agents)

        if count < self.min_agents:
            return {
                "valid": False,
                "error": f"Agent数量不足。最少需要{self.min_agents}个，当前只有{count}个",
                "suggestion": "请添加更多Agent或使用select_agents自动选择",
            }

        if count > self.max_agents:
            return {
                "valid": False,
                "error": f"Agent数量过多。最多{self.max_agents}个，当前有{count}个",
                "suggestion": "请减少Agent数量或优先选择最重要的Agent",
            }

        return {
            "valid": True,
            "message": f"Agent数量合适: {count}个",
            "complexity": self._get_complexity_by_count(count),
        }

    def _get_complexity_by_count(self, count: int) -> str:
        """根据Agent数量判断复杂度"""
        if count <= 4:
            return ComplexityLevel.SIMPLE.value
        elif count <= 6:
            return ComplexityLevel.STANDARD.value
        else:
            return ComplexityLevel.COMPLEX.value

    def generate_parallel_command(self, agents: List[str], task: str) -> str:
        """生成并行执行命令"""
        command = "# Claude Code应该使用以下Agent并行执行:\n"
        command += "# 在一个消息中同时调用所有Agent\n\n"

        for agent in agents:
            command += f"Task(subagent_type='{agent}', prompt='{task}')\n"

        return command

    def check_parallel_execution(self, execution_plan: str) -> bool:
        """检查是否真的是并行执行"""
        # 简单检查：是否在同一个function_calls块中
        lines = execution_plan.split("\n")
        function_calls_count = sum(1 for line in lines if "<function_calls>" in line)
        task_count = sum(
            1 for line in lines if "Task" in line or "subagent_type" in line
        )

        # 如果只有一个function_calls块且包含多个Task，认为是并行
        return function_calls_count == 1 and task_count >= self.min_agents


# CLI接口
if __name__ == "__main__":
    orchestrator = AgentOrchestrator()

    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command> [args]")
        print("Commands:")
        print("  select <description> - Select agents for task")
        print("  validate <agent1,agent2,...> - Validate agent count")
        print("  complexity <description> - Detect task complexity")
        sys.exit(1)

    command = sys.argv[1]

    if command == "select" and len(sys.argv) > 2:
        description = " ".join(sys.argv[2:])
        result = orchestrator.select_agents(description)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "validate" and len(sys.argv) > 2:
        agents = sys.argv[2].split(",")
        result = orchestrator.validate_agent_count(agents)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "complexity" and len(sys.argv) > 2:
        description = " ".join(sys.argv[2:])
        complexity = orchestrator.detect_complexity(description)
        print(f"Task complexity: {complexity.value}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
