# 任务管理系统后端架构设计

## 🎯 架构概览

基于 FastAPI 的任务管理系统采用分层架构设计，提供高性能、可扩展的任务管理服务。

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                      │
│                   (FastAPI Application)                     │
├─────────────────────────────────────────────────────────────┤
│                    Middleware Layer                         │
│  认证 │ 权限 │ 日志 │ 限流 │ 监控 │ 缓存 │ 错误处理         │
├─────────────────────────────────────────────────────────────┤
│                     API Router Layer                        │
│   Task │ Project │ Team │ Comment │ File │ Notification     │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                            │
│   业务逻辑处理 │ 数据校验 │ 事务管理 │ 消息发布           │
├─────────────────────────────────────────────────────────────┤
│                   Repository Layer                          │
│   数据访问抽象 │ 查询构建 │ 缓存策略 │ 性能优化           │
├─────────────────────────────────────────────────────────────┤
│                    Database Layer                           │
│        PostgreSQL │ Redis │ Elasticsearch                   │
└─────────────────────────────────────────────────────────────┘
```

## 📋 1. API 路由设计（RESTful接口）

### 1.1 核心资源路由

```python
# 任务管理路由
/api/v1/tasks/
├── GET     /              # 获取任务列表 (支持筛选、搜索、分页)
├── POST    /              # 创建新任务
├── GET     /{task_id}     # 获取任务详情
├── PUT     /{task_id}     # 更新任务
├── DELETE  /{task_id}     # 删除任务
├── PATCH   /{task_id}/status  # 更新任务状态
├── POST    /{task_id}/assign  # 分配任务
├── POST    /{task_id}/comments # 添加评论
├── GET     /{task_id}/history # 获取任务历史
├── POST    /{task_id}/files   # 上传附件
└── GET     /{task_id}/dependencies # 获取任务依赖

# 项目管理路由
/api/v1/projects/
├── GET     /              # 获取项目列表
├── POST    /              # 创建项目
├── GET     /{project_id}  # 获取项目详情
├── PUT     /{project_id}  # 更新项目
├── DELETE  /{project_id}  # 删除项目
├── GET     /{project_id}/tasks    # 获取项目任务
├── GET     /{project_id}/members  # 获取项目成员
├── POST    /{project_id}/members  # 添加项目成员
└── GET     /{project_id}/statistics # 项目统计

# 团队管理路由
/api/v1/teams/
├── GET     /              # 获取团队列表
├── POST    /              # 创建团队
├── GET     /{team_id}     # 获取团队详情
├── PUT     /{team_id}     # 更新团队
├── DELETE  /{team_id}     # 删除团队
├── GET     /{team_id}/members # 获取团队成员
├── POST    /{team_id}/members # 添加团队成员
└── GET     /{team_id}/projects # 获取团队项目

# 通知管理路由
/api/v1/notifications/
├── GET     /              # 获取通知列表
├── POST    /              # 创建通知
├── PUT     /{notification_id}/read # 标记已读
├── DELETE  /{notification_id}      # 删除通知
└── PATCH   /mark-all-read          # 标记全部已读

# 仪表板路由
/api/v1/dashboard/
├── GET     /stats         # 获取统计数据
├── GET     /recent-tasks  # 获取最近任务
├── GET     /workload      # 获取工作负载
└── GET     /timeline      # 获取时间线
```

### 1.2 查询参数标准化

```python
# 列表查询通用参数
class BaseListQuery:
    page: int = 1          # 页码
    size: int = 20         # 每页数量
    sort: str = "created_at"  # 排序字段
    order: str = "desc"    # 排序方向 (asc/desc)
    search: str = None     # 搜索关键词

# 任务查询参数
class TaskListQuery(BaseListQuery):
    status: str = None     # 任务状态筛选
    priority: str = None   # 优先级筛选
    assignee: str = None   # 责任人筛选
    project_id: str = None # 项目筛选
    due_date_from: datetime = None  # 截止日期范围
    due_date_to: datetime = None
    tags: List[str] = []   # 标签筛选
```

## 🏗️ 2. 服务层架构（业务逻辑分层）

### 2.1 服务层结构

```python
# 服务层基础接口
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any

T = TypeVar('T')
CreateSchema = TypeVar('CreateSchema')
UpdateSchema = TypeVar('UpdateSchema')

class BaseService(Generic[T, CreateSchema, UpdateSchema], ABC):
    """服务层基础抽象类"""

    @abstractmethod
    async def create(self, data: CreateSchema, user_id: str) -> T:
        """创建实体"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str, user_id: str) -> Optional[T]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: UpdateSchema, user_id: str) -> T:
        """更新实体"""
        pass

    @abstractmethod
    async def delete(self, entity_id: str, user_id: str) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def list(self, filters: Dict[str, Any], user_id: str) -> List[T]:
        """获取实体列表"""
        pass
```

### 2.2 任务服务实现

```python
# services/task_service.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.models.task import Task
from backend.repositories.task_repository import TaskRepository
from backend.services.notification_service import NotificationService
from backend.services.activity_service import ActivityService

class TaskService(BaseService[Task, TaskCreateSchema, TaskUpdateSchema]):
    """任务管理服务"""

    def __init__(
        self,
        task_repo: TaskRepository,
        notification_service: NotificationService,
        activity_service: ActivityService,
    ):
        self.task_repo = task_repo
        self.notification_service = notification_service
        self.activity_service = activity_service

    async def create(self, data: TaskCreateSchema, user_id: str) -> Task:
        """创建任务"""
        # 1. 数据校验和预处理
        await self._validate_task_data(data, user_id)

        # 2. 创建任务
        task = await self.task_repo.create({
            **data.dict(),
            "created_by": user_id,
            "status": "todo",
        })

        # 3. 发送通知
        if task.assignee_id:
            await self.notification_service.send_task_assigned(
                task_id=str(task.id),
                assignee_id=task.assignee_id,
                created_by=user_id
            )

        # 4. 记录活动
        await self.activity_service.log_activity(
            entity_type="task",
            entity_id=str(task.id),
            action="created",
            user_id=user_id,
            details={"title": task.title}
        )

        return task

    async def update_status(
        self,
        task_id: str,
        new_status: str,
        user_id: str
    ) -> Task:
        """更新任务状态"""
        # 1. 获取当前任务
        task = await self.get_by_id(task_id, user_id)
        if not task:
            raise ValueError("任务不存在")

        old_status = task.status

        # 2. 状态转换校验
        await self._validate_status_transition(old_status, new_status)

        # 3. 更新状态
        task = await self.task_repo.update(task_id, {
            "status": new_status,
            "completed_at": datetime.utcnow() if new_status == "done" else None
        })

        # 4. 发送状态变更通知
        await self.notification_service.send_task_status_changed(
            task_id=task_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=user_id
        )

        # 5. 记录活动
        await self.activity_service.log_activity(
            entity_type="task",
            entity_id=task_id,
            action="status_changed",
            user_id=user_id,
            details={
                "old_status": old_status,
                "new_status": new_status
            }
        )

        return task

    async def assign_task(
        self,
        task_id: str,
        assignee_id: str,
        user_id: str
    ) -> Task:
        """分配任务"""
        # 权限检查
        await self._check_assignment_permission(task_id, user_id)

        # 更新分配
        task = await self.task_repo.update(task_id, {
            "assignee_id": assignee_id,
            "assigned_at": datetime.utcnow(),
            "assigned_by": user_id
        })

        # 发送分配通知
        await self.notification_service.send_task_assigned(
            task_id=task_id,
            assignee_id=assignee_id,
            assigned_by=user_id
        )

        return task

    async def search_tasks(
        self,
        query: str,
        filters: Dict[str, Any],
        user_id: str
    ) -> List[Task]:
        """搜索任务"""
        # 构建搜索条件
        search_filters = {
            **filters,
            "user_access": user_id,  # 确保只搜索用户有权限的任务
        }

        return await self.task_repo.search(query, search_filters)

    async def get_task_dependencies(self, task_id: str, user_id: str) -> Dict[str, List[Task]]:
        """获取任务依赖关系"""
        # 获取前置依赖
        dependencies = await self.task_repo.get_dependencies(task_id)

        # 获取后续依赖
        dependents = await self.task_repo.get_dependents(task_id)

        return {
            "dependencies": dependencies,
            "dependents": dependents
        }

    async def _validate_task_data(self, data: TaskCreateSchema, user_id: str):
        """校验任务数据"""
        # 校验项目权限
        if data.project_id:
            has_permission = await self.task_repo.check_project_permission(
                data.project_id, user_id
            )
            if not has_permission:
                raise ValueError("没有项目权限")

        # 校验分配权限
        if data.assignee_id:
            can_assign = await self.task_repo.check_assignment_permission(
                data.assignee_id, user_id
            )
            if not can_assign:
                raise ValueError("无法分配给指定用户")

    async def _validate_status_transition(self, old_status: str, new_status: str):
        """校验状态转换"""
        valid_transitions = {
            "todo": ["in_progress", "done"],
            "in_progress": ["todo", "done", "blocked"],
            "blocked": ["todo", "in_progress"],
            "done": ["todo", "in_progress"]
        }

        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(f"无效的状态转换: {old_status} -> {new_status}")
```

### 2.3 其他核心服务

```python
# services/project_service.py
class ProjectService(BaseService[Project, ProjectCreateSchema, ProjectUpdateSchema]):
    """项目管理服务"""

    async def create_with_team(
        self,
        data: ProjectCreateSchema,
        team_members: List[str],
        user_id: str
    ) -> Project:
        """创建项目并添加团队成员"""
        pass

    async def get_project_statistics(self, project_id: str, user_id: str) -> Dict:
        """获取项目统计数据"""
        pass

# services/notification_service.py
class NotificationService:
    """通知服务"""

    async def send_task_assigned(self, task_id: str, assignee_id: str, assigned_by: str):
        """发送任务分配通知"""
        pass

    async def send_task_status_changed(
        self,
        task_id: str,
        old_status: str,
        new_status: str,
        changed_by: str
    ):
        """发送任务状态变更通知"""
        pass

# services/activity_service.py
class ActivityService:
    """活动记录服务"""

    async def log_activity(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: str,
        details: Dict[str, Any] = None
    ):
        """记录活动日志"""
        pass
```

## 🗄️ 3. 数据访问层设计（Repository模式）

### 3.1 Repository 基础接口

```python
# repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T], ABC):
    """Repository 基础抽象类"""

    def __init__(self, db: Session, model_class: type[T]):
        self.db = db
        self.model_class = model_class

    async def create(self, data: Dict[str, Any]) -> T:
        """创建记录"""
        instance = self.model_class(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """根据ID获取记录"""
        return await self.db.get(self.model_class, entity_id)

    async def update(self, entity_id: str, data: Dict[str, Any]) -> T:
        """更新记录"""
        instance = await self.get_by_id(entity_id)
        if not instance:
            raise ValueError("记录不存在")

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, entity_id: str) -> bool:
        """删除记录（软删除）"""
        instance = await self.get_by_id(entity_id)
        if instance:
            instance.soft_delete()
            await self.db.commit()
            return True
        return False

    async def list_with_pagination(
        self,
        filters: Dict[str, Any] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """分页查询"""
        query = self._build_query(filters)

        # 总数
        total = await query.count()

        # 排序
        if hasattr(self.model_class, sort_by):
            order_column = getattr(self.model_class, sort_by)
            if sort_order == "desc":
                order_column = order_column.desc()
            query = query.order_by(order_column)

        # 分页
        offset = (page - 1) * size
        items = await query.offset(offset).limit(size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }

    def _build_query(self, filters: Dict[str, Any] = None):
        """构建查询条件"""
        query = self.db.query(self.model_class).filter(
            self.model_class.is_deleted == False
        )

        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    query = query.filter(getattr(self.model_class, key) == value)

        return query
```

### 3.2 任务Repository实现

```python
# repositories/task_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import joinedload, selectinload
from backend.models.task import Task
from backend.models.project import Project
from backend.models.user import User

class TaskRepository(BaseRepository[Task]):
    """任务数据访问类"""

    def __init__(self, db: Session):
        super().__init__(db, Task)

    async def get_by_id_with_relations(self, task_id: str) -> Optional[Task]:
        """获取任务详情（包含关联数据）"""
        return await self.db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.creator),
            selectinload(Task.comments),
            selectinload(Task.attachments),
            selectinload(Task.dependencies),
        ).filter(
            and_(
                Task.id == task_id,
                Task.is_deleted == False
            )
        ).first()

    async def search(self, query: str, filters: Dict[str, Any]) -> List[Task]:
        """全文搜索任务"""
        # 构建基础查询
        base_query = self.db.query(Task).filter(Task.is_deleted == False)

        # 用户权限过滤
        if "user_access" in filters:
            user_id = filters.pop("user_access")
            base_query = base_query.filter(
                or_(
                    Task.created_by == user_id,
                    Task.assignee_id == user_id,
                    Task.project.has(Project.members.any(User.id == user_id))
                )
            )

        # 应用其他过滤条件
        for key, value in filters.items():
            if hasattr(Task, key) and value is not None:
                if isinstance(value, list):
                    base_query = base_query.filter(getattr(Task, key).in_(value))
                else:
                    base_query = base_query.filter(getattr(Task, key) == value)

        # 全文搜索
        if query:
            search_filter = or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%"),
                Task.tags.contains([query])  # JSON数组搜索
            )
            base_query = base_query.filter(search_filter)

        return await base_query.all()

    async def get_user_tasks(
        self,
        user_id: str,
        status: str = None,
        project_id: str = None
    ) -> List[Task]:
        """获取用户相关任务"""
        query = self.db.query(Task).filter(
            and_(
                Task.is_deleted == False,
                or_(
                    Task.created_by == user_id,
                    Task.assignee_id == user_id
                )
            )
        )

        if status:
            query = query.filter(Task.status == status)

        if project_id:
            query = query.filter(Task.project_id == project_id)

        return await query.order_by(Task.updated_at.desc()).all()

    async def get_dependencies(self, task_id: str) -> List[Task]:
        """获取任务依赖"""
        return await self.db.query(Task).join(
            TaskDependency, Task.id == TaskDependency.dependency_id
        ).filter(
            and_(
                TaskDependency.task_id == task_id,
                Task.is_deleted == False
            )
        ).all()

    async def get_dependents(self, task_id: str) -> List[Task]:
        """获取依赖此任务的任务"""
        return await self.db.query(Task).join(
            TaskDependency, Task.id == TaskDependency.task_id
        ).filter(
            and_(
                TaskDependency.dependency_id == task_id,
                Task.is_deleted == False
            )
        ).all()

    async def get_overdue_tasks(self) -> List[Task]:
        """获取逾期任务"""
        from datetime import datetime

        return await self.db.query(Task).filter(
            and_(
                Task.is_deleted == False,
                Task.status.in_(["todo", "in_progress"]),
                Task.due_date < datetime.utcnow()
            )
        ).all()

    async def get_project_task_statistics(self, project_id: str) -> Dict[str, int]:
        """获取项目任务统计"""
        result = await self.db.execute(text("""
            SELECT
                status,
                COUNT(*) as count
            FROM task
            WHERE project_id = :project_id
                AND is_deleted = false
            GROUP BY status
        """), {"project_id": project_id})

        stats = {row.status: row.count for row in result.fetchall()}

        # 确保所有状态都有值
        for status in ["todo", "in_progress", "done", "blocked"]:
            stats.setdefault(status, 0)

        return stats

    async def check_project_permission(self, project_id: str, user_id: str) -> bool:
        """检查用户是否有项目权限"""
        result = await self.db.query(Project).join(
            ProjectMember, Project.id == ProjectMember.project_id
        ).filter(
            and_(
                Project.id == project_id,
                ProjectMember.user_id == user_id,
                Project.is_deleted == False
            )
        ).first()

        return result is not None

    async def check_assignment_permission(self, assignee_id: str, assigner_id: str) -> bool:
        """检查是否可以分配给指定用户"""
        # 简化版：检查用户是否存在且激活
        user = await self.db.query(User).filter(
            and_(
                User.id == assignee_id,
                User.status == "active"
            )
        ).first()

        return user is not None
```

### 3.3 缓存策略

```python
# repositories/cached_task_repository.py
from typing import List, Optional, Dict, Any
import json
from redis import Redis
from backend.repositories.task_repository import TaskRepository

class CachedTaskRepository(TaskRepository):
    """带缓存的任务Repository"""

    def __init__(self, db: Session, redis_client: Redis):
        super().__init__(db)
        self.redis = redis_client
        self.cache_ttl = 300  # 5分钟

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """从缓存获取任务"""
        # 先尝试从缓存获取
        cache_key = f"task:{task_id}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            # 反序列化并重建对象
            task_data = json.loads(cached_data)
            return self._deserialize_task(task_data)

        # 缓存未命中，从数据库获取
        task = await super().get_by_id(task_id)

        if task:
            # 存储到缓存
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(task.to_dict())
            )

        return task

    async def update(self, task_id: str, data: Dict[str, Any]) -> Task:
        """更新任务并清除缓存"""
        # 先清除缓存
        await self.redis.delete(f"task:{task_id}")

        # 更新数据库
        task = await super().update(task_id, data)

        # 更新缓存
        await self.redis.setex(
            f"task:{task_id}",
            self.cache_ttl,
            json.dumps(task.to_dict())
        )

        return task

    async def delete(self, task_id: str) -> bool:
        """删除任务并清除缓存"""
        # 清除缓存
        await self.redis.delete(f"task:{task_id}")

        return await super().delete(task_id)

    def _deserialize_task(self, data: Dict[str, Any]) -> Task:
        """反序列化任务对象"""
        task = Task()
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return task
```

## 🛡️ 4. 中间件设计

### 4.1 认证中间件

```python
# middleware/auth_middleware.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.services.jwt_service import JWTTokenManager

class AuthenticationMiddleware:
    """JWT认证中间件"""

    def __init__(self, jwt_manager: JWTTokenManager):
        self.jwt_manager = jwt_manager
        self.security = HTTPBearer()

    async def __call__(self, request: Request, call_next):
        """中间件处理逻辑"""
        # 跳过认证的路径
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/auth/login"]

        if request.url.path in skip_paths:
            return await call_next(request)

        # 获取Authorization头
        try:
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            token = credentials.credentials
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )

        # 验证Token
        try:
            payload = await self.jwt_manager.decode_token(token)
            request.state.user_id = payload["user_id"]
            request.state.permissions = payload.get("permissions", [])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        return await call_next(request)
```

### 4.2 权限控制中间件

```python
# middleware/permission_middleware.py
from functools import wraps
from fastapi import Request, HTTPException, status
from typing import List, Callable

def require_permissions(required_permissions: List[str]):
    """权限装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # 检查权限
            user_permissions = getattr(request.state, "permissions", [])

            if not all(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

class RoleBasedAccessControl:
    """基于角色的访问控制"""

    ROLE_PERMISSIONS = {
        "admin": ["*"],  # 管理员拥有所有权限
        "project_manager": [
            "project:create", "project:update", "project:delete",
            "task:create", "task:update", "task:assign",
            "team:manage"
        ],
        "developer": [
            "task:create", "task:update", "task:view",
            "project:view"
        ],
        "viewer": [
            "task:view", "project:view"
        ]
    }

    @classmethod
    def get_permissions_for_role(cls, role: str) -> List[str]:
        """获取角色权限"""
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def check_permission(cls, user_permissions: List[str], required: str) -> bool:
        """检查权限"""
        return "*" in user_permissions or required in user_permissions
```

### 4.3 限流中间件

```python
# middleware/rate_limit_middleware.py
import time
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from redis import Redis

class RateLimitMiddleware:
    """API限流中间件"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

        # 不同端点的限流配置
        self.rate_limits = {
            "/api/v1/auth/login": {"requests": 5, "window": 60},  # 登录：1分钟5次
            "/api/v1/tasks": {"requests": 100, "window": 60},     # 任务：1分钟100次
            "default": {"requests": 1000, "window": 60}           # 默认：1分钟1000次
        }

    async def __call__(self, request: Request, call_next):
        """限流检查"""
        # 获取客户端标识（IP + 用户ID）
        client_ip = request.client.host
        user_id = getattr(request.state, "user_id", "anonymous")
        client_key = f"{client_ip}:{user_id}"

        # 获取限流配置
        path = request.url.path
        limit_config = self.rate_limits.get(path, self.rate_limits["default"])

        # 检查限流
        if await self._is_rate_limited(client_key, path, limit_config):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        return await call_next(request)

    async def _is_rate_limited(
        self,
        client_key: str,
        path: str,
        config: Dict[str, int]
    ) -> bool:
        """检查是否超出限流"""
        cache_key = f"rate_limit:{client_key}:{path}"

        # 使用滑动窗口计数器
        current_time = int(time.time())
        window_start = current_time - config["window"]

        # 清理过期记录
        await self.redis.zremrangebyscore(cache_key, 0, window_start)

        # 获取当前窗口内的请求数
        current_requests = await self.redis.zcard(cache_key)

        if current_requests >= config["requests"]:
            return True

        # 记录当前请求
        await self.redis.zadd(cache_key, {str(current_time): current_time})
        await self.redis.expire(cache_key, config["window"])

        return False
```

### 4.4 日志中间件

```python
# middleware/logging_middleware.py
import time
import uuid
import logging
from fastapi import Request
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """请求日志中间件"""

    async def __call__(self, request: Request, call_next):
        """记录请求和响应"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()

        # 构建请求日志
        request_log = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "user_id": getattr(request.state, "user_id", None),
            "timestamp": start_time
        }

        logger.info(f"Request started: {request_log}")

        # 处理请求
        try:
            response = await call_next(request)

            # 记录响应
            duration = time.time() - start_time

            response_log = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": response.headers.get("content-length", 0)
            }

            logger.info(f"Request completed: {response_log}")

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(duration)

            return response

        except Exception as e:
            # 记录异常
            duration = time.time() - start_time

            error_log = {
                "request_id": request_id,
                "error": str(e),
                "duration_ms": round(duration * 1000, 2)
            }

            logger.error(f"Request failed: {error_log}", exc_info=True)
            raise
```

### 4.5 错误处理中间件

```python
# middleware/error_middleware.py
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    """全局错误处理中间件"""

    async def __call__(self, request: Request, call_next):
        """统一错误处理"""
        try:
            return await call_next(request)
        except HTTPException:
            # HTTP异常直接抛出，由FastAPI处理
            raise
        except ValueError as e:
            # 业务逻辑错误
            return self._create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e),
                request=request
            )
        except PermissionError as e:
            # 权限错误
            return self._create_error_response(
                status_code=403,
                error_code="PERMISSION_DENIED",
                message=str(e),
                request=request
            )
        except Exception as e:
            # 未知错误
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=True
            )

            return self._create_error_response(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request=request,
                debug_info=str(e) if request.state.get("debug", False) else None
            )

    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        request: Request,
        debug_info: str = None
    ) -> JSONResponse:
        """创建统一错误响应"""
        content = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": time.time(),
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None)
            }
        }

        if debug_info:
            content["error"]["debug"] = debug_info

        return JSONResponse(
            status_code=status_code,
            content=content
        )
```

## 📊 5. 数据模型设计

### 5.1 任务模型

```python
# models/task.py
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from backend.models.base import BaseModel, AuditMixin

class Task(BaseModel, AuditMixin):
    """任务模型"""
    __tablename__ = "tasks"
    __table_args__ = {'comment': '任务表'}

    # 基本信息
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(
        String(20),
        nullable=False,
        default="todo",
        comment="任务状态: todo, in_progress, done, blocked"
    )
    priority = Column(
        String(10),
        nullable=False,
        default="medium",
        comment="优先级: low, medium, high, urgent"
    )

    # 分配信息
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # 项目关联
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    # 时间信息
    due_date = Column(DateTime(timezone=True), nullable=True, comment="截止日期")
    estimated_hours = Column(Integer, nullable=True, comment="预估工时（小时）")
    actual_hours = Column(Integer, nullable=True, comment="实际工时（小时）")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")

    # 附加信息
    tags = Column(ARRAY(String), nullable=True, comment="标签数组")
    labels = Column(JSONB, nullable=True, comment="标签元数据")
    custom_fields = Column(JSONB, nullable=True, comment="自定义字段")

    # 关联关系
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    assigner = relationship("User", foreign_keys=[assigned_by])
    project = relationship("Project", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")

    # 任务依赖关系
    dependencies = relationship(
        "Task",
        secondary="task_dependencies",
        primaryjoin="Task.id == TaskDependency.task_id",
        secondaryjoin="Task.id == TaskDependency.dependency_id",
        back_populates="dependents"
    )

    dependents = relationship(
        "Task",
        secondary="task_dependencies",
        primaryjoin="Task.id == TaskDependency.dependency_id",
        secondaryjoin="Task.id == TaskDependency.task_id",
        back_populates="dependencies"
    )

class TaskDependency(BaseModel):
    """任务依赖关系"""
    __tablename__ = "task_dependencies"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    dependency_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    dependency_type = Column(String(20), default="blocks", comment="依赖类型")

class TaskComment(BaseModel, AuditMixin):
    """任务评论"""
    __tablename__ = "task_comments"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    content = Column(Text, nullable=False, comment="评论内容")
    is_internal = Column(Boolean, default=False, comment="是否内部评论")

    task = relationship("Task", back_populates="comments")
    author = relationship("User", foreign_keys=[created_by])

class TaskAttachment(BaseModel, AuditMixin):
    """任务附件"""
    __tablename__ = "task_attachments"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    filename = Column(String(255), nullable=False, comment="文件名")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    mime_type = Column(String(100), nullable=True, comment="MIME类型")

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[created_by])
```

### 5.2 项目模型

```python
# models/project.py
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import BaseModel, AuditMixin

class Project(BaseModel, AuditMixin):
    """项目模型"""
    __tablename__ = "projects"
    __table_args__ = {'comment': '项目表'}

    # 基本信息
    name = Column(String(100), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    status = Column(
        String(20),
        nullable=False,
        default="active",
        comment="项目状态: planning, active, on_hold, completed, cancelled"
    )

    # 时间信息
    start_date = Column(DateTime(timezone=True), nullable=True, comment="开始日期")
    end_date = Column(DateTime(timezone=True), nullable=True, comment="结束日期")

    # 团队关联
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)

    # 项目设置
    settings = Column(JSONB, nullable=True, comment="项目设置")
    is_public = Column(Boolean, default=False, comment="是否公开项目")

    # 关联关系
    team = relationship("Team", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(BaseModel):
    """项目成员"""
    __tablename__ = "project_members"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member", comment="角色: owner, admin, member, viewer")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="members")
    user = relationship("User")
```

## 🚀 6. 应用程序入口配置

```python
# main.py - 任务管理系统主应用
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

# 导入路由
from backend.api.routes import tasks, projects, teams, notifications, dashboard
from backend.middleware import (
    AuthenticationMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware
)
from backend.core.database import DatabaseManager
from backend.core.cache import CacheManager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 Starting Task Management System...")

    # 初始化数据库
    database_manager = DatabaseManager()
    await database_manager.initialize()

    # 初始化缓存
    cache_manager = CacheManager()
    await cache_manager.initialize()

    app.state.database = database_manager
    app.state.cache = cache_manager

    yield

    # 关闭时清理
    logger.info("🛑 Shutting down Task Management System...")
    await cache_manager.close()
    await database_manager.close()

# 创建FastAPI应用
app = FastAPI(
    title="Task Management System API",
    description="企业级任务管理系统 - 提供完整的项目和任务管理功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# 添加其他中间件
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.middleware("http")(ErrorHandlingMiddleware())
app.middleware("http")(RequestLoggingMiddleware())
app.middleware("http")(RateLimitMiddleware(app.state.cache.redis))
app.middleware("http")(AuthenticationMiddleware())

# 注册路由
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

# 健康检查
@app.get("/health")
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "service": "task-management-system",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📈 7. 性能优化建议

### 7.1 数据库优化
- **索引策略**: 为常用查询字段添加索引
- **查询优化**: 使用`joinedload`预加载关联数据
- **分页查询**: 使用游标分页处理大数据集
- **读写分离**: 查询操作使用只读副本

### 7.2 缓存策略
- **Redis缓存**: 缓存热点数据和查询结果
- **应用层缓存**: 使用Python的`lru_cache`
- **CDN缓存**: 静态资源使用CDN分发

### 7.3 异步处理
- **消息队列**: 使用Celery处理重任务
- **WebSocket**: 实时通知和协作功能
- **批量操作**: 批量处理数据库操作

## 🔐 8. 安全考虑

### 8.1 认证授权
- **JWT令牌**: 无状态认证
- **刷新令牌**: 令牌轮换机制
- **权限控制**: 基于角色的访问控制

### 8.2 数据安全
- **输入验证**: 所有输入数据校验
- **SQL注入防护**: 使用ORM参数化查询
- **XSS防护**: 输出数据转义
- **HTTPS**: 强制使用SSL/TLS

### 8.3 操作审计
- **活动日志**: 记录所有关键操作
- **数据变更**: 跟踪数据修改历史
- **访问日志**: 记录API访问情况

---

这个架构设计提供了一个完整的、可扩展的任务管理系统后端实现。基于FastAPI的分层架构确保了高性能、易维护和良好的可测试性。通过Repository模式实现了数据访问层的抽象，中间件提供了横切关注点的处理，整体架构遵循了SOLID原则和领域驱动设计的最佳实践。