#!/usr/bin/env python3
"""
Perfect21工作流编排器单元测试
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import yaml

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from features.workflow_orchestrator.orchestrator import (
    WorkflowOrchestrator,
    ExecutionMode
)

class TestWorkflowOrchestrator(unittest.TestCase):
    """工作流编排器测试类"""

    def setUp(self):
        """测试前准备"""
        self.orchestrator = WorkflowOrchestrator()

        # 创建临时工作流文件
        self.temp_dir = tempfile.mkdtemp()
        self.workflows_path = os.path.join(self.temp_dir, "workflows", "templates")
        os.makedirs(self.workflows_path, exist_ok=True)

        # 创建测试工作流模板
        self.test_workflow = {
            "name": "test_workflow",
            "version": "1.0",
            "philosophy": "test philosophy",
            "stages": [
                {
                    "name": "stage1",
                    "description": "Stage 1",
                    "execution_mode": "parallel",
                    "thinking_mode": "normal",
                    "agents": ["agent1", "agent2"],
                    "claude_instruction": "Test instruction for {task_description}"
                },
                {
                    "name": "stage2",
                    "description": "Stage 2",
                    "execution_mode": "sequential",
                    "thinking_mode": "think",
                    "agents": ["agent3"],
                    "depends_on": ["stage1"],
                    "optional": True
                }
            ]
        }

        # 保存测试工作流
        test_workflow_file = os.path.join(self.workflows_path, "test_workflow.yaml")
        with open(test_workflow_file, 'w') as f:
            yaml.dump(self.test_workflow, f)

        # Mock工作流路径
        self.orchestrator.workflows_path = os.path.join(self.temp_dir, "workflows")

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.orchestrator)
        self.assertIsNotNone(self.orchestrator.agent_capabilities)
        self.assertIsNone(self.orchestrator.current_execution)
        self.assertEqual(len(self.orchestrator.execution_history), 0)

    def test_load_workflow_template(self):
        """测试加载工作流模板"""
        workflow = self.orchestrator._load_workflow_template("test_workflow")
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow["name"], "test_workflow")
        self.assertEqual(len(workflow["stages"]), 2)

    def test_load_nonexistent_workflow(self):
        """测试加载不存在的工作流"""
        workflow = self.orchestrator._load_workflow_template("nonexistent")
        self.assertIsNone(workflow)

    def test_analyze_task_complexity(self):
        """测试任务复杂度分析"""
        # 测试简单任务
        simple_task = "修复登录按钮的小bug"
        complexity = self.orchestrator._analyze_task_complexity(simple_task)
        self.assertEqual(complexity, "simple")

        # 测试复杂任务
        complex_task = "实现分布式微服务架构的高可用系统"
        complexity = self.orchestrator._analyze_task_complexity(complex_task)
        self.assertEqual(complexity, "complex")

        # 测试中等任务
        medium_task = "添加用户管理功能"
        complexity = self.orchestrator._analyze_task_complexity(medium_task)
        self.assertEqual(complexity, "medium")

    def test_analyze_project_type(self):
        """测试项目类型分析"""
        # 测试API服务
        api_task = "开发RESTful API接口"
        project_type = self.orchestrator._analyze_project_type(api_task)
        self.assertEqual(project_type, "api_service")

        # 测试Web应用
        web_task = "创建前端界面和网站"
        project_type = self.orchestrator._analyze_project_type(web_task)
        self.assertEqual(project_type, "web_app")

        # 测试通用项目
        general_task = "优化系统性能"
        project_type = self.orchestrator._analyze_project_type(general_task)
        self.assertEqual(project_type, "general")

    def test_simplify_workflow(self):
        """测试简化工作流"""
        simplified = self.orchestrator._simplify_workflow(self.test_workflow)

        # 应该移除可选阶段
        self.assertEqual(len(simplified["stages"]), 1)
        self.assertEqual(simplified["stages"][0]["name"], "stage1")

    def test_enhance_workflow(self):
        """测试增强工作流"""
        enhanced = self.orchestrator._enhance_workflow(self.test_workflow)

        # 所有阶段都不应该是可选的
        for stage in enhanced["stages"]:
            self.assertFalse(stage.get("optional", False))

        # 思考模式应该被增强
        self.assertEqual(enhanced["stages"][0]["thinking_mode"], "think")

    def test_get_agent_task(self):
        """测试获取agent任务描述"""
        task_desc = "实现用户认证"

        # 测试已知agent
        pm_task = self.orchestrator._get_agent_task("project-manager", task_desc)
        self.assertIn("产品和项目管理角度", pm_task)
        self.assertIn(task_desc, pm_task)

        # 测试未知agent
        unknown_task = self.orchestrator._get_agent_task("unknown-agent", task_desc)
        self.assertIn("执行任务", unknown_task)
        self.assertIn(task_desc, unknown_task)

    def test_generate_workflow_instructions(self):
        """测试生成工作流指令"""
        task_description = "实现用户登录功能"

        with patch.object(self.orchestrator, '_load_workflow_template', return_value=self.test_workflow):
            instructions = self.orchestrator.generate_workflow_instructions(
                task_description,
                "test_workflow"
            )

            self.assertIsNotNone(instructions)
            self.assertEqual(instructions["workflow_name"], "test_workflow")
            self.assertEqual(instructions["task_description"], task_description)
            self.assertTrue(instructions["execution_ready"])
            self.assertIn("instructions", instructions)
            self.assertIn("monitoring", instructions)
            self.assertIn("quality_gates", instructions)

    def test_generate_stage_instruction(self):
        """测试生成阶段指令"""
        stage = self.test_workflow["stages"][0]
        instruction = self.orchestrator._generate_stage_instruction(
            stage, 1, 2, "test task"
        )

        self.assertIn("阶段 1/2", instruction)
        self.assertIn(stage["name"], instruction)
        self.assertIn(stage["description"], instruction)
        self.assertIn("并行执行指令", instruction)  # 因为execution_mode是parallel

    def test_parallel_execution_instruction(self):
        """测试并行执行指令生成"""
        stage = {
            "name": "parallel_stage",
            "description": "Parallel execution",
            "execution_mode": "parallel",
            "agents": ["agent1", "agent2", "agent3"]
        }

        instruction = self.orchestrator._generate_stage_instruction(
            stage, 1, 1, "parallel task"
        )

        self.assertIn("并行执行指令", instruction)
        self.assertIn("请在一个消息中同时调用", instruction)
        self.assertIn("3个SubAgents", instruction)

    def test_sequential_execution_instruction(self):
        """测试顺序执行指令生成"""
        stage = {
            "name": "sequential_stage",
            "description": "Sequential execution",
            "execution_mode": "sequential",
            "agents": ["agent1", "agent2"]
        }

        instruction = self.orchestrator._generate_stage_instruction(
            stage, 1, 1, "sequential task"
        )

        self.assertIn("顺序执行指令", instruction)
        self.assertIn("1. 调用", instruction)

    def test_current_execution_tracking(self):
        """测试执行跟踪"""
        task_description = "test task"

        with patch.object(self.orchestrator, '_load_workflow_template', return_value=self.test_workflow):
            self.orchestrator.generate_workflow_instructions(task_description, "test_workflow")

            self.assertIsNotNone(self.orchestrator.current_execution)
            self.assertEqual(self.orchestrator.current_execution.workflow_name, "test_workflow")
            self.assertEqual(self.orchestrator.current_execution.task_description, task_description)
            self.assertEqual(self.orchestrator.current_execution.status, "running")

    def test_execution_modes_enum(self):
        """测试执行模式枚举"""
        self.assertEqual(ExecutionMode.PARALLEL.value, "parallel")
        self.assertEqual(ExecutionMode.SEQUENTIAL.value, "sequential")
        self.assertEqual(ExecutionMode.DOMAIN_PARALLEL.value, "domain_parallel")
        self.assertEqual(ExecutionMode.LAYERED_SEQUENTIAL.value, "layered_sequential")

    def test_thinking_modes_enum(self):
        """测试思考模式枚举"""
        self.assertEqual(ThinkingMode.NORMAL.value, "normal")
        self.assertEqual(ThinkingMode.THINK.value, "think")
        self.assertEqual(ThinkingMode.THINK_HARD.value, "think_hard")
        self.assertEqual(ThinkingMode.ULTRATHINK.value, "ultrathink")


class TestStageConfig(unittest.TestCase):
    """测试阶段配置数据类"""

    def test_stage_config_creation(self):
        """测试创建阶段配置"""
        stage = StageConfig(
            name="test_stage",
            description="Test stage",
            execution_mode=ExecutionMode.PARALLEL,
            thinking_mode=ThinkingMode.NORMAL,
            depends_on=["stage1"],
            agents_required=["agent1", "agent2"],
            estimated_time=30,
            quality_gate_required=True
        )

        self.assertEqual(stage.name, "test_stage")
        self.assertEqual(stage.execution_mode, ExecutionMode.PARALLEL)
        self.assertEqual(stage.thinking_mode, ThinkingMode.NORMAL)
        self.assertEqual(len(stage.agents_required), 2)
        self.assertTrue(stage.quality_gate_required)


class TestWorkflowExecution(unittest.TestCase):
    """测试工作流执行记录数据类"""

    def test_workflow_execution_creation(self):
        """测试创建工作流执行记录"""
        from datetime import datetime

        execution = WorkflowExecution(
            workflow_name="test_workflow",
            task_description="test task",
            start_time=datetime.now(),
            current_stage="stage1",
            total_stages=3,
            execution_id="exec_123"
        )

        self.assertEqual(execution.workflow_name, "test_workflow")
        self.assertEqual(execution.task_description, "test task")
        self.assertEqual(execution.current_stage, "stage1")
        self.assertEqual(execution.total_stages, 3)
        self.assertEqual(execution.status, "running")
        self.assertIsNone(execution.completed_stages)


if __name__ == "__main__":
    unittest.main()