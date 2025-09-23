#!/usr/bin/env python3
"""
Claude Enhancer执行监控系统
实时监控和报告执行状态
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time


class ExecutionMonitor:
    """执行监控器"""

    def __init__(self):
        self.log_file = ".claude/execution_log.json"
        self.stats_file = ".claude/execution_stats.json"
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "task_description": "",
            "phase_executions": [],
            "agent_executions": [],
            "violations": [],
            "status": "running",
        }
        self._load_history()

    def _load_history(self):
        """加载历史记录"""
        self.history = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def _save_history(self):
        """保存历史记录"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def start_task(self, task_description: str, task_type: str = None):
        """开始任务监控"""
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "task_description": task_description,
            "task_type": task_type,
            "phase_executions": [],
            "agent_executions": [],
            "violations": [],
            "status": "running",
        }
        self._report_status(f"🚀 开始任务: {task_description[:50]}...")

    def record_phase(self, phase_id: int, phase_name: str, success: bool = True):
        """记录Phase执行"""
        phase_record = {
            "phase_id": phase_id,
            "phase_name": phase_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
        }
        self.current_session["phase_executions"].append(phase_record)

        status = "✅" if success else "❌"
        self._report_status(f"{status} Phase {phase_id}: {phase_name}")

    def record_agent(self, agent_name: str, execution_mode: str = "parallel"):
        """记录Agent执行"""
        agent_record = {
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "execution_mode": execution_mode,
        }
        self.current_session["agent_executions"].append(agent_record)

    def record_violation(self, violation_type: str, message: str):
        """记录违规"""
        violation = {
            "type": violation_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.current_session["violations"].append(violation)
        self._report_status(f"⚠️ 违规: {message}")

    def end_task(self, success: bool = True, result: Any = None):
        """结束任务监控"""
        self.current_session["end_time"] = datetime.now().isoformat()
        self.current_session["status"] = "completed" if success else "failed"
        self.current_session["result"] = result

        # 计算执行时间
        start = datetime.fromisoformat(self.current_session["start_time"])
        end = datetime.fromisoformat(self.current_session["end_time"])
        duration = (end - start).total_seconds()
        self.current_session["duration_seconds"] = duration

        # 保存到历史
        self.history.append(self.current_session)
        self._save_history()

        # 更新统计
        self._update_statistics()

        # 生成报告
        self._generate_report()

    def _update_statistics(self):
        """更新统计信息"""
        stats = {
            "total_tasks": len(self.history),
            "successful_tasks": sum(
                1 for h in self.history if h["status"] == "completed"
            ),
            "failed_tasks": sum(1 for h in self.history if h["status"] == "failed"),
            "total_agents_used": sum(
                len(h.get("agent_executions", [])) for h in self.history
            ),
            "total_violations": sum(len(h.get("violations", [])) for h in self.history),
            "average_duration": self._calculate_average_duration(),
            "phase_statistics": self._calculate_phase_stats(),
            "agent_statistics": self._calculate_agent_stats(),
            "last_updated": datetime.now().isoformat(),
        }

        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, "w") as f:
            json.dump(stats, f, indent=2)

    def _calculate_average_duration(self) -> float:
        """计算平均执行时间"""
        durations = [
            h.get("duration_seconds", 0)
            for h in self.history
            if "duration_seconds" in h
        ]
        return sum(durations) / len(durations) if durations else 0

    def _calculate_phase_stats(self) -> Dict[str, int]:
        """计算Phase统计"""
        phase_count = {}
        for history in self.history:
            for phase in history.get("phase_executions", []):
                phase_name = phase["phase_name"]
                phase_count[phase_name] = phase_count.get(phase_name, 0) + 1
        return phase_count

    def _calculate_agent_stats(self) -> Dict[str, int]:
        """计算Agent使用统计"""
        agent_count = {}
        for history in self.history:
            for agent in history.get("agent_executions", []):
                agent_name = agent["agent_name"]
                agent_count[agent_name] = agent_count.get(agent_name, 0) + 1

        # 按使用次数排序
        return dict(sorted(agent_count.items(), key=lambda x: x[1], reverse=True)[:10])

    def _generate_report(self):
        """生成执行报告"""
        session = self.current_session

        print("\n" + "=" * 60)
        print("📊 Claude Enhancer执行报告")
        print("=" * 60)

        print(f"\n📋 任务信息:")
        print(f"  • 描述: {session['task_description'][:80]}")
        print(f"  • 类型: {session.get('task_type', 'unknown')}")
        print(f"  • 状态: {session['status']}")
        print(f"  • 耗时: {session.get('duration_seconds', 0):.2f}秒")

        if session["phase_executions"]:
            print(f"\n🔄 Phase执行记录:")
            for phase in session["phase_executions"]:
                status = "✅" if phase["success"] else "❌"
                print(f"  {status} {phase['phase_name']}")

        if session["agent_executions"]:
            print(f"\n🤖 Agent使用情况:")
            print(f"  • 总数: {len(session['agent_executions'])}个")
            print(
                f"  • 模式: {session['agent_executions'][0].get('execution_mode', 'unknown')}"
            )
            # 显示前5个Agent
            for agent in session["agent_executions"][:5]:
                print(f"    - {agent['agent_name']}")
            if len(session["agent_executions"]) > 5:
                print(f"    ... 还有{len(session['agent_executions'])-5}个")

        if session["violations"]:
            print(f"\n⚠️ 违规记录:")
            for violation in session["violations"]:
                print(f"  • {violation['type']}: {violation['message']}")

        print("\n" + "=" * 60)

    def _report_status(self, message: str):
        """实时报告状态"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def get_live_status(self) -> Dict[str, Any]:
        """获取实时状态"""
        if not self.current_session["status"] == "running":
            return {"status": "idle", "message": "No task running"}

        start = datetime.fromisoformat(self.current_session["start_time"])
        elapsed = (datetime.now() - start).total_seconds()

        return {
            "status": "running",
            "task": self.current_session["task_description"][:50],
            "elapsed_seconds": elapsed,
            "current_phase": self.current_session["phase_executions"][-1]["phase_name"]
            if self.current_session["phase_executions"]
            else None,
            "agents_used": len(self.current_session["agent_executions"]),
            "violations": len(self.current_session["violations"]),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r") as f:
                return json.load(f)
        return {}


# CLI接口
if __name__ == "__main__":
    monitor = ExecutionMonitor()

    if len(sys.argv) < 2:
        print("Usage: execution_monitor.py <command> [args]")
        print("Commands:")
        print("  start <description> - Start task monitoring")
        print("  phase <id> <name> - Record phase execution")
        print("  agent <name> - Record agent execution")
        print("  violation <type> <message> - Record violation")
        print("  end [success|failure] - End task monitoring")
        print("  status - Get live status")
        print("  stats - Get statistics")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start" and len(sys.argv) > 2:
        description = " ".join(sys.argv[2:])
        monitor.start_task(description)

    elif command == "phase" and len(sys.argv) > 3:
        phase_id = int(sys.argv[2])
        phase_name = sys.argv[3]
        monitor.record_phase(phase_id, phase_name)

    elif command == "agent" and len(sys.argv) > 2:
        agent_name = sys.argv[2]
        monitor.record_agent(agent_name)

    elif command == "violation" and len(sys.argv) > 3:
        violation_type = sys.argv[2]
        message = " ".join(sys.argv[3:])
        monitor.record_violation(violation_type, message)

    elif command == "end":
        success = len(sys.argv) <= 2 or sys.argv[2] != "failure"
        monitor.end_task(success)

    elif command == "status":
        status = monitor.get_live_status()
        print(json.dumps(status, indent=2))

    elif command == "stats":
        stats = monitor.get_statistics()
        print(json.dumps(stats, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
