#!/usr/bin/env python3
"""
Perfect21 Orchestrator工作流集成
将workflow_engine与orchestrator联通，实现真正的多Agent并行执行
"""

import logging
import json
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("OrchestratorIntegration")

class OrchestratorIntegration:
    """Orchestrator与工作流引擎的集成桥梁"""

    def __init__(self):
        self.workflow_engine = None
        self._init_workflow_engine()

    def _init_workflow_engine(self):
        """初始化工作流引擎"""
        try:
            from features.workflow_engine import create_workflow_engine
            self.workflow_engine = create_workflow_engine(max_workers=10)
            logger.info("Orchestrator工作流引擎集成成功")
        except Exception as e:
            logger.error(f"初始化工作流引擎失败: {e}")

    def execute_parallel_delegation(self, task_description: str,
                                  agent_assignments: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        执行并行Agent委托

        Args:
            task_description: 主任务描述
            agent_assignments: Agent分配列表 [{"agent": "backend-architect", "task": "...", "prompt": "..."}]

        Returns:
            Dict: 执行结果
        """
        if not self.workflow_engine:
            return {"error": "工作流引擎未初始化"}

        logger.info(f"开始并行执行: {task_description} - {len(agent_assignments)}个Agent")

        # 转换为工作流引擎格式
        tasks = []
        for assignment in agent_assignments:
            tasks.append({
                'agent_name': assignment.get('agent'),
                'description': assignment.get('task'),
                'prompt': assignment.get('prompt')
            })

        # 执行并行任务
        workflow_result = self.workflow_engine.execute_parallel_tasks(
            tasks,
            workflow_id=f"orchestrator_parallel_{len(agent_assignments)}agents"
        )

        # 转换结果格式
        return self._format_orchestrator_result(workflow_result)

    def execute_sequential_pipeline(self, task_description: str,
                                   pipeline_steps: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        执行顺序管道

        Args:
            task_description: 主任务描述
            pipeline_steps: 管道步骤列表

        Returns:
            Dict: 执行结果
        """
        if not self.workflow_engine:
            return {"error": "工作流引擎未初始化"}

        logger.info(f"开始顺序执行: {task_description} - {len(pipeline_steps)}个阶段")

        # 转换为工作流引擎格式
        pipeline = []
        for step in pipeline_steps:
            pipeline.append({
                'agent_name': step.get('agent'),
                'description': step.get('task'),
                'prompt': step.get('prompt')
            })

        # 执行顺序管道
        workflow_result = self.workflow_engine.execute_sequential_pipeline(
            pipeline,
            workflow_id=f"orchestrator_sequential_{len(pipeline_steps)}stages"
        )

        return self._format_orchestrator_result(workflow_result)

    def create_task_delegation_prompt(self, base_prompt: str, task_analysis: Dict[str, Any]) -> str:
        """
        创建任务委托的增强提示词

        Args:
            base_prompt: 基础提示词
            task_analysis: 任务分析结果

        Returns:
            str: 增强后的提示词
        """
        enhanced_prompt = f"""
{base_prompt}

## Perfect21工作流上下文

**主任务**: {task_analysis.get('main_task', '未指定')}
**执行模式**: {task_analysis.get('execution_mode', 'parallel')}
**依赖关系**: {json.dumps(task_analysis.get('dependencies', {}), ensure_ascii=False, indent=2)}

## 协作要求

1. **结果格式标准化**: 输出结果必须是JSON格式，包含status, result, metadata字段
2. **进度报告**: 重要步骤请实时反馈
3. **错误处理**: 遇到问题立即报告，不要静默失败
4. **上下文保持**: 记住你在整体工作流中的作用

## 集成指令

请执行你的专业任务，并确保结果可以与其他Agent的输出有效整合。
"""
        return enhanced_prompt

    def _format_orchestrator_result(self, workflow_result) -> Dict[str, Any]:
        """
        格式化给orchestrator的结果

        Args:
            workflow_result: 工作流执行结果

        Returns:
            Dict: 格式化的结果
        """
        return {
            "workflow_id": workflow_result.workflow_id,
            "status": workflow_result.status.value,
            "execution_time": workflow_result.execution_time,
            "summary": {
                "total_agents": len(workflow_result.tasks),
                "successful": workflow_result.success_count,
                "failed": workflow_result.failure_count,
                "success_rate": workflow_result.success_count / len(workflow_result.tasks) if workflow_result.tasks else 0
            },
            "agent_results": [
                {
                    "agent": task.agent_name,
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "description": task.description,
                    "result": task.result,
                    "error": task.error,
                    "execution_time": (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else 0
                }
                for task in workflow_result.tasks
            ],
            "integrated_result": workflow_result.integrated_result,
            "recommendations": self._generate_recommendations(workflow_result)
        }

    def _generate_recommendations(self, workflow_result) -> List[str]:
        """
        基于执行结果生成改进建议

        Args:
            workflow_result: 工作流执行结果

        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []

        if workflow_result.failure_count > 0:
            recommendations.append(f"有{workflow_result.failure_count}个Agent任务失败，建议检查错误日志")

        if workflow_result.execution_time > 300:  # 超过5分钟
            recommendations.append("执行时间较长，考虑优化任务分配或增加并行度")

        success_rate = workflow_result.success_count / len(workflow_result.tasks)
        if success_rate < 0.8:
            recommendations.append("成功率偏低，建议优化任务描述和Agent选择")

        return recommendations

    def get_available_agents(self) -> List[str]:
        """
        获取可用的Agent列表

        Returns:
            List[str]: 可用Agent名称列表
        """
        # 从claude-code-unified-agents获取Agent列表
        agents = [
            # Development Team
            "backend-architect",
            "frontend-specialist",
            "python-pro",
            "fullstack-engineer",
            "mobile-developer",
            "blockchain-developer",
            "typescript-pro",
            "javascript-pro",
            "react-pro",
            "vue-specialist",
            "nextjs-pro",
            "angular-expert",
            "golang-pro",
            "rust-pro",
            "java-enterprise",

            # Infrastructure Team
            "devops-engineer",
            "cloud-architect",
            "kubernetes-expert",
            "deployment-manager",
            "monitoring-specialist",

            # Quality Team
            "code-reviewer",
            "test-engineer",
            "e2e-test-specialist",
            "performance-tester",
            "accessibility-auditor",
            "security-auditor",

            # Data & AI Team
            "ai-engineer",
            "data-engineer",
            "data-scientist",
            "analytics-engineer",
            "mlops-engineer",
            "prompt-engineer",

            # Business Team
            "project-manager",
            "product-strategist",
            "business-analyst",
            "requirements-analyst",
            "api-designer",
            "technical-writer",

            # Creative Team
            "ux-designer",

            # Specialized
            "database-specialist",
            "performance-engineer",
            "incident-responder",
            "workflow-optimizer",
            "context-manager",
            "documentation-writer",
            "embedded-engineer",
            "fintech-specialist",
            "healthcare-dev",
            "ecommerce-expert",
            "game-developer",
            "error-detective",
            "agent-generator"
        ]

        return sorted(agents)

    def analyze_task_for_agents(self, task_description: str) -> Dict[str, Any]:
        """
        分析任务并推荐合适的Agent

        Args:
            task_description: 任务描述

        Returns:
            Dict: 分析结果和Agent推荐
        """
        # 简化的任务分析逻辑
        # 实际应该使用更智能的NLP分析

        task_lower = task_description.lower()
        recommended_agents = []
        execution_mode = "parallel"

        # 关键词匹配推荐
        if any(word in task_lower for word in ["api", "backend", "database", "server"]):
            recommended_agents.append("backend-architect")

        if any(word in task_lower for word in ["frontend", "ui", "react", "vue", "angular"]):
            recommended_agents.append("frontend-specialist")

        if any(word in task_lower for word in ["test", "testing", "qa"]):
            recommended_agents.append("test-engineer")

        if any(word in task_lower for word in ["deploy", "docker", "kubernetes", "ci/cd"]):
            recommended_agents.append("devops-engineer")

        if any(word in task_lower for word in ["security", "vulnerability", "audit"]):
            recommended_agents.append("security-auditor")

        if any(word in task_lower for word in ["review", "quality", "code quality"]):
            recommended_agents.append("code-reviewer")

        if any(word in task_lower for word in ["data", "ml", "ai", "machine learning"]):
            recommended_agents.append("ai-engineer")

        # 判断执行模式
        if any(word in task_lower for word in ["step by step", "sequential", "pipeline", "stage"]):
            execution_mode = "sequential"

        # 如果没有匹配到，使用通用Agent
        if not recommended_agents:
            recommended_agents = ["fullstack-engineer", "project-manager"]

        return {
            "main_task": task_description,
            "recommended_agents": recommended_agents,
            "execution_mode": execution_mode,
            "confidence": len(recommended_agents) / 10.0,  # 简化的置信度
            "dependencies": self._analyze_dependencies(recommended_agents),
            "estimated_time": len(recommended_agents) * 60  # 简化的时间估算
        }

    def _analyze_dependencies(self, agents: List[str]) -> Dict[str, List[str]]:
        """
        分析Agent之间的依赖关系

        Args:
            agents: Agent列表

        Returns:
            Dict: 依赖关系映射
        """
        # 简化的依赖关系定义
        dependencies = {}

        if "backend-architect" in agents and "test-engineer" in agents:
            dependencies["test-engineer"] = ["backend-architect"]

        if "frontend-specialist" in agents and "backend-architect" in agents:
            dependencies["frontend-specialist"] = ["backend-architect"]

        if "devops-engineer" in agents:
            # DevOps通常依赖其他开发完成
            deps = [agent for agent in agents if agent in ["backend-architect", "frontend-specialist", "fullstack-engineer"]]
            if deps:
                dependencies["devops-engineer"] = deps

        return dependencies

# 全局集成实例
_orchestrator_integration = None

def get_orchestrator_integration() -> OrchestratorIntegration:
    """获取全局orchestrator集成实例"""
    global _orchestrator_integration
    if _orchestrator_integration is None:
        _orchestrator_integration = OrchestratorIntegration()
    return _orchestrator_integration

def setup_orchestrator_workflow_capability():
    """
    为orchestrator设置工作流能力
    这个函数将在系统初始化时调用
    """
    integration = get_orchestrator_integration()
    logger.info("Orchestrator工作流能力设置完成")
    return integration