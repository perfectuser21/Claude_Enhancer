#!/usr/bin/env python3
"""
Todo API 集成测试套件

这个测试套件专门测试Todo API的端到端功能，验证整个系统的协作能力。
就像测试整个生产线是否正常运作 - 从原材料到成品的每个环节都要检查。

测试覆盖：
- HTTP API端点的完整流程
- 数据库集成测试
- 认证和授权集成
- 错误响应和状态码验证
- 并发请求处理

质量要求：
- 集成测试覆盖率 > 85%
- 真实环境模拟
- 完整的请求-响应周期测试
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
import jwt
from werkzeug.security import generate_password_hash, check_password_hash


# ========================================
# 测试配置和常量 (Test Configuration)
# ========================================

TEST_CONFIG = {
    'DATABASE_URL': 'sqlite:///:memory:',
    'JWT_SECRET_KEY': 'test-secret-key-for-jwt-tokens',
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_HOURS': 24,
    'API_VERSION': 'v1',
    'TEST_USER_EMAIL': 'test@example.com',
    'TEST_USER_PASSWORD': 'TestPassword123!',
    'BASE_URL': 'http://localhost:8080'
}


class HTTPStatus:
    """HTTP状态码常量 - 像交通信号灯的标准化含义"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500


# ========================================
# 模拟API服务器 (Mock API Server)
# ========================================

class Priority(Enum):
    """优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class User:
    """用户模型"""
    id: str
    email: str
    password_hash: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)


@dataclass  
class Todo:
    """待办事项模型"""
    id: str
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: TodoStatus = TodoStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    due_date: Optional[datetime] = None
    tags: List[str] = None
    user_id: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        # 处理枚举类型
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        # 处理日期时间
        for field in ['created_at', 'updated_at', 'due_date']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data


class MockDatabase:
    """模拟数据库 - 像一个内存中的简单数据存储"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.todos: Dict[str, Todo] = {}
        self.email_to_user_id: Dict[str, str] = {}
    
    def create_user(self, email: str, password: str) -> User:
        """创建用户"""
        if email in self.email_to_user_id:
            raise ValueError("User already exists")
        
        user_id = str(uuid4())
        password_hash = generate_password_hash(password)
        
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash
        )
        
        self.users[user_id] = user
        self.email_to_user_id[email] = user_id
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user_id = self.email_to_user_id.get(email)
        return self.users.get(user_id) if user_id else None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def create_todo(self, todo: Todo) -> Todo:
        """创建待办事项"""
        self.todos[todo.id] = todo
        return todo
    
    def get_todo_by_id(self, todo_id: str) -> Optional[Todo]:
        """根据ID获取待办事项"""
        return self.todos.get(todo_id)
    
    def get_todos_by_user(self, user_id: str) -> List[Todo]:
        """获取用户的所有待办事项"""
        return [todo for todo in self.todos.values() if todo.user_id == user_id]
    
    def update_todo(self, todo: Todo) -> Todo:
        """更新待办事项"""
        todo.updated_at = datetime.utcnow()
        self.todos[todo.id] = todo
        return todo
    
    def delete_todo(self, todo_id: str) -> bool:
        """删除待办事项"""
        if todo_id in self.todos:
            del self.todos[todo_id]
            return True
        return False


class JWTService:
    """JWT令牌服务 - 像一个智能的身份证制作机"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_token(self, user_id: str, expiration_hours: int = 24) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expiration_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict:
        """解码JWT令牌"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")


class MockTodoAPIServer:
    """模拟Todo API服务器 - 像一个完整的后端服务"""
    
    def __init__(self):
        self.db = MockDatabase()
        self.jwt_service = JWTService(
            TEST_CONFIG['JWT_SECRET_KEY'],
            TEST_CONFIG['JWT_ALGORITHM']
        )
        self.app = web.Application()
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """设置中间件"""
        @web.middleware
        async def cors_handler(request, handler):
            """CORS处理"""
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        @web.middleware
        async def error_handler(request, handler):
            """错误处理中间件"""
            try:
                return await handler(request)
            except Exception as e:
                return web.json_response(
                    {'error': str(e)},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR
                )
        
        self.app.middlewares.append(cors_handler)
        self.app.middlewares.append(error_handler)
    
    def _setup_routes(self):
        """设置路由"""
        # 认证路由
        self.app.router.add_post('/api/v1/auth/register', self.register)
        self.app.router.add_post('/api/v1/auth/login', self.login)
        
        # Todo路由
        self.app.router.add_get('/api/v1/todos', self.get_todos)
        self.app.router.add_post('/api/v1/todos', self.create_todo)
        self.app.router.add_get('/api/v1/todos/{todo_id}', self.get_todo)
        self.app.router.add_put('/api/v1/todos/{todo_id}', self.update_todo)
        self.app.router.add_delete('/api/v1/todos/{todo_id}', self.delete_todo)
        self.app.router.add_patch('/api/v1/todos/{todo_id}/complete', self.complete_todo)
        
        # 健康检查
        self.app.router.add_get('/health', self.health_check)
    
    def _get_current_user(self, request) -> Optional[str]:
        """从请求中获取当前用户ID"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]  # Remove 'Bearer '
        try:
            payload = self.jwt_service.decode_token(token)
            return payload['user_id']
        except ValueError:
            return None
    
    def _require_auth(self, request) -> str:
        """要求认证，返回用户ID"""
        user_id = self._get_current_user(request)
        if not user_id:
            raise web.HTTPUnauthorized(text=json.dumps({'error': 'Authentication required'}))
        return user_id
    
    async def health_check(self, request):
        """健康检查端点"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': TEST_CONFIG['API_VERSION']
        })
    
    async def register(self, request):
        """用户注册"""
        try:
            data = await request.json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return web.json_response(
                    {'error': 'Email and password are required'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            # 验证密码强度
            if len(password) < 8:
                return web.json_response(
                    {'error': 'Password must be at least 8 characters'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            user = self.db.create_user(email, password)
            token = self.jwt_service.generate_token(user.id)
            
            return web.json_response({
                'user_id': user.id,
                'email': user.email,
                'token': token
            }, status=HTTPStatus.CREATED)
            
        except ValueError as e:
            return web.json_response(
                {'error': str(e)},
                status=HTTPStatus.CONFLICT
            )
        except Exception as e:
            return web.json_response(
                {'error': 'Invalid request data'},
                status=HTTPStatus.BAD_REQUEST
            )
    
    async def login(self, request):
        """用户登录"""
        try:
            data = await request.json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return web.json_response(
                    {'error': 'Email and password are required'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            user = self.db.get_user_by_email(email)
            if not user or not user.check_password(password):
                return web.json_response(
                    {'error': 'Invalid credentials'},
                    status=HTTPStatus.UNAUTHORIZED
                )
            
            token = self.jwt_service.generate_token(user.id)
            
            return web.json_response({
                'user_id': user.id,
                'email': user.email,
                'token': token
            })
            
        except Exception as e:
            return web.json_response(
                {'error': 'Invalid request data'},
                status=HTTPStatus.BAD_REQUEST
            )
    
    async def get_todos(self, request):
        """获取用户的待办事项列表"""
        user_id = self._require_auth(request)
        
        # 解析查询参数
        status = request.query.get('status')
        priority = request.query.get('priority')
        limit = int(request.query.get('limit', 100))
        offset = int(request.query.get('offset', 0))
        
        todos = self.db.get_todos_by_user(user_id)
        
        # 过滤
        if status:
            todos = [todo for todo in todos if todo.status.value == status]
        if priority:
            todos = [todo for todo in todos if todo.priority.value == priority]
        
        # 排序（按创建时间倒序）
        todos.sort(key=lambda x: x.created_at, reverse=True)
        
        # 分页
        total = len(todos)
        todos = todos[offset:offset + limit]
        
        return web.json_response({
            'todos': [todo.to_dict() for todo in todos],
            'total': total,
            'limit': limit,
            'offset': offset
        })
    
    async def create_todo(self, request):
        """创建新的待办事项"""
        user_id = self._require_auth(request)
        
        try:
            data = await request.json()
            title = data.get('title', '').strip()
            
            if not title:
                return web.json_response(
                    {'error': 'Title is required'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            if len(title) > 200:
                return web.json_response(
                    {'error': 'Title cannot exceed 200 characters'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            description = data.get('description')
            if description and len(description) > 1000:
                return web.json_response(
                    {'error': 'Description cannot exceed 1000 characters'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            # 解析优先级
            priority_str = data.get('priority', 'medium')
            try:
                priority = Priority(priority_str)
            except ValueError:
                return web.json_response(
                    {'error': f'Invalid priority: {priority_str}'},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            # 解析截止日期
            due_date = None
            if data.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                    if due_date < datetime.utcnow():
                        return web.json_response(
                            {'error': 'Due date cannot be in the past'},
                            status=HTTPStatus.BAD_REQUEST
                        )
                except ValueError:
                    return web.json_response(
                        {'error': 'Invalid due_date format. Use ISO format.'},
                        status=HTTPStatus.BAD_REQUEST
                    )
            
            todo = Todo(
                id=str(uuid4()),
                title=title,
                description=description,
                priority=priority,
                user_id=user_id,
                due_date=due_date,
                tags=data.get('tags', [])
            )
            
            created_todo = self.db.create_todo(todo)
            
            return web.json_response(
                created_todo.to_dict(),
                status=HTTPStatus.CREATED
            )
            
        except Exception as e:
            return web.json_response(
                {'error': 'Invalid request data'},
                status=HTTPStatus.BAD_REQUEST
            )
    
    async def get_todo(self, request):
        """获取单个待办事项"""
        user_id = self._require_auth(request)
        todo_id = request.match_info['todo_id']
        
        todo = self.db.get_todo_by_id(todo_id)
        if not todo:
            return web.json_response(
                {'error': 'Todo not found'},
                status=HTTPStatus.NOT_FOUND
            )
        
        if todo.user_id != user_id:
            return web.json_response(
                {'error': 'Access denied'},
                status=HTTPStatus.FORBIDDEN
            )
        
        return web.json_response(todo.to_dict())
    
    async def update_todo(self, request):
        """更新待办事项"""
        user_id = self._require_auth(request)
        todo_id = request.match_info['todo_id']
        
        todo = self.db.get_todo_by_id(todo_id)
        if not todo:
            return web.json_response(
                {'error': 'Todo not found'},
                status=HTTPStatus.NOT_FOUND
            )
        
        if todo.user_id != user_id:
            return web.json_response(
                {'error': 'Access denied'},
                status=HTTPStatus.FORBIDDEN
            )
        
        try:
            data = await request.json()
            
            # 更新字段
            if 'title' in data:
                title = data['title'].strip()
                if not title:
                    return web.json_response(
                        {'error': 'Title cannot be empty'},
                        status=HTTPStatus.BAD_REQUEST
                    )
                if len(title) > 200:
                    return web.json_response(
                        {'error': 'Title cannot exceed 200 characters'},
                        status=HTTPStatus.BAD_REQUEST
                    )
                todo.title = title
            
            if 'description' in data:
                description = data['description']
                if description and len(description) > 1000:
                    return web.json_response(
                        {'error': 'Description cannot exceed 1000 characters'},
                        status=HTTPStatus.BAD_REQUEST
                    )
                todo.description = description
            
            if 'priority' in data:
                try:
                    todo.priority = Priority(data['priority'])
                except ValueError:
                    return web.json_response(
                        {'error': f"Invalid priority: {data['priority']}"},
                        status=HTTPStatus.BAD_REQUEST
                    )
            
            if 'status' in data:
                try:
                    todo.status = TodoStatus(data['status'])
                except ValueError:
                    return web.json_response(
                        {'error': f"Invalid status: {data['status']}"},
                        status=HTTPStatus.BAD_REQUEST
                    )
            
            if 'due_date' in data:
                if data['due_date']:
                    try:
                        due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                        if due_date < datetime.utcnow():
                            return web.json_response(
                                {'error': 'Due date cannot be in the past'},
                                status=HTTPStatus.BAD_REQUEST
                            )
                        todo.due_date = due_date
                    except ValueError:
                        return web.json_response(
                            {'error': 'Invalid due_date format'},
                            status=HTTPStatus.BAD_REQUEST
                        )
                else:
                    todo.due_date = None
            
            if 'tags' in data:
                todo.tags = data['tags']
            
            updated_todo = self.db.update_todo(todo)
            return web.json_response(updated_todo.to_dict())
            
        except Exception as e:
            return web.json_response(
                {'error': 'Invalid request data'},
                status=HTTPStatus.BAD_REQUEST
            )
    
    async def delete_todo(self, request):
        """删除待办事项"""
        user_id = self._require_auth(request)
        todo_id = request.match_info['todo_id']
        
        todo = self.db.get_todo_by_id(todo_id)
        if not todo:
            return web.json_response(
                {'error': 'Todo not found'},
                status=HTTPStatus.NOT_FOUND
            )
        
        if todo.user_id != user_id:
            return web.json_response(
                {'error': 'Access denied'},
                status=HTTPStatus.FORBIDDEN
            )
        
        self.db.delete_todo(todo_id)
        return web.Response(status=HTTPStatus.NO_CONTENT)
    
    async def complete_todo(self, request):
        """标记待办事项为完成"""
        user_id = self._require_auth(request)
        todo_id = request.match_info['todo_id']
        
        todo = self.db.get_todo_by_id(todo_id)
        if not todo:
            return web.json_response(
                {'error': 'Todo not found'},
                status=HTTPStatus.NOT_FOUND
            )
        
        if todo.user_id != user_id:
            return web.json_response(
                {'error': 'Access denied'},
                status=HTTPStatus.FORBIDDEN
            )
        
        todo.status = TodoStatus.COMPLETED
        updated_todo = self.db.update_todo(todo)
        
        return web.json_response(updated_todo.to_dict())


# ========================================
# 集成测试类 (Integration Test Classes)
# ========================================

class TestTodoAPIIntegration(AioHTTPTestCase):
    """Todo API集成测试 - 像测试整个系统的协调能力"""
    
    async def get_application(self):
        """获取测试应用实例"""
        self.api_server = MockTodoAPIServer()
        return self.api_server.app
    
    async def setUp(self):
        """测试设置"""
        await super().setUp()
        
        # 创建测试用户
        self.test_user_data = {
            'email': TEST_CONFIG['TEST_USER_EMAIL'],
            'password': TEST_CONFIG['TEST_USER_PASSWORD']
        }
        
        # 注册测试用户
        resp = await self.client.request(
            'POST', 
            '/api/v1/auth/register',
            json=self.test_user_data
        )
        self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        user_data = await resp.json()
        self.user_id = user_data['user_id']
        self.auth_token = user_data['token']
        self.auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
    
    # ========================================
    # 认证相关测试
    # ========================================
    
    @unittest_run_loop
    async def test_user_registration_success(self):
        """测试用户注册成功"""
        new_user_data = {
            'email': 'newuser@example.com',
            'password': 'NewPassword123!'
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/auth/register',
            json=new_user_data
        )
        
        self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        data = await resp.json()
        self.assertIn('user_id', data)
        self.assertIn('email', data)
        self.assertIn('token', data)
        self.assertEqual(data['email'], new_user_data['email'])
    
    @unittest_run_loop
    async def test_user_registration_duplicate_email(self):
        """测试重复邮箱注册"""
        resp = await self.client.request(
            'POST',
            '/api/v1/auth/register',
            json=self.test_user_data
        )
        
        self.assertEqual(resp.status, HTTPStatus.CONFLICT)
        data = await resp.json()
        self.assertIn('error', data)
    
    @unittest_run_loop
    async def test_user_registration_invalid_data(self):
        """测试无效数据注册"""
        invalid_cases = [
            {'email': '', 'password': 'ValidPass123!'},  # 空邮箱
            {'email': 'valid@example.com', 'password': ''},  # 空密码
            {'email': 'valid@example.com', 'password': '123'},  # 密码太短
            {'email': 'valid@example.com'},  # 缺少密码
            {'password': 'ValidPass123!'},  # 缺少邮箱
        ]
        
        for case in invalid_cases:
            resp = await self.client.request(
                'POST',
                '/api/v1/auth/register',
                json=case
            )
            
            self.assertEqual(resp.status, HTTPStatus.BAD_REQUEST)
            data = await resp.json()
            self.assertIn('error', data)
    
    @unittest_run_loop
    async def test_user_login_success(self):
        """测试用户登录成功"""
        resp = await self.client.request(
            'POST',
            '/api/v1/auth/login',
            json=self.test_user_data
        )
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        data = await resp.json()
        self.assertIn('user_id', data)
        self.assertIn('email', data)
        self.assertIn('token', data)
        self.assertEqual(data['email'], self.test_user_data['email'])
    
    @unittest_run_loop
    async def test_user_login_invalid_credentials(self):
        """测试无效凭据登录"""
        invalid_cases = [
            {'email': 'wrong@example.com', 'password': self.test_user_data['password']},
            {'email': self.test_user_data['email'], 'password': 'WrongPassword'},
            {'email': 'wrong@example.com', 'password': 'WrongPassword'},
        ]
        
        for case in invalid_cases:
            resp = await self.client.request(
                'POST',
                '/api/v1/auth/login',
                json=case
            )
            
            self.assertEqual(resp.status, HTTPStatus.UNAUTHORIZED)
            data = await resp.json()
            self.assertIn('error', data)
    
    # ========================================
    # 待办事项CRUD测试
    # ========================================
    
    @unittest_run_loop
    async def test_create_todo_success(self):
        """测试创建待办事项成功"""
        todo_data = {
            'title': 'Test Todo',
            'description': 'This is a test todo',
            'priority': 'high',
            'tags': ['test', 'api']
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json=todo_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        data = await resp.json()
        self.assertIn('id', data)
        self.assertEqual(data['title'], todo_data['title'])
        self.assertEqual(data['description'], todo_data['description'])
        self.assertEqual(data['priority'], todo_data['priority'])
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['tags'], todo_data['tags'])
        self.assertEqual(data['user_id'], self.user_id)
    
    @unittest_run_loop
    async def test_create_todo_unauthorized(self):
        """测试未授权创建待办事项"""
        todo_data = {
            'title': 'Test Todo',
            'description': 'This should fail'
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json=todo_data
        )
        
        self.assertEqual(resp.status, HTTPStatus.UNAUTHORIZED)
    
    @unittest_run_loop
    async def test_create_todo_invalid_data(self):
        """测试无效数据创建待办事项"""
        invalid_cases = [
            {'description': 'No title'},  # 缺少标题
            {'title': ''},  # 空标题
            {'title': 'x' * 201},  # 标题过长
            {'title': 'Valid', 'description': 'x' * 1001},  # 描述过长
            {'title': 'Valid', 'priority': 'invalid'},  # 无效优先级
            {'title': 'Valid', 'due_date': '2020-01-01T00:00:00Z'},  # 过去的日期
        ]
        
        for case in invalid_cases:
            resp = await self.client.request(
                'POST',
                '/api/v1/todos',
                json=case,
                headers=self.auth_headers
            )
            
            self.assertEqual(resp.status, HTTPStatus.BAD_REQUEST)
            data = await resp.json()
            self.assertIn('error', data)
    
    @unittest_run_loop
    async def test_get_todos_success(self):
        """测试获取待办事项列表成功"""
        # 创建几个测试待办事项
        todo_titles = ['Todo 1', 'Todo 2', 'Todo 3']
        created_todos = []
        
        for title in todo_titles:
            resp = await self.client.request(
                'POST',
                '/api/v1/todos',
                json={'title': title},
                headers=self.auth_headers
            )
            self.assertEqual(resp.status, HTTPStatus.CREATED)
            created_todos.append(await resp.json())
        
        # 获取待办事项列表
        resp = await self.client.request(
            'GET',
            '/api/v1/todos',
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        data = await resp.json()
        self.assertIn('todos', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], len(todo_titles))
        self.assertEqual(len(data['todos']), len(todo_titles))
        
        # 验证返回的待办事项
        returned_titles = [todo['title'] for todo in data['todos']]
        for title in todo_titles:
            self.assertIn(title, returned_titles)
    
    @unittest_run_loop
    async def test_get_todos_with_filters(self):
        """测试带过滤器的获取待办事项"""
        # 创建不同状态和优先级的待办事项
        todos_data = [
            {'title': 'High Priority Pending', 'priority': 'high'},
            {'title': 'Medium Priority Pending', 'priority': 'medium'},
            {'title': 'Low Priority Pending', 'priority': 'low'},
        ]
        
        created_todos = []
        for todo_data in todos_data:
            resp = await self.client.request(
                'POST',
                '/api/v1/todos',
                json=todo_data,
                headers=self.auth_headers
            )
            created_todos.append(await resp.json())
        
        # 完成一个待办事项
        resp = await self.client.request(
            'PATCH',
            f"/api/v1/todos/{created_todos[0]['id']}/complete",
            headers=self.auth_headers
        )
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        # 测试按状态过滤
        resp = await self.client.request(
            'GET',
            '/api/v1/todos?status=pending',
            headers=self.auth_headers
        )
        data = await resp.json()
        self.assertEqual(len(data['todos']), 2)  # 两个pending状态
        
        # 测试按优先级过滤
        resp = await self.client.request(
            'GET',
            '/api/v1/todos?priority=high',
            headers=self.auth_headers
        )
        data = await resp.json()
        self.assertEqual(len(data['todos']), 1)  # 一个high优先级
    
    @unittest_run_loop
    async def test_get_single_todo_success(self):
        """测试获取单个待办事项成功"""
        # 创建待办事项
        todo_data = {
            'title': 'Single Todo Test',
            'description': 'Test getting single todo'
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json=todo_data,
            headers=self.auth_headers
        )
        created_todo = await resp.json()
        
        # 获取单个待办事项
        resp = await self.client.request(
            'GET',
            f"/api/v1/todos/{created_todo['id']}",
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        data = await resp.json()
        self.assertEqual(data['id'], created_todo['id'])
        self.assertEqual(data['title'], todo_data['title'])
        self.assertEqual(data['description'], todo_data['description'])
    
    @unittest_run_loop
    async def test_get_single_todo_not_found(self):
        """测试获取不存在的待办事项"""
        fake_id = str(uuid4())
        
        resp = await self.client.request(
            'GET',
            f'/api/v1/todos/{fake_id}',
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.NOT_FOUND)
        data = await resp.json()
        self.assertIn('error', data)
    
    @unittest_run_loop
    async def test_update_todo_success(self):
        """测试更新待办事项成功"""
        # 创建待办事项
        original_data = {
            'title': 'Original Title',
            'description': 'Original description',
            'priority': 'medium'
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json=original_data,
            headers=self.auth_headers
        )
        created_todo = await resp.json()
        
        # 更新待办事项
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'priority': 'high',
            'status': 'in_progress'
        }
        
        resp = await self.client.request(
            'PUT',
            f"/api/v1/todos/{created_todo['id']}",
            json=update_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        updated_todo = await resp.json()
        self.assertEqual(updated_todo['title'], update_data['title'])
        self.assertEqual(updated_todo['description'], update_data['description'])
        self.assertEqual(updated_todo['priority'], update_data['priority'])
        self.assertEqual(updated_todo['status'], update_data['status'])
        
        # 验证updated_at时间戳更新了
        self.assertNotEqual(updated_todo['updated_at'], created_todo['updated_at'])
    
    @unittest_run_loop
    async def test_delete_todo_success(self):
        """测试删除待办事项成功"""
        # 创建待办事项
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json={'title': 'To Delete'},
            headers=self.auth_headers
        )
        created_todo = await resp.json()
        
        # 删除待办事项
        resp = await self.client.request(
            'DELETE',
            f"/api/v1/todos/{created_todo['id']}",
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.NO_CONTENT)
        
        # 验证已删除
        resp = await self.client.request(
            'GET',
            f"/api/v1/todos/{created_todo['id']}",
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.NOT_FOUND)
    
    @unittest_run_loop
    async def test_complete_todo_success(self):
        """测试标记待办事项完成"""
        # 创建待办事项
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json={'title': 'To Complete'},
            headers=self.auth_headers
        )
        created_todo = await resp.json()
        
        # 标记完成
        resp = await self.client.request(
            'PATCH',
            f"/api/v1/todos/{created_todo['id']}/complete",
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        completed_todo = await resp.json()
        self.assertEqual(completed_todo['status'], 'completed')
        self.assertNotEqual(completed_todo['updated_at'], created_todo['updated_at'])
    
    # ========================================
    # 权限和安全测试
    # ========================================
    
    @unittest_run_loop
    async def test_access_control_between_users(self):
        """测试用户间的访问控制"""
        # 创建第二个用户
        user2_data = {
            'email': 'user2@example.com',
            'password': 'User2Password123!'
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/auth/register',
            json=user2_data
        )
        user2_info = await resp.json()
        user2_headers = {'Authorization': f"Bearer {user2_info['token']}"}
        
        # 用户1创建待办事项
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json={'title': 'User 1 Todo'},
            headers=self.auth_headers
        )
        user1_todo = await resp.json()
        
        # 用户2尝试访问用户1的待办事项
        resp = await self.client.request(
            'GET',
            f"/api/v1/todos/{user1_todo['id']}",
            headers=user2_headers
        )
        self.assertEqual(resp.status, HTTPStatus.FORBIDDEN)
        
        # 用户2尝试更新用户1的待办事项
        resp = await self.client.request(
            'PUT',
            f"/api/v1/todos/{user1_todo['id']}",
            json={'title': 'Hacked'},
            headers=user2_headers
        )
        self.assertEqual(resp.status, HTTPStatus.FORBIDDEN)
        
        # 用户2尝试删除用户1的待办事项
        resp = await self.client.request(
            'DELETE',
            f"/api/v1/todos/{user1_todo['id']}",
            headers=user2_headers
        )
        self.assertEqual(resp.status, HTTPStatus.FORBIDDEN)
    
    @unittest_run_loop
    async def test_invalid_token_access(self):
        """测试无效令牌访问"""
        invalid_tokens = [
            'invalid-token',
            'Bearer invalid-token',
            f'Bearer {self.auth_token[:-5]}invalid',  # 篡改的令牌
        ]
        
        for token in invalid_tokens:
            headers = {'Authorization': token}
            
            resp = await self.client.request(
                'GET',
                '/api/v1/todos',
                headers=headers
            )
            
            self.assertEqual(resp.status, HTTPStatus.UNAUTHORIZED)
    
    # ========================================
    # 边界条件和性能测试
    # ========================================
    
    @unittest_run_loop
    async def test_large_todo_list_pagination(self):
        """测试大量待办事项的分页"""
        # 创建大量待办事项
        num_todos = 50
        for i in range(num_todos):
            resp = await self.client.request(
                'POST',
                '/api/v1/todos',
                json={'title': f'Todo {i:03d}'},
                headers=self.auth_headers
            )
            self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        # 测试分页
        limit = 10
        offset = 0
        all_todos = []
        
        while True:
            resp = await self.client.request(
                'GET',
                f'/api/v1/todos?limit={limit}&offset={offset}',
                headers=self.auth_headers
            )
            
            data = await resp.json()
            todos = data['todos']
            all_todos.extend(todos)
            
            if len(todos) < limit:
                break
            
            offset += limit
        
        self.assertEqual(len(all_todos), num_todos)
    
    @unittest_run_loop
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        # 创建多个并发请求
        tasks = []
        num_concurrent = 10
        
        for i in range(num_concurrent):
            task = self.client.request(
                'POST',
                '/api/v1/todos',
                json={'title': f'Concurrent Todo {i}'},
                headers=self.auth_headers
            )
            tasks.append(task)
        
        # 等待所有请求完成
        responses = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        for resp in responses:
            self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        # 验证创建了正确数量的待办事项
        resp = await self.client.request(
            'GET',
            '/api/v1/todos',
            headers=self.auth_headers
        )
        
        data = await resp.json()
        self.assertEqual(data['total'], num_concurrent)
    
    @unittest_run_loop
    async def test_unicode_content_handling(self):
        """测试Unicode内容处理"""
        unicode_data = {
            'title': '🚀 项目任务 - 测试Unicode支持 🎯',
            'description': '这是一个包含中文、emoji和特殊字符的描述：∑∏∆∇√∞',
            'tags': ['中文标签', 'emoji🎉', 'special∑']
        }
        
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json=unicode_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        created_todo = await resp.json()
        self.assertEqual(created_todo['title'], unicode_data['title'])
        self.assertEqual(created_todo['description'], unicode_data['description'])
        self.assertEqual(created_todo['tags'], unicode_data['tags'])
    
    @unittest_run_loop
    async def test_api_health_check(self):
        """测试API健康检查"""
        resp = await self.client.request('GET', '/health')
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        
        data = await resp.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['version'], TEST_CONFIG['API_VERSION'])


# ========================================
# 性能和负载测试
# ========================================

class TestTodoAPIPerformance(AioHTTPTestCase):
    """Todo API性能测试 - 像压力测试系统的承受能力"""
    
    async def get_application(self):
        self.api_server = MockTodoAPIServer()
        return self.api_server.app
    
    async def setUp(self):
        await super().setUp()
        
        # 注册测试用户
        resp = await self.client.request(
            'POST',
            '/api/v1/auth/register',
            json={
                'email': 'perf@example.com',
                'password': 'PerfTest123!'
            }
        )
        user_data = await resp.json()
        self.auth_headers = {'Authorization': f"Bearer {user_data['token']}"}
    
    @unittest_run_loop
    async def test_bulk_todo_creation_performance(self):
        """测试批量创建待办事项的性能"""
        import time
        
        num_todos = 100
        start_time = time.time()
        
        tasks = []
        for i in range(num_todos):
            task = self.client.request(
                'POST',
                '/api/v1/todos',
                json={'title': f'Performance Test Todo {i}'},
                headers=self.auth_headers
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证所有请求成功
        for resp in responses:
            self.assertEqual(resp.status, HTTPStatus.CREATED)
        
        # 性能要求：100个待办事项的创建应该在2秒内完成
        execution_time = end_time - start_time
        self.assertLess(execution_time, 2.0, 
                       f"Bulk creation took {execution_time:.2f}s, expected < 2.0s")
    
    @unittest_run_loop
    async def test_large_list_retrieval_performance(self):
        """测试大列表检索性能"""
        # 创建大量待办事项
        num_todos = 500
        tasks = []
        
        for i in range(num_todos):
            task = self.client.request(
                'POST',
                '/api/v1/todos',
                json={'title': f'Large List Todo {i}'},
                headers=self.auth_headers
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # 测试检索性能
        import time
        start_time = time.time()
        
        resp = await self.client.request(
            'GET',
            '/api/v1/todos',
            headers=self.auth_headers
        )
        
        end_time = time.time()
        
        self.assertEqual(resp.status, HTTPStatus.OK)
        data = await resp.json()
        self.assertEqual(data['total'], num_todos)
        
        # 性能要求：检索500个待办事项应该在1秒内完成
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0,
                       f"Large list retrieval took {execution_time:.2f}s, expected < 1.0s")


# ========================================
# 错误处理和边界测试
# ========================================

class TestTodoAPIErrorHandling(AioHTTPTestCase):
    """Todo API错误处理测试 - 像测试系统在异常情况下的表现"""
    
    async def get_application(self):
        self.api_server = MockTodoAPIServer()
        return self.api_server.app
    
    async def setUp(self):
        await super().setUp()
        
        # 注册测试用户
        resp = await self.client.request(
            'POST',
            '/api/v1/auth/register',
            json={
                'email': 'error@example.com',
                'password': 'ErrorTest123!'
            }
        )
        user_data = await resp.json()
        self.auth_headers = {'Authorization': f"Bearer {user_data['token']}"}
    
    @unittest_run_loop
    async def test_malformed_json_request(self):
        """测试格式错误的JSON请求"""
        # 发送格式错误的JSON
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            data='{ "title": "Test" invalid json }',
            headers={
                **self.auth_headers,
                'Content-Type': 'application/json'
            }
        )
        
        self.assertEqual(resp.status, HTTPStatus.BAD_REQUEST)
    
    @unittest_run_loop
    async def test_missing_content_type(self):
        """测试缺少Content-Type头"""
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            data=json.dumps({'title': 'Test'}),
            headers=self.auth_headers
        )
        
        # 应该能够处理或返回适当的错误
        self.assertIn(resp.status, [HTTPStatus.BAD_REQUEST, HTTPStatus.CREATED])
    
    @unittest_run_loop
    async def test_extremely_large_request(self):
        """测试极大的请求负载"""
        # 创建一个非常大的描述
        large_description = 'x' * 10000  # 10KB的数据
        
        resp = await self.client.request(
            'POST',
            '/api/v1/todos',
            json={
                'title': 'Large Request Test',
                'description': large_description
            },
            headers=self.auth_headers
        )
        
        # 应该返回400错误（描述太长）
        self.assertEqual(resp.status, HTTPStatus.BAD_REQUEST)
    
    @unittest_run_loop
    async def test_special_characters_in_urls(self):
        """测试URL中的特殊字符"""
        special_ids = [
            'id with spaces',
            'id/with/slashes',
            'id%20with%20encoding',
            '../../../etc/passwd',  # 路径遍历攻击
            '<script>alert("xss")</script>',  # XSS攻击
        ]
        
        for special_id in special_ids:
            resp = await self.client.request(
                'GET',
                f'/api/v1/todos/{special_id}',
                headers=self.auth_headers
            )
            
            # 应该返回404或400，不应该导致服务器错误
            self.assertIn(resp.status, [HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST])


if __name__ == '__main__':
    # 运行集成测试的示例
    import unittest
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_suite.addTest(unittest.makeSuite(TestTodoAPIIntegration))
    test_suite.addTest(unittest.makeSuite(TestTodoAPIPerformance))
    test_suite.addTest(unittest.makeSuite(TestTodoAPIErrorHandling))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有集成测试通过！")
    else:
        print(f"\n❌ 有 {len(result.failures)} 个测试失败，{len(result.errors)} 个错误")
