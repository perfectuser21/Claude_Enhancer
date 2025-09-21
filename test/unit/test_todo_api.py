#!/usr/bin/env python3
"""
Todo API 单元测试套件

这个测试套件专门测试待办事项API的核心功能，确保每个组件都能正确工作。
就像检查每个零件是否完好一样 - 我们要确保每个功能都按预期工作。

测试覆盖：
- Todo模型的数据验证
- CRUD操作的业务逻辑
- 错误处理机制
- 边界条件测试

质量要求：
- 单元测试覆盖率 > 90%
- 每个测试独立且可重复
- 清晰的测试描述和断言
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


# ========================================
# 测试数据模型 (Test Data Models)
# ========================================

class Priority(Enum):
    """优先级枚举 - 像交通信号灯一样，表示任务的紧急程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoStatus(Enum):
    """任务状态枚举 - 像任务的生命周期标签"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Todo:
    """待办事项模型 - 就像一张数字化的便签纸"""
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


class TodoRepository:
    """Todo数据访问层 - 像一个智能的文件柜管理员"""
    
    def __init__(self):
        self._todos: Dict[str, Todo] = {}
    
    def create(self, todo: Todo) -> Todo:
        """创建新的待办事项 - 像添加一张新的便签"""
        if todo.id in self._todos:
            raise ValueError(f"Todo with id {todo.id} already exists")
        self._todos[todo.id] = todo
        return todo
    
    def get_by_id(self, todo_id: str) -> Optional[Todo]:
        """根据ID获取待办事项 - 像从文件柜中找特定文件"""
        return self._todos.get(todo_id)
    
    def get_all(self, user_id: str = None) -> List[Todo]:
        """获取所有待办事项 - 像查看所有便签"""
        if user_id:
            return [todo for todo in self._todos.values() if todo.user_id == user_id]
        return list(self._todos.values())
    
    def update(self, todo: Todo) -> Todo:
        """更新待办事项 - 像修改便签内容"""
        if todo.id not in self._todos:
            raise ValueError(f"Todo with id {todo.id} not found")
        todo.updated_at = datetime.utcnow()
        self._todos[todo.id] = todo
        return todo
    
    def delete(self, todo_id: str) -> bool:
        """删除待办事项 - 像撕掉一张便签"""
        if todo_id in self._todos:
            del self._todos[todo_id]
            return True
        return False


class TodoService:
    """Todo业务逻辑层 - 像一个聪明的助手，处理所有复杂的逻辑"""
    
    def __init__(self, repository: TodoRepository):
        self._repository = repository
    
    def create_todo(self, title: str, description: str = None, 
                   priority: Priority = Priority.MEDIUM, 
                   user_id: str = None, 
                   due_date: datetime = None,
                   tags: List[str] = None) -> Todo:
        """创建新待办事项 - 包含验证和业务规则"""
        # 输入验证 - 像检查表单是否填写正确
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        
        if len(title) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        
        if description and len(description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        
        if due_date and due_date < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        
        # 创建Todo对象
        todo = Todo(
            id=str(uuid4()),
            title=title.strip(),
            description=description.strip() if description else None,
            priority=priority,
            user_id=user_id,
            due_date=due_date,
            tags=tags or []
        )
        
        return self._repository.create(todo)
    
    def get_todo(self, todo_id: str, user_id: str = None) -> Optional[Todo]:
        """获取待办事项 - 包含权限检查"""
        todo = self._repository.get_by_id(todo_id)
        if todo and user_id and todo.user_id != user_id:
            # 权限检查 - 像检查是否有权限查看文件
            return None
        return todo
    
    def update_todo(self, todo_id: str, user_id: str = None, **updates) -> Todo:
        """更新待办事项 - 包含验证和权限检查"""
        todo = self.get_todo(todo_id, user_id)
        if not todo:
            raise ValueError("Todo not found or access denied")
        
        # 应用更新
        for field, value in updates.items():
            if hasattr(todo, field):
                if field == 'title' and (not value or not value.strip()):
                    raise ValueError("Title cannot be empty")
                if field == 'title' and len(value) > 200:
                    raise ValueError("Title cannot exceed 200 characters")
                if field == 'description' and value and len(value) > 1000:
                    raise ValueError("Description cannot exceed 1000 characters")
                if field == 'due_date' and value and value < datetime.utcnow():
                    raise ValueError("Due date cannot be in the past")
                setattr(todo, field, value)
        
        return self._repository.update(todo)
    
    def delete_todo(self, todo_id: str, user_id: str = None) -> bool:
        """删除待办事项 - 包含权限检查"""
        todo = self.get_todo(todo_id, user_id)
        if not todo:
            return False
        return self._repository.delete(todo_id)
    
    def get_user_todos(self, user_id: str, status: TodoStatus = None,
                      priority: Priority = None) -> List[Todo]:
        """获取用户的待办事项 - 支持过滤"""
        todos = self._repository.get_all(user_id)
        
        if status:
            todos = [todo for todo in todos if todo.status == status]
        
        if priority:
            todos = [todo for todo in todos if todo.priority == priority]
        
        return sorted(todos, key=lambda x: x.created_at, reverse=True)
    
    def mark_completed(self, todo_id: str, user_id: str = None) -> Todo:
        """标记任务完成 - 专门的业务方法"""
        return self.update_todo(todo_id, user_id, status=TodoStatus.COMPLETED)
    
    def get_overdue_todos(self, user_id: str = None) -> List[Todo]:
        """获取过期的待办事项 - 像找出过期的任务"""
        now = datetime.utcnow()
        todos = self._repository.get_all(user_id)
        return [
            todo for todo in todos 
            if todo.due_date and todo.due_date < now and todo.status != TodoStatus.COMPLETED
        ]


# ========================================
# 单元测试类 (Unit Test Classes)
# ========================================

class TestTodoModel:
    """测试Todo模型 - 像检查便签的格式是否正确"""
    
    def test_todo_creation_with_defaults(self):
        """测试使用默认值创建Todo"""
        todo = Todo(id="test-1", title="Test Todo")
        
        assert todo.id == "test-1"
        assert todo.title == "Test Todo"
        assert todo.description is None
        assert todo.priority == Priority.MEDIUM
        assert todo.status == TodoStatus.PENDING
        assert todo.tags == []
        assert isinstance(todo.created_at, datetime)
        assert isinstance(todo.updated_at, datetime)
    
    def test_todo_creation_with_all_fields(self):
        """测试创建包含所有字段的Todo"""
        created_at = datetime.utcnow()
        due_date = datetime.utcnow() + timedelta(days=7)
        
        todo = Todo(
            id="test-2",
            title="Complex Todo",
            description="This is a detailed description",
            priority=Priority.HIGH,
            status=TodoStatus.IN_PROGRESS,
            created_at=created_at,
            due_date=due_date,
            tags=["work", "urgent"],
            user_id="user-123"
        )
        
        assert todo.id == "test-2"
        assert todo.title == "Complex Todo"
        assert todo.description == "This is a detailed description"
        assert todo.priority == Priority.HIGH
        assert todo.status == TodoStatus.IN_PROGRESS
        assert todo.created_at == created_at
        assert todo.due_date == due_date
        assert todo.tags == ["work", "urgent"]
        assert todo.user_id == "user-123"
    
    def test_priority_enum_values(self):
        """测试优先级枚举值"""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.URGENT.value == "urgent"
    
    def test_status_enum_values(self):
        """测试状态枚举值"""
        assert TodoStatus.PENDING.value == "pending"
        assert TodoStatus.IN_PROGRESS.value == "in_progress"
        assert TodoStatus.COMPLETED.value == "completed"
        assert TodoStatus.CANCELLED.value == "cancelled"


class TestTodoRepository:
    """测试Todo数据访问层 - 像测试文件柜的操作"""
    
    @pytest.fixture
    def repository(self):
        """创建测试用的仓库实例"""
        return TodoRepository()
    
    @pytest.fixture
    def sample_todo(self):
        """创建测试用的Todo实例"""
        return Todo(
            id="test-todo-1",
            title="Sample Todo",
            description="This is a sample todo",
            user_id="user-123"
        )
    
    def test_create_todo(self, repository, sample_todo):
        """测试创建待办事项"""
        result = repository.create(sample_todo)
        
        assert result == sample_todo
        assert repository.get_by_id("test-todo-1") == sample_todo
    
    def test_create_duplicate_todo_raises_error(self, repository, sample_todo):
        """测试创建重复ID的待办事项应该抛出错误"""
        repository.create(sample_todo)
        
        with pytest.raises(ValueError, match="already exists"):
            repository.create(sample_todo)
    
    def test_get_by_id_existing_todo(self, repository, sample_todo):
        """测试获取存在的待办事项"""
        repository.create(sample_todo)
        result = repository.get_by_id("test-todo-1")
        
        assert result == sample_todo
    
    def test_get_by_id_nonexistent_todo(self, repository):
        """测试获取不存在的待办事项"""
        result = repository.get_by_id("nonexistent")
        assert result is None
    
    def test_get_all_empty_repository(self, repository):
        """测试空仓库获取所有待办事项"""
        result = repository.get_all()
        assert result == []
    
    def test_get_all_with_todos(self, repository):
        """测试有数据时获取所有待办事项"""
        todo1 = Todo(id="1", title="Todo 1", user_id="user-1")
        todo2 = Todo(id="2", title="Todo 2", user_id="user-2")
        
        repository.create(todo1)
        repository.create(todo2)
        
        result = repository.get_all()
        assert len(result) == 2
        assert todo1 in result
        assert todo2 in result
    
    def test_get_all_filtered_by_user(self, repository):
        """测试按用户过滤获取待办事项"""
        todo1 = Todo(id="1", title="Todo 1", user_id="user-1")
        todo2 = Todo(id="2", title="Todo 2", user_id="user-2")
        todo3 = Todo(id="3", title="Todo 3", user_id="user-1")
        
        repository.create(todo1)
        repository.create(todo2)
        repository.create(todo3)
        
        result = repository.get_all(user_id="user-1")
        assert len(result) == 2
        assert todo1 in result
        assert todo3 in result
        assert todo2 not in result
    
    def test_update_existing_todo(self, repository, sample_todo):
        """测试更新存在的待办事项"""
        repository.create(sample_todo)
        
        # 修改todo
        sample_todo.title = "Updated Title"
        sample_todo.status = TodoStatus.COMPLETED
        
        result = repository.update(sample_todo)
        
        assert result.title == "Updated Title"
        assert result.status == TodoStatus.COMPLETED
        assert isinstance(result.updated_at, datetime)
        
        # 验证仓库中的数据也被更新
        stored_todo = repository.get_by_id(sample_todo.id)
        assert stored_todo.title == "Updated Title"
    
    def test_update_nonexistent_todo_raises_error(self, repository):
        """测试更新不存在的待办事项应该抛出错误"""
        nonexistent_todo = Todo(id="nonexistent", title="Test")
        
        with pytest.raises(ValueError, match="not found"):
            repository.update(nonexistent_todo)
    
    def test_delete_existing_todo(self, repository, sample_todo):
        """测试删除存在的待办事项"""
        repository.create(sample_todo)
        
        result = repository.delete(sample_todo.id)
        
        assert result is True
        assert repository.get_by_id(sample_todo.id) is None
    
    def test_delete_nonexistent_todo(self, repository):
        """测试删除不存在的待办事项"""
        result = repository.delete("nonexistent")
        assert result is False


class TestTodoService:
    """测试Todo业务逻辑层 - 像测试助手的决策能力"""
    
    @pytest.fixture
    def repository(self):
        """创建测试用的仓库实例"""
        return TodoRepository()
    
    @pytest.fixture
    def service(self, repository):
        """创建测试用的服务实例"""
        return TodoService(repository)
    
    @pytest.fixture
    def user_id(self):
        """测试用户ID"""
        return "test-user-123"
    
    # ========================================
    # 创建待办事项测试
    # ========================================
    
    def test_create_todo_with_valid_data(self, service, user_id):
        """测试使用有效数据创建待办事项"""
        todo = service.create_todo(
            title="Test Todo",
            description="Test description",
            priority=Priority.HIGH,
            user_id=user_id
        )
        
        assert todo.title == "Test Todo"
        assert todo.description == "Test description"
        assert todo.priority == Priority.HIGH
        assert todo.user_id == user_id
        assert todo.status == TodoStatus.PENDING
        assert isinstance(todo.id, str)
        assert len(todo.id) > 0
    
    def test_create_todo_with_minimal_data(self, service):
        """测试使用最少数据创建待办事项"""
        todo = service.create_todo(title="Minimal Todo")
        
        assert todo.title == "Minimal Todo"
        assert todo.description is None
        assert todo.priority == Priority.MEDIUM
        assert todo.status == TodoStatus.PENDING
    
    def test_create_todo_with_whitespace_title(self, service):
        """测试标题包含空白字符时的处理"""
        todo = service.create_todo(title="  Trimmed Title  ")
        assert todo.title == "Trimmed Title"
    
    def test_create_todo_with_empty_title_raises_error(self, service):
        """测试空标题应该抛出错误"""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.create_todo(title="")
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.create_todo(title="   ")
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.create_todo(title=None)
    
    def test_create_todo_with_too_long_title_raises_error(self, service):
        """测试过长标题应该抛出错误"""
        long_title = "x" * 201
        
        with pytest.raises(ValueError, match="Title cannot exceed 200 characters"):
            service.create_todo(title=long_title)
    
    def test_create_todo_with_too_long_description_raises_error(self, service):
        """测试过长描述应该抛出错误"""
        long_description = "x" * 1001
        
        with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
            service.create_todo(title="Test", description=long_description)
    
    def test_create_todo_with_past_due_date_raises_error(self, service):
        """测试过去的截止日期应该抛出错误"""
        past_date = datetime.utcnow() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            service.create_todo(title="Test", due_date=past_date)
    
    def test_create_todo_with_future_due_date(self, service):
        """测试未来的截止日期"""
        future_date = datetime.utcnow() + timedelta(days=7)
        
        todo = service.create_todo(title="Test", due_date=future_date)
        assert todo.due_date == future_date
    
    def test_create_todo_with_tags(self, service):
        """测试创建带标签的待办事项"""
        tags = ["work", "urgent", "meeting"]
        
        todo = service.create_todo(title="Test", tags=tags)
        assert todo.tags == tags
    
    # ========================================
    # 获取待办事项测试
    # ========================================
    
    def test_get_todo_existing(self, service, user_id):
        """测试获取存在的待办事项"""
        created_todo = service.create_todo(title="Test", user_id=user_id)
        
        retrieved_todo = service.get_todo(created_todo.id, user_id)
        
        assert retrieved_todo == created_todo
    
    def test_get_todo_nonexistent(self, service, user_id):
        """测试获取不存在的待办事项"""
        result = service.get_todo("nonexistent-id", user_id)
        assert result is None
    
    def test_get_todo_wrong_user(self, service):
        """测试用错误用户ID获取待办事项"""
        created_todo = service.create_todo(title="Test", user_id="user-1")
        
        # 用不同的用户ID尝试获取
        result = service.get_todo(created_todo.id, "user-2")
        assert result is None
    
    def test_get_todo_without_user_id(self, service, user_id):
        """测试不指定用户ID获取待办事项"""
        created_todo = service.create_todo(title="Test", user_id=user_id)
        
        result = service.get_todo(created_todo.id)
        assert result == created_todo
    
    # ========================================
    # 更新待办事项测试
    # ========================================
    
    def test_update_todo_title(self, service, user_id):
        """测试更新待办事项标题"""
        todo = service.create_todo(title="Original", user_id=user_id)
        
        updated_todo = service.update_todo(todo.id, user_id, title="Updated Title")
        
        assert updated_todo.title == "Updated Title"
        assert updated_todo.id == todo.id
        assert updated_todo.updated_at > todo.updated_at
    
    def test_update_todo_multiple_fields(self, service, user_id):
        """测试更新多个字段"""
        todo = service.create_todo(title="Original", user_id=user_id)
        
        updated_todo = service.update_todo(
            todo.id, user_id,
            title="New Title",
            description="New Description",
            priority=Priority.HIGH,
            status=TodoStatus.IN_PROGRESS
        )
        
        assert updated_todo.title == "New Title"
        assert updated_todo.description == "New Description"
        assert updated_todo.priority == Priority.HIGH
        assert updated_todo.status == TodoStatus.IN_PROGRESS
    
    def test_update_todo_nonexistent_raises_error(self, service, user_id):
        """测试更新不存在的待办事项应该抛出错误"""
        with pytest.raises(ValueError, match="Todo not found or access denied"):
            service.update_todo("nonexistent", user_id, title="New Title")
    
    def test_update_todo_wrong_user_raises_error(self, service):
        """测试用错误用户更新待办事项应该抛出错误"""
        todo = service.create_todo(title="Test", user_id="user-1")
        
        with pytest.raises(ValueError, match="Todo not found or access denied"):
            service.update_todo(todo.id, "user-2", title="New Title")
    
    def test_update_todo_with_empty_title_raises_error(self, service, user_id):
        """测试更新为空标题应该抛出错误"""
        todo = service.create_todo(title="Original", user_id=user_id)
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.update_todo(todo.id, user_id, title="")
    
    def test_update_todo_with_invalid_fields(self, service, user_id):
        """测试更新时输入验证"""
        todo = service.create_todo(title="Original", user_id=user_id)
        
        # 测试过长标题
        with pytest.raises(ValueError, match="Title cannot exceed 200 characters"):
            service.update_todo(todo.id, user_id, title="x" * 201)
        
        # 测试过长描述
        with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
            service.update_todo(todo.id, user_id, description="x" * 1001)
        
        # 测试过去的截止日期
        past_date = datetime.utcnow() - timedelta(days=1)
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            service.update_todo(todo.id, user_id, due_date=past_date)
    
    # ========================================
    # 删除待办事项测试
    # ========================================
    
    def test_delete_todo_existing(self, service, user_id):
        """测试删除存在的待办事项"""
        todo = service.create_todo(title="To Delete", user_id=user_id)
        
        result = service.delete_todo(todo.id, user_id)
        
        assert result is True
        assert service.get_todo(todo.id, user_id) is None
    
    def test_delete_todo_nonexistent(self, service, user_id):
        """测试删除不存在的待办事项"""
        result = service.delete_todo("nonexistent", user_id)
        assert result is False
    
    def test_delete_todo_wrong_user(self, service):
        """测试用错误用户删除待办事项"""
        todo = service.create_todo(title="Test", user_id="user-1")
        
        result = service.delete_todo(todo.id, "user-2")
        assert result is False
        
        # 验证原用户仍能访问
        assert service.get_todo(todo.id, "user-1") is not None
    
    # ========================================
    # 获取用户待办事项列表测试
    # ========================================
    
    def test_get_user_todos_empty(self, service, user_id):
        """测试获取空的用户待办事项列表"""
        result = service.get_user_todos(user_id)
        assert result == []
    
    def test_get_user_todos_with_data(self, service, user_id):
        """测试获取有数据的用户待办事项列表"""
        todo1 = service.create_todo(title="Todo 1", user_id=user_id)
        todo2 = service.create_todo(title="Todo 2", user_id=user_id)
        
        # 创建其他用户的待办事项（不应该出现在结果中）
        service.create_todo(title="Other User Todo", user_id="other-user")
        
        result = service.get_user_todos(user_id)
        
        assert len(result) == 2
        assert todo1 in result or todo2 in result
        # 验证按创建时间倒序排列
        assert result[0].created_at >= result[1].created_at
    
    def test_get_user_todos_filtered_by_status(self, service, user_id):
        """测试按状态过滤用户待办事项"""
        todo1 = service.create_todo(title="Pending", user_id=user_id)
        todo2 = service.create_todo(title="In Progress", user_id=user_id)
        service.update_todo(todo2.id, user_id, status=TodoStatus.IN_PROGRESS)
        
        # 测试获取待处理的任务
        pending_todos = service.get_user_todos(user_id, status=TodoStatus.PENDING)
        assert len(pending_todos) == 1
        assert pending_todos[0].id == todo1.id
        
        # 测试获取进行中的任务
        in_progress_todos = service.get_user_todos(user_id, status=TodoStatus.IN_PROGRESS)
        assert len(in_progress_todos) == 1
        assert in_progress_todos[0].id == todo2.id
    
    def test_get_user_todos_filtered_by_priority(self, service, user_id):
        """测试按优先级过滤用户待办事项"""
        todo1 = service.create_todo(title="High Priority", user_id=user_id, priority=Priority.HIGH)
        service.create_todo(title="Medium Priority", user_id=user_id, priority=Priority.MEDIUM)
        
        high_priority_todos = service.get_user_todos(user_id, priority=Priority.HIGH)
        assert len(high_priority_todos) == 1
        assert high_priority_todos[0].id == todo1.id
    
    def test_get_user_todos_filtered_by_status_and_priority(self, service, user_id):
        """测试同时按状态和优先级过滤"""
        # 创建不同组合的待办事项
        todo1 = service.create_todo(title="High Pending", user_id=user_id, priority=Priority.HIGH)
        todo2 = service.create_todo(title="High In Progress", user_id=user_id, priority=Priority.HIGH)
        service.update_todo(todo2.id, user_id, status=TodoStatus.IN_PROGRESS)
        service.create_todo(title="Medium Pending", user_id=user_id, priority=Priority.MEDIUM)
        
        # 测试高优先级且待处理的任务
        filtered_todos = service.get_user_todos(
            user_id, 
            status=TodoStatus.PENDING, 
            priority=Priority.HIGH
        )
        
        assert len(filtered_todos) == 1
        assert filtered_todos[0].id == todo1.id
    
    # ========================================
    # 标记完成测试
    # ========================================
    
    def test_mark_completed(self, service, user_id):
        """测试标记任务完成"""
        todo = service.create_todo(title="To Complete", user_id=user_id)
        
        completed_todo = service.mark_completed(todo.id, user_id)
        
        assert completed_todo.status == TodoStatus.COMPLETED
        assert completed_todo.updated_at > todo.updated_at
    
    def test_mark_completed_nonexistent_raises_error(self, service, user_id):
        """测试标记不存在的任务完成应该抛出错误"""
        with pytest.raises(ValueError, match="Todo not found or access denied"):
            service.mark_completed("nonexistent", user_id)
    
    # ========================================
    # 获取过期任务测试
    # ========================================
    
    def test_get_overdue_todos_empty(self, service, user_id):
        """测试获取空的过期任务列表"""
        result = service.get_overdue_todos(user_id)
        assert result == []
    
    def test_get_overdue_todos_with_overdue_tasks(self, service, user_id):
        """测试获取过期任务"""
        # 创建过期任务
        past_date = datetime.utcnow() - timedelta(days=1)
        overdue_todo = service.create_todo(
            title="Overdue Task", 
            user_id=user_id, 
            due_date=past_date
        )
        
        # 创建未过期任务
        future_date = datetime.utcnow() + timedelta(days=1)
        service.create_todo(
            title="Future Task", 
            user_id=user_id, 
            due_date=future_date
        )
        
        # 创建无截止日期的任务
        service.create_todo(title="No Due Date", user_id=user_id)
        
        result = service.get_overdue_todos(user_id)
        
        assert len(result) == 1
        assert result[0].id == overdue_todo.id
    
    def test_get_overdue_todos_excludes_completed(self, service, user_id):
        """测试过期任务列表不包含已完成的任务"""
        # 创建过期但已完成的任务
        past_date = datetime.utcnow() - timedelta(days=1)
        overdue_todo = service.create_todo(
            title="Overdue but Completed", 
            user_id=user_id, 
            due_date=past_date
        )
        service.mark_completed(overdue_todo.id, user_id)
        
        result = service.get_overdue_todos(user_id)
        assert len(result) == 0
    
    def test_get_overdue_todos_all_users(self, service):
        """测试获取所有用户的过期任务"""
        past_date = datetime.utcnow() - timedelta(days=1)
        
        # 为不同用户创建过期任务
        todo1 = service.create_todo("User 1 Overdue", user_id="user-1", due_date=past_date)
        todo2 = service.create_todo("User 2 Overdue", user_id="user-2", due_date=past_date)
        
        result = service.get_overdue_todos()
        
        assert len(result) == 2
        todo_ids = [todo.id for todo in result]
        assert todo1.id in todo_ids
        assert todo2.id in todo_ids


# ========================================
# 边界条件和错误处理测试
# ========================================

class TestTodoServiceEdgeCases:
    """测试边界条件和特殊情况 - 像测试极端天气下的表现"""
    
    @pytest.fixture
    def service(self):
        return TodoService(TodoRepository())
    
    def test_concurrent_updates_simulation(self, service):
        """模拟并发更新场景"""
        user_id = "user-123"
        todo = service.create_todo(title="Concurrent Test", user_id=user_id)
        
        # 模拟两个并发更新
        updated_todo1 = service.update_todo(todo.id, user_id, title="Update 1")
        updated_todo2 = service.update_todo(todo.id, user_id, title="Update 2")
        
        # 最后的更新应该生效
        assert updated_todo2.title == "Update 2"
        assert updated_todo2.updated_at >= updated_todo1.updated_at
    
    def test_large_dataset_performance(self, service):
        """测试大数据集的性能表现"""
        user_id = "performance-user"
        
        # 创建大量待办事项
        todos = []
        for i in range(100):
            todo = service.create_todo(
                title=f"Performance Test Todo {i}",
                user_id=user_id,
                priority=Priority.HIGH if i % 2 == 0 else Priority.LOW
            )
            todos.append(todo)
        
        # 测试获取所有待办事项的性能
        import time
        start_time = time.time()
        result = service.get_user_todos(user_id)
        end_time = time.time()
        
        assert len(result) == 100
        # 性能要求：100个待办事项的查询应该在100ms内完成
        assert (end_time - start_time) < 0.1
    
    def test_unicode_content_handling(self, service):
        """测试Unicode内容处理"""
        unicode_title = "🚀 项目任务 - 测试Unicode支持 🎯"
        unicode_description = "这是一个包含中文、emoji和特殊字符的描述：∑∏∆∇√∞"
        
        todo = service.create_todo(
            title=unicode_title,
            description=unicode_description
        )
        
        assert todo.title == unicode_title
        assert todo.description == unicode_description
    
    def test_boundary_length_inputs(self, service):
        """测试边界长度输入"""
        # 测试刚好200字符的标题
        title_200_chars = "x" * 200
        todo = service.create_todo(title=title_200_chars)
        assert todo.title == title_200_chars
        
        # 测试刚好1000字符的描述
        description_1000_chars = "y" * 1000
        todo_with_desc = service.create_todo(
            title="Test",
            description=description_1000_chars
        )
        assert todo_with_desc.description == description_1000_chars
    
    def test_special_characters_in_input(self, service):
        """测试输入中的特殊字符"""
        special_chars_title = "Title with \n\t\r and 'quotes' and \"double quotes\""
        
        todo = service.create_todo(title=special_chars_title)
        assert todo.title == special_chars_title
    
    def test_timezone_aware_dates(self, service):
        """测试时区感知的日期处理"""
        from datetime import timezone
        
        # 使用UTC时区的日期
        utc_date = datetime.now(timezone.utc) + timedelta(days=1)
        todo = service.create_todo(title="Timezone Test", due_date=utc_date)
        
        assert todo.due_date == utc_date
    
    def test_memory_usage_with_large_tags(self, service):
        """测试大量标签的内存使用"""
        large_tags = [f"tag-{i}" for i in range(1000)]
        
        todo = service.create_todo(title="Memory Test", tags=large_tags)
        assert len(todo.tags) == 1000
        assert todo.tags == large_tags


# ========================================
# 集成测试场景
# ========================================

class TestTodoServiceIntegrationScenarios:
    """测试完整的业务场景 - 像测试真实的用户工作流"""
    
    @pytest.fixture
    def service(self):
        return TodoService(TodoRepository())
    
    def test_complete_todo_lifecycle(self, service):
        """测试完整的待办事项生命周期"""
        user_id = "lifecycle-user"
        
        # 1. 创建待办事项
        todo = service.create_todo(
            title="Complete Project Documentation",
            description="Write comprehensive API documentation",
            priority=Priority.HIGH,
            user_id=user_id,
            due_date=datetime.utcnow() + timedelta(days=7),
            tags=["documentation", "api", "urgent"]
        )
        
        assert todo.status == TodoStatus.PENDING
        
        # 2. 开始工作
        in_progress_todo = service.update_todo(
            todo.id, user_id, 
            status=TodoStatus.IN_PROGRESS
        )
        
        assert in_progress_todo.status == TodoStatus.IN_PROGRESS
        
        # 3. 更新进度和细节
        updated_todo = service.update_todo(
            todo.id, user_id,
            description="Write comprehensive API documentation - 50% complete",
            tags=["documentation", "api", "urgent", "in-progress"]
        )
        
        assert "in-progress" in updated_todo.tags
        
        # 4. 完成任务
        completed_todo = service.mark_completed(todo.id, user_id)
        
        assert completed_todo.status == TodoStatus.COMPLETED
        
        # 5. 验证在过期任务中不出现
        overdue_todos = service.get_overdue_todos(user_id)
        assert completed_todo not in overdue_todos
    
    def test_multi_user_workspace_simulation(self, service):
        """模拟多用户工作空间场景"""
        # 创建不同用户的待办事项
        alice_todos = []
        bob_todos = []
        
        # Alice的任务
        for i in range(3):
            todo = service.create_todo(
                title=f"Alice Task {i+1}",
                user_id="alice",
                priority=Priority.HIGH if i == 0 else Priority.MEDIUM
            )
            alice_todos.append(todo)
        
        # Bob的任务
        for i in range(2):
            todo = service.create_todo(
                title=f"Bob Task {i+1}",
                user_id="bob",
                priority=Priority.LOW
            )
            bob_todos.append(todo)
        
        # 验证用户隔离
        alice_retrieved = service.get_user_todos("alice")
        bob_retrieved = service.get_user_todos("bob")
        
        assert len(alice_retrieved) == 3
        assert len(bob_retrieved) == 2
        
        # 验证Alice不能访问Bob的任务
        bob_todo = bob_todos[0]
        alice_access = service.get_todo(bob_todo.id, "alice")
        assert alice_access is None
        
        # 验证Bob不能删除Alice的任务
        alice_todo = alice_todos[0]
        bob_delete_result = service.delete_todo(alice_todo.id, "bob")
        assert bob_delete_result is False
    
    def test_project_management_workflow(self, service):
        """测试项目管理工作流场景"""
        project_manager = "pm-001"
        
        # 创建项目相关的待办事项
        project_todos = [
            service.create_todo(
                title="项目启动会议",
                description="召集所有团队成员进行项目启动",
                priority=Priority.URGENT,
                user_id=project_manager,
                due_date=datetime.utcnow() + timedelta(days=1),
                tags=["meeting", "kickoff", "team"]
            ),
            service.create_todo(
                title="需求分析",
                description="收集和分析项目需求",
                priority=Priority.HIGH,
                user_id=project_manager,
                due_date=datetime.utcnow() + timedelta(days=3),
                tags=["analysis", "requirements"]
            ),
            service.create_todo(
                title="技术方案设计",
                description="设计技术架构和实现方案",
                priority=Priority.HIGH,
                user_id=project_manager,
                due_date=datetime.utcnow() + timedelta(days=7),
                tags=["design", "architecture"]
            ),
            service.create_todo(
                title="开发环境搭建",
                description="搭建开发和测试环境",
                priority=Priority.MEDIUM,
                user_id=project_manager,
                due_date=datetime.utcnow() + timedelta(days=5),
                tags=["setup", "environment"]
            )
        ]
        
        # 模拟项目进展
        # 1. 完成启动会议
        service.mark_completed(project_todos[0].id, project_manager)
        
        # 2. 开始需求分析
        service.update_todo(
            project_todos[1].id, project_manager,
            status=TodoStatus.IN_PROGRESS
        )
        
        # 验证项目状态
        all_todos = service.get_user_todos(project_manager)
        completed_todos = service.get_user_todos(project_manager, status=TodoStatus.COMPLETED)
        in_progress_todos = service.get_user_todos(project_manager, status=TodoStatus.IN_PROGRESS)
        pending_todos = service.get_user_todos(project_manager, status=TodoStatus.PENDING)
        
        assert len(all_todos) == 4
        assert len(completed_todos) == 1
        assert len(in_progress_todos) == 1
        assert len(pending_todos) == 2
        
        # 验证高优先级任务
        high_priority_todos = service.get_user_todos(project_manager, priority=Priority.HIGH)
        assert len(high_priority_todos) == 2
    
    def test_deadline_management_scenario(self, service):
        """测试截止日期管理场景"""
        user_id = "deadline-user"
        now = datetime.utcnow()
        
        # 创建不同截止日期的任务
        todos = [
            service.create_todo(
                title="今天截止的紧急任务",
                user_id=user_id,
                due_date=now + timedelta(hours=2),  # 2小时后
                priority=Priority.URGENT
            ),
            service.create_todo(
                title="明天截止的重要任务",
                user_id=user_id,
                due_date=now + timedelta(days=1),
                priority=Priority.HIGH
            ),
            service.create_todo(
                title="下周截止的常规任务",
                user_id=user_id,
                due_date=now + timedelta(days=7),
                priority=Priority.MEDIUM
            ),
            service.create_todo(
                title="已过期的任务",
                user_id=user_id,
                due_date=now - timedelta(days=1),  # 昨天就过期了
                priority=Priority.HIGH
            )
        ]
        
        # 获取过期任务
        overdue_todos = service.get_overdue_todos(user_id)
        assert len(overdue_todos) == 1
        assert overdue_todos[0].title == "已过期的任务"
        
        # 处理过期任务
        service.mark_completed(todos[3].id, user_id)
        
        # 验证过期任务列表更新
        updated_overdue_todos = service.get_overdue_todos(user_id)
        assert len(updated_overdue_todos) == 0


if __name__ == "__main__":
    # 运行测试的示例
    pytest.main([
        __file__,
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误追踪
        "--cov=.",  # 代码覆盖率
        "--cov-report=html",  # HTML覆盖率报告
        "--cov-fail-under=80"  # 要求80%以上覆盖率
    ])
