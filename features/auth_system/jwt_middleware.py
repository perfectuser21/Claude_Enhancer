#!/usr/bin/env python3
"""
Perfect21 JWT认证中间件
提供JWT令牌验证、会话管理和安全检查
"""

import os
import sys
import time
from typing import Callable, Dict, Any, Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from modules.logger import log_info, log_error, log_warning
from .auth_manager import AuthManager
from .redis_session_manager import RedisSessionManager
from .token_manager import TokenManager

class JWTAuthenticationMiddleware:
    """JWT认证中间件"""

    def __init__(self, auth_manager: AuthManager = None,
                 session_manager: RedisSessionManager = None):
        """初始化JWT认证中间件"""
        self.auth_manager = auth_manager or AuthManager()
        self.session_manager = session_manager or RedisSessionManager()
        self.token_manager = TokenManager()

        # 公开路径（不需要认证）
        self.public_paths = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/favicon.ico",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/api/auth/health",
            "/api/auth/reset-password",
            "/api/auth/verify-email"
        }

        # 可选认证路径（认证用户可以获得额外功能）
        self.optional_auth_paths = {
            "/api/public",
            "/api/search"
        }

        log_info("JWT认证中间件初始化完成")

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        path = request.url.path
        method = request.method

        # 跳过静态文件
        if path.startswith(("/static/", "/assets/")):
            return await call_next(request)

        # 跳过公开路径
        if path in self.public_paths:
            return await call_next(request)

        # 检查认证
        auth_result = await self._authenticate_request(request)

        # 处理可选认证路径
        if path in self.optional_auth_paths:
            if auth_result['authenticated']:
                request.state.user = auth_result['user']
                request.state.session = auth_result['session']
            return await call_next(request)

        # 必需认证的路径
        if not auth_result['authenticated']:
            return self._create_unauthorized_response(auth_result['error'])

        # 设置请求状态
        request.state.user = auth_result['user']
        request.state.session = auth_result['session']
        request.state.token_info = auth_result['token_info']

        # 检查用户状态
        if not self._check_user_status(auth_result['user']):
            return self._create_forbidden_response("账户已被禁用或未激活")

        # 检查权限
        if not await self._check_permissions(request, auth_result['user']):
            return self._create_forbidden_response("权限不足")

        # 更新会话活跃时间
        if auth_result['session']:
            self.session_manager.update_session(
                auth_result['session']['session_id'],
                {'last_activity': time.time()}
            )

        try:
            response = await call_next(request)

            # 添加安全头部
            self._add_security_headers(response)

            return response

        except Exception as e:
            log_error(f"请求处理异常: {path}", e)
            raise

    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """认证请求"""
        try:
            # 获取Authorization头
            authorization = request.headers.get("Authorization")
            if not authorization:
                return {
                    'authenticated': False,
                    'error': 'MISSING_AUTH_HEADER',
                    'message': '缺少Authorization头部'
                }

            # 验证格式
            if not authorization.startswith("Bearer "):
                return {
                    'authenticated': False,
                    'error': 'INVALID_AUTH_FORMAT',
                    'message': 'Authorization头部格式错误'
                }

            # 提取令牌
            token = authorization.split(" ")[1].strip()
            if not token:
                return {
                    'authenticated': False,
                    'error': 'EMPTY_TOKEN',
                    'message': '令牌为空'
                }

            # 验证JWT令牌
            token_result = self.auth_manager.verify_token(token)
            if not token_result['success']:
                return {
                    'authenticated': False,
                    'error': token_result.get('error', 'INVALID_TOKEN'),
                    'message': token_result.get('message', '令牌无效')
                }

            user = token_result['user']
            token_info = token_result['token_data']

            # 获取会话信息（如果存在）
            session = None
            session_id = token_info.get('session_id')
            if session_id:
                session = self.session_manager.get_session(session_id)
                if not session:
                    log_warning(f"会话不存在或已过期: {session_id}")

            # 记录成功认证
            client_ip = self._get_client_ip(request)
            log_info(f"用户认证成功: {user['username']} - IP: {client_ip}")

            return {
                'authenticated': True,
                'user': user,
                'session': session,
                'token_info': token_info,
                'token': token
            }

        except Exception as e:
            log_error("认证过程异常", e)
            return {
                'authenticated': False,
                'error': 'AUTH_EXCEPTION',
                'message': '认证过程中发生错误'
            }

    def _check_user_status(self, user: Dict[str, Any]) -> bool:
        """检查用户状态"""
        status = user.get('status', 'inactive')
        return status == 'active'

    async def _check_permissions(self, request: Request, user: Dict[str, Any]) -> bool:
        """检查用户权限"""
        path = request.url.path
        method = request.method
        user_role = user.get('role', 'user')

        # 管理员路径检查
        if path.startswith('/api/admin/'):
            return user_role in ['admin', 'super_admin']

        # 用户管理路径检查
        if path.startswith('/api/users/') and method in ['PUT', 'DELETE']:
            # 只能管理自己的用户信息，或者管理员可以管理所有用户
            if user_role in ['admin', 'super_admin']:
                return True

            # 检查是否是用户自己的资源
            user_id_in_path = self._extract_user_id_from_path(path)
            return user_id_in_path == str(user['id'])

        # 默认允许
        return True

    def _extract_user_id_from_path(self, path: str) -> Optional[str]:
        """从路径中提取用户ID"""
        # 例如: /api/users/123/profile -> 123
        parts = path.split('/')
        if len(parts) >= 4 and parts[2] == 'users':
            return parts[3]
        return None

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _create_unauthorized_response(self, error: str) -> JSONResponse:
        """创建未授权响应"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": error,
                "message": "认证失败，请登录后重试",
                "timestamp": time.time()
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    def _create_forbidden_response(self, message: str) -> JSONResponse:
        """创建禁止访问响应"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "FORBIDDEN",
                "message": message,
                "timestamp": time.time()
            }
        )

    def _add_security_headers(self, response: Response):
        """添加安全头部"""
        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # 防止内容类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS保护
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    def add_public_path(self, path: str):
        """添加公开路径"""
        self.public_paths.add(path)

    def remove_public_path(self, path: str):
        """移除公开路径"""
        self.public_paths.discard(path)

    def add_optional_auth_path(self, path: str):
        """添加可选认证路径"""
        self.optional_auth_paths.add(path)

    def remove_optional_auth_path(self, path: str):
        """移除可选认证路径"""
        self.optional_auth_paths.discard(path)


class JWTDependency:
    """JWT依赖注入类"""

    def __init__(self, auth_manager: AuthManager = None):
        self.auth_manager = auth_manager or AuthManager()

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """获取当前认证用户"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return request.state.user


class OptionalJWTDependency:
    """可选JWT依赖注入类"""

    def __init__(self, auth_manager: AuthManager = None):
        self.auth_manager = auth_manager or AuthManager()

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        """获取当前认证用户（可选）"""
        return getattr(request.state, 'user', None)


class AdminRequiredDependency:
    """管理员权限依赖"""

    def __init__(self, auth_manager: AuthManager = None):
        self.auth_manager = auth_manager or AuthManager()

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """检查管理员权限"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user = request.state.user
        if user.get('role') not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )

        return user


# 全局依赖实例
get_current_user = JWTDependency()
get_current_user_optional = OptionalJWTDependency()
require_admin = AdminRequiredDependency()


def create_jwt_middleware(auth_manager: AuthManager = None,
                         session_manager: RedisSessionManager = None) -> JWTAuthenticationMiddleware:
    """创建JWT中间件实例"""
    return JWTAuthenticationMiddleware(auth_manager, session_manager)