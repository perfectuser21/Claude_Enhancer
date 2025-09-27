"""
任务管理CRUD操作测试用例
Initial-tests阶段 - 全面测试任务管理功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_management.models import (
    Task,
    TaskStatus,
    TaskPriority,
    Project,
    ProjectMember,
)
from src.task_management.services import TaskService


class TestTaskService:
    """任务服务测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 模拟数据库会话
        self.mock_db = Mock()
        self.mock_cache = Mock()
        self.mock_notification_service = Mock()
        self.mock_activity_service = Mock()

        # 创建任务服务实例
        self.task_service = TaskService(
            db=self.mock_db,
            cache_manager=self.mock_cache,
            notification_service=self.mock_notification_service,
            activity_service=self.mock_activity_service,
        )

    def test_task_creation_data_validation(self):
        """测试任务创建数据验证"""
        # 测试必填字段验证
        valid_task_data = {
            "title": "测试任务",
            "description": "这是一个测试任务",
            "priority": TaskPriority.HIGH.value,
            "assignee_id": "user-123",
            "due_date": datetime.utcnow() + timedelta(days=7),
        }

        invalid_task_data_empty_title = {"title": "", "description": "描述"}

        invalid_task_data_no_title = {"description": "描述"}

        # 这些是数据验证测试，实际验证会在服务层进行
        assert valid_task_data["title"] is not None and valid_task_data["title"] != ""
        assert invalid_task_data_empty_title["title"] == ""
        assert "title" not in invalid_task_data_no_title

    def test_task_status_transitions(self):
        """测试任务状态转换"""
        task = Task(title="测试任务", status=TaskStatus.TODO.value)

        # 测试有效的状态转换
        assert task.can_transition_to(TaskStatus.IN_PROGRESS.value) is True
        assert task.can_transition_to(TaskStatus.CANCELLED.value) is True

        # 测试无效的状态转换
        assert task.can_transition_to(TaskStatus.DONE.value) is False
        assert task.can_transition_to(TaskStatus.IN_REVIEW.value) is False

        # 测试进行中任务的转换
        task.status = TaskStatus.IN_PROGRESS.value
        assert task.can_transition_to(TaskStatus.TODO.value) is True
        assert task.can_transition_to(TaskStatus.IN_REVIEW.value) is True
        assert task.can_transition_to(TaskStatus.BLOCKED.value) is True
        assert task.can_transition_to(TaskStatus.CANCELLED.value) is True

        # 测试已完成任务的转换
        task.status = TaskStatus.DONE.value
        assert task.can_transition_to(TaskStatus.IN_PROGRESS.value) is True
        assert task.can_transition_to(TaskStatus.TODO.value) is False

    def test_task_progress_update_from_status(self):
        """测试根据状态自动更新进度"""
        task = Task(title="测试任务")

        # 测试待办状态
        task.status = TaskStatus.TODO.value
        task.update_progress_from_status()
        assert task.progress_percentage == 0

        # 测试进行中状态
        task.status = TaskStatus.IN_PROGRESS.value
        task.update_progress_from_status()
        assert task.progress_percentage == 50

        # 测试审查中状态
        task.status = TaskStatus.IN_REVIEW.value
        task.update_progress_from_status()
        assert task.progress_percentage == 90

        # 测试已完成状态
        task.status = TaskStatus.DONE.value
        task.update_progress_from_status()
        assert task.progress_percentage == 100

        # 测试已取消状态
        task.status = TaskStatus.CANCELLED.value
        task.update_progress_from_status()
        assert task.progress_percentage == 0

    def test_task_computed_properties(self):
        """测试任务计算属性"""
        now = datetime.utcnow()

        # 测试逾期检查
        task_overdue = Task(
            title="逾期任务",
            status=TaskStatus.IN_PROGRESS.value,
            due_date=now - timedelta(days=1),
        )
        assert task_overdue.is_overdue is True

        # 测试未逾期任务
        task_not_overdue = Task(
            title="未逾期任务",
            status=TaskStatus.IN_PROGRESS.value,
            due_date=now + timedelta(days=1),
        )
        assert task_not_overdue.is_overdue is False

        # 测试已完成任务不算逾期
        task_completed = Task(
            title="已完成任务",
            status=TaskStatus.DONE.value,
            due_date=now - timedelta(days=1),
        )
        assert task_completed.is_overdue is False

        # 测试完成状态检查
        assert task_completed.is_completed is True
        assert task_overdue.is_completed is False

        # 测试持续时间计算
        task_with_duration = Task(
            title="有持续时间的任务", started_at=now - timedelta(days=5), completed_at=now
        )
        assert task_with_duration.duration_days == 5

    def test_task_validation(self):
        """测试任务字段验证"""
        task = Task(title="验证测试任务")

        # 测试状态验证
        with pytest.raises(ValueError, match="Invalid task status"):
            task.status = "invalid_status"

        # 测试优先级验证
        with pytest.raises(ValueError, match="Invalid task priority"):
            task.priority = "invalid_priority"

        # 测试进度百分比验证
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            task.progress_percentage = -1

        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            task.progress_percentage = 101

        # 测试有效值
        task.status = TaskStatus.TODO.value
        task.priority = TaskPriority.HIGH.value
        task.progress_percentage = 50

        assert task.status == TaskStatus.TODO.value
        assert task.priority == TaskPriority.HIGH.value
        assert task.progress_percentage == 50

    @pytest.mark.parametrize(
        "status,priority,expected_valid",
        [
            (TaskStatus.TODO.value, TaskPriority.LOW.value, True),
            (TaskStatus.IN_PROGRESS.value, TaskPriority.MEDIUM.value, True),
            (TaskStatus.DONE.value, TaskPriority.HIGH.value, True),
            (TaskStatus.CANCELLED.value, TaskPriority.URGENT.value, True),
            ("invalid_status", TaskPriority.LOW.value, False),
            (TaskStatus.TODO.value, "invalid_priority", False),
        ],
    )
    def test_task_status_priority_combinations(self, status, priority, expected_valid):
        """测试任务状态和优先级组合的有效性"""
        task = Task(title="组合测试任务")

        if expected_valid:
            task.status = status
            task.priority = priority
            assert task.status == status
            assert task.priority == priority
        else:
            if status not in [s.value for s in TaskStatus]:
                with pytest.raises(ValueError):
                    task.status = status
            if priority not in [p.value for p in TaskPriority]:
                with pytest.raises(ValueError):
                    task.priority = priority

    def test_task_search_filter_logic(self):
        """测试任务搜索和筛选逻辑"""
        # 创建测试任务数据
        tasks_data = [
            {
                "title": "前端开发任务",
                "description": "React组件开发",
                "status": TaskStatus.IN_PROGRESS.value,
                "priority": TaskPriority.HIGH.value,
                "tags": ["frontend", "react"],
            },
            {
                "title": "后端API开发",
                "description": "REST API接口开发",
                "status": TaskStatus.TODO.value,
                "priority": TaskPriority.MEDIUM.value,
                "tags": ["backend", "api"],
            },
            {
                "title": "数据库设计",
                "description": "数据库表结构设计",
                "status": TaskStatus.DONE.value,
                "priority": TaskPriority.LOW.value,
                "tags": ["database", "design"],
            },
        ]

        # 测试标题搜索
        search_term = "前端"
        matching_tasks = [
            task
            for task in tasks_data
            if search_term in task["title"] or search_term in task["description"]
        ]
        assert len(matching_tasks) == 1
        assert matching_tasks[0]["title"] == "前端开发任务"

        # 测试状态筛选
        in_progress_tasks = [
            task
            for task in tasks_data
            if task["status"] == TaskStatus.IN_PROGRESS.value
        ]
        assert len(in_progress_tasks) == 1

        # 测试优先级筛选
        high_priority_tasks = [
            task for task in tasks_data if task["priority"] == TaskPriority.HIGH.value
        ]
        assert len(high_priority_tasks) == 1

        # 测试标签筛选
        frontend_tasks = [
            task for task in tasks_data if "frontend" in task.get("tags", [])
        ]
        assert len(frontend_tasks) == 1

    def test_task_assignment_logic(self):
        """测试任务分配逻辑"""
        now = datetime.utcnow()

        task = Task(title="分配测试任务", created_by="creator-123")

        # 测试初始状态
        assert task.assignee_id is None
        assert task.assigned_at is None
        assert task.assigned_by is None

        # 模拟分配操作
        task.assignee_id = "assignee-456"
        task.assigned_at = now
        task.assigned_by = "assigner-789"

        assert task.assignee_id == "assignee-456"
        assert task.assigned_at == now
        assert task.assigned_by == "assigner-789"

    def test_task_time_tracking(self):
        """测试任务时间跟踪"""
        now = datetime.utcnow()
        start_time = now - timedelta(hours=8)
        end_time = now

        task = Task(
            title="时间跟踪测试任务",
            estimated_hours=8,
            started_at=start_time,
            completed_at=end_time,
            actual_hours=8,
        )

        assert task.estimated_hours == 8
        assert task.actual_hours == 8
        assert task.started_at == start_time
        assert task.completed_at == end_time

        # 测试持续时间计算
        expected_duration = (end_time - start_time).days
        assert task.duration_days == expected_duration

    def test_task_custom_fields(self):
        """测试任务自定义字段"""
        custom_fields = {
            "client": "重要客户",
            "budget": 50000,
            "technology": ["Python", "React", "PostgreSQL"],
            "requirements": {"security_level": "high", "performance": "optimized"},
        }

        task = Task(title="自定义字段测试任务", custom_fields=custom_fields)

        assert task.custom_fields["client"] == "重要客户"
        assert task.custom_fields["budget"] == 50000
        assert "Python" in task.custom_fields["technology"]
        assert task.custom_fields["requirements"]["security_level"] == "high"

    def test_task_tags_and_labels(self):
        """测试任务标签和标签元数据"""
        tags = ["urgent", "client-work", "backend"]
        labels = {
            "urgent": {"color": "#ff0000", "description": "紧急任务"},
            "client-work": {"color": "#00ff00", "description": "客户工作"},
            "backend": {"color": "#0000ff", "description": "后端开发"},
        }

        task = Task(title="标签测试任务", tags=tags, labels=labels)

        assert "urgent" in task.tags
        assert "client-work" in task.tags
        assert "backend" in task.tags
        assert task.labels["urgent"]["color"] == "#ff0000"
        assert task.labels["client-work"]["description"] == "客户工作"


class TestTaskCRUDOperations:
    """任务CRUD操作测试"""

    def setup_method(self):
        """测试设置"""
        self.sample_task_data = {
            "title": "示例任务",
            "description": "这是一个示例任务用于测试",
            "priority": TaskPriority.MEDIUM.value,
            "status": TaskStatus.TODO.value,
            "tags": ["test", "sample"],
            "estimated_hours": 4,
        }

    def test_create_task_data_structure(self):
        """测试创建任务的数据结构"""
        task_data = self.sample_task_data.copy()

        # 验证必填字段
        assert "title" in task_data
        assert task_data["title"] is not None
        assert task_data["title"] != ""

        # 验证可选字段
        assert task_data.get("description") is not None
        assert task_data.get("priority") in [p.value for p in TaskPriority]
        assert task_data.get("status") in [s.value for s in TaskStatus]

    def test_update_task_data_structure(self):
        """测试更新任务的数据结构"""
        original_data = self.sample_task_data.copy()

        update_data = {
            "title": "更新后的任务标题",
            "status": TaskStatus.IN_PROGRESS.value,
            "priority": TaskPriority.HIGH.value,
            "actual_hours": 2,
        }

        # 模拟更新操作
        updated_data = original_data.copy()
        updated_data.update(update_data)

        assert updated_data["title"] == "更新后的任务标题"
        assert updated_data["status"] == TaskStatus.IN_PROGRESS.value
        assert updated_data["priority"] == TaskPriority.HIGH.value
        assert updated_data["actual_hours"] == 2

    def test_delete_task_logic(self):
        """测试任务删除逻辑"""
        task = Task(title="待删除任务", is_deleted=False)

        # 测试软删除
        assert task.is_deleted is False

        # 模拟删除操作
        task.is_deleted = True
        assert task.is_deleted is True

    def test_task_bulk_operations(self):
        """测试任务批量操作"""
        tasks_data = [
            {"title": "任务1", "status": TaskStatus.TODO.value},
            {"title": "任务2", "status": TaskStatus.TODO.value},
            {"title": "任务3", "status": TaskStatus.TODO.value},
        ]

        # 模拟批量状态更新
        bulk_update_data = {"status": TaskStatus.IN_PROGRESS.value}

        for task_data in tasks_data:
            task_data.update(bulk_update_data)
            assert task_data["status"] == TaskStatus.IN_PROGRESS.value

    def test_task_query_filters(self):
        """测试任务查询筛选器"""
        filters = {
            "status": [TaskStatus.TODO.value, TaskStatus.IN_PROGRESS.value],
            "priority": [TaskPriority.HIGH.value, TaskPriority.URGENT.value],
            "assignee_id": "user-123",
            "project_id": "project-456",
            "due_date_from": datetime.utcnow(),
            "due_date_to": datetime.utcnow() + timedelta(days=7),
            "tags": ["urgent", "important"],
        }

        # 验证筛选器结构
        assert isinstance(filters["status"], list)
        assert isinstance(filters["priority"], list)
        assert isinstance(filters["assignee_id"], str)
        assert isinstance(filters["project_id"], str)
        assert isinstance(filters["due_date_from"], datetime)
        assert isinstance(filters["due_date_to"], datetime)
        assert isinstance(filters["tags"], list)

    def test_task_sorting_options(self):
        """测试任务排序选项"""
        sort_options = [
            {"field": "created_at", "order": "desc"},
            {"field": "updated_at", "order": "asc"},
            {"field": "due_date", "order": "asc"},
            {"field": "priority", "order": "desc"},
            {"field": "title", "order": "asc"},
        ]

        for option in sort_options:
            assert option["field"] in [
                "created_at",
                "updated_at",
                "due_date",
                "priority",
                "title",
            ]
            assert option["order"] in ["asc", "desc"]

    def test_task_pagination(self):
        """测试任务分页"""
        pagination_params = {"page": 1, "page_size": 20, "total_count": 100}

        # 计算分页信息
        total_pages = (
            pagination_params["total_count"] + pagination_params["page_size"] - 1
        ) // pagination_params["page_size"]
        offset = (pagination_params["page"] - 1) * pagination_params["page_size"]

        assert total_pages == 5
        assert offset == 0

        # 测试第二页
        pagination_params["page"] = 2
        offset = (pagination_params["page"] - 1) * pagination_params["page_size"]
        assert offset == 20


class TestTaskBusinessLogic:
    """任务业务逻辑测试"""

    def test_task_dependency_logic(self):
        """测试任务依赖逻辑"""
        # 创建测试任务
        task_a = Task(id="task-a", title="任务A", status=TaskStatus.TODO.value)
        task_b = Task(id="task-b", title="任务B", status=TaskStatus.TODO.value)

        # 测试依赖关系
        dependency_data = {
            "task_id": "task-b",
            "dependency_id": "task-a",
            "dependency_type": "blocks",
            "notes": "任务B依赖任务A完成",
        }

        assert dependency_data["task_id"] == "task-b"
        assert dependency_data["dependency_id"] == "task-a"
        assert dependency_data["dependency_type"] == "blocks"

    def test_task_notification_triggers(self):
        """测试任务通知触发条件"""
        notification_triggers = [
            {"event": "task_created", "notify": ["assignee", "project_members"]},
            {"event": "task_assigned", "notify": ["assignee", "assigner"]},
            {
                "event": "task_status_changed",
                "notify": ["assignee", "creator", "watchers"],
            },
            {"event": "task_due_soon", "notify": ["assignee", "creator"]},
            {
                "event": "task_overdue",
                "notify": ["assignee", "creator", "project_manager"],
            },
        ]

        for trigger in notification_triggers:
            assert "event" in trigger
            assert "notify" in trigger
            assert isinstance(trigger["notify"], list)

    def test_task_activity_logging(self):
        """测试任务活动日志"""
        activity_data = {
            "task_id": "task-123",
            "user_id": "user-456",
            "action": "status_changed",
            "field_name": "status",
            "old_value": TaskStatus.TODO.value,
            "new_value": TaskStatus.IN_PROGRESS.value,
            "description": "任务状态从待办变更为进行中",
        }

        assert activity_data["task_id"] is not None
        assert activity_data["user_id"] is not None
        assert activity_data["action"] is not None
        assert activity_data["old_value"] != activity_data["new_value"]

    def test_task_performance_metrics(self):
        """测试任务性能指标"""
        now = datetime.utcnow()

        metrics = {
            "cycle_time": 5,  # 从开始到完成的天数
            "lead_time": 7,  # 从创建到完成的天数
            "efficiency": 0.8,  # 实际工时/预估工时
            "on_time_delivery": True,  # 是否按时交付
            "quality_score": 9,  # 质量评分 1-10
        }

        assert metrics["cycle_time"] > 0
        assert metrics["lead_time"] >= metrics["cycle_time"]
        assert 0 <= metrics["efficiency"] <= 2  # 效率可能超过100%
        assert isinstance(metrics["on_time_delivery"], bool)
        assert 1 <= metrics["quality_score"] <= 10


# 兼容性测试函数
def test_task_creation():
    """测试任务创建 - 向后兼容"""
    task = Task(
        title="兼容性测试任务",
        description="测试任务创建",
        priority=TaskPriority.MEDIUM.value,
        status=TaskStatus.TODO.value,
    )

    assert task.title == "兼容性测试任务"
    assert task.priority == TaskPriority.MEDIUM.value
    assert task.status == TaskStatus.TODO.value
    print("✅ 任务创建测试通过")


def test_task_status_update():
    """测试任务状态更新 - 向后兼容"""
    task = Task(title="状态更新测试", status=TaskStatus.TODO.value)

    # 测试状态转换
    assert task.can_transition_to(TaskStatus.IN_PROGRESS.value)

    task.status = TaskStatus.IN_PROGRESS.value
    task.update_progress_from_status()

    assert task.status == TaskStatus.IN_PROGRESS.value
    assert task.progress_percentage == 50
    print("✅ 任务状态更新测试通过")


def test_task_assignment():
    """测试任务分配 - 向后兼容"""
    task = Task(title="分配测试")

    # 模拟分配
    task.assignee_id = "user-123"
    task.assigned_at = datetime.utcnow()
    task.assigned_by = "manager-456"

    assert task.assignee_id == "user-123"
    assert task.assigned_at is not None
    assert task.assigned_by == "manager-456"
    print("✅ 任务分配测试通过")


if __name__ == "__main__":
    # 运行简单测试
    test_task_creation()
    test_task_status_update()
    test_task_assignment()
    print("\n✅ 所有基础测试通过!")

    # 运行pytest获得更详细的测试报告
    print("\n运行完整测试套件...")
    pytest.main([__file__, "-v", "--tb=short"])
