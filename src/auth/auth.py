"""
用户认证模块 - 核心认证服务
集成JWT令牌管理、密码安全处理、用户管理等功能
实现完整的认证和授权系统
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from .jwt import JWTTokenManager, jwt_manager, token_blacklist
from .password import PasswordManager, password_manager


class User:
    """用户模型"""

    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        password_hash: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        is_active: bool = True,
        created_at: datetime = None,
        last_login: datetime = None,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.roles = roles or ["user"]
        self.permissions = permissions or []
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self.failed_login_attempts = 0
        self.locked_until = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "failed_login_attempts": self.failed_login_attempts,
            "locked_until": self.locked_until.isoformat()
            if self.locked_until
            else None,
        }

    def has_role(self, role: str) -> bool:
        """检查用户是否有指定角色"""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions

    def is_locked(self) -> bool:
        """检查用户是否被锁定"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until


class AuthService:
    """认证服务 - 主要的认证和授权处理类"""

    def __init__(
        self,
        jwt_manager: JWTTokenManager = None,
        password_manager: PasswordManager = None,
        max_login_attempts: int = 5,
        lockout_duration_minutes: int = 30,
    ):
        """
        初始化认证服务

        Args:
            jwt_manager: JWT令牌管理器
            password_manager: 密码管理器
            max_login_attempts: 最大登录尝试次数
            lockout_duration_minutes: 锁定持续时间（分钟）
        """
        # 导入全局实例以避免循环引用
        if jwt_manager is None:
            from .jwt import jwt_manager as global_jwt_manager

            self.jwt_manager = global_jwt_manager
        else:
            self.jwt_manager = jwt_manager

        if password_manager is None:
            from .password import password_manager as global_password_manager

            self.password_manager = global_password_manager
        else:
            self.password_manager = password_manager
        self.max_login_attempts = max_login_attempts
        self.lockout_duration_minutes = lockout_duration_minutes

        # 用户存储（生产环境应使用数据库）
        self.users = {}
        self.users_by_email = {}
        self.users_by_username = {}
        self.next_user_id = 1

        # 登录尝试记录
        self.login_attempts = {}

    def register(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[str] = None,
        permissions: List[str] = None,
    ) -> Dict[str, Any]:
        """
        用户注册

        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            roles: 用户角色列表
            permissions: 用户权限列表

        Returns:
            Dict: 注册结果
        """
        try:
            # 验证输入
            if not username or not email or not password:
                return {
                    "success": False,
                    "error": "用户名、邮箱和密码都是必需的",
                    "code": "MISSING_FIELDS",
                }

            # 检查用户名是否已存在
            if username in self.users_by_username:
                return {"success": False, "error": "用户名已存在", "code": "USERNAME_EXISTS"}

            # 检查邮箱是否已存在
            if email in self.users_by_email:
                return {"success": False, "error": "邮箱已被注册", "code": "EMAIL_EXISTS"}

            # 验证密码强度
            password_validation = self.password_manager.validate_password_strength(
                password, username
            )
            if not password_validation["is_valid"]:
                return {
                    "success": False,
                    "error": "密码不符合安全要求",
                    "code": "WEAK_PASSWORD",
                    "details": password_validation["errors"],
                }

            # 加密密码
            password_hash = self.password_manager.hash_password(password)

            # 创建用户
            user_id = self.next_user_id
            self.next_user_id += 1

            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                roles=roles or ["user"],
                permissions=permissions or [],
            )

            # 存储用户
            self.users[user_id] = user
            self.users_by_email[email] = user
            self.users_by_username[username] = user

            # 添加到密码历史
            self.password_manager.add_password_to_history(user_id, password_hash)

            return {
                "success": True,
                "message": "注册成功",
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "roles": user.roles,
                    "permissions": user.permissions,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"注册失败: {str(e)}",
                "code": "REGISTRATION_ERROR",
            }

    def login(
        self, email_or_username: str, password: str, remember_me: bool = False
    ) -> Dict[str, Any]:
        """
        用户登录

        Args:
            email_or_username: 邮箱或用户名
            password: 密码
            remember_me: 是否记住登录状态

        Returns:
            Dict: 登录结果，包含令牌信息
        """
        try:
            # 查找用户
            user = self._find_user(email_or_username)
            if not user:
                self._record_failed_login(email_or_username)
                return {"success": False, "error": "用户不存在", "code": "USER_NOT_FOUND"}

            # 检查用户是否被锁定
            if user.is_locked():
                return {
                    "success": False,
                    "error": f'账户已被锁定，请在{user.locked_until.strftime("%Y-%m-%d %H:%M:%S")}后重试',
                    "code": "ACCOUNT_LOCKED",
                }

            # 检查用户是否激活
            if not user.is_active:
                return {"success": False, "error": "账户已被禁用", "code": "ACCOUNT_DISABLED"}

            # 验证密码
            if not self.password_manager.verify_password(password, user.password_hash):
                self._record_failed_login(email_or_username, user)
                return {"success": False, "error": "密码错误", "code": "INVALID_PASSWORD"}

            # 重置失败登录计数
            self._reset_failed_login(email_or_username, user)

            # 更新最后登录时间
            user.last_login = datetime.utcnow()

            # 生成令牌
            user_data = user.to_dict()
            access_token = self.jwt_manager.generate_access_token(user_data)
            refresh_token = self.jwt_manager.generate_refresh_token(user.user_id)

            # 设置令牌过期时间
            if remember_me:
                # 记住登录状态时延长令牌有效期
                self.jwt_manager.access_token_expire_minutes = 60 * 24  # 24小时
                self.jwt_manager.refresh_token_expire_days = 30  # 30天

            return {
                "success": True,
                "message": "登录成功",
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "roles": user.roles,
                    "permissions": user.permissions,
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "Bearer",
                    "expires_in": self.jwt_manager.access_token_expire_minutes * 60,
                },
            }

        except Exception as e:
            return {"success": False, "error": f"登录失败: {str(e)}", "code": "LOGIN_ERROR"}

    def logout(self, access_token: str, refresh_token: str = None) -> Dict[str, Any]:
        """
        用户登出

        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌（可选）

        Returns:
            Dict: 登出结果
        """
        try:
            # 将令牌加入黑名单
            token_blacklist.add_token(access_token, "User logout")

            if refresh_token:
                # 验证并撤销刷新令牌
                payload = self.jwt_manager.verify_token(refresh_token, "refresh")
                if payload:
                    user_id = payload.get("user_id")
                    self.jwt_manager.revoke_user_tokens(user_id)
                    token_blacklist.add_token(refresh_token, "User logout")

            return {"success": True, "message": "登出成功"}

        except Exception as e:
            return {
                "success": False,
                "error": f"登出失败: {str(e)}",
                "code": "LOGOUT_ERROR",
            }

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            Dict: 刷新结果
        """
        try:
            # 验证刷新令牌
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            if not payload:
                return {
                    "success": False,
                    "error": "刷新令牌无效或已过期",
                    "code": "INVALID_REFRESH_TOKEN",
                }

            user_id = payload.get("user_id")
            user = self.users.get(user_id)

            if not user or not user.is_active:
                return {"success": False, "error": "用户不存在或已被禁用", "code": "USER_INVALID"}

            # 生成新的访问令牌
            user_data = user.to_dict()
            new_access_token = self.jwt_manager.refresh_access_token(
                refresh_token, user_data
            )

            if not new_access_token:
                return {"success": False, "error": "令牌刷新失败", "code": "REFRESH_FAILED"}

            return {
                "success": True,
                "message": "令牌刷新成功",
                "tokens": {
                    "access_token": new_access_token,
                    "token_type": "Bearer",
                    "expires_in": self.jwt_manager.access_token_expire_minutes * 60,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"令牌刷新失败: {str(e)}",
                "code": "REFRESH_ERROR",
            }

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> Dict[str, Any]:
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            Dict: 修改结果
        """
        try:
            user = self.users.get(user_id)
            if not user:
                return {"success": False, "error": "用户不存在", "code": "USER_NOT_FOUND"}

            # 验证旧密码
            if not self.password_manager.verify_password(
                old_password, user.password_hash
            ):
                return {
                    "success": False,
                    "error": "旧密码错误",
                    "code": "INVALID_OLD_PASSWORD",
                }

            # 验证新密码强度
            password_validation = self.password_manager.validate_password_strength(
                new_password, user.username
            )
            if not password_validation["is_valid"]:
                return {
                    "success": False,
                    "error": "新密码不符合安全要求",
                    "code": "WEAK_PASSWORD",
                    "details": password_validation["errors"],
                }

            # 检查密码历史
            if not self.password_manager.check_password_history(user_id, new_password):
                return {
                    "success": False,
                    "error": "不能使用最近使用过的密码",
                    "code": "PASSWORD_REUSED",
                }

            # 更新密码
            new_password_hash = self.password_manager.hash_password(new_password)
            user.password_hash = new_password_hash

            # 添加到密码历史
            self.password_manager.add_password_to_history(user_id, new_password_hash)

            # 撤销用户的所有令牌
            self.jwt_manager.revoke_user_tokens(user_id)

            return {"success": True, "message": "密码修改成功，请重新登录"}

        except Exception as e:
            return {
                "success": False,
                "error": f"密码修改失败: {str(e)}",
                "code": "PASSWORD_CHANGE_ERROR",
            }

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌

        Args:
            token: 访问令牌

        Returns:
            Dict: 用户信息，验证失败返回None
        """
        payload = self.jwt_manager.verify_token(token, "access")
        if not payload:
            return None

        user_id = payload.get("user_id")
        user = self.users.get(user_id)

        if not user or not user.is_active:
            return None

        return payload

    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            Dict: 用户信息
        """
        user = self.users.get(user_id)
        if not user:
            return None

        return user.to_dict()

    def _find_user(self, email_or_username: str) -> Optional[User]:
        """根据邮箱或用户名查找用户"""
        user = self.users_by_email.get(email_or_username)
        if not user:
            user = self.users_by_username.get(email_or_username)
        return user

    def _record_failed_login(self, identifier: str, user: User = None):
        """记录失败的登录尝试"""
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.lockout_duration_minutes
                )

        # 记录IP级别的失败尝试（这里简化处理）
        self.login_attempts[identifier] = self.login_attempts.get(identifier, 0) + 1

    def _reset_failed_login(self, identifier: str, user: User = None):
        """重置失败登录计数"""
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None

        self.login_attempts.pop(identifier, None)


# 全局认证服务实例
auth_service = AuthService()
