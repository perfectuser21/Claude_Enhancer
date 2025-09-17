#!/usr/bin/env python3
"""
Pytest配置文件 - Perfect21测试环境配置
提供共享的测试夹具和配置
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.update({
    'TESTING': 'true',
    'LOG_LEVEL': 'INFO',
    'DB_URL': 'sqlite:///test.db',
    'REDIS_URL': 'redis://localhost:6379/1'
})

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def clean_environment():
    """自动清理测试环境"""
    # 测试前清理
    yield
    # 测试后清理
    pass

@pytest.fixture
def test_config():
    """测试配置"""
    return {
        'api_timeout': 30,
        'max_retry_attempts': 3,
        'test_data_path': project_root / 'tests' / 'fixtures',
        'temp_dir': project_root / 'tests' / 'temp'
    }

@pytest.fixture
def temp_workspace(tmp_path):
    """临时工作空间固件"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    old_cwd = os.getcwd()
    os.chdir(workspace)
    yield workspace
    os.chdir(old_cwd)

@pytest.fixture
def mock_perfect21_core():
    """Mock Perfect21Core"""
    core = Perfect21Core()
    core.execute_parallel_task = lambda task, **kwargs: {
        'success': True,
        'task': task,
        'results': 'mocked_results'
    }
    return core

@pytest.fixture
def mock_git_hooks():
    """Mock GitHooks"""
    class MockGitHooks:
        def install_hooks(self):
            return {'success': True, 'installed': ['pre-commit', 'pre-push']}

        def get_status(self):
            return {'installed': True, 'hooks': ['pre-commit', 'pre-push']}

        def uninstall_hooks(self):
            return {'success': True, 'uninstalled': ['pre-commit', 'pre-push']}

    return MockGitHooks()

@pytest.fixture(autouse=True)
def auto_cleanup_db():
    """自动清理测试数据库"""
    # 测试前清理
    import sqlite3
    test_db_paths = [
        'data/test_auth.db',
        'data/test.db',
        'test.db'
    ]

    for db_path in test_db_paths:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass

    yield

    # 测试后清理
    for db_path in test_db_paths:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass

@pytest.fixture
def isolated_auth_manager():
    """隔离的认证管理器"""
    import uuid
    test_db = f"data/test_auth_{uuid.uuid4().hex[:8]}.db"

    # 确保目录存在
    os.makedirs('data', exist_ok=True)

    from features.auth_system import AuthManager
    manager = AuthManager(db_path=test_db)

    yield manager

    # 清理
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except:
            pass

# Mock类定义 - 解决测试导入错误
class Perfect21Core:
    """Mock Perfect21Core for testing"""
    def __init__(self):
        self.agents = {}
        self.capabilities = {}
        self.version = "3.0.0"

    def register_agent(self, name, agent):
        self.agents[name] = agent

    def get_agent(self, name):
        return self.agents.get(name)

class ExecutionMode:
    """Mock ExecutionMode for testing"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"

class WorkflowEngine:
    """Mock WorkflowEngine for testing"""
    def __init__(self):
        self.workflows = {}

    def register_workflow(self, name, workflow):
        self.workflows[name] = workflow

    def execute_workflow(self, name, *args, **kwargs):
        if name in self.workflows:
            return self.workflows[name](*args, **kwargs)
        return None

class AgentOrchestrator:
    """Mock AgentOrchestrator for testing"""
    def __init__(self):
        self.agents = []

    def add_agent(self, agent):
        self.agents.append(agent)

    def orchestrate(self, task):
        return {"status": "completed", "task": task}

# Mock Redis客户端
class MockRedis:
    """Mock Redis client for testing"""
    def __init__(self):
        self.data = {}
        self.expiry = {}

    def setex(self, key, ttl, value):
        self.data[key] = value
        self.expiry[key] = ttl

    def get(self, key):
        return self.data.get(key)

    def exists(self, key):
        return key in self.data

    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
            self.expiry.pop(key, None)

    def keys(self, pattern):
        import fnmatch
        return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]

    def ping(self):
        return True

    def close(self):
        pass

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis for testing"""
    mock = MockRedis()
    monkeypatch.setattr("redis.Redis", lambda **kwargs: mock)
    return mock

@pytest.fixture
def mock_env(monkeypatch):
    """设置测试环境变量"""
    test_env = {
        "JWT_SECRET_KEY": "test_secret_key_for_testing_only",
        "DATABASE_URL": "sqlite:///./test.db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "ENVIRONMENT": "test"
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env

# 设置pytest标记
pytest_plugins = [
    'tests.plugins.performance',
    'tests.plugins.database',
    'tests.plugins.security'
]
