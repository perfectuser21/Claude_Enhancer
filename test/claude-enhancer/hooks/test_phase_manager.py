#!/usr/bin/env python3
"""
Claude Enhancer Phase Manager 测试套件
测试5阶段执行管理器的所有功能
"""

import pytest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / ".claude/hooks"))

try:
    from phase_manager import PhaseManager, ExecutionPhase, get_phase_manager
except ImportError as e:
    pytest.skip(f"Cannot import phase_manager: {e}", allow_module_level=True)


class TestPhaseManager:
    """阶段管理器测试类"""

    def setup_method(self):
        """每个测试方法的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "phase_state.json")

        # 创建测试用的阶段管理器
        with patch.object(PhaseManager, '__init__', self._mock_init):
            self.phase_manager = PhaseManager()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _mock_init(self, instance):
        """模拟阶段管理器初始化"""
        # 调用原始的 __init__ 但使用测试状态文件
        instance.phase_config = {
            ExecutionPhase.ANALYSIS: {
                "name": "需求分析",
                "agents": ["requirements-analyst", "business-analyst", "project-manager"],
                "min_agents": 3,
                "execution_mode": "parallel",
                "prompts": {
                    "requirements-analyst": "分析用户需求",
                    "business-analyst": "分析业务流程",
                    "project-manager": "创建项目计划",
                },
                "sync_point": "requirements_review",
                "git_operations": [],
            },
            ExecutionPhase.DESIGN: {
                "name": "架构设计",
                "agents": ["api-designer", "backend-architect", "database-specialist", "frontend-specialist"],
                "min_agents": 4,
                "execution_mode": "parallel",
                "prompts": {
                    "api-designer": "设计API接口",
                    "backend-architect": "设计后端架构",
                    "database-specialist": "设计数据库",
                    "frontend-specialist": "设计前端架构",
                },
                "sync_point": "design_review",
                "git_operations": ["create_feature_branch", "init_project_structure"],
            },
            ExecutionPhase.IMPLEMENTATION: {
                "name": "实现开发",
                "agents": ["fullstack-engineer", "backend-architect", "frontend-specialist", "database-specialist", "test-engineer"],
                "min_agents": 5,
                "execution_mode": "parallel",
                "prompts": {
                    "fullstack-engineer": "实现核心功能",
                    "backend-architect": "实现后端服务",
                    "frontend-specialist": "实现前端组件",
                    "database-specialist": "创建数据库脚本",
                    "test-engineer": "编写测试",
                },
                "sync_point": "code_review",
                "git_operations": ["commit_changes", "run_pre_commit_hooks"],
            },
            ExecutionPhase.TESTING: {
                "name": "测试验证",
                "agents": ["test-engineer", "e2e-test-specialist", "performance-tester", "security-auditor"],
                "min_agents": 4,
                "execution_mode": "parallel",
                "prompts": {
                    "test-engineer": "执行测试套件",
                    "e2e-test-specialist": "执行端到端测试",
                    "performance-tester": "执行性能测试",
                    "security-auditor": "执行安全审计",
                },
                "sync_point": "quality_gate",
                "git_operations": ["run_tests", "generate_coverage_report"],
            },
            ExecutionPhase.DEPLOYMENT: {
                "name": "部署上线",
                "agents": ["devops-engineer", "monitoring-specialist", "technical-writer"],
                "min_agents": 3,
                "execution_mode": "sequential",
                "prompts": {
                    "devops-engineer": "准备部署配置",
                    "monitoring-specialist": "设置监控",
                    "technical-writer": "更新文档",
                },
                "sync_point": "deployment_verification",
                "git_operations": ["tag_release", "merge_to_main"],
            },
        }

        instance.current_phase = None
        instance.phase_history = []
        instance.context_pool = {}
        instance.state_file = self.state_file

    def test_detect_task_type_programming_keywords(self):
        """测试编程任务关键词检测"""
        programming_requests = [
            "实现用户认证系统",
            "开发API接口",
            "创建数据库设计",
            "构建前端组件",
            "implement user authentication",
            "develop REST API",
            "create database schema",
            "build React components"
        ]

        for request in programming_requests:
            assert self.phase_manager.detect_task_type(request), f"Should detect programming task: {request}"

    def test_detect_task_type_non_programming(self):
        """测试非编程任务"""
        non_programming_requests = [
            "查看文件内容",
            "分析错误日志",
            "更新文档",
            "read file content",
            "analyze error logs",
            "update documentation"
        ]

        for request in non_programming_requests:
            assert not self.phase_manager.detect_task_type(request), f"Should not detect programming task: {request}"

    def test_should_start_phases_detection(self):
        """测试5阶段执行开始条件检测"""
        # Task工具调用且是编程任务
        assert self.phase_manager.should_start_phases("Task", {"prompt": "实现用户认证系统"})

        # Task工具调用但非编程任务
        assert not self.phase_manager.should_start_phases("Task", {"prompt": "查看文件"})

        # 非Task工具调用
        assert not self.phase_manager.should_start_phases("Read", {"file_path": "/some/file"})

        # 已在阶段中
        self.phase_manager.current_phase = ExecutionPhase.ANALYSIS
        assert not self.phase_manager.should_start_phases("Task", {"prompt": "实现功能"})

    def test_get_current_phase_config(self):
        """测试获取当前阶段配置"""
        # 没有当前阶段时，应该默认为 ANALYSIS
        config = self.phase_manager.get_current_phase_config()
        assert config["name"] == "需求分析"

        # 设置当前阶段
        self.phase_manager.current_phase = ExecutionPhase.DESIGN
        config = self.phase_manager.get_current_phase_config()
        assert config["name"] == "架构设计"

    def test_get_phase_agents(self):
        """测试获取阶段所需的agents"""
        analysis_agents = self.phase_manager.get_phase_agents(ExecutionPhase.ANALYSIS)
        assert "requirements-analyst" in analysis_agents
        assert "business-analyst" in analysis_agents
        assert "project-manager" in analysis_agents

        design_agents = self.phase_manager.get_phase_agents(ExecutionPhase.DESIGN)
        assert "api-designer" in design_agents
        assert "backend-architect" in design_agents

    def test_generate_phase_instructions(self):
        """测试生成阶段执行指令"""
        context = {"previous_analysis": "用户需要认证系统"}

        instructions = self.phase_manager.generate_phase_instructions(ExecutionPhase.ANALYSIS, context)

        assert instructions["phase"] == "analysis"
        assert instructions["phase_name"] == "需求分析"
        assert len(instructions["agents_to_call"]) == 3
        assert instructions["min_agents"] == 3

        # 检查agent调用包含上下文
        for agent_call in instructions["agents_to_call"]:
            assert "基于之前的分析结果" in agent_call["prompt"]

    def test_validate_agent_execution_sufficient(self):
        """测试足够的agent执行验证"""
        self.phase_manager.current_phase = ExecutionPhase.ANALYSIS

        agents_used = ["requirements-analyst", "business-analyst", "project-manager"]
        is_valid, errors = self.phase_manager.validate_agent_execution(agents_used)

        assert is_valid
        assert len(errors) == 0

    def test_validate_agent_execution_insufficient(self):
        """测试不足的agent执行验证"""
        self.phase_manager.current_phase = ExecutionPhase.ANALYSIS

        agents_used = ["requirements-analyst", "business-analyst"]  # 缺少一个
        is_valid, errors = self.phase_manager.validate_agent_execution(agents_used)

        assert not is_valid
        assert len(errors) > 0
        assert "需要至少3个agents" in errors[0]

    def test_validate_agent_execution_missing_required(self):
        """测试缺少必需agent的验证"""
        self.phase_manager.current_phase = ExecutionPhase.ANALYSIS

        agents_used = ["requirements-analyst", "business-analyst", "wrong-agent"]
        is_valid, errors = self.phase_manager.validate_agent_execution(agents_used)

        assert not is_valid
        assert any("缺少必需的agents" in error for error in errors)

    def test_advance_to_next_phase(self):
        """测试推进到下一阶段"""
        # 初始状态
        next_phase = self.phase_manager.advance_to_next_phase()
        assert next_phase == ExecutionPhase.ANALYSIS
        assert self.phase_manager.current_phase == ExecutionPhase.ANALYSIS

        # 从 ANALYSIS 到 DESIGN
        next_phase = self.phase_manager.advance_to_next_phase()
        assert next_phase == ExecutionPhase.DESIGN
        assert self.phase_manager.current_phase == ExecutionPhase.DESIGN

        # 继续推进到最后
        self.phase_manager.advance_to_next_phase()  # IMPLEMENTATION
        self.phase_manager.advance_to_next_phase()  # TESTING
        self.phase_manager.advance_to_next_phase()  # DEPLOYMENT

        # 已经在最后阶段
        final_phase = self.phase_manager.advance_to_next_phase()
        assert final_phase is None
        assert self.phase_manager.current_phase == ExecutionPhase.DEPLOYMENT

    def test_save_and_load_phase_results(self):
        """测试保存和加载阶段结果"""
        results = {
            "requirements": ["需求1", "需求2"],
            "analysis_complete": True
        }

        self.phase_manager.save_phase_results(ExecutionPhase.ANALYSIS, results)

        # 检查上下文池
        assert ExecutionPhase.ANALYSIS.value in self.phase_manager.context_pool
        assert self.phase_manager.context_pool[ExecutionPhase.ANALYSIS.value]["results"] == results

        # 检查历史记录
        assert len(self.phase_manager.phase_history) == 1
        assert self.phase_manager.phase_history[0]["phase"] == "analysis"

    def test_get_context_for_phase(self):
        """测试获取阶段所需的上下文"""
        # 保存一些前序阶段的结果
        analysis_results = {"requirements": ["需求1", "需求2"]}
        design_results = {"architecture": "微服务架构"}

        self.phase_manager.save_phase_results(ExecutionPhase.ANALYSIS, analysis_results)
        self.phase_manager.save_phase_results(ExecutionPhase.DESIGN, design_results)

        # 获取 IMPLEMENTATION 阶段的上下文
        context = self.phase_manager.get_context_for_phase(ExecutionPhase.IMPLEMENTATION)

        assert "analysis" in context
        assert "design" in context
        assert context["analysis"]["results"] == analysis_results
        assert context["design"]["results"] == design_results

    def test_reset_phases(self):
        """测试重置阶段状态"""
        # 设置一些状态
        self.phase_manager.current_phase = ExecutionPhase.DESIGN
        self.phase_manager.save_phase_results(ExecutionPhase.ANALYSIS, {"test": "data"})

        # 重置
        self.phase_manager.reset_phases()

        assert self.phase_manager.current_phase is None
        assert len(self.phase_manager.phase_history) == 0
        assert len(self.phase_manager.context_pool) == 0

    def test_save_and_load_state(self):
        """测试状态保存和加载"""
        # 设置状态
        self.phase_manager.current_phase = ExecutionPhase.DESIGN
        self.phase_manager.save_phase_results(ExecutionPhase.ANALYSIS, {"test": "data"})

        # 保存状态
        self.phase_manager.save_state()

        # 创建新的管理器并加载状态
        with patch.object(PhaseManager, '__init__', self._mock_init):
            new_manager = PhaseManager()

        new_manager.load_state()

        assert new_manager.current_phase == ExecutionPhase.DESIGN
        assert len(new_manager.context_pool) == 1
        assert "analysis" in new_manager.context_pool

    def test_generate_phase_summary(self):
        """测试生成阶段执行摘要"""
        # 空历史
        summary = self.phase_manager.generate_phase_summary()
        assert "尚未执行任何阶段" in summary

        # 添加一些历史
        self.phase_manager.save_phase_results(ExecutionPhase.ANALYSIS, {"test": "data"})
        self.phase_manager.current_phase = ExecutionPhase.DESIGN

        summary = self.phase_manager.generate_phase_summary()
        assert "需求分析" in summary
        assert "当前阶段" in summary
        assert "架构设计" in summary

    def test_state_file_error_handling(self):
        """测试状态文件错误处理"""
        # 创建无效的状态文件
        with open(self.state_file, 'w') as f:
            f.write("invalid json content")

        # 加载时应该重置状态而不崩溃
        self.phase_manager.load_state()

        assert self.phase_manager.current_phase is None
        assert len(self.phase_manager.phase_history) == 0
        assert len(self.phase_manager.context_pool) == 0


class TestPhaseManagerIntegration:
    """阶段管理器集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_five_phase_workflow(self):
        """测试完整的5阶段工作流"""
        with patch.object(PhaseManager, 'state_file', os.path.join(self.temp_dir, "test_state.json")):
            manager = get_phase_manager()

            # 开始分析阶段
            assert manager.should_start_phases("Task", {"prompt": "实现用户认证系统"})

            phase_order = [
                ExecutionPhase.ANALYSIS,
                ExecutionPhase.DESIGN,
                ExecutionPhase.IMPLEMENTATION,
                ExecutionPhase.TESTING,
                ExecutionPhase.DEPLOYMENT
            ]

            for phase in phase_order:
                # 推进到下一阶段
                current_phase = manager.advance_to_next_phase()
                assert current_phase == phase

                # 获取阶段指令
                instructions = manager.generate_phase_instructions(phase, {})
                assert instructions["phase"] == phase.value

                # 验证足够的agents
                required_agents = manager.get_phase_agents(phase)
                is_valid, errors = manager.validate_agent_execution(required_agents[:manager.phase_config[phase]["min_agents"]])
                assert is_valid

                # 保存阶段结果
                manager.save_phase_results(phase, {"completed": True, "phase": phase.value})

            # 检查最终状态
            assert manager.current_phase == ExecutionPhase.DEPLOYMENT
            assert len(manager.phase_history) == 5

            # 尝试推进超出最后阶段
            next_phase = manager.advance_to_next_phase()
            assert next_phase is None

    def test_singleton_behavior(self):
        """测试单例行为"""
        manager1 = get_phase_manager()
        manager2 = get_phase_manager()

        assert manager1 is manager2


class TestPhaseManagerPerformance:
    """阶段管理器性能测试"""

    def test_phase_transition_performance(self):
        """测试阶段转换性能"""
        import time

        temp_dir = tempfile.mkdtemp()
        state_file = os.path.join(temp_dir, "perf_test_state.json")

        try:
            with patch.object(PhaseManager, 'state_file', state_file):
                manager = get_phase_manager()

                start_time = time.time()

                # 执行多次阶段转换
                for _ in range(100):
                    manager.advance_to_next_phase()
                    if manager.current_phase == ExecutionPhase.DEPLOYMENT:
                        manager.reset_phases()

                end_time = time.time()
                execution_time = end_time - start_time

                # 100次阶段转换应该在1秒内完成
                assert execution_time < 1.0, f"Phase transitions too slow: {execution_time}s"

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_context_handling_performance(self):
        """测试上下文处理性能"""
        import time

        temp_dir = tempfile.mkdtemp()
        state_file = os.path.join(temp_dir, "context_perf_test.json")

        try:
            with patch.object(PhaseManager, 'state_file', state_file):
                manager = get_phase_manager()

                # 创建大量上下文数据
                large_context = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}

                start_time = time.time()

                # 保存和检索大量上下文
                for phase in ExecutionPhase:
                    manager.save_phase_results(phase, large_context)

                context = manager.get_context_for_phase(ExecutionPhase.DEPLOYMENT)

                end_time = time.time()
                execution_time = end_time - start_time

                # 大上下文处理应该在0.5秒内完成
                assert execution_time < 0.5, f"Context handling too slow: {execution_time}s"
                assert len(context) > 0

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])