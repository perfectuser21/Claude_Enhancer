#!/usr/bin/env python3
"""
Perfect21 并行Agent协调器
实现多个SubAgent同时工作，智能协调和任务分配
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import threading

logger = logging.getLogger("ParallelCoordinator")

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_SYNC = "waiting_sync"

@dataclass
class AgentTask:
    """Agent任务定义"""
    agent_name: str
    task_description: str
    dependencies: List[str] = None  # 依赖的其他agent
    priority: int = 1  # 优先级 1-10
    estimated_time: int = 300  # 预估时间(秒)
    workspace: str = "default"
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.context is None:
            self.context = {}

@dataclass
class AgentResult:
    """Agent执行结果"""
    agent_name: str
    status: AgentStatus
    output: str
    files_created: List[str] = None
    files_modified: List[str] = None
    execution_time: float = 0
    error_message: str = ""

    def __post_init__(self):
        if self.files_created is None:
            self.files_created = []
        if self.files_modified is None:
            self.files_modified = []

class ParallelCoordinator:
    """并行Agent协调器"""

    def __init__(self, max_parallel_agents=6):
        """初始化协调器"""
        self.max_parallel_agents = max_parallel_agents
        self.active_agents: Dict[str, AgentStatus] = {}
        self.agent_results: Dict[str, AgentResult] = {}
        self.task_queue: List[AgentTask] = []
        self.sync_points: Dict[str, List[str]] = {}  # 同步点配置
        self.workspace_locks: Dict[str, threading.Lock] = {}

        logger.info(f"并行协调器初始化 - 最大并行数: {max_parallel_agents}")

    def decompose_task(self, user_request: str) -> List[AgentTask]:
        """智能任务分解"""
        logger.info(f"分解用户任务: {user_request}")

        # 基于任务类型的智能分解策略
        tasks = []

        if "认证" in user_request or "登录" in user_request or "auth" in user_request.lower():
            tasks = self._decompose_auth_system()
        elif "API" in user_request or "接口" in user_request:
            tasks = self._decompose_api_development()
        elif "前端" in user_request or "界面" in user_request or "UI" in user_request:
            tasks = self._decompose_frontend_development()
        else:
            tasks = self._decompose_generic_development(user_request)

        logger.info(f"任务分解完成 - 共{len(tasks)}个并行任务")
        return tasks

    def _decompose_auth_system(self) -> List[AgentTask]:
        """分解认证系统开发任务"""
        return [
            AgentTask(
                agent_name="spec-architect",
                task_description="设计用户认证系统架构，包括数据模型、API设计、安全策略",
                priority=10,
                estimated_time=180
            ),
            AgentTask(
                agent_name="backend-developer",
                task_description="实现用户注册、登录、JWT令牌管理的后端API",
                dependencies=["spec-architect"],
                priority=8,
                estimated_time=600
            ),
            AgentTask(
                agent_name="frontend-developer",
                task_description="创建登录表单、注册页面、用户状态管理组件",
                dependencies=["spec-architect"],
                priority=7,
                estimated_time=480
            ),
            AgentTask(
                agent_name="security-auditor",
                task_description="审查认证系统安全性，检查密码策略、会话管理、CSRF防护",
                dependencies=["backend-developer"],
                priority=9,
                estimated_time=300
            ),
            AgentTask(
                agent_name="test-generator",
                task_description="生成认证系统的单元测试、集成测试、端到端测试",
                dependencies=["backend-developer", "frontend-developer"],
                priority=6,
                estimated_time=360
            ),
            AgentTask(
                agent_name="doc-writer",
                task_description="编写认证API文档、用户指南、部署说明",
                priority=5,
                estimated_time=240
            )
        ]

    def _decompose_api_development(self) -> List[AgentTask]:
        """分解API开发任务"""
        return [
            AgentTask(
                agent_name="spec-architect",
                task_description="设计API规范、数据模型、接口定义",
                priority=10,
                estimated_time=120
            ),
            AgentTask(
                agent_name="backend-developer",
                task_description="实现API接口、数据验证、错误处理",
                dependencies=["spec-architect"],
                priority=9,
                estimated_time=420
            ),
            AgentTask(
                agent_name="test-generator",
                task_description="生成API测试用例、性能测试、边界测试",
                dependencies=["backend-developer"],
                priority=8,
                estimated_time=240
            ),
            AgentTask(
                agent_name="doc-writer",
                task_description="编写API文档、使用示例、集成指南",
                dependencies=["spec-architect"],
                priority=6,
                estimated_time=180
            )
        ]

    def _decompose_generic_development(self, request: str) -> List[AgentTask]:
        """通用开发任务分解"""
        return [
            AgentTask(
                agent_name="spec-planner",
                task_description=f"分析需求并制定开发计划: {request}",
                priority=10,
                estimated_time=120
            ),
            AgentTask(
                agent_name="developer-coder",
                task_description=f"实现核心功能: {request}",
                dependencies=["spec-planner"],
                priority=9,
                estimated_time=480
            ),
            AgentTask(
                agent_name="code-reviewer",
                task_description="代码质量审查和优化建议",
                dependencies=["developer-coder"],
                priority=7,
                estimated_time=180
            ),
            AgentTask(
                agent_name="test-runner",
                task_description="执行测试并修复发现的问题",
                dependencies=["developer-coder"],
                priority=8,
                estimated_time=240
            )
        ]

    async def execute_parallel_development(self, user_request: str) -> Dict[str, Any]:
        """执行并行开发流程"""
        start_time = time.time()
        logger.info(f"开始并行开发: {user_request}")

        # 1. 任务分解
        tasks = self.decompose_task(user_request)
        self.task_queue = tasks

        # 2. 创建执行计划
        execution_plan = self._create_execution_plan(tasks)
        logger.info(f"执行计划创建完成: {len(execution_plan['waves'])}个阶段")

        # 3. 分阶段并行执行
        all_results = {}
        for wave_num, wave_tasks in enumerate(execution_plan['waves']):
            logger.info(f"执行第{wave_num + 1}阶段 - {len(wave_tasks)}个并行任务")
            wave_results = await self._execute_wave(wave_tasks)
            all_results.update(wave_results)

            # 检查是否有失败的关键任务
            failed_critical = [name for name, result in wave_results.items()
                             if result.status == AgentStatus.FAILED and
                             any(task.agent_name == name and task.priority >= 8 for task in tasks)]

            if failed_critical:
                logger.error(f"关键任务失败，停止执行: {failed_critical}")
                break

        # 4. 结果汇总和冲突解决
        final_result = await self._consolidate_results(all_results, user_request)

        execution_time = time.time() - start_time
        logger.info(f"并行开发完成 - 耗时: {execution_time:.2f}秒")

        return {
            "success": True,
            "execution_time": execution_time,
            "agents_used": len(all_results),
            "parallel_efficiency": self._calculate_efficiency(tasks, execution_time),
            "results": all_results,
            "final_output": final_result,
            "user_request": user_request
        }

    def _create_execution_plan(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """创建分阶段执行计划"""
        # 使用拓扑排序确定执行顺序
        waves = []
        remaining_tasks = {task.agent_name: task for task in tasks}
        completed_tasks = set()

        while remaining_tasks:
            # 找出所有依赖已满足的任务
            ready_tasks = []
            for task_name, task in remaining_tasks.items():
                if all(dep in completed_tasks for dep in task.dependencies):
                    ready_tasks.append(task)

            if not ready_tasks:
                logger.warning("发现循环依赖或无法满足的依赖")
                # 强制添加剩余任务
                ready_tasks = list(remaining_tasks.values())

            # 按优先级排序，限制并行数量
            ready_tasks.sort(key=lambda x: x.priority, reverse=True)
            wave_tasks = ready_tasks[:self.max_parallel_agents]

            waves.append(wave_tasks)

            # 从剩余任务中移除
            for task in wave_tasks:
                del remaining_tasks[task.agent_name]
                completed_tasks.add(task.agent_name)

        return {
            "waves": waves,
            "total_estimated_time": max(sum(task.estimated_time for task in wave)
                                       for wave in waves) if waves else 0
        }

    async def _execute_wave(self, wave_tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        """执行一个阶段的并行任务"""
        logger.info(f"并行执行 {len(wave_tasks)} 个任务")

        # 创建并发执行器
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(wave_tasks)) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self._execute_single_agent, task): task
                for task in wave_tasks
            }

            results = {}

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_task, timeout=1800):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.agent_name] = result
                    logger.info(f"Agent {task.agent_name} 完成: {result.status.value}")
                except Exception as e:
                    logger.error(f"Agent {task.agent_name} 执行异常: {e}")
                    results[task.agent_name] = AgentResult(
                        agent_name=task.agent_name,
                        status=AgentStatus.FAILED,
                        output="",
                        error_message=str(e)
                    )

        return results

    def _execute_single_agent(self, task: AgentTask) -> AgentResult:
        """执行单个Agent任务"""
        start_time = time.time()
        agent_name = task.agent_name

        logger.info(f"启动Agent: {agent_name}")
        self.active_agents[agent_name] = AgentStatus.WORKING

        try:
            # 构建Claude Code Task命令
            task_prompt = self._build_task_prompt(task)

            # 执行Claude Code SubAgent
            result = subprocess.run([
                "claude", "--agent", agent_name,
                "--task", task_prompt,
                "--workspace", task.workspace,
                "--json-output"
            ], capture_output=True, text=True, timeout=task.estimated_time)

            execution_time = time.time() - start_time

            if result.returncode == 0:
                # 解析输出
                try:
                    output_data = json.loads(result.stdout)
                    files_created = output_data.get('files_created', [])
                    files_modified = output_data.get('files_modified', [])
                    output_text = output_data.get('summary', result.stdout)
                except:
                    files_created = []
                    files_modified = []
                    output_text = result.stdout

                agent_result = AgentResult(
                    agent_name=agent_name,
                    status=AgentStatus.COMPLETED,
                    output=output_text,
                    files_created=files_created,
                    files_modified=files_modified,
                    execution_time=execution_time
                )
            else:
                agent_result = AgentResult(
                    agent_name=agent_name,
                    status=AgentStatus.FAILED,
                    output=result.stdout,
                    error_message=result.stderr,
                    execution_time=execution_time
                )

            self.active_agents[agent_name] = agent_result.status
            self.agent_results[agent_name] = agent_result

            return agent_result

        except subprocess.TimeoutExpired:
            logger.warning(f"Agent {agent_name} 执行超时")
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.FAILED,
                output="",
                error_message=f"执行超时 ({task.estimated_time}秒)",
                execution_time=task.estimated_time
            )
        except Exception as e:
            logger.error(f"Agent {agent_name} 执行异常: {e}")
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.FAILED,
                output="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _build_task_prompt(self, task: AgentTask) -> str:
        """构建Agent任务提示"""
        prompt_parts = [
            f"任务: {task.task_description}",
            f"优先级: {task.priority}/10",
            f"工作空间: {task.workspace}"
        ]

        if task.dependencies:
            prompt_parts.append(f"依赖完成: {', '.join(task.dependencies)}")

        if task.context:
            prompt_parts.append("上下文:")
            for key, value in task.context.items():
                prompt_parts.append(f"  {key}: {value}")

        # 添加协作指导
        prompt_parts.extend([
            "",
            "🤝 并行协作指导:",
            "- 这是多Agent并行开发项目",
            "- 其他Agent可能同时在相关文件上工作",
            "- 请在修改共享文件前检查最新状态",
            "- 优先完成自己负责的核心部分",
            "- 输出JSON格式结果便于自动化处理"
        ])

        return "\n".join(prompt_parts)

    async def _consolidate_results(self, results: Dict[str, AgentResult],
                                 user_request: str) -> Dict[str, Any]:
        """合并和协调Agent结果"""
        logger.info("开始结果合并和冲突解决")

        # 收集所有创建和修改的文件
        all_files_created = []
        all_files_modified = []

        for result in results.values():
            all_files_created.extend(result.files_created)
            all_files_modified.extend(result.files_modified)

        # 检测文件冲突
        conflicts = self._detect_file_conflicts(results)

        # 生成最终摘要
        successful_agents = [name for name, result in results.items()
                           if result.status == AgentStatus.COMPLETED]
        failed_agents = [name for name, result in results.items()
                        if result.status == AgentStatus.FAILED]

        consolidation = {
            "user_request": user_request,
            "total_agents": len(results),
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "files_created": list(set(all_files_created)),
            "files_modified": list(set(all_files_modified)),
            "conflicts_detected": conflicts,
            "next_actions": self._generate_next_actions(results, conflicts)
        }

        # 如果有冲突，尝试自动解决
        if conflicts:
            logger.warning(f"检测到 {len(conflicts)} 个冲突，尝试自动解决")
            resolution_result = await self._resolve_conflicts(conflicts, results)
            consolidation["conflict_resolution"] = resolution_result

        return consolidation

    def _detect_file_conflicts(self, results: Dict[str, AgentResult]) -> List[Dict[str, Any]]:
        """检测文件修改冲突"""
        conflicts = []
        file_modifications = {}

        # 收集每个文件的修改者
        for agent_name, result in results.items():
            for file_path in result.files_modified + result.files_created:
                if file_path not in file_modifications:
                    file_modifications[file_path] = []
                file_modifications[file_path].append(agent_name)

        # 找出有多个修改者的文件
        for file_path, modifiers in file_modifications.items():
            if len(modifiers) > 1:
                conflicts.append({
                    "file": file_path,
                    "agents": modifiers,
                    "type": "concurrent_modification"
                })

        return conflicts

    async def _resolve_conflicts(self, conflicts: List[Dict[str, Any]],
                               results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """自动解决冲突"""
        logger.info("启动智能冲突解决")

        resolution_results = []

        for conflict in conflicts:
            file_path = conflict["file"]
            agents = conflict["agents"]

            # 调用冲突解决Agent
            try:
                resolve_result = subprocess.run([
                    "claude", "--agent", "conflict-resolver",
                    "--task", f"解决文件冲突: {file_path}, 涉及Agents: {', '.join(agents)}",
                    "--context", json.dumps({
                        "file_path": file_path,
                        "conflicting_agents": agents,
                        "agent_results": {name: results[name].output for name in agents}
                    })
                ], capture_output=True, text=True, timeout=300)

                if resolve_result.returncode == 0:
                    resolution_results.append({
                        "file": file_path,
                        "status": "resolved",
                        "resolution": resolve_result.stdout
                    })
                else:
                    resolution_results.append({
                        "file": file_path,
                        "status": "failed",
                        "error": resolve_result.stderr
                    })

            except Exception as e:
                logger.error(f"冲突解决失败: {e}")
                resolution_results.append({
                    "file": file_path,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "conflicts_resolved": len([r for r in resolution_results if r["status"] == "resolved"]),
            "conflicts_failed": len([r for r in resolution_results if r["status"] != "resolved"]),
            "details": resolution_results
        }

    def _generate_next_actions(self, results: Dict[str, AgentResult],
                             conflicts: List[Dict[str, Any]]) -> List[str]:
        """生成后续行动建议"""
        actions = []

        # 检查失败的Agent
        failed_agents = [name for name, result in results.items()
                        if result.status == AgentStatus.FAILED]
        if failed_agents:
            actions.append(f"重新执行失败的Agents: {', '.join(failed_agents)}")

        # 检查冲突
        if conflicts:
            actions.append("手动检查和解决剩余冲突")

        # 建议测试
        if any("test" not in name.lower() for name in results.keys()):
            actions.append("运行完整测试套件验证集成")

        # 建议代码审查
        actions.append("进行整体代码审查确保一致性")

        # 建议文档更新
        actions.append("更新项目文档反映新变更")

        return actions

    def _calculate_efficiency(self, tasks: List[AgentTask], actual_time: float) -> float:
        """计算并行执行效率"""
        serial_time = sum(task.estimated_time for task in tasks)
        if actual_time > 0:
            efficiency = serial_time / actual_time
            return min(efficiency, len(tasks))  # 理论最大效率等于任务数
        return 0.0

    def get_status_report(self) -> Dict[str, Any]:
        """获取实时状态报告"""
        return {
            "active_agents": dict(self.active_agents),
            "completed_results": len([r for r in self.agent_results.values()
                                    if r.status == AgentStatus.COMPLETED]),
            "failed_results": len([r for r in self.agent_results.values()
                                 if r.status == AgentStatus.FAILED]),
            "queue_length": len(self.task_queue),
            "timestamp": datetime.now().isoformat()
        }

# 全局协调器实例
coordinator = ParallelCoordinator()

async def parallel_develop(user_request: str) -> Dict[str, Any]:
    """对外API：并行开发入口"""
    return await coordinator.execute_parallel_development(user_request)

if __name__ == "__main__":
    # 测试用例
    async def test_parallel_development():
        result = await parallel_develop("实现用户认证系统")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test_parallel_development())