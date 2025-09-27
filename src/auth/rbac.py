"""
RBAC (Role-Based Access Control) 角色权限管理系统
实现角色定义、权限分配、权限检查等功能
支持层级角色和动态权限管理
"""

from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from enum import Enum


class Permission:
    """权限类"""

    def __init__(
        self,
        name: str,
        resource: str,
        action: str,
        description: str = "",
        conditions: Dict[str, Any] = None,
    ):
        """
        初始化权限

        Args:
            name: 权限名称
            resource: 资源名称 (如: users, posts, files)
            action: 操作名称 (如: create, read, update, delete)
            description: 权限描述
            conditions: 权限条件 (如: own_only=True 表示只能操作自己的资源)
        """
        self.name = name
        self.resource = resource
        self.action = action
        self.description = description
        self.conditions = conditions or {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat(),
        }

    def __str__(self):
        return f"{self.resource}:{self.action}"

    def __hash__(self):
        return hash(f"{self.resource}:{self.action}")

    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return self.resource == other.resource and self.action == other.action


class Role:
    """角色类"""

    def __init__(
        self,
        name: str,
        description: str = "",
        permissions: List[Permission] = None,
        parent_roles: List[str] = None,
        is_system_role: bool = False,
    ):
        """
        初始化角色

        Args:
            name: 角色名称
            description: 角色描述
            permissions: 权限列表
            parent_roles: 父角色列表（继承权限）
            is_system_role: 是否为系统角色（不可删除）
        """
        self.name = name
        self.description = description
        self.permissions = set(permissions or [])
        self.parent_roles = parent_roles or []
        self.is_system_role = is_system_role
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_permission(self, permission: Permission):
        """添加权限"""
        self.permissions.add(permission)
        self.updated_at = datetime.utcnow()

    def remove_permission(self, permission: Permission):
        """移除权限"""
        self.permissions.discard(permission)
        self.updated_at = datetime.utcnow()

    def has_permission(self, permission: Permission) -> bool:
        """检查是否有指定权限"""
        return permission in self.permissions

    def has_permission_by_name(self, resource: str, action: str) -> bool:
        """根据资源和操作检查权限"""
        for perm in self.permissions:
            if perm.resource == resource and perm.action == action:
                return True
        return False

    def get_all_permissions(self, rbac_manager=None) -> Set[Permission]:
        """获取所有权限（包括继承的权限）"""
        all_permissions = self.permissions.copy()

        if rbac_manager:
            for parent_role_name in self.parent_roles:
                parent_role = rbac_manager.get_role(parent_role_name)
                if parent_role:
                    all_permissions.update(
                        parent_role.get_all_permissions(rbac_manager)
                    )

        return all_permissions

    def to_dict(self, include_inherited=False, rbac_manager=None) -> Dict[str, Any]:
        """转换为字典格式"""
        permissions_list = (
            list(self.permissions)
            if not include_inherited
            else list(self.get_all_permissions(rbac_manager))
        )

        return {
            "name": self.name,
            "description": self.description,
            "permissions": [perm.to_dict() for perm in permissions_list],
            "parent_roles": self.parent_roles,
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RBACManager:
    """RBAC管理器"""

    def __init__(self):
        self.permissions = {}  # name -> Permission
        self.roles = {}  # name -> Role
        self.user_roles = {}  # user_id -> List[role_name]

        # 初始化默认权限和角色
        self._initialize_default_permissions()
        self._initialize_default_roles()

    def _initialize_default_permissions(self):
        """初始化默认权限"""
        default_permissions = [
            # 用户管理权限
            Permission("user.create", "user", "create", "创建用户"),
            Permission("user.read", "user", "read", "查看用户信息"),
            Permission("user.update", "user", "update", "更新用户信息"),
            Permission("user.delete", "user", "delete", "删除用户"),
            Permission("user.list", "user", "list", "列出用户"),
            Permission(
                "user.self_update", "user", "update", "更新自己的信息", {"own_only": True}
            ),
            # 角色管理权限
            Permission("role.create", "role", "create", "创建角色"),
            Permission("role.read", "role", "read", "查看角色"),
            Permission("role.update", "role", "update", "更新角色"),
            Permission("role.delete", "role", "delete", "删除角色"),
            Permission("role.assign", "role", "assign", "分配角色"),
            # 权限管理权限
            Permission("permission.create", "permission", "create", "创建权限"),
            Permission("permission.read", "permission", "read", "查看权限"),
            Permission("permission.update", "permission", "update", "更新权限"),
            Permission("permission.delete", "permission", "delete", "删除权限"),
            # 系统管理权限
            Permission("system.admin", "system", "admin", "系统管理"),
            Permission("system.monitor", "system", "monitor", "系统监控"),
            Permission("system.config", "system", "config", "系统配置"),
            # 文件管理权限
            Permission("file.upload", "file", "upload", "上传文件"),
            Permission("file.download", "file", "download", "下载文件"),
            Permission("file.delete", "file", "delete", "删除文件"),
            # API访问权限
            Permission("api.access", "api", "access", "API访问"),
            Permission("api.admin", "api", "admin", "API管理"),
        ]

        for perm in default_permissions:
            self.permissions[perm.name] = perm

    def _initialize_default_roles(self):
        """初始化默认角色"""
        # 超级管理员 - 拥有所有权限
        super_admin = Role(
            "super_admin",
            "超级管理员 - 拥有所有系统权限",
            list(self.permissions.values()),
            is_system_role=True,
        )

        # 管理员 - 除系统管理外的所有权限
        admin_permissions = [
            perm for perm in self.permissions.values() if not perm.resource == "system"
        ]
        admin = Role("admin", "管理员 - 用户和内容管理权限", admin_permissions, is_system_role=True)

        # 用户管理员 - 只有用户管理权限
        user_admin_permissions = [
            perm for perm in self.permissions.values() if perm.resource == "user"
        ]
        user_admin = Role(
            "user_admin", "用户管理员 - 用户管理权限", user_admin_permissions, is_system_role=True
        )

        # 普通用户 - 基本权限
        user_permissions = [
            self.permissions["user.read"],
            self.permissions["user.self_update"],
            self.permissions["file.upload"],
            self.permissions["file.download"],
            self.permissions["api.access"],
        ]
        user = Role("user", "普通用户 - 基本操作权限", user_permissions, is_system_role=True)

        # 访客 - 最低权限
        guest_permissions = [
            self.permissions["user.read"],
            self.permissions["api.access"],
        ]
        guest = Role("guest", "访客 - 只读权限", guest_permissions, is_system_role=True)

        # 存储角色
        roles = [super_admin, admin, user_admin, user, guest]
        for role in roles:
            self.roles[role.name] = role

    def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: str = "",
        conditions: Dict[str, Any] = None,
    ) -> Permission:
        """
        创建权限

        Args:
            name: 权限名称
            resource: 资源名称
            action: 操作名称
            description: 权限描述
            conditions: 权限条件

        Returns:
            Permission: 创建的权限对象
        """
        if name in self.permissions:
            raise ValueError(f"权限 '{name}' 已存在")

        permission = Permission(name, resource, action, description, conditions)
        self.permissions[name] = permission
        return permission

    def get_permission(self, name: str) -> Optional[Permission]:
        """获取权限"""
        return self.permissions.get(name)

    def list_permissions(self, resource: str = None) -> List[Permission]:
        """列出权限"""
        if resource:
            return [
                perm for perm in self.permissions.values() if perm.resource == resource
            ]
        return list(self.permissions.values())

    def delete_permission(self, name: str) -> bool:
        """删除权限"""
        if name not in self.permissions:
            return False

        permission = self.permissions[name]

        # 从所有角色中移除此权限
        for role in self.roles.values():
            role.remove_permission(permission)

        del self.permissions[name]
        return True

    def create_role(
        self,
        name: str,
        description: str = "",
        permission_names: List[str] = None,
        parent_roles: List[str] = None,
    ) -> Role:
        """
        创建角色

        Args:
            name: 角色名称
            description: 角色描述
            permission_names: 权限名称列表
            parent_roles: 父角色列表

        Returns:
            Role: 创建的角色对象
        """
        if name in self.roles:
            raise ValueError(f"角色 '{name}' 已存在")

        permissions = []
        if permission_names:
            for perm_name in permission_names:
                if perm_name in self.permissions:
                    permissions.append(self.permissions[perm_name])

        role = Role(name, description, permissions, parent_roles)
        self.roles[name] = role
        return role

    def get_role(self, name: str) -> Optional[Role]:
        """获取角色"""
        return self.roles.get(name)

    def list_roles(self) -> List[Role]:
        """列出所有角色"""
        return list(self.roles.values())

    def update_role(
        self,
        name: str,
        description: str = None,
        permission_names: List[str] = None,
        parent_roles: List[str] = None,
    ) -> bool:
        """
        更新角色

        Args:
            name: 角色名称
            description: 新的描述
            permission_names: 新的权限列表
            parent_roles: 新的父角色列表

        Returns:
            bool: 更新成功返回True
        """
        role = self.roles.get(name)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError(f"系统角色 '{name}' 不能修改")

        if description is not None:
            role.description = description

        if permission_names is not None:
            new_permissions = set()
            for perm_name in permission_names:
                if perm_name in self.permissions:
                    new_permissions.add(self.permissions[perm_name])
            role.permissions = new_permissions

        if parent_roles is not None:
            role.parent_roles = parent_roles

        role.updated_at = datetime.utcnow()
        return True

    def delete_role(self, name: str) -> bool:
        """删除角色"""
        role = self.roles.get(name)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError(f"系统角色 '{name}' 不能删除")

        # 移除所有用户的此角色
        for user_id, user_roles in self.user_roles.items():
            if name in user_roles:
                user_roles.remove(name)

        del self.roles[name]
        return True

    def assign_role_to_user(self, user_id: int, role_name: str) -> bool:
        """为用户分配角色"""
        if role_name not in self.roles:
            return False

        if user_id not in self.user_roles:
            self.user_roles[user_id] = []

        if role_name not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_name)

        return True

    def remove_role_from_user(self, user_id: int, role_name: str) -> bool:
        """移除用户角色"""
        if user_id not in self.user_roles:
            return False

        if role_name in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_name)
            return True

        return False

    def get_user_roles(self, user_id: int) -> List[Role]:
        """获取用户角色"""
        role_names = self.user_roles.get(user_id, [])
        return [self.roles[name] for name in role_names if name in self.roles]

    def get_user_permissions(self, user_id: int) -> Set[Permission]:
        """获取用户所有权限（包括继承的权限）"""
        all_permissions = set()
        user_roles = self.get_user_roles(user_id)

        for role in user_roles:
            all_permissions.update(role.get_all_permissions(self))

        return all_permissions

    def check_permission(
        self, user_id: int, resource: str, action: str, context: Dict[str, Any] = None
    ) -> bool:
        """
        检查用户权限

        Args:
            user_id: 用户ID
            resource: 资源名称
            action: 操作名称
            context: 上下文信息（用于条件权限检查）

        Returns:
            bool: 有权限返回True
        """
        user_permissions = self.get_user_permissions(user_id)

        for permission in user_permissions:
            if permission.resource == resource and permission.action == action:
                # 检查权限条件
                if self._check_permission_conditions(permission, user_id, context):
                    return True

        return False

    def _check_permission_conditions(
        self, permission: Permission, user_id: int, context: Dict[str, Any] = None
    ) -> bool:
        """检查权限条件"""
        if not permission.conditions:
            return True

        context = context or {}

        # 检查 own_only 条件
        if permission.conditions.get("own_only", False):
            resource_owner_id = context.get("owner_id")
            if resource_owner_id != user_id:
                return False

        # 可以添加更多条件检查逻辑

        return True

    def get_role_hierarchy(self) -> Dict[str, List[str]]:
        """获取角色层级关系"""
        hierarchy = {}
        for role_name, role in self.roles.items():
            hierarchy[role_name] = role.parent_roles
        return hierarchy

    def export_rbac_config(self) -> Dict[str, Any]:
        """导出RBAC配置"""
        return {
            "permissions": {
                name: perm.to_dict() for name, perm in self.permissions.items()
            },
            "roles": {name: role.to_dict() for name, role in self.roles.items()},
            "user_roles": self.user_roles,
            "exported_at": datetime.utcnow().isoformat(),
        }

    def import_rbac_config(self, config: Dict[str, Any]) -> bool:
        """导入RBAC配置"""
        try:
            # 导入权限
            for perm_name, perm_data in config.get("permissions", {}).items():
                permission = Permission(
                    perm_data["name"],
                    perm_data["resource"],
                    perm_data["action"],
                    perm_data.get("description", ""),
                    perm_data.get("conditions", {}),
                )
                self.permissions[perm_name] = permission

            # 导入角色
            for role_name, role_data in config.get("roles", {}).items():
                permissions = []
                for perm_data in role_data.get("permissions", []):
                    perm_name = perm_data["name"]
                    if perm_name in self.permissions:
                        permissions.append(self.permissions[perm_name])

                role = Role(
                    role_data["name"],
                    role_data.get("description", ""),
                    permissions,
                    role_data.get("parent_roles", []),
                    role_data.get("is_system_role", False),
                )
                self.roles[role_name] = role

            # 导入用户角色关系
            self.user_roles.update(config.get("user_roles", {}))

            return True

        except Exception:
            return False


# 全局RBAC管理器实例
rbac_manager = RBACManager()


# 权限检查装饰器
def require_permission(resource: str, action: str):
    """
    需要特定权限的装饰器

    Args:
        resource: 资源名称
        action: 操作名称
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取用户ID（需要根据实际框架调整）
            user_id = (
                kwargs.get("user_id") or getattr(args[0], "user_id", None)
                if args
                else None
            )

            if not user_id:
                return {"error": "User ID required", "code": 401}

            # 获取上下文信息
            context = kwargs.get("context", {})

            # 检查权限
            if not rbac_manager.check_permission(user_id, resource, action, context):
                return {"error": "Insufficient permissions", "code": 403}

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_role(role_names: List[str]):
    """
    需要任一角色的装饰器

    Args:
        role_names: 角色名称列表
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = (
                kwargs.get("user_id") or getattr(args[0], "user_id", None)
                if args
                else None
            )

            if not user_id:
                return {"error": "User ID required", "code": 401}

            user_roles = rbac_manager.get_user_roles(user_id)
            user_role_names = [role.name for role in user_roles]

            if not any(role_name in user_role_names for role_name in role_names):
                return {"error": "Insufficient role permissions", "code": 403}

            return func(*args, **kwargs)

        return wrapper

    return decorator
