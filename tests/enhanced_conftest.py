#!/usr/bin/env python3
"""
Enhanced Pytest配置文件 - Perfect21增强测试环境
提供更强大的测试夹具和测试隔离机制
"""

import os
import sys
import uuid
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.update({
    'TESTING': 'true',
    'LOG_LEVEL': 'ERROR',  # 减少测试期间的日志输出
    'DB_URL': 'sqlite:///test.db',
    'REDIS_URL': 'redis://localhost:6379/1'
})

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def temp_workspace():
    """为每个测试创建临时工作空间"""
    temp_dir = tempfile.mkdtemp(prefix="perfect21_test_")
    yield temp_dir
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def isolated_database():
    """为每个测试创建隔离的数据库"""
    db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    db_path = f"data/{db_name}"

    # 确保目录存在
    os.makedirs('data', exist_ok=True)

    yield db_path

    # 清理数据库文件
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass

@pytest.fixture(scope="function")
def clean_auth_environment(isolated_database):
    """清理认证测试环境"""
    # 清理所有可能的测试数据库
    test_db_patterns = [
        'data/test_*.db',
        'test_*.db',
        '*.db'
    ]

    # 测试前清理
    for pattern in test_db_patterns:
        import glob
        for db_file in glob.glob(pattern):
            if 'test' in db_file.lower():
                try:
                    os.remove(db_file)
                except:
                    pass

    yield isolated_database

    # 测试后清理
    for pattern in test_db_patterns:
        for db_file in glob.glob(pattern):
            if 'test' in db_file.lower():
                try:
                    os.remove(db_file)
                except:
                    pass

@pytest.fixture
def mock_git_repo(temp_workspace):
    """创建模拟的Git仓库"""
    repo_path = temp_workspace
    git_dir = os.path.join(repo_path, '.git')
    os.makedirs(git_dir, exist_ok=True)

    # 创建基本的Git结构
    with open(os.path.join(git_dir, 'HEAD'), 'w') as f:
        f.write('ref: refs/heads/main\n')

    refs_heads_dir = os.path.join(git_dir, 'refs', 'heads')
    os.makedirs(refs_heads_dir, exist_ok=True)

    yield repo_path

@pytest.fixture
def enhanced_test_config():
    """增强的测试配置"""
    return {
        'api_timeout': 30,
        'max_retry_attempts': 3,
        'test_data_path': project_root / 'tests' / 'fixtures',
        'temp_dir': project_root / 'tests' / 'temp',
        'isolation_level': 'function',
        'cleanup_strategy': 'aggressive',
        'mock_external_services': True
    }

@pytest.fixture
def auth_test_client(clean_auth_environment):
    """认证测试客户端"""
    from api.rest_server import app
    from fastapi.testclient import TestClient
    from features.auth_system import AuthManager

    # 使用隔离的认证管理器
    auth_manager = AuthManager(db_path=clean_auth_environment)
    app.state.auth_manager = auth_manager

    client = TestClient(app)
    yield client

    # 清理
    if hasattr(app.state, 'auth_manager'):
        delattr(app.state, 'auth_manager')

@pytest.fixture
def unique_test_user():
    """生成唯一的测试用户数据"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "TestPass123!",
        "role": "user"
    }

@pytest.fixture
def mock_external_services():
    """模拟外部服务"""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get, \
         patch('subprocess.run') as mock_subprocess:

        # 配置默认的mock响应
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}

        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "success"

        yield {
            'post': mock_post,
            'get': mock_get,
            'subprocess': mock_subprocess
        }

@pytest.fixture
def performance_monitor():
    """性能监控fixture"""
    import time
    start_time = time.time()

    yield

    end_time = time.time()
    execution_time = end_time - start_time

    # 警告执行时间过长的测试
    if execution_time > 5.0:  # 5秒
        pytest.warnings.warn(
            f"Test execution time: {execution_time:.2f}s (> 5s threshold)",
            category=UserWarning
        )

# 自动使用性能监控
pytestmark = pytest.mark.usefixtures("performance_monitor")

# 测试标记
pytest_plugins = [
    'tests.plugins.performance',
    'tests.plugins.database',
    'tests.plugins.security'
]