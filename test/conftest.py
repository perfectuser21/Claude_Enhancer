#!/usr/bin/env python3
"""
Pytest 配置文件

这个文件包含了所有测试用的共享配置、fixtures和工具函数。
就像一个测试实验室的基础设施 - 为所有测试提供统一的环境和工具。

主要功能：
- 测试数据库连接
- 测试用户和认证
- 模拟服务和依赖
- 测试环境清理
- 公共的测试工具函数
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import aiohttp
from aiohttp import web
import jwt
from werkzeug.security import generate_password_hash


# ========================================
# 测试配置 (Test Configuration)
# ========================================

@pytest.fixture(scope="session")
def test_config():
    """测试配置 - 像测试实验室的基本设置"""
    return {
        'DATABASE_URL': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key-for-jwt-tokens-very-secure',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION_HOURS': 24,
        'API_VERSION': 'v1',
        'BASE_URL': 'http://localhost:8080',
        'TEST_DATA_DIR': tempfile.mkdtemp(),
        'LOG_LEVEL': 'INFO',
        'RATE_LIMIT_REQUESTS': 1000,
        'RATE_LIMIT_WINDOW': 3600,
    }


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ========================================
# 数据库相关 Fixtures
# ========================================

@pytest.fixture
def mock_database():
    """模拟数据库 - 像一个在内存中的临时数据存储"""
    from test.unit.test_todo_api import TodoRepository
    return TodoRepository()


@pytest.fixture
def todo_service(mock_database):
    """创建待办事项服务实例"""
    from test.unit.test_todo_api import TodoService
    return TodoService(mock_database)


@pytest.fixture
def sample_user_data():
    """样例用户数据"""
    return {
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'user_id': 'test-user-123'
    }


@pytest.fixture
def sample_todo_data():
    """样例待办事项数据"""
    return {
        'title': 'Sample Todo',
        'description': 'This is a sample todo for testing',
        'priority': 'medium',
        'status': 'pending',
        'due_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
        'tags': ['test', 'sample']
    }


@pytest.fixture
def jwt_service(test_config):
    """
JWT服务实例用于令牌管理"""
    from test.integration.test_todo_api_integration import JWTService
    return JWTService(
        test_config['JWT_SECRET_KEY'],
        test_config['JWT_ALGORITHM']
    )


@pytest.fixture
def auth_token(jwt_service, sample_user_data):
    """生成测试用的认证令牌"""
    return jwt_service.generate_token(sample_user_data['user_id'])


@pytest.fixture
def auth_headers(auth_token):
    """创建认证头"""
    return {'Authorization': f'Bearer {auth_token}'}


# ========================================
# 测试数据生成器 (Test Data Generators)
# ========================================

class TestDataGenerator:
    """测试数据生成器 - 像一个测试数据工厂"""
    
    @staticmethod
    def create_users(count: int = 5) -> List[Dict]:
        """生成多个测试用户"""
        users = []
        for i in range(count):
            users.append({
                'email': f'user{i}@example.com',
                'password': f'Password{i}123!',
                'user_id': f'user-{i:03d}'
            })
        return users
    
    @staticmethod
    def create_todos(count: int = 10, user_id: str = 'test-user') -> List[Dict]:
        """生成多个测试待办事项"""
        from test.unit.test_todo_api import Priority, TodoStatus
        
        priorities = list(Priority)
        statuses = list(TodoStatus)
        todos = []
        
        for i in range(count):
            todo = {
                'title': f'Test Todo {i:03d}',
                'description': f'This is test todo number {i}',
                'priority': priorities[i % len(priorities)].value,
                'status': statuses[i % len(statuses)].value,
                'user_id': user_id,
                'tags': [f'tag{i}', 'test'],
                'due_date': (datetime.utcnow() + timedelta(days=i)).isoformat()
            }
            todos.append(todo)
        
        return todos
    
    @staticmethod
    def create_invalid_todo_data() -> List[Dict]:
        """生成无效的待办事项数据用于负面测试"""
        return [
            {'description': 'No title'},  # 缺少标题
            {'title': ''},  # 空标题
            {'title': 'x' * 201},  # 标题过长
            {'title': 'Valid', 'description': 'x' * 1001},  # 描述过长
            {'title': 'Valid', 'priority': 'invalid'},  # 无效优先级
            {'title': 'Valid', 'status': 'unknown'},  # 无效状态
            {'title': 'Valid', 'due_date': '2020-01-01'},  # 过去的日期
            {'title': 'Valid', 'due_date': 'invalid-date'},  # 无效日期格式
        ]
    
    @staticmethod
    def create_unicode_test_data() -> Dict:
        """创建Unicode测试数据"""
        return {
            'title': '🚀 项目任务 - 测试Unicode支持 🎯',
            'description': '这是一个包含中文、emoji和特殊字符的描述：∑∏∆∇√∞',
            'tags': ['中文标签', 'emoji🎉', 'special∑'],
            'priority': 'high'
        }


@pytest.fixture
def test_data_generator():
    """测试数据生成器实例"""
    return TestDataGenerator()


# ========================================
# 测试工具函数 (Test Utilities)
# ========================================

class TestUtils:
    """测试工具类 - 像一个测试工具箱"""
    
    @staticmethod
    def assert_todo_fields(todo_dict: Dict, expected_fields: List[str]):
        """验证待办事项包含必要字段"""
        for field in expected_fields:
            assert field in todo_dict, f"Missing field: {field}"
    
    @staticmethod
    def assert_valid_iso_datetime(date_string: str):
        """验证ISO格式的日期时间"""
        try:
            datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid ISO datetime format: {date_string}")
    
    @staticmethod
    def assert_valid_uuid(uuid_string: str):
        """验证UUID格式"""
        import uuid
        try:
            uuid.UUID(uuid_string)
        except ValueError:
            pytest.fail(f"Invalid UUID format: {uuid_string}")
    
    @staticmethod
    def create_auth_headers(token: str) -> Dict[str, str]:
        """创建认证头"""
        return {'Authorization': f'Bearer {token}'}
    
    @staticmethod
    def assert_error_response(response_data: Dict, expected_error_msg: str = None):
        """验证错误响应格式"""
        assert 'error' in response_data, "Error response should contain 'error' field"
        if expected_error_msg:
            assert expected_error_msg in response_data['error'], \
                f"Expected error message '{expected_error_msg}' not found in '{response_data['error']}'"
    
    @staticmethod
    def assert_success_response(response_data: Dict, required_fields: List[str] = None):
        """验证成功响应格式"""
        assert 'error' not in response_data, f"Unexpected error in response: {response_data.get('error')}"
        if required_fields:
            for field in required_fields:
                assert field in response_data, f"Missing required field: {field}"
    
    @staticmethod
    def compare_todos(todo1: Dict, todo2: Dict, ignore_fields: List[str] = None):
        """比较两个待办事项，忽略指定字段"""
        ignore_fields = ignore_fields or ['created_at', 'updated_at']
        
        for key, value in todo1.items():
            if key not in ignore_fields:
                assert todo2.get(key) == value, \
                    f"Field '{key}' mismatch: {todo2.get(key)} != {value}"
    
    @staticmethod
    def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """等待条件满足，用于异步测试"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        
        return False


@pytest.fixture
def test_utils():
    """测试工具实例"""
    return TestUtils()


# ========================================
# 性能测试工具 (Performance Testing Utilities)
# ========================================

class PerformanceTestUtils:
    """性能测试工具类"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """测量函数执行时间"""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    async def measure_async_execution_time(async_func, *args, **kwargs):
        """测量异步函数执行时间"""
        import time
        start_time = time.time()
        result = await async_func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def assert_performance_threshold(execution_time: float, threshold: float, operation_name: str):
        """断言性能阈值"""
        assert execution_time <= threshold, \
            f"{operation_name} took {execution_time:.3f}s, exceeds threshold of {threshold}s"
    
    @staticmethod
    def create_load_test_data(num_requests: int, base_data: Dict) -> List[Dict]:
        """创建负载测试数据"""
        test_data = []
        for i in range(num_requests):
            data = base_data.copy()
            data['title'] = f"{data.get('title', 'Load Test')} {i:05d}"
            test_data.append(data)
        return test_data


@pytest.fixture
def performance_utils():
    """性能测试工具实例"""
    return PerformanceTestUtils()


# ========================================
# Mock 服务和依赖 (Mock Services and Dependencies)
# ========================================

@pytest.fixture
def mock_external_api():
    """模拟外部API服务"""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = Mock(return_value={'status': 'success'})
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        yield mock_session


@pytest.fixture
def mock_email_service():
    """模拟邮件服务"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.return_value.send_message = Mock(return_value={})
        yield mock_smtp


@pytest.fixture
def mock_redis_cache():
    """模拟Redis缓存服务"""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=0)
    return mock_redis


# ========================================
# 测试环境清理 (Test Environment Cleanup)
# ========================================

@pytest.fixture(autouse=True)
def cleanup_test_environment(test_config):
    """自动清理测试环境"""
    # 测试前准备
    yield
    
    # 测试后清理
    import shutil
    test_data_dir = test_config.get('TEST_DATA_DIR')
    if test_data_dir and os.path.exists(test_data_dir):
        try:
            shutil.rmtree(test_data_dir)
        except OSError:
            pass  # 忽略清理错误


# ========================================
# 测试数据库初始化 (Test Database Initialization)
# ========================================

@pytest.fixture
def init_test_database(mock_database, test_data_generator):
    """初始化测试数据库并添加示例数据"""
    from test.unit.test_todo_api import Todo, Priority, TodoStatus
    
    # 创建一些示例数据
    sample_todos = test_data_generator.create_todos(5)
    
    created_todos = []
    for todo_data in sample_todos:
        todo = Todo(
            id=f"todo-{len(created_todos):03d}",
            title=todo_data['title'],
            description=todo_data['description'],
            priority=Priority(todo_data['priority']),
            status=TodoStatus(todo_data['status']),
            user_id=todo_data['user_id'],
            tags=todo_data['tags']
        )
        created_todos.append(mock_database.create(todo))
    
    return created_todos


# ========================================
# API客户端测试工具 (API Client Test Utilities)
# ========================================

class APITestClient:
    """
API测试客户端 - 像一个专门的API测试工具"""
    
    def __init__(self, base_url: str, default_headers: Dict = None):
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def request(self, method: str, path: str, **kwargs):
        """发送HTTP请求"""
        url = f"{self.base_url}{path}"
        headers = {**self.default_headers, **kwargs.pop('headers', {})}
        
        async with self.session.request(method, url, headers=headers, **kwargs) as response:
            return response
    
    async def get(self, path: str, **kwargs):
        return await self.request('GET', path, **kwargs)
    
    async def post(self, path: str, **kwargs):
        return await self.request('POST', path, **kwargs)
    
    async def put(self, path: str, **kwargs):
        return await self.request('PUT', path, **kwargs)
    
    async def patch(self, path: str, **kwargs):
        return await self.request('PATCH', path, **kwargs)
    
    async def delete(self, path: str, **kwargs):
        return await self.request('DELETE', path, **kwargs)


@pytest.fixture
async def api_client(test_config):
    """创建API测试客户端"""
    async with APITestClient(test_config['BASE_URL']) as client:
        yield client


# ========================================
# 日志和调试工具 (Logging and Debug Utilities)
# ========================================

@pytest.fixture
def test_logger():
    """测试专用日志记录器"""
    import logging
    
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    
    # 如果还没有handler，添加一个
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


@pytest.fixture
def debug_mode():
    """调试模式标志"""
    import os
    return os.getenv('DEBUG', 'false').lower() == 'true'


# ========================================
# 测试结果统计和报告 (Test Statistics and Reporting)
# ========================================

class TestStatistics:
    """测试统计信息收集器"""
    
    def __init__(self):
        self.stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'execution_times': [],
            'error_types': {},
        }
    
    def record_test_result(self, test_name: str, result: str, execution_time: float = None, error_type: str = None):
        """记录测试结果"""
        self.stats['total_tests'] += 1
        
        if result == 'passed':
            self.stats['passed_tests'] += 1
        elif result == 'failed':
            self.stats['failed_tests'] += 1
        elif result == 'skipped':
            self.stats['skipped_tests'] += 1
        
        if execution_time is not None:
            self.stats['execution_times'].append(execution_time)
        
        if error_type:
            self.stats['error_types'][error_type] = \
                self.stats['error_types'].get(error_type, 0) + 1
    
    def get_summary(self) -> Dict:
        """获取测试统计摘要"""
        execution_times = self.stats['execution_times']
        
        summary = self.stats.copy()
        
        if execution_times:
            summary.update({
                'avg_execution_time': sum(execution_times) / len(execution_times),
                'max_execution_time': max(execution_times),
                'min_execution_time': min(execution_times),
            })
        
        return summary


@pytest.fixture(scope="session")
def test_statistics():
    """测试统计收集器"""
    return TestStatistics()


# ========================================
# Pytest Hooks 和配置 (Pytest Hooks and Configuration)
# ========================================

def pytest_configure(config):
    """
Pytest配置钩子"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    # 为没有标记的测试添加默认标记
    for item in items:
        if "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """测试运行前的设置"""
    # 设置测试环境变量
    os.environ['TESTING'] = 'true'
    os.environ['ENV'] = 'test'


def pytest_runtest_teardown(item):
    """测试运行后的清理"""
    # 清理环境变量
    os.environ.pop('TESTING', None)
    os.environ.pop('ENV', None)


# ========================================
# 特殊场景测试工具 (Special Scenario Test Utilities)
# ========================================

@pytest.fixture
def network_failure_simulator():
    """网络故障模拟器"""
    class NetworkFailureSimulator:
        def __init__(self):
            self.failure_rate = 0.0
            self.delay_ms = 0
        
        def set_failure_rate(self, rate: float):
            """Setting network failure rate (0.0 to 1.0)"""
            self.failure_rate = max(0.0, min(1.0, rate))
        
        def set_delay(self, delay_ms: int):
            """Setting network delay in milliseconds"""
            self.delay_ms = max(0, delay_ms)
        
        async def should_fail(self) -> bool:
            """Determine if this request should fail"""
            import random
            return random.random() < self.failure_rate
        
        async def apply_delay(self):
            """Apply network delay"""
            if self.delay_ms > 0:
                await asyncio.sleep(self.delay_ms / 1000.0)
    
    return NetworkFailureSimulator()


@pytest.fixture
def memory_pressure_simulator():
    """内存压力模拟器"""
    class MemoryPressureSimulator:
        def __init__(self):
            self.allocated_memory = []
        
        def allocate_memory(self, size_mb: int):
            """Allocate memory to simulate pressure"""
            # 分配指定大小的内存
            chunk = bytearray(size_mb * 1024 * 1024)
            self.allocated_memory.append(chunk)
        
        def release_memory(self):
            """Release all allocated memory"""
            self.allocated_memory.clear()
    
    simulator = MemoryPressureSimulator()
    yield simulator
    simulator.release_memory()  # 清理


# ========================================
# 测试数据验证器 (Test Data Validators)
# ========================================

class DataValidators:
    """数据验证器集合"""
    
    @staticmethod
    def validate_todo_structure(todo_data: Dict) -> bool:
        """验证待办事项数据结构"""
        required_fields = ['id', 'title', 'status', 'created_at', 'updated_at']
        return all(field in todo_data for field in required_fields)
    
    @staticmethod
    def validate_user_structure(user_data: Dict) -> bool:
        """验证用户数据结构"""
        required_fields = ['id', 'email']
        return all(field in user_data for field in required_fields)
    
    @staticmethod
    def validate_api_response_structure(response_data: Dict, response_type: str) -> bool:
        """验证API响应结构"""
        if response_type == 'list':
            return 'total' in response_data and 'data' in response_data
        elif response_type == 'error':
            return 'error' in response_data
        elif response_type == 'success':
            return 'error' not in response_data
        return False


@pytest.fixture
def data_validators():
    """数据验证器实例"""
    return DataValidators()


# ========================================
# 测试环境信息 (Test Environment Info)
# ========================================

@pytest.fixture(scope="session")
def test_environment_info():
    """收集测试环境信息"""
    import platform
    import sys
    
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'processor': platform.processor(),
        'pytest_version': pytest.__version__,
        'test_start_time': datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    print("📝 测试配置模块 - 为所有测试提供统一的基础设施")
    print("✅ 包含以下组件:")
    print("  - 测试数据库和数据生成器")
    print("  - 认证和JWT服务")
    print("  - 测试工具和验证器")
    print("  - 性能测试工具")
    print("  - Mock服务和依赖")
    print("  - 测试环境清理")
    print("  - API测试客户端")
    print("🚀 Ready for comprehensive testing!")
