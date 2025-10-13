#!/usr/bin/env python3
"""
Claude Enhancer Phase State Machine
智能8-Phase工作流状态管理与自动转换
"""

import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
import subprocess
import os
import sys
from pathlib import Path

# 添加Git自动化支持
sys.path.insert(0, str(Path(__file__).parent))
try:
    from git_automation import GitAutomation

    GIT_AUTOMATION_AVAILABLE = True
except ImportError:
    GIT_AUTOMATION_AVAILABLE = False
    print("⚠️ Git automation module not available")


class PhaseType(Enum):
    # 统一为6-Phase标准流程
    P1_REQUIREMENTS = "P1_requirements"  # 需求分析
    P2_DESIGN = "P2_design"  # 架构设计
    P3_IMPLEMENTATION = "P3_implementation"  # 功能实现
    P4_TESTING = "P4_testing"  # 测试验证
    P5_REVIEW = "P5_review"  # 代码审查
    P6_RELEASE = "P6_release"  # 发布准备


class PhaseStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class PhaseTransition:
    """Phase transition record"""

    from_phase: PhaseType
    to_phase: PhaseType
    trigger: str
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class PhaseState:
    """Current phase state"""

    phase: PhaseType
    status: PhaseStatus
    progress: float  # 0.0 to 1.0
    started_at: float
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = None
    issues: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.issues is None:
            self.issues = []


class PhaseStateMachine:
    """Intelligent 8-Phase workflow state machine"""

    def __init__(self, state_file: str = "/tmp/claude_phase_state.json"):
        self.state_file = state_file
        self.current_state = None
        self.history = []
        self.lock = threading.RLock()

        # Phase dependencies and transitions
        self.phase_dependencies = {
            PhaseType.P1_REQUIREMENTS: [],
            PhaseType.P2_DESIGN: [PhaseType.P1_REQUIREMENTS],
            PhaseType.P3_IMPLEMENTATION: [PhaseType.P2_DESIGN],
            PhaseType.P4_TESTING: [PhaseType.P3_IMPLEMENTATION],
            PhaseType.P5_REVIEW: [PhaseType.P4_TESTING],
            PhaseType.P6_RELEASE: [PhaseType.P5_REVIEW],
        }

        # Tool to phase mapping
        self.tool_phase_mapping = {
            "Read": [PhaseType.P1_REQUIREMENTS, PhaseType.P2_DESIGN],
            "Grep": [PhaseType.P1_REQUIREMENTS, PhaseType.P2_DESIGN],
            "Task": [PhaseType.P3_IMPLEMENTATION],
            "Write": [PhaseType.P3_IMPLEMENTATION],
            "Edit": [PhaseType.P3_IMPLEMENTATION],
            "MultiEdit": [PhaseType.P3_IMPLEMENTATION],
            "Bash": [
                PhaseType.P4_TESTING,
                PhaseType.P6_RELEASE,
            ],
        }

        # Initialize state
        self._load_or_initialize_state()

    def _load_or_initialize_state(self):
        """Load state from file or initialize new state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    data = json.load(f)

                # Reconstruct state from JSON
                phase_data = data.get("current_state", {})
                if phase_data:
                    self.current_state = PhaseState(
                        phase=PhaseType(phase_data["phase"]),
                        status=PhaseStatus(phase_data["status"]),
                        progress=phase_data.get("progress", 0.0),
                        started_at=phase_data["started_at"],
                        completed_at=phase_data.get("completed_at"),
                        metadata=phase_data.get("metadata", {}),
                        issues=phase_data.get("issues", []),
                    )

                # Load history
                history_data = data.get("history", [])
                for transition_data in history_data:
                    transition = PhaseTransition(
                        from_phase=PhaseType(transition_data["from_phase"]),
                        to_phase=PhaseType(transition_data["to_phase"]),
                        trigger=transition_data["trigger"],
                        timestamp=transition_data["timestamp"],
                        metadata=transition_data.get("metadata", {}),
                    )
                    self.history.append(transition)
            else:
                pass  # Auto-fixed empty block
                # Initialize with P0 phase
                self._start_new_workflow()

        except Exception as e:
            print(f"Error loading phase state: {e}")
            self._start_new_workflow()

    def _start_new_workflow(self):
        """Start new workflow from P1"""
        self.current_state = PhaseState(
            phase=PhaseType.P1_REQUIREMENTS,
            status=PhaseStatus.NOT_STARTED,
            progress=0.0,
            started_at=time.time(),
            metadata={"workflow_id": f"wf_{int(time.time())}"},
        )
        self.history = []
        self._save_state()

    def _save_state(self):
        """Save current state to file"""
        try:
            data = {
                "current_state": asdict(self.current_state)
                if self.current_state
                else None,
                "history": [asdict(t) for t in self.history],
                "last_updated": time.time(),
            }

            # Convert enums to strings for JSON serialization
            if data["current_state"]:
                data["current_state"]["phase"] = data["current_state"]["phase"].value
                data["current_state"]["status"] = data["current_state"]["status"].value

            for h in data["history"]:
                h["from_phase"] = h["from_phase"].value
                h["to_phase"] = h["to_phase"].value

            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving phase state: {e}")

    def detect_current_phase_from_context(
        self,
        tool_name: str,
        task_description: str = "",
        git_context: Dict[str, Any] = None,
    ) -> PhaseType:
        """Detect current phase from execution context"""

        if git_context is None:
            git_context = self._get_git_context()

        # P0: Branch creation - on main/master branch
        if git_context.get("branch") in ["main", "master"]:
            return PhaseType.P0_BRANCH_CREATION

        # P1: Requirements analysis - reading/analyzing phase
        if tool_name in ["Read", "Grep", "Glob"] and not git_context.get("has_changes"):
            return PhaseType.P1_REQUIREMENTS

        # P2: Design planning - still analyzing but have some context
        if tool_name in ["Read", "Write"] and not git_context.get("has_implementation"):
            return PhaseType.P2_DESIGN

        # P3: Implementation - active coding
        if tool_name in ["Task", "Write", "Edit", "MultiEdit"]:
            return PhaseType.P3_IMPLEMENTATION

        # P4: Testing - running tests
        if tool_name == "Bash" and any(
            keyword in task_description.lower()
            for keyword in ["test", "pytest", "jest", "spec", "vitest"]
        ):
            return PhaseType.P4_TESTING

        # P5: Review - code review tasks
        if "review" in task_description.lower() or "audit" in task_description.lower():
            return PhaseType.P5_REVIEW

        # P6: Release - deployment and release tasks
        if any(
            keyword in task_description.lower()
            for keyword in ["deploy", "release", "tag", "publish"]
        ):
            return PhaseType.P6_RELEASE

        # Default: return current phase if no clear indicator
        return (
            self.current_state.phase
            if self.current_state
            else PhaseType.P1_REQUIREMENTS
        )

    def transition_to_phase(
        self, target_phase: PhaseType, trigger: str, metadata: Dict[str, Any] = None
    ) -> bool:
        """Transition to target phase with validation"""

        with self.lock:
            if not self.current_state:
                return False

            current_phase = self.current_state.phase

            # Check if transition is valid
            if not self._is_valid_transition(current_phase, target_phase):
                print(
                    f"Invalid transition from {current_phase.value} to {target_phase.value}"
                )
                return False

            # Record transition
            transition = PhaseTransition(
                from_phase=current_phase,
                to_phase=target_phase,
                trigger=trigger,
                timestamp=time.time(),
                metadata=metadata or {},
            )
            self.history.append(transition)

            # Complete current phase if moving forward
            if self._is_forward_transition(current_phase, target_phase):
                self.current_state.status = PhaseStatus.COMPLETED
                self.current_state.completed_at = time.time()
                self.current_state.progress = 1.0

            # Start new phase
            self.current_state = PhaseState(
                phase=target_phase,
                status=PhaseStatus.IN_PROGRESS,
                progress=0.0,
                started_at=time.time(),
                metadata=metadata or {},
            )

            self._save_state()
            return True

    def update_phase_progress(self, progress: float, metadata: Dict[str, Any] = None):
        """Update current phase progress"""
        with self.lock:
            if self.current_state:
                self.current_state.progress = max(0.0, min(1.0, progress))
                if metadata:
                    self.current_state.metadata.update(metadata)

                # Auto-complete if progress reaches 100%
                if progress >= 1.0:
                    self.current_state.status = PhaseStatus.COMPLETED
                    self.current_state.completed_at = time.time()

                    # 触发Git自动化
                    self._trigger_git_automation()

                self._save_state()

    def add_phase_issue(self, issue: str):
        """Add issue to current phase"""
        with self.lock:
            if self.current_state:
                self.current_state.issues.append(f"{time.time()}: {issue}")
                self._save_state()

    def auto_detect_and_transition(
        self, tool_name: str, task_description: str = "", force_transition: bool = False
    ) -> Tuple[PhaseType, bool]:
        """Auto-detect phase and transition if needed"""

        detected_phase = self.detect_current_phase_from_context(
            tool_name, task_description
        )

        # Check if we need to transition
        if not self.current_state or detected_phase != self.current_state.phase:
            if force_transition or self._should_auto_transition(detected_phase):
                success = self.transition_to_phase(
                    detected_phase,
                    f"auto_transition_from_{tool_name}",
                    {"tool": tool_name, "task": task_description[:100]},
                )
                return detected_phase, success

        return self.current_state.phase, False

    def get_phase_summary(self) -> Dict[str, Any]:
        """Get comprehensive phase summary"""
        if not self.current_state:
            return {"error": "No active workflow"}

        # Calculate overall workflow progress
        phase_weights = {
            PhaseType.P0_BRANCH_CREATION: 0.05,
            PhaseType.P1_REQUIREMENTS: 0.1,
            PhaseType.P2_DESIGN: 0.15,
            PhaseType.P3_IMPLEMENTATION: 0.4,
            PhaseType.P4_TESTING: 0.15,
            PhaseType.P5_COMMIT: 0.05,
            PhaseType.P6_REVIEW: 0.05,
            PhaseType.P7_DEPLOYMENT: 0.05,
        }

        completed_phases = set()
        for transition in self.history:
            if self._is_forward_transition(transition.from_phase, transition.to_phase):
                completed_phases.add(transition.from_phase)

        # Add current phase if completed
        if self.current_state.status == PhaseStatus.COMPLETED:
            completed_phases.add(self.current_state.phase)

        total_progress = sum(phase_weights[phase] for phase in completed_phases)
        if self.current_state.status == PhaseStatus.IN_PROGRESS:
            total_progress += (
                phase_weights[self.current_state.phase] * self.current_state.progress
            )

        # Get recommended next actions
        next_actions = self._get_recommended_actions()

        return {
            "current_phase": self.current_state.phase.value,
            "phase_status": self.current_state.status.value,
            "phase_progress": self.current_state.progress,
            "overall_progress": min(1.0, total_progress),
            "workflow_duration": time.time() - self.current_state.started_at,
            "completed_phases": [p.value for p in completed_phases],
            "issues_count": len(self.current_state.issues),
            "next_actions": next_actions,
            "phase_metadata": self.current_state.metadata,
        }

    def _get_git_context(self) -> Dict[str, Any]:
        """Get current git context"""
        try:
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )

            status_output = subprocess.check_output(
                ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL
            ).decode()

            has_changes = len(status_output.strip()) > 0

            # Check for implementation files
            has_implementation = False
            try:
                files = subprocess.check_output(
                    ["git", "ls-files"], stderr=subprocess.DEVNULL
                ).decode()
                implementation_patterns = [
                    ".js",
                    ".py",
                    ".ts",
                    ".java",
                    ".cpp",
                    ".c",
                    ".go",
                    ".rs",
                ]
                has_implementation = any(
                    pattern in files for pattern in implementation_patterns
                )
            except:
                pass

            return {
                "branch": branch,
                "has_changes": has_changes,
                "has_implementation": has_implementation,
                "change_count": len(status_output.strip().split("\n"))
                if has_changes
                else 0,
            }

        except:
            return {
                "branch": "unknown",
                "has_changes": False,
                "has_implementation": False,
                "change_count": 0,
            }

    def _trigger_git_automation(self):
        """触发Git自动化操作"""
        if not GIT_AUTOMATION_AVAILABLE:
            return

        if not self.current_state:
            return

        phase = self.current_state.phase
        phase_name = phase.value.split("_")[0]  # 获取P1, P2等

        try:
            git = GitAutomation()

            # 根据Phase执行相应的Git操作
            if phase == PhaseType.P3_IMPLEMENTATION:
                print("🔄 Auto-committing P3 implementation...")
                git.auto_commit_phase("P3", "feat: 完成功能实现")

            elif phase == PhaseType.P4_TESTING:
                print("🔄 Auto-committing P4 test results...")
                git.auto_commit_phase("P4", "test: 完成测试验证")

            elif phase == PhaseType.P5_REVIEW:
                print("🔄 Auto-committing P5 review changes...")
                git.auto_commit_phase("P5", "review: 完成代码审查")

            elif phase == PhaseType.P6_RELEASE:
                print("🔄 Auto-committing P6 and creating release tag...")
                git.auto_commit_phase("P6", "release: 准备发布版本")
                git.auto_tag_release()

                # 可选：创建PR
                if os.environ.get("AUTO_CREATE_PR", "true").lower() == "true":
                    git.auto_create_pr()

        except Exception as e:
            print(f"⚠️ Git automation failed: {e}")

    def _is_valid_transition(self, from_phase: PhaseType, to_phase: PhaseType) -> bool:
        """Check if phase transition is valid"""
        # Allow backward transitions for iteration
        if self._get_phase_order(to_phase) <= self._get_phase_order(from_phase):
            return True

        # Check forward dependencies
        dependencies = self.phase_dependencies.get(to_phase, [])
        completed_phases = self._get_completed_phases()

        return all(dep in completed_phases for dep in dependencies)

    def _is_forward_transition(
        self, from_phase: PhaseType, to_phase: PhaseType
    ) -> bool:
        """Check if transition is forward (progressing)"""
        return self._get_phase_order(to_phase) > self._get_phase_order(from_phase)

    def _get_phase_order(self, phase: PhaseType) -> int:
        """Get numerical order of phase"""
        order_map = {
            PhaseType.P1_REQUIREMENTS: 1,
            PhaseType.P2_DESIGN: 2,
            PhaseType.P3_IMPLEMENTATION: 3,
            PhaseType.P4_TESTING: 4,
            PhaseType.P5_REVIEW: 5,
            PhaseType.P6_RELEASE: 6,
        }
        return order_map.get(phase, 0)

    def _get_completed_phases(self) -> set:
        """Get set of completed phases"""
        completed = set()
        for transition in self.history:
            if self._is_forward_transition(transition.from_phase, transition.to_phase):
                completed.add(transition.from_phase)

        if self.current_state and self.current_state.status == PhaseStatus.COMPLETED:
            completed.add(self.current_state.phase)

        return completed

    def _should_auto_transition(self, detected_phase: PhaseType) -> bool:
        """Determine if should auto-transition to detected phase"""
        if not self.current_state:
            return True

        # Don't auto-transition backward unless explicitly needed
        if self._get_phase_order(detected_phase) < self._get_phase_order(
            self.current_state.phase
        ):
            return False

        # Allow transition if current phase is completed or stuck
        if self.current_state.status in [PhaseStatus.COMPLETED, PhaseStatus.BLOCKED]:
            return True

        # Allow transition to next logical phase if current has significant progress
        if (
            self._get_phase_order(detected_phase)
            == self._get_phase_order(self.current_state.phase) + 1
            and self.current_state.progress > 0.7
        ):
            return True

        return False

    def _get_recommended_actions(self) -> List[str]:
        """Get recommended actions for current phase"""
        if not self.current_state:
            return ["Start new workflow"]

        phase = self.current_state.phase
        progress = self.current_state.progress

        actions = []

        if phase == PhaseType.P0_BRANCH_CREATION:
            actions.append(
                "Create feature branch: git checkout -b feature/your-feature"
            )

        elif phase == PhaseType.P1_REQUIREMENTS:
            if progress < 0.5:
                actions.append("Read and analyze project requirements")
                actions.append("Use Read/Grep tools to understand codebase")
            else:
                actions.append("Document requirements and move to design phase")

        elif phase == PhaseType.P2_DESIGN:
            if progress < 0.5:
                actions.append("Design system architecture")
                actions.append("Plan implementation approach")
            else:
                actions.append("Finalize design and start implementation")

        elif phase == PhaseType.P3_IMPLEMENTATION:
            if progress < 0.3:
                actions.append("Use Task tool to coordinate agents")
                actions.append("Start with core functionality")
            elif progress < 0.8:
                actions.append("Continue implementation with Write/Edit tools")
                actions.append("Focus on remaining features")
            else:
                actions.append("Complete implementation and prepare for testing")

        elif phase == PhaseType.P4_TESTING:
            actions.append("Run unit tests")
            actions.append("Perform integration testing")
            actions.append("Verify functionality")

        elif phase == PhaseType.P5_COMMIT:
            actions.append("Review changes: git status")
            actions.append("Stage changes: git add .")
            actions.append("Commit changes with descriptive message")

        elif phase == PhaseType.P6_REVIEW:
            actions.append("Create Pull Request")
            actions.append("Request team review")
            actions.append("Address review feedback")

        elif phase == PhaseType.P7_DEPLOYMENT:
            actions.append("Merge PR to main branch")
            actions.append("Deploy to production")
            actions.append("Monitor deployment")

        return actions


# Singleton instance
_phase_machine_instance = None


def get_phase_machine() -> PhaseStateMachine:
    """Get singleton phase state machine instance"""
    global _phase_machine_instance
    if _phase_machine_instance is None:
        _phase_machine_instance = PhaseStateMachine()
    return _phase_machine_instance


# CLI interface for testing
if __name__ == "__main__":
    import sys

    machine = get_phase_machine()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            summary = machine.get_phase_summary()
            print(json.dumps(summary, indent=2))

        elif command == "detect" and len(sys.argv) > 2:
            tool_name = sys.argv[2]
            task_desc = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""

            detected_phase, transitioned = machine.auto_detect_and_transition(
                tool_name, task_desc
            )
            print(f"Detected phase: {detected_phase.value}")
            print(f"Transitioned: {transitioned}")

        elif command == "progress" and len(sys.argv) > 2:
            progress = float(sys.argv[2])
            machine.update_phase_progress(progress)
            print(f"Updated progress to {progress}")

        elif command == "reset":
            machine._start_new_workflow()
            print("Workflow reset to P0")

    else:
        summary = machine.get_phase_summary()
        print("Claude Enhancer Phase State Machine")
        print("=" * 40)
        print(f"Current Phase: {summary['current_phase']}")
        print(f"Status: {summary['phase_status']}")
        print(f"Progress: {summary['phase_progress']:.1%}")
        print(f"Overall Progress: {summary['overall_progress']:.1%}")
        print(f"Issues: {summary['issues_count']}")
        print("\nRecommended Actions:")
        for i, action in enumerate(summary["next_actions"], 1):
            print(f"  {i}. {action}")
