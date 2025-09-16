#!/usr/bin/env python3
"""
Perfect21 开发任务编排器
将所有开发任务智能路由到适合的SubAgent组合
实现多Agent协作开发的统一入口
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.parallel_monitor import get_global_monitor, monitor_task

class TaskType(Enum):
    """开发任务类型"""
    # 代码开发
    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    CODE_REVIEW = "code_review"

    # 测试相关
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    E2E_TESTING = "e2e_testing"
    PERFORMANCE_TESTING = "performance_testing"

    # 架构设计
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"
    SYSTEM_ARCHITECTURE = "system_architecture"
    MICROSERVICES_DESIGN = "microservices_design"

    # 部署运维
    CI_CD_SETUP = "ci_cd_setup"
    DEPLOYMENT = "deployment"
    MONITORING_SETUP = "monitoring_setup"
    SECURITY_AUDIT = "security_audit"

    # 文档和分析
    DOCUMENTATION = "documentation"
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    BUSINESS_ANALYSIS = "business_analysis"

    # 技术栈特定
    FRONTEND_DEVELOPMENT = "frontend_development"
    BACKEND_DEVELOPMENT = "backend_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    DATA_ENGINEERING = "data_engineering"
    AI_ML_DEVELOPMENT = "ai_ml_development"

@dataclass
class AgentCapability:
    """Agent能力定义"""
    agent_name: str
    specialties: List[str]
    task_types: List[TaskType]
    collaboration_level: int  # 1-5，协作复杂度
    parallel_safe: bool  # 是否支持并行执行

@dataclass
class DevelopmentTask:
    """开发任务定义"""
    task_id: str
    description: str
    task_type: TaskType
    priority: int  # 1-5
    estimated_complexity: int  # 1-10
    required_agents: List[str]
    context: Dict[str, Any]
    dependencies: List[str] = None

class DevelopmentOrchestrator:
    """开发任务编排器"""

    def __init__(self):
        self.agents_registry = self._initialize_agents_registry()
        self.active_tasks: Dict[str, DevelopmentTask] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.monitor = get_global_monitor()

    def _initialize_agents_registry(self) -> Dict[str, AgentCapability]:
        """初始化Agent注册表"""
        agents = {
            # 编程语言专家
            "@python-pro": AgentCapability(
                "@python-pro",
                ["Python", "异步编程", "性能优化"],
                [TaskType.FEATURE_DEVELOPMENT, TaskType.BUG_FIX, TaskType.BACKEND_DEVELOPMENT],
                3, True
            ),
            "@javascript-pro": AgentCapability(
                "@javascript-pro",
                ["JavaScript", "ES6+", "Node.js"],
                [TaskType.FEATURE_DEVELOPMENT, TaskType.FRONTEND_DEVELOPMENT],
                3, True
            ),
            "@typescript-pro": AgentCapability(
                "@typescript-pro",
                ["TypeScript", "类型系统", "大型应用"],
                [TaskType.FEATURE_DEVELOPMENT, TaskType.REFACTORING],
                4, True
            ),
            "@rust-pro": AgentCapability(
                "@rust-pro",
                ["Rust", "系统编程", "内存安全"],
                [TaskType.FEATURE_DEVELOPMENT, TaskType.PERFORMANCE_TESTING],
                4, True
            ),
            "@golang-pro": AgentCapability(
                "@golang-pro",
                ["Go", "并发编程", "微服务"],
                [TaskType.MICROSERVICES_DESIGN, TaskType.BACKEND_DEVELOPMENT],
                3, True
            ),
            "@java-enterprise": AgentCapability(
                "@java-enterprise",
                ["Java", "Spring Boot", "企业应用"],
                [TaskType.FEATURE_DEVELOPMENT, TaskType.SYSTEM_ARCHITECTURE],
                4, True
            ),

            # 前端框架专家
            "@react-pro": AgentCapability(
                "@react-pro",
                ["React", "Hooks", "状态管理"],
                [TaskType.FRONTEND_DEVELOPMENT, TaskType.FEATURE_DEVELOPMENT],
                3, True
            ),
            "@vue-specialist": AgentCapability(
                "@vue-specialist",
                ["Vue.js", "Composition API", "Nuxt"],
                [TaskType.FRONTEND_DEVELOPMENT, TaskType.FEATURE_DEVELOPMENT],
                3, True
            ),
            "@angular-expert": AgentCapability(
                "@angular-expert",
                ["Angular", "RxJS", "企业前端"],
                [TaskType.FRONTEND_DEVELOPMENT, TaskType.SYSTEM_ARCHITECTURE],
                4, True
            ),
            "@nextjs-pro": AgentCapability(
                "@nextjs-pro",
                ["Next.js", "SSR", "全栈开发"],
                [TaskType.FRONTEND_DEVELOPMENT, TaskType.BACKEND_DEVELOPMENT],
                4, True
            ),

            # 架构和设计专家
            "@backend-architect": AgentCapability(
                "@backend-architect",
                ["后端架构", "API设计", "数据库设计"],
                [TaskType.SYSTEM_ARCHITECTURE, TaskType.API_DESIGN, TaskType.DATABASE_DESIGN],
                5, False
            ),
            "@fullstack-engineer": AgentCapability(
                "@fullstack-engineer",
                ["全栈开发", "系统整合", "端到端"],
                [TaskType.FEATURE_DEVELOPMENT, TaskType.SYSTEM_ARCHITECTURE],
                4, True
            ),
            "@api-designer": AgentCapability(
                "@api-designer",
                ["REST API", "GraphQL", "OpenAPI"],
                [TaskType.API_DESIGN, TaskType.DOCUMENTATION],
                3, True
            ),
            "@database-specialist": AgentCapability(
                "@database-specialist",
                ["数据库设计", "性能优化", "SQL/NoSQL"],
                [TaskType.DATABASE_DESIGN, TaskType.PERFORMANCE_TESTING],
                3, True
            ),

            # DevOps和基础设施
            "@devops-engineer": AgentCapability(
                "@devops-engineer",
                ["CI/CD", "容器化", "云平台"],
                [TaskType.CI_CD_SETUP, TaskType.DEPLOYMENT],
                4, True
            ),
            "@cloud-architect": AgentCapability(
                "@cloud-architect",
                ["云架构", "AWS", "可扩展性"],
                [TaskType.SYSTEM_ARCHITECTURE, TaskType.DEPLOYMENT],
                5, False
            ),
            "@kubernetes-expert": AgentCapability(
                "@kubernetes-expert",
                ["Kubernetes", "容器编排", "云原生"],
                [TaskType.DEPLOYMENT, TaskType.MONITORING_SETUP],
                4, True
            ),
            "@monitoring-specialist": AgentCapability(
                "@monitoring-specialist",
                ["系统监控", "日志分析", "告警"],
                [TaskType.MONITORING_SETUP, TaskType.PERFORMANCE_TESTING],
                3, True
            ),

            # 质量保证
            "@test-engineer": AgentCapability(
                "@test-engineer",
                ["测试策略", "自动化测试", "质量保证"],
                [TaskType.UNIT_TESTING, TaskType.INTEGRATION_TESTING, TaskType.E2E_TESTING],
                3, True
            ),
            "@e2e-test-specialist": AgentCapability(
                "@e2e-test-specialist",
                ["端到端测试", "Playwright", "测试自动化"],
                [TaskType.E2E_TESTING, TaskType.INTEGRATION_TESTING],
                3, True
            ),
            "@performance-tester": AgentCapability(
                "@performance-tester",
                ["性能测试", "负载测试", "基准测试"],
                [TaskType.PERFORMANCE_TESTING],
                3, True
            ),
            "@code-reviewer": AgentCapability(
                "@code-reviewer",
                ["代码审查", "最佳实践", "质量检查"],
                [TaskType.CODE_REVIEW, TaskType.REFACTORING],
                2, True
            ),

            # 安全专家
            "@security-auditor": AgentCapability(
                "@security-auditor",
                ["安全审计", "漏洞扫描", "合规检查"],
                [TaskType.SECURITY_AUDIT, TaskType.CODE_REVIEW],
                3, True
            ),

            # 业务和需求
            "@business-analyst": AgentCapability(
                "@business-analyst",
                ["业务分析", "流程优化", "需求分析"],
                [TaskType.BUSINESS_ANALYSIS, TaskType.REQUIREMENTS_ANALYSIS],
                4, False
            ),
            "@requirements-analyst": AgentCapability(
                "@requirements-analyst",
                ["需求工程", "用户故事", "需求文档"],
                [TaskType.REQUIREMENTS_ANALYSIS, TaskType.DOCUMENTATION],
                3, False
            ),
            "@product-strategist": AgentCapability(
                "@product-strategist",
                ["产品策略", "市场分析", "功能规划"],
                [TaskType.REQUIREMENTS_ANALYSIS, TaskType.BUSINESS_ANALYSIS],
                4, False
            ),

            # 文档和设计
            "@technical-writer": AgentCapability(
                "@technical-writer",
                ["技术文档", "用户指南", "API文档"],
                [TaskType.DOCUMENTATION],
                2, True
            ),
            "@ux-designer": AgentCapability(
                "@ux-designer",
                ["用户体验", "界面设计", "用户研究"],
                [TaskType.FRONTEND_DEVELOPMENT, TaskType.REQUIREMENTS_ANALYSIS],
                3, True
            ),

            # 专业领域
            "@ai-engineer": AgentCapability(
                "@ai-engineer",
                ["AI/ML", "深度学习", "模型部署"],
                [TaskType.AI_ML_DEVELOPMENT, TaskType.DATA_ENGINEERING],
                5, True
            ),
            "@data-scientist": AgentCapability(
                "@data-scientist",
                ["数据科学", "统计分析", "机器学习"],
                [TaskType.AI_ML_DEVELOPMENT, TaskType.DATA_ENGINEERING],
                4, True
            ),
            "@data-engineer": AgentCapability(
                "@data-engineer",
                ["数据工程", "ETL", "大数据处理"],
                [TaskType.DATA_ENGINEERING, TaskType.DATABASE_DESIGN],
                4, True
            ),
            "@mobile-developer": AgentCapability(
                "@mobile-developer",
                ["移动开发", "iOS", "Android", "跨平台"],
                [TaskType.MOBILE_DEVELOPMENT, TaskType.FEATURE_DEVELOPMENT],
                4, True
            ),

            # 特殊协调者
            "@orchestrator": AgentCapability(
                "@orchestrator",
                ["多域协调", "复杂任务管理", "质量门禁"],
                list(TaskType),  # 支持所有任务类型
                5, False
            ),
            "@error-detective": AgentCapability(
                "@error-detective",
                ["问题诊断", "根因分析", "调试"],
                [TaskType.BUG_FIX, TaskType.PERFORMANCE_TESTING],
                3, True
            )
        }

        return agents

    def analyze_task(self, description: str, context: Dict[str, Any] = None) -> DevelopmentTask:
        """智能分析开发任务"""
        task_id = str(uuid.uuid4())
        context = context or {}

        # 简单的任务类型推断（实际可用AI模型）
        task_type = self._infer_task_type(description)
        priority = self._estimate_priority(description, context)
        complexity = self._estimate_complexity(description, context)
        required_agents = self._select_agents_for_task(task_type, complexity, description)

        return DevelopmentTask(
            task_id=task_id,
            description=description,
            task_type=task_type,
            priority=priority,
            estimated_complexity=complexity,
            required_agents=required_agents,
            context=context
        )

    def _infer_task_type(self, description: str) -> TaskType:
        """推断任务类型"""
        description_lower = description.lower()

        # 关键词映射
        type_keywords = {
            TaskType.FEATURE_DEVELOPMENT: ["功能", "新增", "实现", "开发", "feature", "implement"],
            TaskType.BUG_FIX: ["修复", "bug", "错误", "问题", "fix", "error"],
            TaskType.REFACTORING: ["重构", "优化", "重写", "refactor", "optimize"],
            TaskType.API_DESIGN: ["api", "接口", "endpoint", "rest", "graphql"],
            TaskType.DATABASE_DESIGN: ["数据库", "表", "sql", "nosql", "database", "schema"],
            TaskType.UNIT_TESTING: ["单元测试", "unit test", "测试", "test"],
            TaskType.FRONTEND_DEVELOPMENT: ["前端", "ui", "界面", "frontend", "react", "vue"],
            TaskType.BACKEND_DEVELOPMENT: ["后端", "backend", "server", "服务器"],
            TaskType.DEPLOYMENT: ["部署", "deploy", "发布", "release"],
            TaskType.DOCUMENTATION: ["文档", "doc", "readme", "documentation"],
            TaskType.SECURITY_AUDIT: ["安全", "security", "审计", "audit"],
            TaskType.PERFORMANCE_TESTING: ["性能", "performance", "优化", "benchmark"]
        }

        for task_type, keywords in type_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return task_type

        return TaskType.FEATURE_DEVELOPMENT  # 默认

    def _estimate_priority(self, description: str, context: Dict[str, Any]) -> int:
        """估算任务优先级"""
        description_lower = description.lower()

        # 高优先级关键词
        high_priority_keywords = ["紧急", "urgent", "critical", "重要", "important", "生产", "production"]
        if any(keyword in description_lower for keyword in high_priority_keywords):
            return 5

        # 中等优先级关键词
        medium_priority_keywords = ["需要", "应该", "should", "must"]
        if any(keyword in description_lower for keyword in medium_priority_keywords):
            return 3

        return 2  # 默认低优先级

    def _estimate_complexity(self, description: str, context: Dict[str, Any]) -> int:
        """估算任务复杂度"""
        description_lower = description.lower()

        # 高复杂度关键词
        high_complexity_keywords = ["架构", "系统", "复杂", "多个", "整合", "microservice", "distributed"]
        if any(keyword in description_lower for keyword in high_complexity_keywords):
            return 8

        # 中等复杂度关键词
        medium_complexity_keywords = ["集成", "设计", "优化", "重构", "integration", "design"]
        if any(keyword in description_lower for keyword in medium_complexity_keywords):
            return 5

        return 3  # 默认简单

    def _select_agents_for_task(self, task_type: TaskType, complexity: int, description: str) -> List[str]:
        """为任务选择合适的Agent组合"""
        suitable_agents = []

        # 找到支持该任务类型的Agent
        for agent_name, capability in self.agents_registry.items():
            if task_type in capability.task_types:
                suitable_agents.append(agent_name)

        # 根据复杂度决定Agent数量
        if complexity >= 7:
            # 高复杂度：需要多个专家 + 协调者
            if "@orchestrator" not in suitable_agents:
                suitable_agents.insert(0, "@orchestrator")
            return suitable_agents[:4]  # 最多4个Agent
        elif complexity >= 4:
            # 中等复杂度：2-3个Agent
            return suitable_agents[:3]
        else:
            # 低复杂度：1-2个Agent
            return suitable_agents[:2]

    async def execute_task(self, task: DevelopmentTask) -> Dict[str, Any]:
        """执行开发任务"""
        print(f"🚀 开始执行任务: {task.description}")
        print(f"📊 任务类型: {task.task_type.value}")
        print(f"🤖 分配Agent: {', '.join(task.required_agents)}")
        print(f"⚖️ 复杂度: {task.estimated_complexity}/10")
        print(f"⭐ 优先级: {task.priority}/5")

        self.active_tasks[task.task_id] = task

        # 记录任务到监控器
        for agent in task.required_agents:
            self.monitor.add_task(f"{task.task_id}_{agent}", agent, task.description)

        # 根据Agent数量决定执行策略
        if len(task.required_agents) == 1:
            # 单Agent执行
            result = await self._execute_single_agent(task)
        else:
            # 多Agent协作执行
            result = await self._execute_multi_agent(task)

        # 清理任务
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]

        return result

    async def _execute_single_agent(self, task: DevelopmentTask) -> Dict[str, Any]:
        """单Agent执行"""
        agent = task.required_agents[0]
        agent_task_id = f"{task.task_id}_{agent}"

        self.monitor.start_task(agent_task_id)

        try:
            # 模拟Agent执行
            print(f"  🔄 {agent} 正在执行任务...")

            # 这里会调用实际的claude-code-unified-agents
            result = await self._call_subagent(agent, task)

            self.monitor.complete_task(agent_task_id, result)
            print(f"  ✅ {agent} 任务完成")

            return {
                'success': True,
                'agent': agent,
                'result': result,
                'execution_mode': '串行'
            }

        except Exception as e:
            self.monitor.fail_task(agent_task_id, str(e))
            print(f"  ❌ {agent} 任务失败: {e}")
            return {
                'success': False,
                'agent': agent,
                'error': str(e),
                'execution_mode': '串行'
            }

    async def _execute_multi_agent(self, task: DevelopmentTask) -> Dict[str, Any]:
        """多Agent协作执行"""
        print(f"  🔄 启动 {len(task.required_agents)} 个Agent并行协作...")

        # 检查是否有协调者
        has_orchestrator = "@orchestrator" in task.required_agents

        if has_orchestrator:
            # 有协调者：串行协调执行
            return await self._execute_with_orchestrator(task)
        else:
            # 无协调者：并行执行
            return await self._execute_parallel_agents(task)

    async def _execute_with_orchestrator(self, task: DevelopmentTask) -> Dict[str, Any]:
        """协调者模式执行"""
        orchestrator_task_id = f"{task.task_id}_@orchestrator"
        other_agents = [a for a in task.required_agents if a != "@orchestrator"]

        try:
            # 1. 协调者分析任务
            self.monitor.start_task(orchestrator_task_id)
            print(f"    🎯 @orchestrator 分析任务和分工...")

            orchestrator_result = await self._call_subagent("@orchestrator", task)

            # 2. 并行执行其他Agent
            agent_tasks = []
            for agent in other_agents:
                agent_task_id = f"{task.task_id}_{agent}"
                self.monitor.start_task(agent_task_id)
                agent_tasks.append(self._call_subagent(agent, task))

            print(f"    ⚡ 并行执行 {len(other_agents)} 个专业Agent...")
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # 3. 更新监控状态
            for i, agent in enumerate(other_agents):
                agent_task_id = f"{task.task_id}_{agent}"
                if isinstance(agent_results[i], Exception):
                    self.monitor.fail_task(agent_task_id, str(agent_results[i]))
                else:
                    self.monitor.complete_task(agent_task_id, agent_results[i])

            self.monitor.complete_task(orchestrator_task_id, orchestrator_result)

            print(f"  ✅ 协调者模式执行完成")

            return {
                'success': True,
                'execution_mode': '协调者+并行',
                'orchestrator_result': orchestrator_result,
                'agent_results': dict(zip(other_agents, agent_results)),
                'agents_count': len(task.required_agents)
            }

        except Exception as e:
            self.monitor.fail_task(orchestrator_task_id, str(e))
            print(f"  ❌ 协调者模式执行失败: {e}")
            return {
                'success': False,
                'execution_mode': '协调者+并行',
                'error': str(e)
            }

    async def _execute_parallel_agents(self, task: DevelopmentTask) -> Dict[str, Any]:
        """纯并行执行"""
        try:
            # 启动所有Agent
            agent_tasks = []
            for agent in task.required_agents:
                agent_task_id = f"{task.task_id}_{agent}"
                self.monitor.start_task(agent_task_id)
                agent_tasks.append(self._call_subagent(agent, task))

            print(f"    ⚡ 并行执行 {len(task.required_agents)} 个Agent...")
            results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # 更新监控状态
            for i, agent in enumerate(task.required_agents):
                agent_task_id = f"{task.task_id}_{agent}"
                if isinstance(results[i], Exception):
                    self.monitor.fail_task(agent_task_id, str(results[i]))
                else:
                    self.monitor.complete_task(agent_task_id, results[i])

            print(f"  ✅ 并行执行完成")

            return {
                'success': True,
                'execution_mode': '纯并行',
                'results': dict(zip(task.required_agents, results)),
                'agents_count': len(task.required_agents)
            }

        except Exception as e:
            print(f"  ❌ 并行执行失败: {e}")
            return {
                'success': False,
                'execution_mode': '纯并行',
                'error': str(e)
            }

    async def _call_subagent(self, agent_name: str, task: DevelopmentTask) -> Dict[str, Any]:
        """调用SubAgent"""
        # 模拟Agent执行时间
        import random
        execution_time = random.uniform(0.5, 3.0)
        await asyncio.sleep(execution_time)

        # 这里应该调用实际的claude-code-unified-agents
        # 现在返回模拟结果
        return {
            'agent': agent_name,
            'task_id': task.task_id,
            'task_description': task.description,
            'result': f"{agent_name} 完成了任务: {task.description[:50]}...",
            'execution_time': execution_time,
            'recommendations': [
                f"{agent_name} 建议进行代码审查",
                f"{agent_name} 建议添加单元测试"
            ]
        }

    async def develop(self, description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """开发任务统一入口"""
        # 1. 任务分析
        task = self.analyze_task(description, context)

        # 2. 任务执行
        result = await self.execute_task(task)

        # 3. 记录历史
        self.task_history.append({
            'task': task.__dict__,
            'result': result,
            'timestamp': asyncio.get_event_loop().time()
        })

        return result

# 全局编排器实例
_global_orchestrator = None

def get_global_orchestrator() -> DevelopmentOrchestrator:
    """获取全局编排器实例"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = DevelopmentOrchestrator()
    return _global_orchestrator

# 便捷函数
async def develop(description: str, **context) -> Dict[str, Any]:
    """快速开发任务入口"""
    orchestrator = get_global_orchestrator()
    return await orchestrator.develop(description, context)

if __name__ == "__main__":
    # 测试示例
    async def test_development_orchestrator():
        orchestrator = DevelopmentOrchestrator()

        # 测试任务
        test_tasks = [
            "实现用户登录API接口",
            "修复支付系统的并发问题",
            "设计微服务架构",
            "编写API文档",
            "进行安全审计",
            "优化数据库查询性能"
        ]

        print("🚀 Perfect21 开发任务编排器测试")
        print("=" * 50)

        for i, task_desc in enumerate(test_tasks, 1):
            print(f"\n📋 任务 {i}: {task_desc}")
            print("-" * 30)

            result = await orchestrator.develop(task_desc)

            print(f"✅ 执行模式: {result.get('execution_mode', '未知')}")
            if result.get('success'):
                print(f"🎯 涉及Agent: {result.get('agents_count', 1)}个")
            else:
                print(f"❌ 执行失败: {result.get('error', '未知错误')}")

            # 短暂延迟以观察监控效果
            await asyncio.sleep(0.5)

        print(f"\n📊 任务历史: {len(orchestrator.task_history)} 个任务")
        print("🎉 测试完成！")

    # 运行测试
    asyncio.run(test_development_orchestrator())