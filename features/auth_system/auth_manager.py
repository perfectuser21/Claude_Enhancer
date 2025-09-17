#!/usr/bin/env python3
"""
Perfect21认证管理器
负责统一管理用户认证、授权和会话
"""

import os
import sys
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# 导入依赖模块
try:
    from shared.types import UserData, AuthResult, UserRole
except ImportError:
    # 如果shared.types不存在，定义基本类型
    UserData = Dict[str, Any]
    AuthResult = Dict[str, Any]
    UserRole = str

from modules.logger import log_info, log_error
from .user_service import UserService
from .token_manager import TokenManager
from .security_service import SecurityService

class AuthManager:
    """认证管理器"""

    def __init__(self, db_path: str = "data/auth.db") -> None:
        """初始化认证管理器"""
        self.db_path: str = db_path
        self.user_service: UserService = UserService(db_path)
        self.token_manager: TokenManager = TokenManager()
        self.security_service: SecurityService = SecurityService()

        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 初始化数据库
        self._init_database()
        log_info("AuthManager初始化完成")

    def _init_database(self) -> None:
        """初始化数据库表"""
        try:
            self.user_service.init_tables()
            log_info("认证数据库初始化完成")
        except Exception as e:
            log_error("认证数据库初始化失败", e)
            raise

    def register(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> AuthResult:
        """用户注册"""
        try:
            # 安全检查
            security_check = self.security_service.validate_registration(
                username, email, password
            )
            if not security_check['valid']:
                return {
                    'success': False,
                    'error': security_check['error'],
                    'message': '注册信息验证失败'
                }

            # 检查用户是否存在
            if self.user_service.user_exists(username, email):
                return {
                    'success': False,
                    'error': 'USER_EXISTS',
                    'message': '用户名或邮箱已存在'
                }

            # 创建用户
            user_id = self.user_service.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )

            # 生成验证令牌
            verification_token = self.token_manager.generate_verification_token(user_id)

            log_info(f"用户注册成功: {username}")

            return {
                'success': True,
                'user_id': user_id,
                'verification_token': verification_token,
                'message': '注册成功，请验证邮箱'
            }

        except Exception as e:
            log_error("用户注册失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '注册过程中发生错误'
            }

    def login(self, identifier: str, password: str,
              remember_me: bool = False) -> Dict[str, Any]:
        """用户登录"""
        try:
            # 安全检查：防止暴力破解
            if not self.security_service.check_login_attempts(identifier):
                return {
                    'success': False,
                    'error': 'TOO_MANY_ATTEMPTS',
                    'message': '登录尝试次数过多，请稍后再试'
                }

            # 查找用户
            user = self.user_service.find_user(identifier)
            if not user:
                self.security_service.record_failed_attempt(identifier)
                return {
                    'success': False,
                    'error': 'INVALID_CREDENTIALS',
                    'message': '用户名或密码错误'
                }

            # 验证密码
            if not self.user_service.verify_password(user['id'], password):
                self.security_service.record_failed_attempt(identifier)
                return {
                    'success': False,
                    'error': 'INVALID_CREDENTIALS',
                    'message': '用户名或密码错误'
                }

            # 检查用户状态
            if user['status'] != 'active':
                return {
                    'success': False,
                    'error': 'ACCOUNT_INACTIVE',
                    'message': '账户未激活或已被禁用'
                }

            # 生成访问令牌
            token_expires = timedelta(days=7 if remember_me else 1)
            access_token = self.token_manager.generate_access_token(
                user['id'], expires_delta=token_expires
            )
            refresh_token = self.token_manager.generate_refresh_token(user['id'])

            # 更新用户最后登录时间
            self.user_service.update_last_login(user['id'])

            # 清除失败登录记录
            self.security_service.clear_failed_attempts(identifier)

            log_info(f"用户登录成功: {user['username']}")

            return {
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                },
                'expires_in': token_expires.total_seconds(),
                'message': '登录成功'
            }

        except Exception as e:
            log_error("用户登录失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '登录过程中发生错误'
            }

    def logout(self, access_token: str) -> Dict[str, Any]:
        """用户登出"""
        try:
            # 将令牌加入黑名单
            self.token_manager.revoke_token(access_token)

            log_info("用户登出成功")

            return {
                'success': True,
                'message': '登出成功'
            }

        except Exception as e:
            log_error("用户登出失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '登出过程中发生错误'
            }

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            # 验证刷新令牌
            token_data = self.token_manager.verify_refresh_token(refresh_token)
            if not token_data:
                return {
                    'success': False,
                    'error': 'INVALID_REFRESH_TOKEN',
                    'message': '刷新令牌无效或已过期'
                }

            # 生成新的访问令牌
            user_id = token_data['user_id']
            new_access_token = self.token_manager.generate_access_token(user_id)

            # 获取用户信息
            user = self.user_service.get_user_by_id(user_id)

            log_info(f"令牌刷新成功: user_id={user_id}")

            return {
                'success': True,
                'access_token': new_access_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                },
                'expires_in': 3600,  # 1小时
                'message': '令牌刷新成功'
            }

        except Exception as e:
            log_error("令牌刷新失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '令牌刷新过程中发生错误'
            }

    def verify_token(self, access_token: str) -> Dict[str, Any]:
        """验证访问令牌"""
        try:
            # 验证令牌
            token_data = self.token_manager.verify_access_token(access_token)
            if not token_data:
                return {
                    'success': False,
                    'error': 'INVALID_TOKEN',
                    'message': '访问令牌无效或已过期'
                }

            # 获取用户信息
            user_id = token_data['user_id']
            user = self.user_service.get_user_by_id(user_id)

            if not user or user['status'] != 'active':
                return {
                    'success': False,
                    'error': 'USER_INACTIVE',
                    'message': '用户不存在或已被禁用'
                }

            return {
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                },
                'token_data': token_data,
                'message': '令牌验证成功'
            }

        except Exception as e:
            log_error("令牌验证失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '令牌验证过程中发生错误'
            }

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """修改密码"""
        try:
            # 验证旧密码
            if not self.user_service.verify_password(user_id, old_password):
                return {
                    'success': False,
                    'error': 'INVALID_OLD_PASSWORD',
                    'message': '原密码错误'
                }

            # 验证新密码强度
            password_check = self.security_service.validate_password(new_password)
            if not password_check['valid']:
                return {
                    'success': False,
                    'error': password_check['error'],
                    'message': '新密码不符合安全要求'
                }

            # 更新密码
            self.user_service.update_password(user_id, new_password)

            # 撤销所有现有令牌（强制重新登录）
            self.token_manager.revoke_user_tokens(user_id)

            log_info(f"密码修改成功: user_id={user_id}")

            return {
                'success': True,
                'message': '密码修改成功，请重新登录'
            }

        except Exception as e:
            log_error("密码修改失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '密码修改过程中发生错误'
            }

    def get_user_profile(self, user_id: str) -> Dict[str, Union[bool, str, UserData]]:
        """获取用户资料"""
        try:
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }

            return {
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'status': user['status'],
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                },
                'message': '获取用户资料成功'
            }

        except Exception as e:
            log_error("获取用户资料失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '获取用户资料过程中发生错误'
            }

    def update_user_profile(self, user_id: str, **kwargs: Any) -> Dict[str, Any]:
        """更新用户资料"""
        try:
            # 允许更新的字段
            allowed_fields = ['username', 'email']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_data:
                return {
                    'success': False,
                    'error': 'NO_UPDATE_DATA',
                    'message': '没有可更新的数据'
                }

            # 更新用户信息
            self.user_service.update_user(user_id, **update_data)

            log_info(f"用户资料更新成功: user_id={user_id}")

            return {
                'success': True,
                'message': '用户资料更新成功'
            }

        except Exception as e:
            log_error("用户资料更新失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '用户资料更新过程中发生错误'
            }

    def cleanup(self) -> None:
        """清理资源"""
        try:
            if hasattr(self, 'user_service'):
                self.user_service.cleanup()
            if hasattr(self, 'token_manager'):
                self.token_manager.cleanup()
            if hasattr(self, 'security_service'):
                self.security_service.cleanup()
        except Exception as e:
            log_error("AuthManager清理失败", e)