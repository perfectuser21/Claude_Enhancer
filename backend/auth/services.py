#!/usr/bin/env python3
"""
认证系统业务逻辑层 - Service模式
负责业务逻辑处理和协调各个组件
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status

from backend.auth.models import UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse
from backend.auth.repositories import UserRepository, SessionRepository, AuditLogRepository
from backend.auth.jwt_manager import JWTManager
from backend.auth.password_manager import PasswordManager
from backend.core.config import get_settings
from backend.core.exceptions import (
    AuthenticationError, ValidationError, UserNotFoundError,
    AccountLockedException, TokenExpiredError
)

class AuthService:
    """认证服务"""

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        audit_repo: AuditLogRepository,
        jwt_manager: JWTManager,
        password_manager: PasswordManager
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.audit_repo = audit_repo
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager
        self.settings = get_settings()

    async def register_user(
        self,
        user_data: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """用户注册"""
        try:
            # 1. 验证密码强度
            password_strength = self.password_manager.check_password_strength(
                user_data.password,
                user_data.username,
                user_data.email
            )

            if not password_strength.is_strong:
                # 记录注册失败日志
                await self._log_event(
                    event_type='register_failed',
                    success=False,
                    error_message=f"密码强度不足: {', '.join(password_strength.issues)}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                raise ValidationError(
                    f"密码强度不足: {', '.join(password_strength.issues)}"
                )

            # 2. 检查用户是否已存在
            existing_user = self.user_repo.get_user_by_identifier(user_data.username)
            if existing_user:
                await self._log_event(
                    event_type='register_failed',
                    success=False,
                    error_message="用户名已存在",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValidationError("用户名已存在")

            existing_email = self.user_repo.get_user_by_email(user_data.email)
            if existing_email:
                await self._log_event(
                    event_type='register_failed',
                    success=False,
                    error_message="邮箱已存在",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValidationError("邮箱已存在")

            # 3. 哈希密码
            password_hash = self.password_manager.hash_password(user_data.password)

            # 4. 创建用户
            user = self.user_repo.create_user({
                'username': user_data.username,
                'email': user_data.email,
                'password_hash': password_hash,
                'role': user_data.role,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'timezone': user_data.timezone
            })

            # 5. 记录成功日志
            await self._log_event(
                user_id=user.id,
                event_type='register',
                success=True,
                event_description=f"用户注册成功: {user.username}",
                ip_address=ip_address,
                user_agent=user_agent
            )

            # 6. 生成邮箱验证令牌（这里简化处理）
            verification_token = str(uuid.uuid4())

            return {
                'success': True,
                'user_id': user.id,
                'verification_token': verification_token,
                'message': '注册成功，请验证邮箱'
            }

        except (ValidationError, AuthenticationError):
            raise
        except Exception as e:
            await self._log_event(
                event_type='register_failed',
                success=False,
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册过程中发生错误"
            )

    async def authenticate_user(
        self,
        login_data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """用户登录认证"""
        try:
            # 1. 检查账户锁定状态
            if self.user_repo.is_user_locked(login_data.identifier):
                await self._log_event(
                    event_type='login_blocked',
                    success=False,
                    error_message=f"账户被锁定: {login_data.identifier}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise AccountLockedException("账户已被锁定，请稍后再试")

            # 2. 查找用户
            user = self.user_repo.get_user_by_identifier(login_data.identifier)
            if not user:
                # 记录失败尝试
                self.user_repo.increment_failed_attempts(login_data.identifier)

                await self._log_event(
                    event_type='failed_login',
                    success=False,
                    error_message=f"用户不存在: {login_data.identifier}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise AuthenticationError("用户名或密码错误")

            # 3. 验证密码
            if not self.password_manager.verify_password(login_data.password, user.password_hash):
                # 增加失败尝试次数
                self.user_repo.increment_failed_attempts(login_data.identifier)

                await self._log_event(
                    user_id=user.id,
                    event_type='failed_login',
                    success=False,
                    error_message="密码错误",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise AuthenticationError("用户名或密码错误")

            # 4. 检查用户状态
            if user.status != 'active':
                await self._log_event(
                    user_id=user.id,
                    event_type='login_blocked',
                    success=False,
                    error_message=f"账户状态不活跃: {user.status}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise AuthenticationError("账户未激活或已被禁用")

            # 5. 创建会话
            session_id = str(uuid.uuid4())
            access_token_jti = str(uuid.uuid4())
            refresh_token_jti = str(uuid.uuid4())

            # 设置会话过期时间
            session_duration = timedelta(days=7 if login_data.remember_me else 1)
            expires_at = datetime.utcnow() + session_duration

            # 创建会话记录
            session = self.session_repo.create_session({
                'user_id': user.id,
                'access_token_jti': access_token_jti,
                'refresh_token_jti': refresh_token_jti,
                'expires_at': expires_at,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_id': login_data.device_id
            })

            # 6. 生成JWT令牌
            access_token = self.jwt_manager.generate_access_token(
                user_id=user.id,
                username=user.username,
                role=user.role,
                session_id=session.id
            )

            refresh_token = self.jwt_manager.generate_refresh_token(
                user_id=user.id,
                username=user.username,
                session_id=session.id
            )

            # 7. 更新用户最后登录时间并清除失败尝试
            self.user_repo.update_last_login(user.id)
            self.user_repo.clear_failed_attempts(login_data.identifier)

            # 8. 记录成功登录日志
            await self._log_event(
                user_id=user.id,
                event_type='login',
                success=True,
                event_description=f"用户登录成功: {user.username}",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=f'{{"session_id": "{session.id}", "remember_me": {login_data.remember_me}}}'
            )

            # 9. 构建响应
            user_response = UserResponse.from_orm(user)

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=15 * 60,  # 15分钟
                user=user_response
            )

        except (AuthenticationError, AccountLockedException, ValidationError):
            raise
        except Exception as e:
            await self._log_event(
                event_type='login_error',
                success=False,
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录过程中发生错误"
            )

    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            # 1. 验证刷新令牌
            token_payload = self.jwt_manager.verify_token(refresh_token, 'refresh')

            # 2. 获取用户信息
            user = self.user_repo.get_user_by_id(token_payload.user_id)
            if not user or user.status != 'active':
                raise AuthenticationError("用户不存在或已被禁用")

            # 3. 检查会话是否有效
            session = self.session_repo.get_session_by_token_jti(token_payload.jti, 'refresh')
            if not session or not session.is_active:
                raise AuthenticationError("会话已失效")

            # 4. 生成新的访问令牌
            new_access_token = self.jwt_manager.generate_access_token(
                user_id=user.id,
                username=user.username,
                role=user.role,
                session_id=session.id
            )

            # 5. 更新会话访问时间
            self.session_repo.update_session_access(session.id)

            # 6. 记录令牌刷新日志
            await self._log_event(
                user_id=user.id,
                event_type='token_refresh',
                success=True,
                event_description="访问令牌刷新成功",
                ip_address=ip_address
            )

            return {
                'access_token': new_access_token,
                'expires_in': 15 * 60,
                'token_type': 'bearer'
            }

        except (AuthenticationError, TokenExpiredError):
            raise
        except Exception as e:
            await self._log_event(
                event_type='token_refresh_error',
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="令牌刷新失败"
            )

    async def logout_user(
        self,
        access_token: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, str]:
        """用户登出"""
        try:
            # 1. 验证访问令牌
            token_payload = self.jwt_manager.verify_token(access_token, 'access')

            # 2. 撤销令牌
            self.jwt_manager.revoke_token(access_token)

            # 3. 撤销会话
            session = self.session_repo.get_session_by_token_jti(token_payload.jti, 'access')
            if session:
                self.session_repo.revoke_session(session.id)
                # 撤销会话的所有令牌
                self.jwt_manager.revoke_session_tokens(session.id)

            # 4. 记录登出日志
            await self._log_event(
                user_id=token_payload.user_id,
                event_type='logout',
                success=True,
                event_description="用户登出成功",
                ip_address=ip_address
            )

            return {'message': '登出成功'}

        except (AuthenticationError, TokenExpiredError):
            # 即使令牌无效，登出操作也算成功
            return {'message': '登出成功'}
        except Exception as e:
            await self._log_event(
                event_type='logout_error',
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登出过程中发生错误"
            )

    async def verify_access_token(self, access_token: str) -> Dict[str, Any]:
        """验证访问令牌并返回用户信息"""
        try:
            # 验证令牌
            token_payload = self.jwt_manager.verify_token(access_token, 'access')

            # 获取用户信息
            user = self.user_repo.get_user_by_id(token_payload.user_id)
            if not user or user.status != 'active':
                raise AuthenticationError("用户不存在或已被禁用")

            # 更新会话访问时间
            session = self.session_repo.get_session_by_token_jti(token_payload.jti, 'access')
            if session:
                self.session_repo.update_session_access(session.id)

            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'session_id': session.id if session else None
            }

        except (AuthenticationError, TokenExpiredError):
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="令牌验证失败"
            )

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, str]:
        """修改密码"""
        try:
            # 1. 获取用户
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError("用户不存在")

            # 2. 验证当前密码
            if not self.password_manager.verify_password(current_password, user.password_hash):
                await self._log_event(
                    user_id=user_id,
                    event_type='password_change_failed',
                    success=False,
                    error_message="当前密码错误",
                    ip_address=ip_address
                )
                raise AuthenticationError("当前密码错误")

            # 3. 检查新密码强度
            password_strength = self.password_manager.check_password_strength(
                new_password,
                user.username,
                user.email
            )

            if not password_strength.is_strong:
                raise ValidationError(
                    f"新密码强度不足: {', '.join(password_strength.issues)}"
                )

            # 4. 哈希新密码
            new_password_hash = self.password_manager.hash_password(new_password)

            # 5. 更新密码
            self.user_repo.update_user(user_id, {
                'password_hash': new_password_hash,
                'password_changed_at': datetime.utcnow()
            })

            # 6. 撤销用户的所有其他会话（强制重新登录）
            revoked_count = self.session_repo.revoke_user_sessions(user_id)
            self.jwt_manager.revoke_user_tokens(user_id)

            # 7. 记录密码修改日志
            await self._log_event(
                user_id=user_id,
                event_type='password_change',
                success=True,
                event_description="密码修改成功",
                ip_address=ip_address,
                metadata=f'{{"revoked_sessions": {revoked_count}}}'
            )

            return {
                'message': '密码修改成功，请重新登录',
                'revoked_sessions': str(revoked_count)
            }

        except (AuthenticationError, UserNotFoundError, ValidationError):
            raise
        except Exception as e:
            await self._log_event(
                user_id=user_id,
                event_type='password_change_error',
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码修改失败"
            )

    async def get_user_profile(self, user_id: str) -> UserResponse:
        """获取用户资料"""
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError("用户不存在")

            return UserResponse.from_orm(user)

        except UserNotFoundError:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户资料失败"
            )

    async def update_user_profile(
        self,
        user_id: str,
        update_data: UserUpdate,
        ip_address: Optional[str] = None
    ) -> Dict[str, str]:
        """更新用户资料"""
        try:
            # 过滤有效的更新字段
            update_dict = {}
            if update_data.username is not None:
                update_dict['username'] = update_data.username
            if update_data.email is not None:
                update_dict['email'] = str(update_data.email)
            if update_data.first_name is not None:
                update_dict['first_name'] = update_data.first_name
            if update_data.last_name is not None:
                update_dict['last_name'] = update_data.last_name
            if update_data.timezone is not None:
                update_dict['timezone'] = update_data.timezone

            if not update_dict:
                raise ValidationError("没有可更新的数据")

            # 更新用户信息
            updated_user = self.user_repo.update_user(user_id, update_dict)

            # 记录更新日志
            await self._log_event(
                user_id=user_id,
                event_type='profile_update',
                success=True,
                event_description=f"用户资料更新: {', '.join(update_dict.keys())}",
                ip_address=ip_address,
                metadata=str(update_dict)
            )

            return {'message': '用户资料更新成功'}

        except (UserNotFoundError, ValidationError):
            raise
        except Exception as e:
            await self._log_event(
                user_id=user_id,
                event_type='profile_update_error',
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户资料更新失败"
            )

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的活跃会话"""
        try:
            sessions = self.session_repo.get_user_sessions(user_id, active_only=True)

            return [
                {
                    'id': session.id,
                    'created_at': session.created_at,
                    'last_accessed_at': session.last_accessed_at,
                    'expires_at': session.expires_at,
                    'ip_address': session.ip_address,
                    'user_agent': session.user_agent,
                    'device_id': session.device_id
                }
                for session in sessions
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户会话失败"
            )

    async def revoke_session(self, user_id: str, session_id: str) -> Dict[str, str]:
        """撤销指定会话"""
        try:
            # 验证会话属于指定用户
            session = self.session_repo.get_session_by_id(session_id)
            if not session or session.user_id != user_id:
                raise ValidationError("会话不存在或无权限")

            # 撤销会话
            self.session_repo.revoke_session(session_id)
            self.jwt_manager.revoke_session_tokens(session_id)

            # 记录撤销日志
            await self._log_event(
                user_id=user_id,
                event_type='session_revoke',
                success=True,
                event_description=f"会话撤销成功: {session_id}"
            )

            return {'message': '会话撤销成功'}

        except ValidationError:
            raise
        except Exception as e:
            await self._log_event(
                user_id=user_id,
                event_type='session_revoke_error',
                success=False,
                error_message=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="会话撤销失败"
            )

    async def _log_event(
        self,
        event_type: str,
        success: bool,
        user_id: Optional[str] = None,
        event_description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[str] = None
    ) -> None:
        """记录审计日志"""
        try:
            self.audit_repo.create_log({
                'user_id': user_id,
                'event_type': event_type,
                'event_description': event_description,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'success': success,
                'error_message': error_message,
                'metadata': metadata
            })
        except Exception:
            # 审计日志失败不应影响主要业务逻辑
            pass

class AdminService:
    """管理员服务"""

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        audit_repo: AuditLogRepository
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.audit_repo = audit_repo

    async def get_users(
        self,
        offset: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户列表（管理员）"""
        try:
            users, total = self.user_repo.list_users(
                offset=offset,
                limit=limit,
                status_filter=status_filter,
                role_filter=role_filter,
                search_query=search_query
            )

            return {
                'users': [UserResponse.from_orm(user) for user in users],
                'total': total,
                'offset': offset,
                'limit': limit
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户列表失败"
            )

    async def get_security_stats(self) -> Dict[str, Any]:
        """获取安全统计信息"""
        try:
            # 24小时内的失败登录统计
            failed_login_stats = self.audit_repo.get_failed_login_stats(24)

            # 活跃会话统计
            # 这里简化处理，实际应该从会话表获取

            return {
                'failed_logins_24h': failed_login_stats,
                'active_sessions': 0,  # 待实现
                'security_events': []   # 待实现
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取安全统计失败"
            )