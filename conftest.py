"""
Pytest配置文件
Claude Enhancer 5.0 - 测试配置和fixture定义
Initial-tests阶段 - 测试框架配置
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Generator
from unittest.mock import Mock, AsyncMock

# 导入项目模块（如果可用）
try:
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

    from src.auth.auth import AuthService
    from src.task_management.models import TaskStatus, TaskPriority
    from src.task_management.services import TaskService
except ImportError:
    # 如果导入失败，创建模拟类
    class AuthService:
        pass

    class TaskStatus:
        TODO = "todo"
        IN_PROGRESS = "in_progress"
        DONE = "done"

    class TaskPriority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"


# ==================== 会话级别的 Fixtures ====================


@pytest.fixture(scope="session")
def event_loop():
    """创建会话级别的事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir():
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "database_url": "sqlite:///:memory:",
        "secret_key": "test-secret-key",
        "debug": True,
        "testing": True,
        "jwt_secret": "test-jwt-secret",
        "jwt_expire_minutes": 30,
        "upload_path": "/tmp/test-uploads",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_file_types": ["jpg", "png", "pdf", "txt", "doc", "docx"],
        "rate_limit": {"requests_per_minute": 100, "burst_limit": 20},
    }


# ==================== 模块级别的 Fixtures ====================


@pytest.fixture(scope="module")
def auth_service():
    """认证服务实例"""
    return AuthService()


@pytest.fixture(scope="module")
def mock_database():
    """模拟数据库连接"""

    class MockDatabase:
        def __init__(self):
            self.connected = True
            self.transactions = []

        def connect(self):
            self.connected = True
            return self

        def disconnect(self):
            self.connected = False

        def execute(self, query, params=None):
            self.transactions.append({"query": query, "params": params})
            return Mock(rowcount=1, fetchall=lambda: [], fetchone=lambda: None)

        def commit(self):
            pass

        def rollback(self):
            pass

    return MockDatabase()


# ==================== 函数级别的 Fixtures ====================


@pytest.fixture
def mock_cache():
    """模拟缓存服务"""

    class MockCache:
        def __init__(self):
            self.data = {}

        async def get(self, key):
            return self.data.get(key)

        async def set(self, key, value, ttl=None):
            self.data[key] = value

        async def delete(self, key):
            self.data.pop(key, None)

        async def clear(self):
            self.data.clear()

    return MockCache()


@pytest.fixture
def mock_notification_service():
    """模拟通知服务"""

    class MockNotificationService:
        def __init__(self):
            self.sent_notifications = []

        async def send_notification(self, user_id, message, type="info"):
            notification = {
                "user_id": user_id,
                "message": message,
                "type": type,
                "timestamp": datetime.utcnow(),
            }
            self.sent_notifications.append(notification)
            return notification

        async def send_task_assigned_notification(
            self, task_id, assignee_id, assigner_id
        ):
            return await self.send_notification(
                assignee_id, f"New task assigned: {task_id}", "task_assigned"
            )

        async def send_task_status_changed_notification(
            self, task_id, old_status, new_status, changed_by
        ):
            return await self.send_notification(
                changed_by,
                f"Task {task_id} status changed from {old_status} to {new_status}",
                "task_status_changed",
            )

    return MockNotificationService()


@pytest.fixture
def mock_activity_service():
    """模拟活动记录服务"""

    class MockActivityService:
        def __init__(self):
            self.activities = []

        async def log_task_activity(self, task_id, user_id, action, **kwargs):
            activity = {
                "task_id": task_id,
                "user_id": user_id,
                "action": action,
                "timestamp": datetime.utcnow(),
                **kwargs,
            }
            self.activities.append(activity)
            return activity

        async def get_task_activities(self, task_id, limit=50):
            return [
                activity
                for activity in self.activities
                if activity["task_id"] == task_id
            ][:limit]

    return MockActivityService()


@pytest.fixture
def task_service(
    mock_database, mock_cache, mock_notification_service, mock_activity_service
):
    """任务服务实例"""
    try:
        return TaskService(
            db=mock_database,
            cache_manager=mock_cache,
            notification_service=mock_notification_service,
            activity_service=mock_activity_service,
        )
    except:
        # 如果TaskService不可用，返回模拟对象
        return Mock()


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "roles": ["user"],
        "permissions": ["read", "write"],
    }


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "title": "测试任务",
        "description": "这是一个测试任务",
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.TODO,
        "estimated_hours": 8,
        "tags": ["test", "sample"],
        "custom_fields": {"client": "测试客户", "urgency": "normal"},
    }


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "name": "测试项目",
        "description": "这是一个测试项目",
        "start_date": datetime.utcnow(),
        "end_date": datetime.utcnow(),
        "status": "active",
        "is_public": False,
        "settings": {
            "workflow": {
                "statuses": ["todo", "in_progress", "done"],
                "transitions": {
                    "todo": ["in_progress"],
                    "in_progress": ["done", "todo"],
                    "done": ["in_progress"],
                },
            }
        },
    }


@pytest.fixture
def mock_file_upload():
    """模拟文件上传"""

    class MockFile:
        def __init__(
            self,
            filename="test.txt",
            content=b"test content",
            content_type="text/plain",
        ):
            self.filename = filename
            self.content = content
            self.content_type = content_type
            self.size = len(content)

        async def read(self):
            return self.content

        async def seek(self, position):
            pass

    return MockFile


@pytest.fixture
def authenticated_user():
    """认证用户"""
    return {
        "user_id": "user-123",
        "username": "authuser",
        "email": "auth@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
    }


# ==================== 测试数据生成器 ====================


@pytest.fixture
def user_factory():
    """用户数据工厂"""

    def create_user(username=None, email=None, **kwargs):
        base_data = {
            "username": username or f"user_{datetime.now().timestamp()}",
            "email": email or f"user_{datetime.now().timestamp()}@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
            "roles": ["user"],
            "permissions": ["read"],
        }
        base_data.update(kwargs)
        return base_data

    return create_user


@pytest.fixture
def task_factory():
    """任务数据工厂"""

    def create_task(title=None, **kwargs):
        base_data = {
            "title": title or f"任务_{datetime.now().timestamp()}",
            "description": "测试任务描述",
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.TODO,
            "estimated_hours": 4,
            "tags": ["test"],
        }
        base_data.update(kwargs)
        return base_data

    return create_task


@pytest.fixture
def project_factory():
    """项目数据工厂"""

    def create_project(name=None, **kwargs):
        base_data = {
            "name": name or f"项目_{datetime.now().timestamp()}",
            "description": "测试项目描述",
            "status": "planning",
            "is_public": False,
        }
        base_data.update(kwargs)
        return base_data

    return create_project


# ==================== 性能测试 Fixtures ====================


@pytest.fixture
def performance_timer():
    """性能计时器"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer


@pytest.fixture
def memory_monitor():
    """内存监控器"""
    import psutil
    import os

    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.initial_memory = self.process.memory_info().rss

        def current_memory(self):
            return self.process.memory_info().rss

        def memory_increase(self):
            return self.current_memory() - self.initial_memory

        def memory_usage_mb(self):
            return self.current_memory() / (1024 * 1024)

    return MemoryMonitor


# ==================== 清理 Fixtures ====================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """测试后自动清理"""
    yield
    # 测试完成后的清理工作
    # 清理临时文件、重置全局状态等


# ==================== 标记配置 ====================


def pytest_configure(config):
    """Pytest配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为集成测试添加标记
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # 为单元测试添加标记
        if "test_" in item.name and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # 为慢速测试添加标记
        if hasattr(item.function, "slow") or "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)


# ==================== 命令行选项 ====================


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )

    parser.addoption(
        "--integration-only",
        action="store_true",
        default=False,
        help="run only integration tests",
    )


def pytest_runtest_setup(item):
    """测试运行前设置"""
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")

    if (
        item.config.getoption("--integration-only")
        and "integration" not in item.keywords
    ):
        pytest.skip("running integration tests only")


# ==================== 测试报告增强 ====================


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告"""
    outcome = yield
    rep = outcome.get_result()

    # 添加测试持续时间到报告中
    if rep.when == "call":
        rep.duration = call.duration

    # 为失败的测试添加额外信息
    if rep.failed and hasattr(item, "function"):
        rep.extra_info = {
            "test_file": item.fspath.basename,
            "test_function": item.function.__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
