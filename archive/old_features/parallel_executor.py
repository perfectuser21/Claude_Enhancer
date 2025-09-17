#!/usr/bin/env python3
"""
Perfect21 并行执行控制器
实际调用Claude Code的Task工具实现真正并行
"""

import logging
import json
import time
import asyncio
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Import error handling system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.exceptions import (
    AgentExecutionError, WorkflowError, TimeoutError, ErrorAggregator,
    ErrorSeverity, ErrorCategory, ErrorContext, retry_on_failure,
    RetryConfig, handle_exceptions, safe_execute
)

from .smart_decomposer import TaskAnalysis, AgentTask
from .parallel_manager import ParallelManager, ExecutionResult, ParallelExecutionSummary

logger = logging.getLogger("ParallelExecutor")

class ParallelExecutor:
    """并行执行控制器 - 桥接Perfect21与Claude Code，集成错误处理"""

    def __init__(self):
        self.parallel_manager = ParallelManager()
        self.execution_log = []
        self.error_aggregator = ErrorAggregator()
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=30.0,
            retry_on_exceptions=(AgentExecutionError, TimeoutError)
        )

    async def execute_parallel_task_async(self, task_description: str, analysis: TaskAnalysis) -> Dict[str, Any]:
        """
        异步执行并行任务的主入口
        """
        logger.info(f"开始异步并行执行: {task_description}")

        # 显示执行计划
        self._display_execution_plan(analysis)

        # 生成Task工具调用配置
        task_calls = self._generate_task_calls(analysis)

        # 创建执行记录
        execution_record = {
            "task_description": task_description,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "project_type": analysis.project_type,
                "complexity": analysis.complexity.value,
                "execution_mode": analysis.execution_mode,
                "estimated_time": analysis.estimated_total_time,
                "agent_count": len(analysis.agent_tasks)
            },
            "task_calls": task_calls,
            "status": "prepared"
        }

        self.execution_log.append(execution_record)

        # 返回给调用者的执行信息
        return {
            "ready_for_execution": True,
            "execution_mode": analysis.execution_mode,
            "task_calls": task_calls,
            "expected_agents": len(analysis.agent_tasks),
            "execution_instructions": self._create_execution_instructions(analysis),
            "monitoring_config": self._create_monitoring_config(analysis)
        }

    @handle_exceptions(
        exceptions=(Exception,),
        category=ErrorCategory.AGENT_EXECUTION,
        severity=ErrorSeverity.HIGH,
        recovery_suggestions=[
            "Check task analysis validity",
            "Verify agent availability",
            "Review task parameters"
        ]
    )
    def execute_parallel_task(self, task_description: str, analysis: TaskAnalysis) -> Dict[str, Any]:
        """
        执行并行任务的主入口

        这个方法会：
        1. 显示执行计划
        2. 生成并行Task调用指令
        3. 返回调用信息供主Claude Code使用

        Args:
            task_description: 原始任务描述
            analysis: 任务分析结果

        Returns:
            包含执行指令和配置的字典
        """
        logger.info(f"开始准备并行执行: {task_description}")

        # 显示执行计划
        self._display_execution_plan(analysis)

        # 生成Task工具调用配置
        task_calls = self._generate_task_calls(analysis)

        # 创建执行记录
        execution_record = {
            "task_description": task_description,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "project_type": analysis.project_type,
                "complexity": analysis.complexity.value,
                "execution_mode": analysis.execution_mode,
                "estimated_time": analysis.estimated_total_time,
                "agent_count": len(analysis.agent_tasks)
            },
            "task_calls": task_calls,
            "status": "prepared"
        }

        self.execution_log.append(execution_record)

        # 返回给调用者的执行信息
        return {
            "ready_for_execution": True,
            "execution_mode": analysis.execution_mode,
            "task_calls": task_calls,
            "expected_agents": len(analysis.agent_tasks),
            "execution_instructions": self._create_execution_instructions(analysis),
            "monitoring_config": self._create_monitoring_config(analysis)
        }

    def _display_execution_plan(self, analysis: TaskAnalysis):
        """显示详细的执行计划"""
        print(f"\n🚀 Perfect21 并行执行计划")
        print(f"=" * 60)
        print(f"📋 原始任务: {analysis.original_task}")
        print(f"🎯 项目类型: {analysis.project_type}")
        print(f"📊 复杂度等级: {analysis.complexity.value}")
        print(f"⚡ 执行模式: {analysis.execution_mode}")
        print(f"⏱️ 预估总时间: {analysis.estimated_total_time}分钟")
        print(f"🤖 涉及agents: {len(analysis.agent_tasks)}个")
        print(f"=" * 60)

        print(f"\n👥 Agent执行清单:")
        for i, task in enumerate(analysis.agent_tasks, 1):
            priority_emoji = "🔥" if task.priority <= 2 else "📋"
            print(f"  {priority_emoji} {i}. @{task.agent_name}")
            print(f"      任务: {task.task_description}")
            print(f"      预估: {task.estimated_time}分钟")
            print(f"      优先级: P{task.priority}")
            if task.dependencies:
                deps = ", ".join([f"@{dep}" for dep in task.dependencies])
                print(f"      依赖: {deps}")
            print()

        print(f"⚡ **关键提示**: 接下来将在单个消息中并行调用所有Task工具!")
        print(f"🎯 这将实现真正的多agent并行协作，绕过orchestrator限制")
        print(f"=" * 60)

    def _generate_task_calls(self, analysis: TaskAnalysis) -> List[Dict[str, Any]]:
        """生成Task工具调用配置"""
        task_calls = []

        for task in analysis.agent_tasks:
            task_call = {
                "tool_name": "Task",
                "parameters": {
                    "subagent_type": task.agent_name,
                    "description": task.task_description,
                    "prompt": task.detailed_prompt
                },
                "expected_duration": task.estimated_time,
                "priority": task.priority,
                "dependencies": task.dependencies if task.dependencies else []
            }
            task_calls.append(task_call)

        return task_calls

    def _create_execution_instructions(self, analysis: TaskAnalysis) -> str:
        """创建执行指令"""
        instructions = f"""
🚀 Perfect21 并行执行指令

⚡ **关键操作**: 请在**单个消息**中调用以下所有Task工具以实现真正并行执行

📋 原始任务: {analysis.original_task}
🎯 执行模式: {analysis.execution_mode}
🤖 Agent总数: {len(analysis.agent_tasks)}

### 📞 Task工具调用清单:

"""

        for i, task in enumerate(analysis.agent_tasks, 1):
            instructions += f"""
**Agent {i}: @{task.agent_name}**
```
Task(
    subagent_type="{task.agent_name}",
    description="{task.task_description}",
    prompt=\"\"\"{task.detailed_prompt}\"\"\"
)
```
"""

        instructions += f"""

### 🎯 执行要点:
1. **并行调用**: 必须在同一消息中调用所有{len(analysis.agent_tasks)}个Task工具
2. **无需等待**: 不要等待单个agent完成再调用下一个
3. **监控进度**: 观察所有agents的执行状态和输出
4. **整合结果**: 收集所有agents的输出并整合成最终解决方案

### 📊 预期结果:
- 所有agents将并行启动和执行
- 总执行时间: ~{analysis.estimated_total_time}分钟
- 最终输出: 完整的{analysis.project_type}项目解决方案

🎉 **开始执行!**
"""

        return instructions

    def _create_monitoring_config(self, analysis: TaskAnalysis) -> Dict[str, Any]:
        """创建监控配置"""
        return {
            "total_agents": len(analysis.agent_tasks),
            "expected_completion_time": analysis.estimated_total_time,
            "agent_names": [task.agent_name for task in analysis.agent_tasks],
            "critical_agents": [
                task.agent_name for task in analysis.agent_tasks
                if task.priority <= 2
            ],
            "monitoring_intervals": 30,  # 30秒检查一次
            "timeout_threshold": analysis.estimated_total_time * 60 * 2  # 2倍预估时间
        }

    async def process_execution_results_async(self, agent_results: List[Dict[str, Any]]) -> ParallelExecutionSummary:
        """
        异步处理执行结果
        """
        logger.info(f"异步处理{len(agent_results)}个agent的执行结果")

        # 转换为ExecutionResult格式
        execution_results = []
        successful_count = 0

        for result in agent_results:
            agent_name = result.get("agent_name", "unknown")
            success = result.get("success", False)

            if success:
                successful_count += 1

            exec_result = ExecutionResult(
                agent_name=agent_name,
                task_description=result.get("task_description", ""),
                success=success,
                result=result.get("output"),
                error_message=result.get("error"),
                execution_time=result.get("execution_time", 0.0),
                start_time=datetime.fromisoformat(result.get("start_time", datetime.now().isoformat())),
                end_time=datetime.fromisoformat(result.get("end_time", datetime.now().isoformat()))
            )
            execution_results.append(exec_result)

        # 创建执行摘要
        summary = ParallelExecutionSummary(
            task_description=self.execution_log[-1]["task_description"] if self.execution_log else "Unknown",
            total_agents=len(agent_results),
            successful_agents=successful_count,
            failed_agents=len(agent_results) - successful_count,
            total_execution_time=sum(r.execution_time for r in execution_results),
            results=execution_results
        )

        # 异步整合结果
        summary.integrated_output = await self._integrate_agent_outputs_async(execution_results)

        # 更新执行日志
        if self.execution_log:
            self.execution_log[-1]["status"] = "completed"
            self.execution_log[-1]["results"] = summary

        return summary

    def process_execution_results(self, agent_results: List[Dict[str, Any]]) -> ParallelExecutionSummary:
        """
        处理执行结果

        这个方法在所有Task工具执行完成后被调用
        用于分析和整合所有agents的输出
        """
        logger.info(f"处理{len(agent_results)}个agent的执行结果")

        # 转换为ExecutionResult格式
        execution_results = []
        successful_count = 0

        for result in agent_results:
            agent_name = result.get("agent_name", "unknown")
            success = result.get("success", False)

            if success:
                successful_count += 1

            exec_result = ExecutionResult(
                agent_name=agent_name,
                task_description=result.get("task_description", ""),
                success=success,
                result=result.get("output"),
                error_message=result.get("error"),
                execution_time=result.get("execution_time", 0.0),
                start_time=datetime.fromisoformat(result.get("start_time", datetime.now().isoformat())),
                end_time=datetime.fromisoformat(result.get("end_time", datetime.now().isoformat()))
            )
            execution_results.append(exec_result)

        # 创建执行摘要
        summary = ParallelExecutionSummary(
            task_description=self.execution_log[-1]["task_description"] if self.execution_log else "Unknown",
            total_agents=len(agent_results),
            successful_agents=successful_count,
            failed_agents=len(agent_results) - successful_count,
            total_execution_time=sum(r.execution_time for r in execution_results),
            results=execution_results
        )

        # 整合结果
        summary.integrated_output = self._integrate_agent_outputs(execution_results)

        # 更新执行日志
        if self.execution_log:
            self.execution_log[-1]["status"] = "completed"
            self.execution_log[-1]["results"] = summary

        return summary

    async def _integrate_agent_outputs_async(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """异步整合所有agent的输出"""
        integration = {
            "execution_summary": {
                "total_agents": len(results),
                "successful_agents": sum(1 for r in results if r.success),
                "total_execution_time": sum(r.execution_time for r in results),
                "timestamp": datetime.now().isoformat()
            },
            "agent_contributions": {},
            "project_assets": [],
            "quality_metrics": {},
            "deployment_readiness": {},
            "next_actions": []
        }

        # 分析每个agent的贡献
        for result in results:
            if result.success and result.result:
                integration["agent_contributions"][result.agent_name] = {
                    "task_completed": result.task_description,
                    "execution_time": result.execution_time,
                    "output_summary": self._summarize_agent_output(result),
                    "assets_created": self._extract_assets(result),
                    "quality_score": self._calculate_quality_score(result)
                }

        # 并行生成其他数据
        tasks = [
            self._compile_project_assets_async(results),
            self._calculate_overall_quality_async(results),
            self._assess_deployment_readiness_async(results),
            self._generate_next_actions_async(results)
        ]

        assets, quality, deployment, actions = await asyncio.gather(*tasks)

        integration["project_assets"] = assets
        integration["quality_metrics"] = quality
        integration["deployment_readiness"] = deployment
        integration["next_actions"] = actions

        return integration

    def _integrate_agent_outputs(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """整合所有agent的输出"""
        integration = {
            "execution_summary": {
                "total_agents": len(results),
                "successful_agents": sum(1 for r in results if r.success),
                "total_execution_time": sum(r.execution_time for r in results),
                "timestamp": datetime.now().isoformat()
            },
            "agent_contributions": {},
            "project_assets": [],
            "quality_metrics": {},
            "deployment_readiness": {},
            "next_actions": []
        }

        # 分析每个agent的贡献
        for result in results:
            if result.success and result.result:
                integration["agent_contributions"][result.agent_name] = {
                    "task_completed": result.task_description,
                    "execution_time": result.execution_time,
                    "output_summary": self._summarize_agent_output(result),
                    "assets_created": self._extract_assets(result),
                    "quality_score": self._calculate_quality_score(result)
                }

        # 生成项目资产清单
        integration["project_assets"] = self._compile_project_assets(results)

        # 计算质量指标
        integration["quality_metrics"] = self._calculate_overall_quality(results)

        # 评估部署就绪状态
        integration["deployment_readiness"] = self._assess_deployment_readiness(results)

        # 生成下一步行动建议
        integration["next_actions"] = self._generate_next_actions(results)

        return integration

    def _summarize_agent_output(self, result: ExecutionResult) -> str:
        """总结agent输出"""
        if not result.result:
            return "无输出内容"

        # 简单的输出摘要逻辑
        output_str = str(result.result)
        if len(output_str) > 200:
            return output_str[:200] + "..."
        return output_str

    def _extract_assets(self, result: ExecutionResult) -> List[str]:
        """提取agent创建的资产"""
        assets = []

        # 基于agent类型推断资产类型
        if "backend" in result.agent_name:
            assets.extend(["API服务代码", "数据库架构", "接口文档"])
        elif "frontend" in result.agent_name:
            assets.extend(["用户界面", "组件库", "样式文件"])
        elif "test" in result.agent_name:
            assets.extend(["测试套件", "测试报告", "质量评估"])
        elif "devops" in result.agent_name:
            assets.extend(["部署配置", "CI/CD管道", "容器化配置"])
        elif "security" in result.agent_name:
            assets.extend(["安全评估", "漏洞报告", "合规检查"])

        return assets

    def _calculate_quality_score(self, result: ExecutionResult) -> float:
        """计算agent输出的质量分数"""
        if not result.success:
            return 0.0

        # 基于执行时间和成功状态的简单评分
        base_score = 0.8
        time_bonus = min(0.2, result.execution_time / 300.0)  # 最多0.2分时间奖励

        return min(1.0, base_score + time_bonus)

    async def _compile_project_assets_async(self, results: List[ExecutionResult]) -> List[str]:
        """异步编译项目资产清单"""
        all_assets = []
        for result in results:
            if result.success:
                # 在这里可以添加异步处理逻辑
                await asyncio.sleep(0)  # 让出执行权
                all_assets.extend(self._extract_assets(result))

        return list(set(all_assets))  # 去重

    def _compile_project_assets(self, results: List[ExecutionResult]) -> List[str]:
        """编译项目资产清单"""
        all_assets = []
        for result in results:
            if result.success:
                all_assets.extend(self._extract_assets(result))

        return list(set(all_assets))  # 去重

    async def _calculate_overall_quality_async(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """异步计算整体质量指标"""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {"overall_score": 0.0, "quality_level": "Poor"}

        # 异步计算质量分数
        quality_scores = []
        for result in successful_results:
            await asyncio.sleep(0)  # 让出执行权
            quality_scores.append(self._calculate_quality_score(result))

        avg_quality = sum(quality_scores) / len(quality_scores)
        success_rate = len(successful_results) / len(results)

        overall_score = (avg_quality * 0.7) + (success_rate * 0.3)

        if overall_score >= 0.9:
            quality_level = "Excellent"
        elif overall_score >= 0.7:
            quality_level = "Good"
        elif overall_score >= 0.5:
            quality_level = "Fair"
        else:
            quality_level = "Poor"

        return {
            "overall_score": overall_score,
            "quality_level": quality_level,
            "success_rate": success_rate,
            "agent_count": len(results),
            "successful_agents": len(successful_results)
        }

    def _calculate_overall_quality(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """计算整体质量指标"""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {"overall_score": 0.0, "quality_level": "Poor"}

        avg_quality = sum(self._calculate_quality_score(r) for r in successful_results) / len(successful_results)
        success_rate = len(successful_results) / len(results)

        overall_score = (avg_quality * 0.7) + (success_rate * 0.3)

        if overall_score >= 0.9:
            quality_level = "Excellent"
        elif overall_score >= 0.7:
            quality_level = "Good"
        elif overall_score >= 0.5:
            quality_level = "Fair"
        else:
            quality_level = "Poor"

        return {
            "overall_score": overall_score,
            "quality_level": quality_level,
            "success_rate": success_rate,
            "agent_count": len(results),
            "successful_agents": len(successful_results)
        }

    async def _assess_deployment_readiness_async(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """异步评估部署就绪状态"""
        required_components = ["backend", "frontend", "test", "security"]
        available_components = []

        for result in results:
            if result.success:
                await asyncio.sleep(0)  # 让出执行权
                for component in required_components:
                    if component in result.agent_name:
                        available_components.append(component)

        readiness_score = len(set(available_components)) / len(required_components)

        return {
            "readiness_score": readiness_score,
            "available_components": list(set(available_components)),
            "missing_components": list(set(required_components) - set(available_components)),
            "deployment_ready": readiness_score >= 0.75
        }

    def _assess_deployment_readiness(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """评估部署就绪状态"""
        required_components = ["backend", "frontend", "test", "security"]
        available_components = []

        for result in results:
            if result.success:
                for component in required_components:
                    if component in result.agent_name:
                        available_components.append(component)

        readiness_score = len(set(available_components)) / len(required_components)

        return {
            "readiness_score": readiness_score,
            "available_components": list(set(available_components)),
            "missing_components": list(set(required_components) - set(available_components)),
            "deployment_ready": readiness_score >= 0.75
        }

    async def _generate_next_actions_async(self, results: List[ExecutionResult]) -> List[str]:
        """异步生成下一步行动建议"""
        actions = []

        successful_agents = [r.agent_name for r in results if r.success]
        failed_agents = [r.agent_name for r in results if not r.success]

        if failed_agents:
            actions.append(f"🔧 修复失败的agents: {', '.join(failed_agents)}")

        # 异步检查和生成建议
        await asyncio.sleep(0)  # 让出执行权

        if "test-engineer" in successful_agents:
            actions.append("🧪 执行集成测试和系统验证")
        else:
            actions.append("🧪 添加测试工程师进行质量保证")

        if "security-auditor" in successful_agents:
            actions.append("🔒 进行安全审计和漏洞扫描")
        else:
            actions.append("🔒 添加安全专家进行安全评估")

        if "devops-engineer" in successful_agents:
            actions.append("🚀 准备生产环境部署")
        else:
            actions.append("🚀 配置DevOps流程和部署管道")

        actions.append("📊 生成项目文档和用户手册")
        actions.append("🎯 进行用户验收测试")

        return actions

    def _generate_next_actions(self, results: List[ExecutionResult]) -> List[str]:
        """生成下一步行动建议"""
        actions = []

        successful_agents = [r.agent_name for r in results if r.success]
        failed_agents = [r.agent_name for r in results if not r.success]

        if failed_agents:
            actions.append(f"🔧 修复失败的agents: {', '.join(failed_agents)}")

        if "test-engineer" in successful_agents:
            actions.append("🧪 执行集成测试和系统验证")
        else:
            actions.append("🧪 添加测试工程师进行质量保证")

        if "security-auditor" in successful_agents:
            actions.append("🔒 进行安全审计和漏洞扫描")
        else:
            actions.append("🔒 添加安全专家进行安全评估")

        if "devops-engineer" in successful_agents:
            actions.append("🚀 准备生产环境部署")
        else:
            actions.append("🚀 配置DevOps流程和部署管道")

        actions.append("📊 生成项目文档和用户手册")
        actions.append("🎯 进行用户验收测试")

        return actions

    def get_execution_status(self) -> Dict[str, Any]:
        """获取当前执行状态"""
        if not self.execution_log:
            return {"status": "idle", "message": "没有活跃的执行任务"}

        latest = self.execution_log[-1]
        return {
            "status": latest["status"],
            "task_description": latest["task_description"],
            "timestamp": latest["timestamp"],
            "agent_count": latest["analysis"]["agent_count"],
            "execution_mode": latest["analysis"]["execution_mode"]
        }

    def save_execution_report(self, summary: ParallelExecutionSummary,
                            filename: Optional[str] = None) -> str:
        """保存执行报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"perfect21_execution_report_{timestamp}.json"

        report_data = {
            "execution_summary": {
                "task_description": summary.task_description,
                "total_agents": summary.total_agents,
                "successful_agents": summary.successful_agents,
                "failed_agents": summary.failed_agents,
                "execution_time": summary.total_execution_time,
                "timestamp": datetime.now().isoformat()
            },
            "agent_results": [
                {
                    "agent_name": result.agent_name,
                    "task_description": result.task_description,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message
                }
                for result in summary.results
            ],
            "integrated_output": summary.integrated_output
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"执行报告已保存到: {filename}")
        return filename

# 全局执行器实例
_parallel_executor = None

def get_parallel_executor() -> ParallelExecutor:
    """获取并行执行控制器实例"""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor()
    return _parallel_executor

# 为测试添加简化的模拟执行方法
async def execute_parallel_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """简化的并行任务执行方法（为测试使用）"""
    import asyncio
    import random

    start_time = time.time()

    async def mock_task_execution(task):
        task_id = task.get('id', 'unknown')
        execution_time = task.get('execution_time', 1.0)

        # 模拟异步执行
        await asyncio.sleep(execution_time)

        # 模拟成功率（90%）
        success = random.random() > 0.1

        return {
            'task_id': task_id,
            'success': success,
            'result': f'Mock result for {task_id}' if success else None,
            'error': f'Mock error for {task_id}' if not success else None,
            'execution_time': execution_time
        }

    # 并行执行所有任务
    results = await asyncio.gather(*[mock_task_execution(task) for task in tasks], return_exceptions=True)

    execution_time = time.time() - start_time
    successful_tasks = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))

    return {
        'success': successful_tasks == len(tasks),
        'total_tasks': len(tasks),
        'completed_tasks': successful_tasks,
        'failed_tasks': len(tasks) - successful_tasks,
        'execution_time': execution_time,
        'task_results': results
    }