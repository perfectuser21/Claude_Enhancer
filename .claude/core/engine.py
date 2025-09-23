#!/usr/bin/env python3
"""
Claude Enhancer Core Engine - 8-Phase工作流执行器
负责控制和执行完整的8-Phase开发生命周期
"""

import json
import os
import sys
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class Phase(Enum):
    """8-Phase工作流定义"""

    PHASE_0_BRANCH = 0  # Git分支创建
    PHASE_1_ANALYSIS = 1  # 需求分析
    PHASE_2_DESIGN = 2  # 设计规划
    PHASE_3_IMPLEMENT = 3  # 实现开发
    PHASE_4_TEST = 4  # 本地测试
    PHASE_5_COMMIT = 5  # 代码提交
    PHASE_6_REVIEW = 6  # 代码审查
    PHASE_7_DEPLOY = 7  # 合并部署


class TaskType(Enum):
    """任务类型定义"""

    BUG_FIX = "bug_fix"
    NEW_FEATURE = "new_feature"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"


class WorkflowEngine:
    """
    核心工作流引擎
    永恒不变的执行逻辑，控制整个开发流程
    """

    def __init__(self, config_path: str = ".claude/core/config.yaml"):
        self.config_path = config_path
        self.current_phase = Phase.PHASE_0_BRANCH
        self.task_type = None
        self.phase_history = []
        self.state_file = ".claude/phase_state.json"
        self._load_state()

    def _load_state(self):
        """加载Phase状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.current_phase = Phase(state.get("current_phase", 0))
                    self.phase_history = state.get("history", [])
            except Exception as e:
                print(f"Warning: Failed to load state: {e}")

    def _save_state(self):
        """保存Phase状态"""
        state = {
            "current_phase": self.current_phase.value,
            "history": self.phase_history,
            "last_updated": datetime.now().isoformat(),
        }
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def detect_task_type(self, description: str) -> TaskType:
        """自动检测任务类型"""
        description_lower = description.lower()

        # 关键词匹配
        if any(word in description_lower for word in ["bug", "fix", "修复", "issue"]):
            return TaskType.BUG_FIX
        elif any(
            word in description_lower for word in ["new", "feature", "新功能", "add"]
        ):
            return TaskType.NEW_FEATURE
        elif any(word in description_lower for word in ["refactor", "重构", "optimize"]):
            return TaskType.REFACTORING
        elif any(word in description_lower for word in ["doc", "文档", "readme"]):
            return TaskType.DOCUMENTATION
        elif any(word in description_lower for word in ["performance", "性能", "speed"]):
            return TaskType.PERFORMANCE
        elif any(
            word in description_lower for word in ["security", "安全", "vulnerability"]
        ):
            return TaskType.SECURITY
        else:
            return TaskType.NEW_FEATURE  # 默认

    def get_required_phases(self, task_type: TaskType) -> List[Phase]:
        """根据任务类型获取必需的Phase"""
        phase_map = {
            TaskType.BUG_FIX: [
                Phase.PHASE_1_ANALYSIS,
                Phase.PHASE_3_IMPLEMENT,
                Phase.PHASE_4_TEST,
                Phase.PHASE_5_COMMIT,
            ],
            TaskType.NEW_FEATURE: [
                Phase.PHASE_0_BRANCH,
                Phase.PHASE_1_ANALYSIS,
                Phase.PHASE_2_DESIGN,
                Phase.PHASE_3_IMPLEMENT,
                Phase.PHASE_4_TEST,
                Phase.PHASE_5_COMMIT,
                Phase.PHASE_6_REVIEW,
            ],
            TaskType.REFACTORING: [
                Phase.PHASE_1_ANALYSIS,
                Phase.PHASE_2_DESIGN,
                Phase.PHASE_3_IMPLEMENT,
                Phase.PHASE_4_TEST,
                Phase.PHASE_5_COMMIT,
            ],
            TaskType.DOCUMENTATION: [
                Phase.PHASE_1_ANALYSIS,
                Phase.PHASE_3_IMPLEMENT,
                Phase.PHASE_5_COMMIT,
            ],
            TaskType.PERFORMANCE: [
                Phase.PHASE_1_ANALYSIS,
                Phase.PHASE_2_DESIGN,
                Phase.PHASE_3_IMPLEMENT,
                Phase.PHASE_4_TEST,
                Phase.PHASE_5_COMMIT,
            ],
            TaskType.SECURITY: [
                Phase.PHASE_1_ANALYSIS,
                Phase.PHASE_3_IMPLEMENT,
                Phase.PHASE_4_TEST,
                Phase.PHASE_5_COMMIT,
                Phase.PHASE_6_REVIEW,
            ],
        }
        return phase_map.get(task_type, list(Phase))

    def can_skip_to_phase(self, target_phase: Phase) -> bool:
        """检查是否可以跳转到目标Phase"""
        if self.task_type is None:
            return False

        required_phases = self.get_required_phases(self.task_type)

        # 如果目标Phase不在必需列表中，可以跳过
        if target_phase not in required_phases:
            return True

        # 检查前置Phase是否完成
        for phase in required_phases:
            if phase.value >= target_phase.value:
                break
            if phase not in [Phase(p["phase"]) for p in self.phase_history]:
                return False

        return True

    def execute_phase(self, phase_id: int, **kwargs) -> Dict[str, Any]:
        """
        执行指定Phase
        这是核心执行逻辑，永恒不变
        """
        phase = Phase(phase_id)

        # 检查是否可以执行该Phase
        if not self.can_skip_to_phase(phase):
            return {
                "success": False,
                "error": f"Cannot execute {phase.name}. Prerequisites not met.",
                "required_phases": [
                    p.name for p in self.get_required_phases(self.task_type)
                ],
            }

        # 记录Phase执行
        execution_record = {
            "phase": phase.value,
            "name": phase.name,
            "timestamp": datetime.now().isoformat(),
            "metadata": kwargs,
        }

        # 执行Phase特定逻辑
        result = self._execute_phase_logic(phase, **kwargs)

        if result["success"]:
            self.phase_history.append(execution_record)
            self.current_phase = phase
            self._save_state()

        return result

    def _execute_phase_logic(self, phase: Phase, **kwargs) -> Dict[str, Any]:
        """Phase具体执行逻辑"""
        phase_handlers = {
            Phase.PHASE_0_BRANCH: self._phase0_branch,
            Phase.PHASE_1_ANALYSIS: self._phase1_analysis,
            Phase.PHASE_2_DESIGN: self._phase2_design,
            Phase.PHASE_3_IMPLEMENT: self._phase3_implement,
            Phase.PHASE_4_TEST: self._phase4_test,
            Phase.PHASE_5_COMMIT: self._phase5_commit,
            Phase.PHASE_6_REVIEW: self._phase6_review,
            Phase.PHASE_7_DEPLOY: self._phase7_deploy,
        }

        handler = phase_handlers.get(phase)
        if handler:
            return handler(**kwargs)
        else:
            return {"success": False, "error": f"No handler for {phase.name}"}

    def _phase0_branch(self, **kwargs):
        """Phase 0: 分支创建"""
        return {
            "success": True,
            "message": "Branch creation phase",
            "actions": [
                "Check current branch",
                "Create feature branch",
                "Switch to new branch",
            ],
        }

    def _phase1_analysis(self, **kwargs):
        """Phase 1: 需求分析"""
        return {
            "success": True,
            "message": "Requirement analysis phase",
            "actions": [
                "Analyze requirements",
                "Identify constraints",
                "Define success criteria",
            ],
        }

    def _phase2_design(self, **kwargs):
        """Phase 2: 设计规划"""
        return {
            "success": True,
            "message": "Design planning phase",
            "actions": ["Architecture design", "API design", "Database design"],
        }

    def _phase3_implement(self, **kwargs):
        """Phase 3: 实现开发"""
        # 这里应该触发Agent并行执行
        return {
            "success": True,
            "message": "Implementation phase",
            "actions": ["Code implementation", "Unit tests", "Documentation"],
            "requires_agents": True,
            "min_agents": 4,
        }

    def _phase4_test(self, **kwargs):
        """Phase 4: 本地测试"""
        return {
            "success": True,
            "message": "Testing phase",
            "actions": ["Run unit tests", "Run integration tests", "Check coverage"],
        }

    def _phase5_commit(self, **kwargs):
        """Phase 5: 代码提交"""
        return {
            "success": True,
            "message": "Commit phase",
            "actions": ["Stage changes", "Write commit message", "Commit to git"],
            "triggers_hooks": ["pre-commit", "commit-msg"],
        }

    def _phase6_review(self, **kwargs):
        """Phase 6: 代码审查"""
        return {
            "success": True,
            "message": "Code review phase",
            "actions": ["Create PR", "Request review", "Address feedback"],
        }

    def _phase7_deploy(self, **kwargs):
        """Phase 7: 合并部署"""
        return {
            "success": True,
            "message": "Deployment phase",
            "actions": ["Merge to main", "Deploy to production", "Monitor"],
        }

    def reset_workflow(self):
        """重置工作流状态"""
        self.current_phase = Phase.PHASE_0_BRANCH
        self.phase_history = []
        self.task_type = None
        self._save_state()
        return {"success": True, "message": "Workflow reset"}

    def get_status(self) -> Dict[str, Any]:
        """获取当前工作流状态"""
        return {
            "current_phase": self.current_phase.name,
            "phase_value": self.current_phase.value,
            "task_type": self.task_type.value if self.task_type else None,
            "completed_phases": [p["name"] for p in self.phase_history],
            "next_phases": self._get_next_phases(),
        }

    def _get_next_phases(self) -> List[str]:
        """获取下一步可执行的Phase"""
        if self.task_type is None:
            return ["Set task type first"]

        required_phases = self.get_required_phases(self.task_type)
        completed = [Phase(p["phase"]) for p in self.phase_history]

        next_phases = []
        for phase in required_phases:
            if phase not in completed:
                next_phases.append(phase.name)
                if len(next_phases) >= 3:  # 只显示接下来3个
                    break

        return next_phases


# CLI接口
if __name__ == "__main__":
    engine = WorkflowEngine()

    if len(sys.argv) < 2:
        print("Usage: engine.py <command> [args]")
        print("Commands:")
        print("  status - Show current workflow status")
        print("  detect <description> - Detect task type")
        print("  execute <phase_id> - Execute a phase")
        print("  reset - Reset workflow")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        status = engine.get_status()
        print(json.dumps(status, indent=2))

    elif command == "detect" and len(sys.argv) > 2:
        description = " ".join(sys.argv[2:])
        task_type = engine.detect_task_type(description)
        engine.task_type = task_type
        engine._save_state()
        print(f"Detected task type: {task_type.value}")
        print(
            f"Required phases: {[p.name for p in engine.get_required_phases(task_type)]}"
        )

    elif command == "execute" and len(sys.argv) > 2:
        phase_id = int(sys.argv[2])
        result = engine.execute_phase(phase_id)
        print(json.dumps(result, indent=2))

    elif command == "reset":
        result = engine.reset_workflow()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
