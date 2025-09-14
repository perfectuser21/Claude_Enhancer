#!/usr/bin/env python3
"""
AI管家核心功能模块
专注于Claude Code的自动化调用和任务处理
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("AI_Butler")

class AIButler:
    """AI管家核心类"""

    def __init__(self):
        """初始化管家"""
        self.session_history = []
        self.claude_available = self._check_claude_availability()
        logger.info(f"AI Butler initialized. Claude available: {self.claude_available}")

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

    async def execute_claude_task(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """执行Claude Code任务 - 使用非交互模式"""
        if not self.claude_available:
            return {
                "success": False,
                "error": "Claude Code不可用",
                "output": ""
            }

        start_time = time.time()

        try:
            # 使用非交互模式调用Claude Code
            cmd = ["claude", "-p", task]
            logger.info(f"执行Claude命令: {' '.join(cmd)}")

            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="/home/xx/dev/VibePilot_Kit_v2"
            )

            # 设置30秒超时
            try:
                stdout, stderr = process.communicate(timeout=30)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return {
                    "success": False,
                    "error": "任务执行超时(30秒)",
                    "output": stdout,
                    "stderr": stderr,
                    "execution_time": 30.0
                }

            execution_time = time.time() - start_time

            if return_code == 0:
                # 记录到会话历史
                self.session_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "task": task,
                    "output": stdout,
                    "execution_time": execution_time,
                    "success": True
                })

                return {
                    "success": True,
                    "output": stdout,
                    "stderr": stderr,
                    "execution_time": execution_time,
                    "return_code": return_code
                }
            else:
                return {
                    "success": False,
                    "error": f"Claude执行失败，返回码: {return_code}",
                    "output": stdout,
                    "stderr": stderr,
                    "execution_time": execution_time,
                    "return_code": return_code
                }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行Claude任务时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": execution_time
            }

    def analyze_user_message(self, message: str) -> Dict[str, Any]:
        """分析用户消息，决定如何处理"""
        message_lower = message.lower()

        # 检查是否是任务型消息
        task_keywords = [
            '创建', '实现', '开发', '设计', '分析', '优化', '重构',
            '帮我', '写', '做', '生成', '修复', '检查', '测试',
            'create', 'implement', 'develop', 'design', 'analyze',
            'optimize', 'refactor', 'help', 'write', 'make', 'generate',
            'fix', 'check', 'test'
        ]

        is_task = any(keyword in message_lower for keyword in task_keywords)

        if is_task:
            return {
                "type": "task",
                "should_execute_claude": True,
                "reason": "检测到任务相关关键词，将调用Claude Code处理"
            }
        else:
            return {
                "type": "chat",
                "should_execute_claude": False,
                "reason": "普通对话，不需要调用Claude Code"
            }

    def generate_chat_response(self, message: str) -> str:
        """生成聊天回复"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['你好', 'hello', 'hi', '嗨']):
            return "你好！我是你的AI管家，可以帮你处理各种编程任务。你可以告诉我具体需要做什么，我会自动调用Claude Code来帮你完成。"

        elif any(word in message_lower for word in ['帮助', 'help', '怎么用']):
            return """🤖 AI管家使用指南:

📋 **任务处理**:
• 直接告诉我你需要做什么，例如：
  - "分析我的代码质量"
  - "创建一个登录API"
  - "优化数据库查询"
  - "重构这个函数"

💬 **特点**:
• 自动调用Claude Code (非交互模式)
• 无需手动确认权限
• 实时显示执行进度
• 保存执行历史

🎯 直接说出你的需求就行！"""

        elif any(word in message_lower for word in ['状态', 'status', '历史']):
            recent_tasks = len(self.session_history)
            if recent_tasks > 0:
                last_task = self.session_history[-1]
                return f"""📊 管家状态:
• Claude Code: {'✅ 可用' if self.claude_available else '❌ 不可用'}
• 本次会话已处理任务: {recent_tasks}个
• 最近任务: {last_task['task'][:50]}...
• 最近执行时间: {last_task['execution_time']:.1f}秒"""
            else:
                return f"""📊 管家状态:
• Claude Code: {'✅ 可用' if self.claude_available else '❌ 不可用'}
• 本次会话已处理任务: 0个
• 等待你的第一个任务指令..."""

        elif any(word in message_lower for word in ['谢谢', 'thanks', '感谢']):
            return "不客气！很高兴能帮助你。有其他任务随时告诉我！🤖"

        else:
            return f"我理解你想聊「{message}」。如果这是一个开发任务，请更具体地告诉我需要做什么，我会立即调用Claude Code来帮你处理！"

    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        return {
            "claude_available": self.claude_available,
            "session_tasks": len(self.session_history),
            "total_tasks": len(self.session_history),
            "successful_tasks": len([t for t in self.session_history if t.get('success')]),
            "timestamp": datetime.now().isoformat()
        }