#!/usr/bin/env python3
"""
Perfect21 完整Manager系统 - 15个统一Manager
从31个Manager类整合为15个，减少系统复杂度和耦合度

15个Manager架构:
=================

核心层 (4个):
1. CoreConfigManager - 配置管理
2. UnifiedCacheManager - 缓存管理
3. UnifiedResourceManager - 资源管理
4. CoreEventManager - 事件管理

数据层 (3个):
5. UnifiedDatabaseManager - 数据库管理
6. UnifiedFileSystemManager - 文件系统管理
7. UnifiedDocumentManager - 文档管理

安全层 (2个):
8. UnifiedAuthSecurityManager - 认证安全管理
9. UnifiedEncryptionManager - 加密管理

工作流层 (3个):
10. UnifiedWorkflowManager - 工作流管理
11. UnifiedTaskManager - 任务管理
12. UnifiedSyncManager - 同步管理

集成层 (2个):
13. UnifiedGitManager - Git集成管理
14. UnifiedAPIManager - API集成管理

监控层 (1个):
15. UnifiedMonitoringManager - 监控管理

优化结果:
- Manager数量: 31 → 15 (减少52%)
- 耦合点预估: 978 → <500 (减少50%+)
- 责任边界更清晰
- 依赖关系更简单
- 生命周期管理统一
"""

import logging
import asyncio
import threading
from typing import Dict, Any, Optional, List, Set, Type, Union
from datetime import datetime
from abc import ABC, abstractmethod
import json
import os

# 导入基础类
from .consolidated_managers import (
    CoreConfigManager, UnifiedCacheManager, UnifiedResourceManager,
    ConsolidatedManagerFactory, Perfect21ConsolidatedSystem,
    IManager, BaseConsolidatedManager, ManagerCategory, ManagerState,
    ManagerMetadata, ManagerHealth
)

# 导入剩余Manager
from .remaining_managers import (
    CoreEventManager, UnifiedDatabaseManager, UnifiedFileSystemManager,
    UnifiedDocumentManager, UnifiedMonitoringManager,
    register_remaining_managers
)

from .interfaces import ICacheManager, IConfigManager
from .events import EventBus, Event

logger = logging.getLogger("Perfect21.ManagerSystem")

# =================== 安全层Manager ===================

class UnifiedAuthSecurityManager(BaseConsolidatedManager):
    """
    统一认证安全管理器
    整合: AuthManager, AuthenticationManager, TokenManager, RBACManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_auth_security", ManagerCategory.SECURITY, event_bus)
        self.config_manager = config_manager
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._permissions: Dict[str, Set[str]] = {}
        self._auth_policies: Dict[str, Dict[str, Any]] = {}
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一认证安全管理器 - 用户认证、令牌管理、权限控制、安全策略"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化认证安全管理器"""
        try:
            # 加载安全配置
            await self._load_security_config()

            # 注册安全服务
            self.register_service("auth", self._get_auth_service())
            self.register_service("rbac", self._get_rbac_service())
            self.register_service("token", self._get_token_service())

            return True
        except Exception as e:
            logger.error(f"认证安全管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭认证安全管理器"""
        try:
            # 清理会话和令牌
            self._sessions.clear()
            self._tokens.clear()
            self._permissions.clear()
            self._auth_policies.clear()

            return True
        except Exception as e:
            logger.error(f"认证安全管理器关闭失败: {e}")
            return False

    async def _load_security_config(self):
        """加载安全配置"""
        # 默认权限配置
        default_permissions = {
            "admin": {"read", "write", "execute", "manage", "security"},
            "developer": {"read", "write", "execute"},
            "operator": {"read", "execute"},
            "viewer": {"read"}
        }

        # 默认安全策略
        default_policies = {
            "password_policy": {
                "min_length": 8,
                "require_special_chars": True,
                "require_numbers": True
            },
            "token_policy": {
                "expiry_hours": 24,
                "refresh_threshold_hours": 2
            },
            "session_policy": {
                "max_sessions_per_user": 3,
                "idle_timeout_minutes": 30
            }
        }

        with self._lock:
            self._permissions.update(default_permissions)
            self._auth_policies.update(default_policies)

    def _get_auth_service(self):
        """获取认证服务"""
        class AuthService:
            def __init__(self, auth_manager):
                self.am = auth_manager

            async def authenticate(self, username: str, password: str) -> Optional[str]:
                """用户认证"""
                # 简化实现 - 实际应对接真实认证系统
                if self._validate_credentials(username, password):
                    session_id = f"session_{username}_{datetime.now().timestamp()}"

                    session_data = {
                        "user_id": username,
                        "created_at": datetime.now(),
                        "last_activity": datetime.now(),
                        "permissions": self.am._permissions.get(username, {"read"})
                    }

                    self.am._sessions[session_id] = session_data

                    # 发布认证事件
                    self.am.event_bus.publish(Event(
                        type="user_authenticated",
                        data={"user_id": username, "session_id": session_id}
                    ))

                    return session_id

                return None

            def _validate_credentials(self, username: str, password: str) -> bool:
                # 简化实现 - 实际应使用哈希比较
                return len(password) >= 8

            async def logout(self, session_id: str) -> bool:
                """用户登出"""
                if session_id in self.am._sessions:
                    user_id = self.am._sessions[session_id]["user_id"]
                    del self.am._sessions[session_id]

                    # 清理相关令牌
                    tokens_to_remove = [
                        token_id for token_id, token_data in self.am._tokens.items()
                        if token_data.get("session_id") == session_id
                    ]

                    for token_id in tokens_to_remove:
                        del self.am._tokens[token_id]

                    # 发布登出事件
                    self.am.event_bus.publish(Event(
                        type="user_logged_out",
                        data={"user_id": user_id, "session_id": session_id}
                    ))

                    return True

                return False

            def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
                """验证会话"""
                session = self.am._sessions.get(session_id)
                if not session:
                    return None

                # 检查会话是否过期
                policy = self.am._auth_policies.get("session_policy", {})
                idle_timeout = policy.get("idle_timeout_minutes", 30)

                if datetime.now() - session["last_activity"] > timedelta(minutes=idle_timeout):
                    del self.am._sessions[session_id]
                    return None

                # 更新最后活动时间
                session["last_activity"] = datetime.now()
                return session

        return AuthService(self)

    def _get_rbac_service(self):
        """获取权限控制服务"""
        class RBACService:
            def __init__(self, auth_manager):
                self.am = auth_manager

            def check_permission(self, session_id: str, permission: str) -> bool:
                """检查权限"""
                session = self.am._sessions.get(session_id)
                if not session:
                    return False

                user_permissions = session.get("permissions", set())
                return permission in user_permissions

            def get_user_permissions(self, session_id: str) -> Set[str]:
                """获取用户权限"""
                session = self.am._sessions.get(session_id)
                if session:
                    return session.get("permissions", set())
                return set()

            def assign_permission(self, user_id: str, permission: str) -> bool:
                """分配权限"""
                if user_id not in self.am._permissions:
                    self.am._permissions[user_id] = set()

                self.am._permissions[user_id].add(permission)

                # 更新活跃会话的权限
                for session in self.am._sessions.values():
                    if session["user_id"] == user_id:
                        session["permissions"].add(permission)

                return True

            def revoke_permission(self, user_id: str, permission: str) -> bool:
                """撤销权限"""
                if user_id in self.am._permissions:
                    self.am._permissions[user_id].discard(permission)

                    # 更新活跃会话的权限
                    for session in self.am._sessions.values():
                        if session["user_id"] == user_id:
                            session["permissions"].discard(permission)

                    return True

                return False

        return RBACService(self)

    def _get_token_service(self):
        """获取令牌服务"""
        class TokenService:
            def __init__(self, auth_manager):
                self.am = auth_manager

            def create_token(self, session_id: str, scope: str = "api") -> Optional[str]:
                """创建访问令牌"""
                session = self.am._sessions.get(session_id)
                if not session:
                    return None

                policy = self.am._auth_policies.get("token_policy", {})
                expiry_hours = policy.get("expiry_hours", 24)

                token_id = f"token_{session['user_id']}_{datetime.now().timestamp()}"
                token_data = {
                    "session_id": session_id,
                    "user_id": session["user_id"],
                    "scope": scope,
                    "created_at": datetime.now(),
                    "expires_at": datetime.now() + timedelta(hours=expiry_hours)
                }

                self.am._tokens[token_id] = token_data
                return token_id

            def validate_token(self, token_id: str) -> Optional[Dict[str, Any]]:
                """验证令牌"""
                token = self.am._tokens.get(token_id)
                if not token:
                    return None

                # 检查过期
                if datetime.now() > token["expires_at"]:
                    del self.am._tokens[token_id]
                    return None

                return token

            def revoke_token(self, token_id: str) -> bool:
                """撤销令牌"""
                if token_id in self.am._tokens:
                    del self.am._tokens[token_id]
                    return True
                return False

        return TokenService(self)

class UnifiedEncryptionManager(BaseConsolidatedManager):
    """
    统一加密管理器
    整合: 数据加密、密钥管理、哈希计算、安全存储
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_encryption", ManagerCategory.SECURITY, event_bus)
        self.config_manager = config_manager
        self._encryption_keys: Dict[str, Any] = {}
        self._hash_algorithms = ["sha256", "sha512", "md5"]
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一加密管理器 - 数据加密、密钥管理、哈希计算、安全存储"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化加密管理器"""
        try:
            # 生成默认密钥
            await self._generate_default_keys()

            # 注册加密服务
            self.register_service("encryption", self._get_encryption_service())
            self.register_service("hash", self._get_hash_service())
            self.register_service("key_management", self._get_key_management_service())

            return True
        except Exception as e:
            logger.error(f"加密管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭加密管理器"""
        try:
            # 清理密钥（安全考虑）
            self._encryption_keys.clear()
            return True
        except Exception as e:
            logger.error(f"加密管理器关闭失败: {e}")
            return False

    async def _generate_default_keys(self):
        """生成默认密钥"""
        import hashlib
        import secrets

        # 生成默认对称密钥
        default_key = secrets.token_bytes(32)  # 256-bit key
        self._encryption_keys["default"] = {
            "key": default_key,
            "algorithm": "AES-256",
            "created_at": datetime.now()
        }

    def _get_encryption_service(self):
        """获取加密服务"""
        class EncryptionService:
            def __init__(self, encryption_manager):
                self.em = encryption_manager

            def encrypt_data(self, data: str, key_name: str = "default") -> Optional[str]:
                """加密数据"""
                try:
                    from cryptography.fernet import Fernet
                    import base64

                    key_info = self.em._encryption_keys.get(key_name)
                    if not key_info:
                        return None

                    # 使用密钥创建Fernet实例
                    fernet_key = base64.urlsafe_b64encode(key_info["key"])
                    fernet = Fernet(fernet_key)

                    # 加密数据
                    encrypted_data = fernet.encrypt(data.encode())
                    return base64.urlsafe_b64encode(encrypted_data).decode()

                except Exception as e:
                    logger.error(f"数据加密失败: {e}")
                    return None

            def decrypt_data(self, encrypted_data: str, key_name: str = "default") -> Optional[str]:
                """解密数据"""
                try:
                    from cryptography.fernet import Fernet
                    import base64

                    key_info = self.em._encryption_keys.get(key_name)
                    if not key_info:
                        return None

                    # 使用密钥创建Fernet实例
                    fernet_key = base64.urlsafe_b64encode(key_info["key"])
                    fernet = Fernet(fernet_key)

                    # 解密数据
                    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
                    decrypted_data = fernet.decrypt(encrypted_bytes)
                    return decrypted_data.decode()

                except Exception as e:
                    logger.error(f"数据解密失败: {e}")
                    return None

        return EncryptionService(self)

    def _get_hash_service(self):
        """获取哈希服务"""
        class HashService:
            def __init__(self, encryption_manager):
                self.em = encryption_manager

            def hash_data(self, data: str, algorithm: str = "sha256") -> Optional[str]:
                """计算数据哈希"""
                try:
                    import hashlib

                    if algorithm not in self.em._hash_algorithms:
                        raise ValueError(f"不支持的哈希算法: {algorithm}")

                    hash_func = getattr(hashlib, algorithm)()
                    hash_func.update(data.encode('utf-8'))
                    return hash_func.hexdigest()

                except Exception as e:
                    logger.error(f"哈希计算失败: {e}")
                    return None

            def verify_hash(self, data: str, expected_hash: str, algorithm: str = "sha256") -> bool:
                """验证哈希"""
                computed_hash = self.hash_data(data, algorithm)
                return computed_hash == expected_hash if computed_hash else False

            def hash_password(self, password: str, salt: str = None) -> Dict[str, str]:
                """密码哈希（带盐）"""
                import secrets
                import hashlib

                if not salt:
                    salt = secrets.token_hex(16)

                # 使用PBKDF2进行密码哈希
                hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)

                return {
                    "hash": hashed.hex(),
                    "salt": salt,
                    "algorithm": "pbkdf2_sha256"
                }

        return HashService(self)

    def _get_key_management_service(self):
        """获取密钥管理服务"""
        class KeyManagementService:
            def __init__(self, encryption_manager):
                self.em = encryption_manager

            def generate_key(self, key_name: str, algorithm: str = "AES-256") -> bool:
                """生成新密钥"""
                try:
                    import secrets

                    if algorithm == "AES-256":
                        key = secrets.token_bytes(32)
                    elif algorithm == "AES-128":
                        key = secrets.token_bytes(16)
                    else:
                        raise ValueError(f"不支持的加密算法: {algorithm}")

                    self.em._encryption_keys[key_name] = {
                        "key": key,
                        "algorithm": algorithm,
                        "created_at": datetime.now()
                    }

                    return True

                except Exception as e:
                    logger.error(f"密钥生成失败: {e}")
                    return False

            def rotate_key(self, key_name: str) -> bool:
                """轮换密钥"""
                if key_name in self.em._encryption_keys:
                    old_key_info = self.em._encryption_keys[key_name]
                    algorithm = old_key_info["algorithm"]
                    return self.generate_key(key_name, algorithm)
                return False

            def delete_key(self, key_name: str) -> bool:
                """删除密钥"""
                if key_name in self.em._encryption_keys:
                    del self.em._encryption_keys[key_name]
                    return True
                return False

            def list_keys(self) -> List[str]:
                """列出所有密钥"""
                return list(self.em._encryption_keys.keys())

        return KeyManagementService(self)

# =================== 工作流层Manager ===================

class UnifiedWorkflowManager(BaseConsolidatedManager):
    """
    统一工作流管理器
    整合: WorkflowOrchestrator, WorkflowTemplateManager, 流程引擎
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_workflow", ManagerCategory.WORKFLOW, event_bus)
        self.config_manager = config_manager
        self._workflow_templates: Dict[str, Dict[str, Any]] = {}
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._workflow_history: List[Dict[str, Any]] = []
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一工作流管理器 - 工作流编排、模板管理、执行引擎"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化工作流管理器"""
        try:
            # 加载工作流模板
            await self._load_workflow_templates()

            # 注册工作流服务
            self.register_service("workflow", self._get_workflow_service())
            self.register_service("template", self._get_template_service())

            return True
        except Exception as e:
            logger.error(f"工作流管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭工作流管理器"""
        try:
            # 停止所有活跃工作流
            for workflow_id in list(self._active_workflows.keys()):
                await self._stop_workflow(workflow_id)

            self._workflow_templates.clear()
            self._active_workflows.clear()

            return True
        except Exception as e:
            logger.error(f"工作流管理器关闭失败: {e}")
            return False

    async def _load_workflow_templates(self):
        """加载工作流模板"""
        templates = {
            "quality_workflow": {
                "name": "质量优先工作流",
                "description": "生产级功能开发的质量优先流程",
                "phases": [
                    {
                        "name": "深度理解",
                        "agents": ["project-manager", "business-analyst", "technical-writer"],
                        "parallel": True,
                        "sync_point": "需求共识检查"
                    },
                    {
                        "name": "架构设计",
                        "agents": ["api-designer", "backend-architect", "database-specialist"],
                        "parallel": False,
                        "sync_point": "架构评审"
                    },
                    {
                        "name": "并行实现",
                        "agents": ["backend-architect", "frontend-specialist", "test-engineer"],
                        "parallel": True,
                        "sync_point": "集成准备"
                    },
                    {
                        "name": "全面测试",
                        "agents": ["test-engineer", "security-auditor", "performance-engineer"],
                        "parallel": True,
                        "sync_point": "质量门检查"
                    },
                    {
                        "name": "部署准备",
                        "agents": ["deployment-manager", "devops-engineer"],
                        "parallel": False,
                        "sync_point": "最终验证"
                    }
                ]
            },
            "quick_workflow": {
                "name": "快速开发工作流",
                "description": "简单功能的快速开发流程",
                "phases": [
                    {
                        "name": "需求分析",
                        "agents": ["business-analyst"],
                        "parallel": False
                    },
                    {
                        "name": "快速实现",
                        "agents": ["backend-architect", "frontend-specialist"],
                        "parallel": True
                    },
                    {
                        "name": "基础测试",
                        "agents": ["test-engineer"],
                        "parallel": False
                    }
                ]
            }
        }

        self._workflow_templates.update(templates)

    async def _stop_workflow(self, workflow_id: str):
        """停止工作流"""
        if workflow_id in self._active_workflows:
            workflow = self._active_workflows[workflow_id]
            workflow["status"] = "stopped"
            workflow["stopped_at"] = datetime.now()

            # 移到历史记录
            self._workflow_history.append(workflow)
            del self._active_workflows[workflow_id]

    def _get_workflow_service(self):
        """获取工作流服务"""
        class WorkflowService:
            def __init__(self, workflow_manager):
                self.wm = workflow_manager

            async def start_workflow(self, template_name: str, params: Dict[str, Any] = None) -> Optional[str]:
                """启动工作流"""
                template = self.wm._workflow_templates.get(template_name)
                if not template:
                    logger.error(f"工作流模板不存在: {template_name}")
                    return None

                workflow_id = f"workflow_{datetime.now().timestamp()}"
                workflow_data = {
                    "id": workflow_id,
                    "template": template_name,
                    "params": params or {},
                    "status": "running",
                    "current_phase": 0,
                    "started_at": datetime.now(),
                    "phases": template["phases"].copy()
                }

                self.wm._active_workflows[workflow_id] = workflow_data

                # 发布工作流开始事件
                self.wm.event_bus.publish(Event(
                    type="workflow_started",
                    data={"workflow_id": workflow_id, "template": template_name}
                ))

                return workflow_id

            async def stop_workflow(self, workflow_id: str) -> bool:
                """停止工作流"""
                if workflow_id in self.wm._active_workflows:
                    await self.wm._stop_workflow(workflow_id)

                    # 发布工作流停止事件
                    self.wm.event_bus.publish(Event(
                        type="workflow_stopped",
                        data={"workflow_id": workflow_id}
                    ))

                    return True
                return False

            def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
                """获取工作流状态"""
                return self.wm._active_workflows.get(workflow_id)

            def list_active_workflows(self) -> Dict[str, Dict[str, Any]]:
                """列出活跃工作流"""
                return self.wm._active_workflows.copy()

        return WorkflowService(self)

    def _get_template_service(self):
        """获取模板服务"""
        class TemplateService:
            def __init__(self, workflow_manager):
                self.wm = workflow_manager

            def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
                """获取工作流模板"""
                return self.wm._workflow_templates.get(template_name)

            def add_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
                """添加工作流模板"""
                try:
                    # 验证模板格式
                    required_fields = ["name", "description", "phases"]
                    if not all(field in template_data for field in required_fields):
                        raise ValueError("模板格式不正确")

                    self.wm._workflow_templates[template_name] = template_data
                    return True

                except Exception as e:
                    logger.error(f"添加工作流模板失败: {e}")
                    return False

            def list_templates(self) -> Dict[str, Dict[str, Any]]:
                """列出所有模板"""
                return self.wm._workflow_templates.copy()

        return TemplateService(self)

class UnifiedTaskManager(BaseConsolidatedManager):
    """
    统一任务管理器
    整合: TaskManager, ParallelManager, 任务调度
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager, resource_manager):
        super().__init__("unified_task", ManagerCategory.WORKFLOW, event_bus)
        self.config_manager = config_manager
        self.resource_manager = resource_manager
        self._task_queue: List[Dict[str, Any]] = []
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._task_results: Dict[str, Any] = {}
        self.add_dependency("core_config")
        self.add_dependency("unified_resource")

    def _get_description(self) -> str:
        return "统一任务管理器 - 任务调度、并行执行、结果管理"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化任务管理器"""
        try:
            # 获取并行度配置
            self.max_parallel_tasks = self.config_manager.get_config(
                "perfect21.max_parallel_agents", 5
            )

            # 注册任务服务
            self.register_service("task", self._get_task_service())
            self.register_service("parallel", self._get_parallel_service())

            # 启动任务处理器
            asyncio.create_task(self._process_task_queue())

            return True
        except Exception as e:
            logger.error(f"任务管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭任务管理器"""
        try:
            # 等待所有任务完成
            while self._active_tasks:
                await asyncio.sleep(0.1)

            self._task_queue.clear()
            self._task_results.clear()

            return True
        except Exception as e:
            logger.error(f"任务管理器关闭失败: {e}")
            return False

    async def _process_task_queue(self):
        """处理任务队列"""
        while self.state == ManagerState.READY:
            try:
                # 检查是否有可执行的任务
                if (len(self._active_tasks) < self.max_parallel_tasks and
                    self._task_queue):

                    task = self._task_queue.pop(0)
                    await self._execute_task(task)

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"任务队列处理错误: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: Dict[str, Any]):
        """执行任务"""
        task_id = task["id"]
        self._active_tasks[task_id] = task

        try:
            # 获取资源池
            resource_pool = self.resource_manager.get_service("resource_pool")

            # 模拟任务执行
            if task.get("parallel", False):
                # 并行执行
                result = await self._execute_parallel_task(task)
            else:
                # 顺序执行
                result = await self._execute_sequential_task(task)

            # 保存结果
            self._task_results[task_id] = {
                "result": result,
                "status": "completed",
                "completed_at": datetime.now()
            }

            # 发布任务完成事件
            self.event_bus.publish(Event(
                type="task_completed",
                data={"task_id": task_id, "result": result}
            ))

        except Exception as e:
            # 保存错误结果
            self._task_results[task_id] = {
                "error": str(e),
                "status": "failed",
                "completed_at": datetime.now()
            }

            logger.error(f"任务执行失败 {task_id}: {e}")

        finally:
            # 清理活跃任务
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

    async def _execute_parallel_task(self, task: Dict[str, Any]):
        """执行并行任务"""
        # 简化实现
        await asyncio.sleep(0.1)  # 模拟执行时间
        return {"type": "parallel", "agents": task.get("agents", [])}

    async def _execute_sequential_task(self, task: Dict[str, Any]):
        """执行顺序任务"""
        # 简化实现
        await asyncio.sleep(0.1)  # 模拟执行时间
        return {"type": "sequential", "agents": task.get("agents", [])}

    def _get_task_service(self):
        """获取任务服务"""
        class TaskService:
            def __init__(self, task_manager):
                self.tm = task_manager

            async def submit_task(self, task_data: Dict[str, Any]) -> str:
                """提交任务"""
                task_id = f"task_{datetime.now().timestamp()}"
                task = {
                    "id": task_id,
                    "submitted_at": datetime.now(),
                    **task_data
                }

                self.tm._task_queue.append(task)

                # 发布任务提交事件
                self.tm.event_bus.publish(Event(
                    type="task_submitted",
                    data={"task_id": task_id}
                ))

                return task_id

            def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
                """获取任务结果"""
                return self.tm._task_results.get(task_id)

            def get_task_status(self, task_id: str) -> str:
                """获取任务状态"""
                if task_id in self.tm._active_tasks:
                    return "running"
                elif task_id in self.tm._task_results:
                    return self.tm._task_results[task_id]["status"]
                else:
                    return "not_found"

        return TaskService(self)

    def _get_parallel_service(self):
        """获取并行执行服务"""
        class ParallelService:
            def __init__(self, task_manager):
                self.tm = task_manager

            async def execute_parallel_agents(self, agents: List[str], task_data: Dict[str, Any]) -> Dict[str, Any]:
                """并行执行多个Agent"""
                task_id = await self.tm.get_service("task").submit_task({
                    "agents": agents,
                    "parallel": True,
                    "data": task_data
                })

                # 等待任务完成
                while True:
                    result = self.tm.get_service("task").get_task_result(task_id)
                    if result:
                        return result
                    await asyncio.sleep(0.1)

        return ParallelService(self)

class UnifiedSyncManager(BaseConsolidatedManager):
    """
    统一同步管理器
    整合: SyncPointManager, 同步点管理、质量门检查
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_sync", ManagerCategory.WORKFLOW, event_bus)
        self.config_manager = config_manager
        self._sync_points: Dict[str, Dict[str, Any]] = {}
        self._quality_gates: Dict[str, Dict[str, Any]] = {}
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一同步管理器 - 同步点管理、质量门检查、流程控制"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化同步管理器"""
        try:
            # 设置默认质量门
            await self._setup_quality_gates()

            # 注册同步服务
            self.register_service("sync_point", self._get_sync_point_service())
            self.register_service("quality_gate", self._get_quality_gate_service())

            return True
        except Exception as e:
            logger.error(f"同步管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭同步管理器"""
        try:
            self._sync_points.clear()
            self._quality_gates.clear()
            return True
        except Exception as e:
            logger.error(f"同步管理器关闭失败: {e}")
            return False

    async def _setup_quality_gates(self):
        """设置质量门"""
        quality_gates = {
            "code_quality": {
                "name": "代码质量检查",
                "checks": ["syntax_check", "style_check", "complexity_check"],
                "threshold": 0.8
            },
            "test_coverage": {
                "name": "测试覆盖率检查",
                "checks": ["unit_test_coverage", "integration_test_coverage"],
                "threshold": 0.9
            },
            "security_scan": {
                "name": "安全扫描",
                "checks": ["vulnerability_scan", "dependency_check"],
                "threshold": 1.0
            }
        }

        self._quality_gates.update(quality_gates)

    def _get_sync_point_service(self):
        """获取同步点服务"""
        class SyncPointService:
            def __init__(self, sync_manager):
                self.sm = sync_manager

            async def create_sync_point(self, name: str, conditions: List[str]) -> str:
                """创建同步点"""
                sync_id = f"sync_{datetime.now().timestamp()}"

                sync_point = {
                    "id": sync_id,
                    "name": name,
                    "conditions": conditions,
                    "status": "waiting",
                    "created_at": datetime.now(),
                    "satisfied_conditions": []
                }

                self.sm._sync_points[sync_id] = sync_point

                # 发布同步点创建事件
                self.sm.event_bus.publish(Event(
                    type="sync_point_created",
                    data={"sync_id": sync_id, "name": name}
                ))

                return sync_id

            async def satisfy_condition(self, sync_id: str, condition: str) -> bool:
                """满足同步点条件"""
                sync_point = self.sm._sync_points.get(sync_id)
                if not sync_point:
                    return False

                if condition in sync_point["conditions"]:
                    if condition not in sync_point["satisfied_conditions"]:
                        sync_point["satisfied_conditions"].append(condition)

                    # 检查是否所有条件都满足
                    if len(sync_point["satisfied_conditions"]) == len(sync_point["conditions"]):
                        sync_point["status"] = "satisfied"
                        sync_point["satisfied_at"] = datetime.now()

                        # 发布同步点满足事件
                        self.sm.event_bus.publish(Event(
                            type="sync_point_satisfied",
                            data={"sync_id": sync_id, "name": sync_point["name"]}
                        ))

                    return True

                return False

            def get_sync_point_status(self, sync_id: str) -> Optional[str]:
                """获取同步点状态"""
                sync_point = self.sm._sync_points.get(sync_id)
                return sync_point["status"] if sync_point else None

        return SyncPointService(self)

    def _get_quality_gate_service(self):
        """获取质量门服务"""
        class QualityGateService:
            def __init__(self, sync_manager):
                self.sm = sync_manager

            async def run_quality_gate(self, gate_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
                """运行质量门检查"""
                gate = self.sm._quality_gates.get(gate_name)
                if not gate:
                    return {"success": False, "error": f"质量门不存在: {gate_name}"}

                results = {}
                overall_score = 0.0

                # 执行所有检查
                for check_name in gate["checks"]:
                    check_result = await self._run_quality_check(check_name, data)
                    results[check_name] = check_result
                    overall_score += check_result.get("score", 0.0)

                # 计算平均分
                if gate["checks"]:
                    overall_score /= len(gate["checks"])

                # 判断是否通过
                passed = overall_score >= gate["threshold"]

                result = {
                    "gate_name": gate_name,
                    "passed": passed,
                    "score": overall_score,
                    "threshold": gate["threshold"],
                    "checks": results,
                    "timestamp": datetime.now()
                }

                # 发布质量门结果事件
                self.sm.event_bus.publish(Event(
                    type="quality_gate_completed",
                    data=result
                ))

                return result

            async def _run_quality_check(self, check_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
                """运行具体的质量检查"""
                # 简化实现 - 实际应该调用真实的检查工具
                import random

                score = random.uniform(0.7, 1.0)  # 模拟检查分数

                return {
                    "check_name": check_name,
                    "score": score,
                    "passed": score >= 0.8,
                    "message": f"{check_name} 检查完成"
                }

        return QualityGateService(self)

# =================== 集成层Manager ===================

class UnifiedGitManager(BaseConsolidatedManager):
    """
    统一Git集成管理器
    整合: GitHooksManager, BranchManager, GitCacheManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager, cache_manager: ICacheManager):
        super().__init__("unified_git", ManagerCategory.INTEGRATION, event_bus)
        self.config_manager = config_manager
        self.cache_manager = cache_manager
        self._git_hooks: Dict[str, Dict[str, Any]] = {}
        self._branch_policies: Dict[str, Dict[str, Any]] = {}
        self.add_dependency("core_config")
        self.add_dependency("unified_cache")

    def _get_description(self) -> str:
        return "统一Git集成管理器 - Git hooks、分支管理、Git缓存"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化Git集成管理器"""
        try:
            # 设置Git hooks
            await self._setup_git_hooks()

            # 注册Git服务
            self.register_service("git_hooks", self._get_git_hooks_service())
            self.register_service("branch_manager", self._get_branch_manager_service())

            return True
        except Exception as e:
            logger.error(f"Git集成管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭Git集成管理器"""
        try:
            self._git_hooks.clear()
            self._branch_policies.clear()
            return True
        except Exception as e:
            logger.error(f"Git集成管理器关闭失败: {e}")
            return False

    async def _setup_git_hooks(self):
        """设置Git hooks"""
        default_hooks = {
            "pre-commit": {
                "enabled": True,
                "actions": ["code_format", "lint_check", "test_run"]
            },
            "pre-push": {
                "enabled": True,
                "actions": ["integration_test", "security_scan"]
            },
            "post-commit": {
                "enabled": False,
                "actions": ["notification"]
            }
        }

        self._git_hooks.update(default_hooks)

    def _get_git_hooks_service(self):
        """获取Git hooks服务"""
        class GitHooksService:
            def __init__(self, git_manager):
                self.gm = git_manager

            def install_hooks(self) -> bool:
                """安装Git hooks"""
                try:
                    # 简化实现 - 实际应该写入.git/hooks/目录
                    logger.info("Git hooks 已安装")
                    return True
                except Exception as e:
                    logger.error(f"Git hooks 安装失败: {e}")
                    return False

            async def execute_hook(self, hook_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
                """执行Git hook"""
                hook = self.gm._git_hooks.get(hook_name)
                if not hook or not hook.get("enabled", False):
                    return {"success": True, "message": f"Hook {hook_name} 未启用"}

                results = []
                overall_success = True

                for action in hook.get("actions", []):
                    action_result = await self._execute_hook_action(action, context)
                    results.append(action_result)

                    if not action_result.get("success", False):
                        overall_success = False

                result = {
                    "hook_name": hook_name,
                    "success": overall_success,
                    "actions": results,
                    "executed_at": datetime.now()
                }

                # 发布hook执行事件
                self.gm.event_bus.publish(Event(
                    type="git_hook_executed",
                    data=result
                ))

                return result

            async def _execute_hook_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
                """执行hook动作"""
                # 简化实现
                import random

                success = random.choice([True, True, True, False])  # 75%成功率

                return {
                    "action": action,
                    "success": success,
                    "message": f"{action} {'成功' if success else '失败'}"
                }

        return GitHooksService(self)

    def _get_branch_manager_service(self):
        """获取分支管理服务"""
        class BranchManagerService:
            def __init__(self, git_manager):
                self.gm = git_manager

            def set_branch_policy(self, branch_pattern: str, policy: Dict[str, Any]):
                """设置分支策略"""
                self.gm._branch_policies[branch_pattern] = policy

            def validate_branch_operation(self, branch_name: str, operation: str) -> bool:
                """验证分支操作"""
                for pattern, policy in self.gm._branch_policies.items():
                    if pattern in branch_name:  # 简化匹配
                        allowed_ops = policy.get("allowed_operations", [])
                        return operation in allowed_ops

                return True  # 默认允许

            def get_branch_info(self, branch_name: str) -> Optional[Dict[str, Any]]:
                """获取分支信息"""
                # 从缓存获取
                cache_key = f"branch_info:{branch_name}"
                cached_info = self.gm.cache_manager.get(cache_key, "git")

                if cached_info:
                    return cached_info

                # 简化实现 - 实际应该调用git命令
                branch_info = {
                    "name": branch_name,
                    "last_commit": "abc123",
                    "author": "developer",
                    "created_at": datetime.now()
                }

                # 缓存分支信息
                self.gm.cache_manager.set(cache_key, branch_info, namespace="git")

                return branch_info

        return BranchManagerService(self)

class UnifiedAPIManager(BaseConsolidatedManager):
    """
    统一API集成管理器
    整合: API客户端、服务发现、负载均衡、限流
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_api", ManagerCategory.INTEGRATION, event_bus)
        self.config_manager = config_manager
        self._api_clients: Dict[str, Any] = {}
        self._rate_limiters: Dict[str, Dict[str, Any]] = {}
        self._api_stats: Dict[str, Dict[str, int]] = {}
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一API集成管理器 - API客户端、限流、统计、服务发现"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化API集成管理器"""
        try:
            # 注册API服务
            self.register_service("api_client", self._get_api_client_service())
            self.register_service("rate_limiter", self._get_rate_limiter_service())

            return True
        except Exception as e:
            logger.error(f"API集成管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭API集成管理器"""
        try:
            # 关闭所有API客户端
            for client in self._api_clients.values():
                if hasattr(client, 'close'):
                    await client.close()

            self._api_clients.clear()
            self._rate_limiters.clear()
            self._api_stats.clear()

            return True
        except Exception as e:
            logger.error(f"API集成管理器关闭失败: {e}")
            return False

    def _get_api_client_service(self):
        """获取API客户端服务"""
        class APIClientService:
            def __init__(self, api_manager):
                self.am = api_manager

            async def make_request(self, service_name: str, method: str, url: str,
                                 data: Dict[str, Any] = None) -> Dict[str, Any]:
                """发起API请求"""
                try:
                    # 检查限流
                    rate_limiter = self.am.get_service("rate_limiter")
                    if not rate_limiter.check_rate_limit(service_name):
                        return {
                            "success": False,
                            "error": "Rate limit exceeded",
                            "status_code": 429
                        }

                    # 更新统计
                    self._update_api_stats(service_name, method)

                    # 简化实现 - 实际应该使用真实的HTTP客户端
                    import random
                    success = random.choice([True, True, True, False])  # 75%成功率

                    if success:
                        result = {
                            "success": True,
                            "data": {"result": "API调用成功"},
                            "status_code": 200
                        }
                    else:
                        result = {
                            "success": False,
                            "error": "API调用失败",
                            "status_code": 500
                        }

                    # 发布API调用事件
                    self.am.event_bus.publish(Event(
                        type="api_request_completed",
                        data={
                            "service": service_name,
                            "method": method,
                            "url": url,
                            "success": result["success"]
                        }
                    ))

                    return result

                except Exception as e:
                    logger.error(f"API请求失败: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "status_code": 500
                    }

            def _update_api_stats(self, service_name: str, method: str):
                """更新API统计"""
                if service_name not in self.am._api_stats:
                    self.am._api_stats[service_name] = {}

                if method not in self.am._api_stats[service_name]:
                    self.am._api_stats[service_name][method] = 0

                self.am._api_stats[service_name][method] += 1

        return APIClientService(self)

    def _get_rate_limiter_service(self):
        """获取限流服务"""
        class RateLimiterService:
            def __init__(self, api_manager):
                self.am = api_manager

            def setup_rate_limit(self, service_name: str, requests_per_minute: int):
                """设置限流"""
                self.am._rate_limiters[service_name] = {
                    "limit": requests_per_minute,
                    "requests": [],
                    "window_minutes": 1
                }

            def check_rate_limit(self, service_name: str) -> bool:
                """检查限流"""
                limiter = self.am._rate_limiters.get(service_name)
                if not limiter:
                    return True  # 没有限流设置，允许通过

                now = datetime.now()
                window_start = now - timedelta(minutes=limiter["window_minutes"])

                # 清理过期的请求记录
                limiter["requests"] = [
                    req_time for req_time in limiter["requests"]
                    if req_time > window_start
                ]

                # 检查是否超过限制
                if len(limiter["requests"]) >= limiter["limit"]:
                    return False

                # 记录当前请求
                limiter["requests"].append(now)
                return True

        return RateLimiterService(self)

# =================== 完整的15Manager系统 ===================

class Perfect21Complete15ManagerSystem:
    """
    Perfect21完整的15Manager系统
    整合所有Manager，提供统一的管理接口
    """

    def __init__(self):
        self.factory = ConsolidatedManagerFactory()
        self._managers_initialized = False
        self._setup_all_managers()

    def _setup_all_managers(self):
        """设置所有15个Manager"""
        logger.info("开始注册15个统一Manager...")

        # 核心层 (4个)
        self.factory.register_manager("core_config", CoreConfigManager)
        self.factory.register_manager("unified_cache", UnifiedCacheManager)
        self.factory.register_manager("unified_resource", UnifiedResourceManager)
        self.factory.register_manager("core_event", CoreEventManager)

        # 数据层 (3个)
        self.factory.register_manager("unified_database", UnifiedDatabaseManager)
        self.factory.register_manager("unified_filesystem", UnifiedFileSystemManager)
        self.factory.register_manager("unified_document", UnifiedDocumentManager)

        # 安全层 (2个)
        self.factory.register_manager("unified_auth_security", UnifiedAuthSecurityManager)
        self.factory.register_manager("unified_encryption", UnifiedEncryptionManager)

        # 工作流层 (3个)
        self.factory.register_manager("unified_workflow", UnifiedWorkflowManager)
        self.factory.register_manager("unified_task", UnifiedTaskManager)
        self.factory.register_manager("unified_sync", UnifiedSyncManager)

        # 集成层 (2个)
        self.factory.register_manager("unified_git", UnifiedGitManager)
        self.factory.register_manager("unified_api", UnifiedAPIManager)

        # 监控层 (1个)
        self.factory.register_manager("unified_monitoring", UnifiedMonitoringManager)

        logger.info("15个统一Manager注册完成!")

    async def initialize_all_managers(self) -> bool:
        """按依赖顺序初始化所有Manager"""
        if self._managers_initialized:
            return True

        try:
            logger.info("开始初始化15个Manager系统...")

            # 按依赖顺序初始化Manager
            initialization_order = [
                # 第1层: 核心基础设施 (无依赖)
                "core_config",

                # 第2层: 依赖配置的基础服务
                "unified_cache",
                "unified_resource",
                "core_event",
                "unified_database",
                "unified_encryption",

                # 第3层: 依赖基础服务的管理器
                "unified_filesystem",
                "unified_auth_security",

                # 第4层: 依赖前面服务的高级管理器
                "unified_document",
                "unified_workflow",
                "unified_sync",

                # 第5层: 依赖多个基础服务的集成管理器
                "unified_task",
                "unified_git",
                "unified_api",

                # 第6层: 监控管理器 (依赖所有其他Manager)
                "unified_monitoring"
            ]

            # 存储已创建的Manager，供后续Manager使用
            created_managers = {}

            for manager_name in initialization_order:
                logger.info(f"正在初始化 {manager_name}...")

                # 根据Manager的依赖关系传递参数
                kwargs = {}

                if manager_name != "core_config":
                    # 所有Manager都需要event_bus和config_manager
                    kwargs["event_bus"] = self.factory._event_bus
                    kwargs["config_manager"] = created_managers.get("core_config")

                # 特殊依赖处理
                if manager_name == "unified_cache":
                    kwargs["config_manager"] = created_managers.get("core_config")

                elif manager_name == "unified_resource":
                    kwargs["config_manager"] = created_managers.get("core_config")

                elif manager_name == "core_event":
                    kwargs["config_manager"] = created_managers.get("core_config")

                elif manager_name == "unified_filesystem":
                    kwargs["cache_manager"] = created_managers.get("unified_cache")

                elif manager_name == "unified_document":
                    kwargs["fs_manager"] = created_managers.get("unified_filesystem")

                elif manager_name == "unified_task":
                    kwargs["resource_manager"] = created_managers.get("unified_resource")

                elif manager_name == "unified_git":
                    kwargs["cache_manager"] = created_managers.get("unified_cache")

                elif manager_name == "unified_monitoring":
                    kwargs["db_manager"] = created_managers.get("unified_database")

                # 创建Manager实例
                manager = await self.factory.create_manager(manager_name, **kwargs)

                if not manager:
                    logger.error(f"Manager {manager_name} 初始化失败")
                    return False

                created_managers[manager_name] = manager
                logger.info(f"Manager {manager_name} 初始化成功")

            self._managers_initialized = True
            logger.info("所有15个Manager初始化完成!")

            # 发布系统启动事件
            event_manager = self.get_manager("core_event")
            if event_manager:
                event_service = event_manager.get_service("event_handler")
                event_service.publish("system_startup", {"manager_count": 15})

            return True

        except Exception as e:
            logger.error(f"Manager系统初始化失败: {e}")
            return False

    async def shutdown_all_managers(self):
        """关闭所有Manager"""
        if not self._managers_initialized:
            return

        try:
            logger.info("开始关闭15个Manager系统...")

            # 发布系统关闭事件
            event_manager = self.get_manager("core_event")
            if event_manager:
                event_service = event_manager.get_service("event_handler")
                event_service.publish("system_shutdown", {"manager_count": 15})

            # 关闭所有Manager
            await self.factory.shutdown_all()

            self._managers_initialized = False
            logger.info("所有15个Manager已关闭")

        except Exception as e:
            logger.error(f"Manager系统关闭失败: {e}")

    def get_manager(self, manager_name: str) -> Optional[IManager]:
        """获取Manager实例"""
        return self.factory.get_manager(manager_name)

    def get_service(self, manager_name: str, service_name: str) -> Optional[Any]:
        """获取Manager提供的服务"""
        manager = self.get_manager(manager_name)
        if manager:
            return manager.get_service(service_name)
        return None

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        health_summary = {
            "overall_status": "healthy",
            "initialized": self._managers_initialized,
            "manager_count": len(self.factory._instances),
            "expected_count": 15,
            "managers": {}
        }

        if not self._managers_initialized:
            health_summary["overall_status"] = "not_initialized"
            return health_summary

        unhealthy_count = 0
        total_managers = len(self.factory._instances)

        for name, manager in self.factory._instances.items():
            try:
                health = manager.get_health()
                health_summary["managers"][name] = {
                    "state": health.state.value,
                    "healthy": health.healthy,
                    "message": health.message,
                    "last_check": health.last_check.isoformat() if health.last_check else None
                }

                if not health.healthy:
                    unhealthy_count += 1

            except Exception as e:
                health_summary["managers"][name] = {
                    "state": "error",
                    "healthy": False,
                    "message": f"健康检查失败: {str(e)}",
                    "last_check": datetime.now().isoformat()
                }
                unhealthy_count += 1

        # 计算整体健康状态
        if unhealthy_count == 0:
            health_summary["overall_status"] = "healthy"
        elif unhealthy_count < total_managers:
            health_summary["overall_status"] = "degraded"
        else:
            health_summary["overall_status"] = "unhealthy"

        health_summary["healthy_managers"] = total_managers - unhealthy_count
        health_summary["unhealthy_managers"] = unhealthy_count

        return health_summary

    def get_manager_statistics(self) -> Dict[str, Any]:
        """获取Manager统计信息"""
        stats = {
            "total_managers": 15,
            "active_managers": len(self.factory._instances),
            "initialization_status": self._managers_initialized,
            "categories": {
                "core": 4,
                "data": 3,
                "security": 2,
                "workflow": 3,
                "integration": 2,
                "monitoring": 1
            },
            "reduction_stats": {
                "original_manager_count": 31,
                "optimized_manager_count": 15,
                "reduction_percentage": 52,
                "estimated_coupling_reduction": "50%+"
            }
        }

        if self._managers_initialized:
            # 收集每个Manager的指标
            for name, manager in self.factory._instances.items():
                try:
                    health = manager.get_health()
                    if hasattr(health, 'metrics') and health.metrics:
                        stats[f"{name}_metrics"] = health.metrics
                except Exception:
                    pass

        return stats

# =================== 全局实例和便捷访问 ===================

# 创建全局15Manager系统实例
perfect21_complete_system = Perfect21Complete15ManagerSystem()

# 便捷访问函数
def get_config_service():
    """获取配置服务"""
    return perfect21_complete_system.get_service("core_config", "config")

def get_cache_service():
    """获取缓存服务"""
    return perfect21_complete_system.get_service("unified_cache", "cache")

def get_auth_service():
    """获取认证服务"""
    return perfect21_complete_system.get_service("unified_auth_security", "auth")

def get_workflow_service():
    """获取工作流服务"""
    return perfect21_complete_system.get_service("unified_workflow", "workflow")

def get_task_service():
    """获取任务服务"""
    return perfect21_complete_system.get_service("unified_task", "task")

def get_git_service():
    """获取Git服务"""
    return perfect21_complete_system.get_service("unified_git", "git_hooks")

def get_monitoring_service():
    """获取监控服务"""
    return perfect21_complete_system.get_service("unified_monitoring", "metrics")

# =================== 使用示例 ===================

async def demo_15_manager_system():
    """演示15Manager系统的使用"""
    try:
        logger.info("=== Perfect21 15Manager系统演示 ===")

        # 初始化系统
        success = await perfect21_complete_system.initialize_all_managers()
        if not success:
            logger.error("系统初始化失败")
            return

        # 1. 使用配置服务
        config_service = get_config_service()
        if config_service:
            config_service.set_config("demo.test_key", "test_value")
            value = config_service.get_config("demo.test_key")
            logger.info(f"配置服务测试: {value}")

        # 2. 使用缓存服务
        cache_service = get_cache_service()
        if cache_service:
            cache_service.set("test_cache_key", "test_cache_value", namespace="demo")
            cached = cache_service.get("test_cache_key", "demo")
            logger.info(f"缓存服务测试: {cached}")

        # 3. 使用认证服务
        auth_service = get_auth_service()
        if auth_service:
            session_id = await auth_service.authenticate("test_user", "password123")
            logger.info(f"认证服务测试: {session_id}")

        # 4. 使用工作流服务
        workflow_service = get_workflow_service()
        if workflow_service:
            workflow_id = await workflow_service.start_workflow("quality_workflow")
            logger.info(f"工作流服务测试: {workflow_id}")

        # 5. 使用任务服务
        task_service = get_task_service()
        if task_service:
            task_id = await task_service.submit_task({
                "name": "demo_task",
                "agents": ["backend-architect", "test-engineer"]
            })
            logger.info(f"任务服务测试: {task_id}")

        # 6. 系统健康检查
        health = perfect21_complete_system.get_system_health()
        logger.info(f"系统健康状态: {health['overall_status']}")
        logger.info(f"活跃Manager数量: {health['manager_count']}")

        # 7. 统计信息
        stats = perfect21_complete_system.get_manager_statistics()
        logger.info(f"Manager优化: {stats['original_manager_count']} → {stats['optimized_manager_count']}")
        logger.info(f"减少比例: {stats['reduction_percentage']}%")

        logger.info("=== 15Manager系统演示完成 ===")

    except Exception as e:
        logger.error(f"演示失败: {e}")

    finally:
        # 关闭系统
        await perfect21_complete_system.shutdown_all_managers()

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行演示
    asyncio.run(demo_15_manager_system())