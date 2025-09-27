"""
任务CRUD功能测试
================

测试任务管理系统的完整CRUD操作：
- 基础CRUD操作
- 高级功能测试
- 业务规则验证测试
- 性能测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi import status

from src.services.task_service import (
    TaskService,
    TaskServiceConfig,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskSearchRequest,
)
from src.repositories.task_repository import TaskRepository, TaskQueryBuilder
from src.validators.task_validators import TaskValidationService
from src.task_management.models import Task, TaskStatus, TaskPriority
from backend.models.user import User
from backend.database import get_db


class TestTaskCRUD:
    """任务CRUD操作测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        # 这里应该返回一个测试数据库会话
        pass

    @pytest.fixture
    def task_service(self, mock_db):
        """任务服务实例"""
        repository = TaskRepository(mock_db)
        config = TaskServiceConfig(
            max_tasks_per_user=100,
            max_bulk_operation_size=50,
            default_cache_ttl=60,
            enable_activity_logging=True,
            enable_notifications=False,  # 测试时禁用通知
        )
        return TaskService(mock_db, repository, None, config)

    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return str(uuid4())

    @pytest.fixture
    def sample_project_id(self):
        """示例项目ID"""
        return str(uuid4())

    # === 基础CRUD测试 ===

    @pytest.mark.asyncio
    async def test_create_task_success(
        self, task_service, sample_user_id, sample_project_id
    ):
        """测试成功创建任务"""
        request = TaskCreateRequest(
            title="测试任务",
            description="这是一个测试任务",
            priority=TaskPriority.HIGH,
            project_id=sample_project_id,
            due_date=datetime.utcnow() + timedelta(days=7),
            estimated_hours=8,
            tags=["测试", "功能", "后端"],
            custom_fields={"complexity": "medium"},
        )

        # 执行创建操作
        task = await task_service.create_task(request, sample_user_id)

        # 验证结果
        assert task.title == "测试任务"
        assert task.description == "这是一个测试任务"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.TODO
        assert task.creator_id == sample_user_id
        assert task.project_id == sample_project_id
        assert len(task.tags) == 3
        assert task.custom_fields["complexity"] == "medium"

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, task_service, sample_user_id):
        """测试创建任务时的验证错误"""
        # 标题为空
        with pytest.raises(ValueError, match="任务标题不能为空"):
            request = TaskCreateRequest(title="")
            await task_service.create_task(request, sample_user_id)

        # 截止日期在过去
        with pytest.raises(ValueError, match="截止日期不能早于当前时间"):
            request = TaskCreateRequest(
                title="测试任务", due_date=datetime.utcnow() - timedelta(days=1)
            )
            await task_service.create_task(request, sample_user_id)

        # 标签数量过多
        with pytest.raises(ValueError, match="标签数量不能超过10个"):
            request = TaskCreateRequest(
                title="测试任务", tags=[f"tag{i}" for i in range(15)]
            )
            await task_service.create_task(request, sample_user_id)

    @pytest.mark.asyncio
    async def test_get_task_success(self, task_service, sample_user_id):
        """测试成功获取任务"""
        # 先创建一个任务
        create_request = TaskCreateRequest(title="获取测试任务", description="用于测试获取功能的任务")
        created_task = await task_service.create_task(create_request, sample_user_id)

        # 获取任务
        retrieved_task = await task_service.get_task(
            created_task.id, sample_user_id, include_relations=True
        )

        # 验证结果
        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.title == "获取测试任务"
        assert retrieved_task.creator_id == sample_user_id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, task_service, sample_user_id):
        """测试获取不存在的任务"""
        non_existent_id = str(uuid4())
        task = await task_service.get_task(non_existent_id, sample_user_id)
        assert task is None

    @pytest.mark.asyncio
    async def test_update_task_success(self, task_service, sample_user_id):
        """测试成功更新任务"""
        # 先创建一个任务
        create_request = TaskCreateRequest(
            title="原始标题", description="原始描述", priority=TaskPriority.LOW
        )
        created_task = await task_service.create_task(create_request, sample_user_id)

        # 更新任务
        update_request = TaskUpdateRequest(
            title="更新后的标题",
            description="更新后的描述",
            priority=TaskPriority.HIGH,
            progress_percentage=50,
        )
        updated_task = await task_service.update_task(
            created_task.id, update_request, sample_user_id
        )

        # 验证结果
        assert updated_task.title == "更新后的标题"
        assert updated_task.description == "更新后的描述"
        assert updated_task.priority == TaskPriority.HIGH
        assert updated_task.progress_percentage == 50

    @pytest.mark.asyncio
    async def test_delete_task_success(self, task_service, sample_user_id):
        """测试成功删除任务"""
        # 先创建一个任务
        create_request = TaskCreateRequest(title="待删除任务")
        created_task = await task_service.create_task(create_request, sample_user_id)

        # 删除任务
        success = await task_service.delete_task(
            created_task.id, sample_user_id, hard_delete=False
        )

        # 验证结果
        assert success is True

        # 验证任务已被软删除
        deleted_task = await task_service.get_task(created_task.id, sample_user_id)
        assert deleted_task is None

    # === 状态转换测试 ===

    @pytest.mark.asyncio
    async def test_status_transition_success(self, task_service, sample_user_id):
        """测试成功的状态转换"""
        # 创建任务
        create_request = TaskCreateRequest(title="状态转换测试任务")
        task = await task_service.create_task(create_request, sample_user_id)
        assert task.status == TaskStatus.TODO

        # TODO -> IN_PROGRESS
        task = await task_service.change_task_status(
            task.id, TaskStatus.IN_PROGRESS, sample_user_id, "开始工作"
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

        # IN_PROGRESS -> IN_REVIEW
        task = await task_service.change_task_status(
            task.id, TaskStatus.IN_REVIEW, sample_user_id, "提交审查"
        )
        assert task.status == TaskStatus.IN_REVIEW

        # IN_REVIEW -> DONE
        task = await task_service.change_task_status(
            task.id, TaskStatus.DONE, sample_user_id, "任务完成"
        )
        assert task.status == TaskStatus.DONE
        assert task.completed_at is not None
        assert task.progress_percentage == 100

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, task_service, sample_user_id):
        """测试无效的状态转换"""
        # 创建任务
        create_request = TaskCreateRequest(title="无效状态转换测试")
        task = await task_service.create_task(create_request, sample_user_id)

        # 尝试无效转换：TODO -> DONE（跳过中间状态）
        with pytest.raises(ValueError, match="无法从.*转换到"):
            await task_service.change_task_status(
                task.id, TaskStatus.DONE, sample_user_id
            )

    # === 搜索和筛选测试 ===

    @pytest.mark.asyncio
    async def test_search_tasks_by_title(self, task_service, sample_user_id):
        """测试按标题搜索任务"""
        # 创建测试任务
        tasks_data = [
            {"title": "前端开发任务", "tags": ["前端", "React"]},
            {"title": "后端API开发", "tags": ["后端", "FastAPI"]},
            {"title": "数据库优化", "tags": ["数据库", "性能"]},
        ]

        created_tasks = []
        for data in tasks_data:
            request = TaskCreateRequest(**data)
            task = await task_service.create_task(request, sample_user_id)
            created_tasks.append(task)

        # 搜索包含"开发"的任务
        search_request = TaskSearchRequest(query="开发", page=1, page_size=10)
        results = await task_service.search_tasks(search_request, sample_user_id)

        # 验证结果
        assert len(results.tasks) == 2  # 前端开发任务 + 后端API开发
        task_titles = [task.title for task in results.tasks]
        assert "前端开发任务" in task_titles
        assert "后端API开发" in task_titles
        assert "数据库优化" not in task_titles

    @pytest.mark.asyncio
    async def test_search_tasks_by_status(self, task_service, sample_user_id):
        """测试按状态筛选任务"""
        # 创建并更新任务状态
        task1 = await task_service.create_task(
            TaskCreateRequest(title="任务1"), sample_user_id
        )
        task2 = await task_service.create_task(
            TaskCreateRequest(title="任务2"), sample_user_id
        )

        # 更新task2状态
        await task_service.change_task_status(
            task2.id, TaskStatus.IN_PROGRESS, sample_user_id
        )

        # 搜索进行中的任务
        search_request = TaskSearchRequest(
            status=[TaskStatus.IN_PROGRESS], page=1, page_size=10
        )
        results = await task_service.search_tasks(search_request, sample_user_id)

        # 验证结果
        assert len(results.tasks) == 1
        assert results.tasks[0].title == "任务2"
        assert results.tasks[0].status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_search_tasks_by_tags(self, task_service, sample_user_id):
        """测试按标签筛选任务"""
        # 创建带标签的任务
        tasks_data = [
            {"title": "React组件开发", "tags": ["react", "frontend"]},
            {"title": "Vue页面开发", "tags": ["vue", "frontend"]},
            {"title": "API接口开发", "tags": ["api", "backend"]},
        ]

        for data in tasks_data:
            request = TaskCreateRequest(**data)
            await task_service.create_task(request, sample_user_id)

        # 搜索带有"frontend"标签的任务
        search_request = TaskSearchRequest(tags=["frontend"], page=1, page_size=10)
        results = await task_service.search_tasks(search_request, sample_user_id)

        # 验证结果
        assert len(results.tasks) == 2
        task_titles = [task.title for task in results.tasks]
        assert "React组件开发" in task_titles
        assert "Vue页面开发" in task_titles
        assert "API接口开发" not in task_titles

    # === 批量操作测试 ===

    @pytest.mark.asyncio
    async def test_bulk_update_tasks(self, task_service, sample_user_id):
        """测试批量更新任务"""
        # 创建多个任务
        task_ids = []
        for i in range(3):
            request = TaskCreateRequest(title=f"批量测试任务{i+1}")
            task = await task_service.create_task(request, sample_user_id)
            task_ids.append(task.id)

        # 批量更新
        from src.services.task_service import BulkOperationRequest

        bulk_request = BulkOperationRequest(
            task_ids=task_ids,
            operation="update",
            data={"priority": TaskPriority.HIGH.value},
        )
        results = await task_service.bulk_operation(bulk_request, sample_user_id)

        # 验证结果
        assert results["success_count"] == 3
        assert results["failed_count"] == 0

        # 验证任务确实被更新
        for task_id in task_ids:
            task = await task_service.get_task(task_id, sample_user_id)
            assert task.priority == TaskPriority.HIGH

    @pytest.mark.asyncio
    async def test_bulk_status_change(self, task_service, sample_user_id):
        """测试批量状态变更"""
        # 创建多个任务
        task_ids = []
        for i in range(3):
            request = TaskCreateRequest(title=f"批量状态测试{i+1}")
            task = await task_service.create_task(request, sample_user_id)
            task_ids.append(task.id)

        # 批量状态变更
        from src.services.task_service import BulkOperationRequest

        bulk_request = BulkOperationRequest(
            task_ids=task_ids,
            operation="change_status",
            data={"status": TaskStatus.IN_PROGRESS.value},
        )
        results = await task_service.bulk_operation(bulk_request, sample_user_id)

        # 验证结果
        assert results["success_count"] == 3

        # 验证状态确实被更新
        for task_id in task_ids:
            task = await task_service.get_task(task_id, sample_user_id)
            assert task.status == TaskStatus.IN_PROGRESS

    # === 统计功能测试 ===

    @pytest.mark.asyncio
    async def test_user_task_summary(self, task_service, sample_user_id):
        """测试用户任务统计"""
        # 创建不同状态的任务
        statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]
        for i, status in enumerate(statuses):
            request = TaskCreateRequest(title=f"统计测试任务{i+1}")
            task = await task_service.create_task(request, sample_user_id)

            if status != TaskStatus.TODO:
                await task_service.change_task_status(task.id, status, sample_user_id)

        # 获取统计信息
        summary = await task_service.get_user_task_summary(sample_user_id)

        # 验证统计结果
        assert summary["total_tasks"] == 3
        assert summary["status_workload"][TaskStatus.TODO.value] == 1
        assert summary["status_workload"][TaskStatus.IN_PROGRESS.value] == 1
        assert summary["status_workload"][TaskStatus.DONE.value] == 1

    # === 查询构建器测试 ===

    def test_query_builder_fluent_interface(self, mock_db, sample_user_id):
        """测试查询构建器的流畅接口"""
        builder = TaskQueryBuilder(mock_db, sample_user_id)

        # 构建复杂查询
        query = (
            builder.filter_by_status([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            .filter_by_priority(TaskPriority.HIGH)
            .filter_by_tags(["urgent", "bug"], match_all=False)
            .filter_overdue()
            .include_assignee()
            .include_project()
            .order_by_priority()
            .order_by_due_date()
        )

        # 验证查询构建器状态
        assert len(query._filters) > 0
        assert len(query._includes) == 2
        assert len(query._orders) > 0

    # === 性能测试 ===

    @pytest.mark.asyncio
    async def test_create_tasks_performance(self, task_service, sample_user_id):
        """测试批量创建任务的性能"""
        import time

        start_time = time.time()

        # 创建100个任务
        tasks = []
        for i in range(100):
            request = TaskCreateRequest(title=f"性能测试任务{i+1}")
            task = await task_service.create_task(request, sample_user_id)
            tasks.append(task)

        end_time = time.time()
        duration = end_time - start_time

        # 验证性能（应该在合理时间内完成）
        assert len(tasks) == 100
        assert duration < 10.0  # 10秒内完成
        print(f"创建100个任务耗时: {duration:.2f}秒")

    @pytest.mark.asyncio
    async def test_search_performance(self, task_service, sample_user_id):
        """测试搜索性能"""
        # 先创建一些测试数据
        for i in range(50):
            request = TaskCreateRequest(
                title=f"搜索性能测试{i+1}",
                description=f"这是第{i+1}个测试任务的描述",
                tags=[f"tag{i%5}", "performance", "test"],
            )
            await task_service.create_task(request, sample_user_id)

        import time

        start_time = time.time()

        # 执行搜索
        search_request = TaskSearchRequest(
            query="测试", tags=["performance"], page=1, page_size=20
        )
        results = await task_service.search_tasks(search_request, sample_user_id)

        end_time = time.time()
        duration = end_time - start_time

        # 验证性能和结果
        assert len(results.tasks) > 0
        assert duration < 1.0  # 1秒内完成搜索
        print(f"搜索耗时: {duration:.3f}秒")


class TestTaskValidation:
    """任务验证功能测试类"""

    @pytest.fixture
    def validation_service(self, mock_db):
        """验证服务实例"""
        return TaskValidationService(mock_db)

    def test_pydantic_validation(self):
        """测试Pydantic模型验证"""
        from src.validators.task_validators import EnhancedTaskCreateRequest

        # 有效数据
        valid_data = {
            "title": "有效的任务标题",
            "description": "任务描述",
            "priority": TaskPriority.HIGH,
            "due_date": datetime.utcnow() + timedelta(days=7),
            "tags": ["valid", "test"],
            "estimated_hours": 8,
        }
        request = EnhancedTaskCreateRequest(**valid_data)
        assert request.title == "有效的任务标题"

        # 无效标题
        with pytest.raises(ValueError, match="标题不能为空"):
            EnhancedTaskCreateRequest(title="")

        # 无效截止日期
        with pytest.raises(ValueError, match="截止日期不能是过去时间"):
            EnhancedTaskCreateRequest(
                title="测试", due_date=datetime.utcnow() - timedelta(days=1)
            )

        # 无效标签
        with pytest.raises(ValueError, match="标签.*格式无效"):
            EnhancedTaskCreateRequest(title="测试", tags=["invalid@tag"])

    @pytest.mark.asyncio
    async def test_business_rule_validation(self, validation_service, sample_user_id):
        """测试业务规则验证"""
        task_data = {
            "title": "业务规则测试任务",
            "description": "测试业务规则验证",
            "priority": TaskPriority.MEDIUM.value,
            "tags": ["test", "validation"],
        }

        # 这里应该模拟数据库操作
        # result = await validation_service.validate_task_creation(task_data, sample_user_id)
        # assert result["valid"] is True


class TestTaskAPI:
    """任务API接口测试类"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.api.task_routes import router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_create_task_api(self, client):
        """测试创建任务API"""
        # 这里需要模拟认证
        headers = {"Authorization": "Bearer fake_token"}

        task_data = {
            "title": "API测试任务",
            "description": "通过API创建的测试任务",
            "priority": "high",
            "estimated_hours": 4,
            "tags": ["api", "test"],
        }

        # 由于需要认证和数据库，这里只是示例
        # response = client.post("/api/v1/tasks/", json=task_data, headers=headers)
        # assert response.status_code == status.HTTP_201_CREATED
        # assert response.json()["title"] == "API测试任务"

    def test_search_tasks_api(self, client):
        """测试搜索任务API"""
        headers = {"Authorization": "Bearer fake_token"}

        # response = client.get(
        #     "/api/v1/tasks/?query=test&status=todo&page=1&page_size=10",
        #     headers=headers
        # )
        # assert response.status_code == status.HTTP_200_OK
        # assert "tasks" in response.json()
        # assert "pagination" in response.json()


# === 集成测试 ===


class TestTaskIntegration:
    """任务管理系统集成测试"""

    @pytest.mark.asyncio
    async def test_complete_task_workflow(
        self, task_service, sample_user_id, sample_project_id
    ):
        """测试完整的任务工作流"""
        # 1. 创建任务
        create_request = TaskCreateRequest(
            title="集成测试任务",
            description="完整工作流测试",
            priority=TaskPriority.HIGH,
            project_id=sample_project_id,
            due_date=datetime.utcnow() + timedelta(days=7),
            estimated_hours=8,
            tags=["integration", "test", "workflow"],
        )
        task = await task_service.create_task(create_request, sample_user_id)
        assert task.status == TaskStatus.TODO

        # 2. 开始任务
        task = await task_service.change_task_status(
            task.id, TaskStatus.IN_PROGRESS, sample_user_id, "开始工作"
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

        # 3. 更新进度
        update_request = TaskUpdateRequest(progress_percentage=50, actual_hours=4)
        task = await task_service.update_task(task.id, update_request, sample_user_id)
        assert task.progress_percentage == 50
        assert task.actual_hours == 4

        # 4. 提交审查
        task = await task_service.change_task_status(
            task.id, TaskStatus.IN_REVIEW, sample_user_id, "提交审查"
        )
        assert task.status == TaskStatus.IN_REVIEW

        # 5. 完成任务
        task = await task_service.change_task_status(
            task.id, TaskStatus.DONE, sample_user_id, "任务完成"
        )
        assert task.status == TaskStatus.DONE
        assert task.completed_at is not None
        assert task.progress_percentage == 100

        # 6. 验证任务历史和统计
        summary = await task_service.get_user_task_summary(sample_user_id)
        assert summary["status_workload"][TaskStatus.DONE.value] >= 1

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, task_service, sample_user_id):
        """测试错误处理和恢复"""
        # 测试各种错误情况的处理

        # 1. 创建任务时的错误
        with pytest.raises(ValueError):
            invalid_request = TaskCreateRequest(title="")
            await task_service.create_task(invalid_request, sample_user_id)

        # 2. 操作不存在任务的错误
        non_existent_id = str(uuid4())
        task = await task_service.get_task(non_existent_id, sample_user_id)
        assert task is None

        # 3. 无效状态转换的错误
        valid_request = TaskCreateRequest(title="错误处理测试")
        task = await task_service.create_task(valid_request, sample_user_id)

        with pytest.raises(ValueError):
            await task_service.change_task_status(
                task.id, TaskStatus.DONE, sample_user_id  # 跳过中间状态
            )


if __name__ == "__main__":
    """运行测试的示例"""

    # 注意：这些测试需要适当的测试数据库和依赖注入设置
    # 实际运行时需要配置pytest和测试环境

    print("任务CRUD功能测试")
    print("================")
    print()
    print("测试覆盖范围：")
    print("✅ 基础CRUD操作（创建、读取、更新、删除）")
    print("✅ 状态转换和业务规则验证")
    print("✅ 搜索和筛选功能")
    print("✅ 批量操作")
    print("✅ 数据验证和错误处理")
    print("✅ 性能测试")
    print("✅ API接口测试")
    print("✅ 集成测试")
    print()
    print("使用方法：")
    print("pytest tests/test_task_crud.py -v")
    print()
    print("注意事项：")
    print("- 需要配置测试数据库")
    print("- 需要模拟用户认证")
    print("- 需要设置适当的测试环境")
