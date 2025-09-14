#!/usr/bin/env python3
"""
Claude Code执行器
封装Claude Code的非交互式执行逻辑
"""

import asyncio
import subprocess
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("ClaudeExecutor")

class ClaudeExecutor:
    """Claude Code执行器"""

    def __init__(self, working_directory: str = None):
        """初始化执行器"""
        import os
        self.working_directory = working_directory or os.getcwd()
        self.execution_history: List[Dict[str, Any]] = []
        self.is_available = self._check_claude_availability()
        logger.info(f"Claude执行器初始化: 可用={self.is_available}, 工作目录={self.working_directory}")

    def _check_claude_availability(self) -> bool:
        """检查Claude Code是否可用"""
        try:
            result = subprocess.run(
                ["claude", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Claude Code不可用: {e}")
            return False

    async def execute_task(self, task: str, context: Dict[str, Any] = None,
                          timeout: int = 30, workspace: str = None) -> Dict[str, Any]:
        """执行Claude Code任务"""

        if not self.is_available:
            return {
                "success": False,
                "error": "Claude Code不可用",
                "output": "",
                "stderr": "",
                "execution_time": 0,
                "task": task
            }

        start_time = time.time()
        execution_id = f"exec_{int(start_time)}"

        # 确定工作目录
        work_dir = workspace if workspace else self.working_directory
        if not Path(work_dir).exists():
            logger.warning(f"工作目录不存在，使用默认: {self.working_directory}")
            work_dir = self.working_directory

        logger.info(f"[{execution_id}] 执行Claude任务: {task[:100]}...")

        try:
            # 构建命令 - 使用-p参数启用非交互模式
            cmd = ["claude", "-p", task]

            # 创建子进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=work_dir
            )

            # 执行并设置超时
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = time.time() - start_time

                result = {
                    "success": False,
                    "error": f"任务执行超时({timeout}秒)",
                    "output": stdout or "",
                    "stderr": stderr or "",
                    "execution_time": execution_time,
                    "return_code": process.returncode,
                    "task": task,
                    "execution_id": execution_id,
                    "workspace": work_dir
                }

                self._record_execution(result)
                return result

            execution_time = time.time() - start_time

            # 构建结果
            result = {
                "success": return_code == 0,
                "output": stdout or "",
                "stderr": stderr or "",
                "execution_time": execution_time,
                "return_code": return_code,
                "task": task,
                "execution_id": execution_id,
                "workspace": work_dir
            }

            if not result["success"]:
                result["error"] = f"Claude执行失败，返回码: {return_code}"
                if stderr:
                    result["error"] += f"\n错误信息: {stderr}"

            # 记录执行历史
            self._record_execution(result)

            logger.info(f"[{execution_id}] 任务完成: 成功={result['success']}, "
                       f"耗时={execution_time:.2f}秒")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            result = {
                "success": False,
                "error": str(e),
                "output": "",
                "stderr": "",
                "execution_time": execution_time,
                "task": task,
                "execution_id": execution_id,
                "workspace": work_dir
            }

            self._record_execution(result)
            logger.error(f"[{execution_id}] 执行异常: {e}")
            return result

    def _record_execution(self, result: Dict[str, Any]):
        """记录执行历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_id": result["execution_id"],
            "task": result["task"][:200] + "..." if len(result["task"]) > 200 else result["task"],
            "success": result["success"],
            "execution_time": result["execution_time"],
            "workspace": result.get("workspace"),
            "error": result.get("error", "")
        }

        self.execution_history.append(history_entry)

        # 保持历史记录在合理范围内
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "avg_execution_time": 0,
                "is_available": self.is_available
            }

        successful = [h for h in self.execution_history if h["success"]]
        execution_times = [h["execution_time"] for h in self.execution_history]

        return {
            "total_executions": len(self.execution_history),
            "successful_executions": len(successful),
            "success_rate": len(successful) / len(self.execution_history),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "is_available": self.is_available,
            "working_directory": self.working_directory,
            "recent_errors": [
                h["error"] for h in self.execution_history[-10:]
                if not h["success"] and h["error"]
            ]
        }

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的执行历史"""
        return self.execution_history[-limit:]

    def clear_history(self):
        """清空执行历史"""
        cleared_count = len(self.execution_history)
        self.execution_history = []
        logger.info(f"清空执行历史: {cleared_count}条记录")

    async def batch_execute(self, tasks: List[str],
                           context: Dict[str, Any] = None,
                           max_concurrent: int = 2) -> List[Dict[str, Any]]:
        """批量执行任务"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(task):
            async with semaphore:
                return await self.execute_task(task, context)

        logger.info(f"批量执行{len(tasks)}个任务，最大并发数: {max_concurrent}")
        results = await asyncio.gather(*[execute_with_semaphore(task) for task in tasks])

        successful = len([r for r in results if r["success"]])
        logger.info(f"批量执行完成: {successful}/{len(tasks)}成功")

        return results

    def refresh_availability(self) -> bool:
        """刷新Claude可用性状态"""
        old_status = self.is_available
        self.is_available = self._check_claude_availability()

        if old_status != self.is_available:
            logger.info(f"Claude可用性状态变更: {old_status} -> {self.is_available}")

        return self.is_available