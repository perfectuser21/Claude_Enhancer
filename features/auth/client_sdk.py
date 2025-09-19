#!/usr/bin/env python3
"""
Perfect21 认证API客户端SDK
提供Python客户端用于与Perfect21认证API交互
"""

import os
import sys
import json
import time
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


@dataclass
class AuthToken:
    """认证令牌数据类"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        return datetime.utcnow() >= self.expires_at

    @property
    def will_expire_soon(self, threshold_seconds: int = 300) -> bool:
        """检查令牌是否即将过期（默认5分钟内）"""
        threshold = datetime.utcnow() + timedelta(seconds=threshold_seconds)
        return self.expires_at <= threshold


@dataclass
class UserProfile:
    """用户档案数据类"""
    user_id: str
    username: str
    email: str
    role: str
    permissions: List[str]
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AuthenticationError(Exception):
    """认证错误异常"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class TokenExpiredError(AuthenticationError):
    """令牌过期异常"""
    pass


class Perfect21AuthClient:
    """Perfect21认证API客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化认证客户端

        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.token: Optional[AuthToken] = None
        self.user_profile: Optional[UserProfile] = None

        # 设置日志
        self.logger = logging.getLogger(__name__)

        # 配置HTTP会话
        self.session = self._create_session()

        # 回调函数
        self.on_token_refreshed = None
        self.on_login_success = None
        self.on_logout = None

    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()

        # 重试策略
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 默认头部
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Perfect21-AuthClient/1.0.0',
            'Accept': 'application/json'
        })

        return session

    def _get_device_fingerprint(self) -> str:
        """生成设备指纹"""
        import platform
        import socket

        device_info = {
            'hostname': socket.gethostname(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }

        # 生成指纹哈希
        device_str = json.dumps(device_info, sort_keys=True)
        return hashlib.sha256(device_str.encode()).hexdigest()[:32]

    def login(self, username: str, password: str, remember_me: bool = False,
              captcha_token: str = None) -> Dict[str, Any]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码
            remember_me: 是否记住登录
            captcha_token: 验证码令牌

        Returns:
            dict: 登录结果

        Raises:
            AuthenticationError: 认证失败
        """
        url = urljoin(self.base_url, '/api/v1/auth/login')

        data = {
            'username': username,
            'password': password,
            'remember_me': remember_me,
            'device_fingerprint': self._get_device_fingerprint()
        }

        if captcha_token:
            data['captcha_token'] = captcha_token

        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            result = response.json()

            if response.status_code == 200 and result.get('success'):
                # 保存令牌
                self.token = AuthToken(
                    access_token=result['access_token'],
                    refresh_token=result['refresh_token'],
                    expires_in=result.get('expires_in', 3600)
                )

                # 保存用户档案
                if result.get('user_profile'):
                    profile_data = result['user_profile']
                    self.user_profile = UserProfile(
                        user_id=profile_data['user_id'],
                        username=profile_data['username'],
                        email=profile_data['email'],
                        role=profile_data['role'],
                        permissions=result.get('permissions', []),
                        is_active=profile_data.get('is_active', True),
                        last_login=datetime.fromisoformat(profile_data['last_login'].replace('Z', '+00:00'))
                        if profile_data.get('last_login') else None
                    )

                # 更新会话头部
                self.session.headers['Authorization'] = f"Bearer {self.token.access_token}"

                self.logger.info(f"登录成功: {username}")

                # 触发回调
                if self.on_login_success:
                    self.on_login_success(self.user_profile)

                return {
                    'success': True,
                    'message': '登录成功',
                    'user_profile': asdict(self.user_profile),
                    'token': asdict(self.token)
                }
            else:
                error_message = result.get('message', '登录失败')
                raise AuthenticationError(error_message, response.status_code)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"登录请求失败: {e}")
            raise AuthenticationError(f"网络请求失败: {str(e)}")

    def logout(self) -> Dict[str, Any]:
        """
        用户登出

        Returns:
            dict: 登出结果
        """
        if not self.token:
            return {'success': True, 'message': '已处于登出状态'}

        url = urljoin(self.base_url, '/api/v1/auth/logout')

        try:
            response = self.session.post(url, timeout=self.timeout)
            result = response.json() if response.content else {}

            # 清理客户端状态
            self.token = None
            self.user_profile = None
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']

            self.logger.info("用户登出成功")

            # 触发回调
            if self.on_logout:
                self.on_logout()

            return {
                'success': True,
                'message': '登出成功'
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"登出请求失败: {e}")
            # 即使请求失败也清理本地状态
            self.token = None
            self.user_profile = None
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']

            return {
                'success': False,
                'message': f"登出请求失败: {str(e)}"
            }

    def validate_token(self, token: str = None) -> Dict[str, Any]:
        """
        验证令牌有效性

        Args:
            token: 要验证的令牌，默认使用当前令牌

        Returns:
            dict: 验证结果
        """
        if not token:
            if not self.token:
                return {'valid': False, 'message': '没有可验证的令牌'}
            token = self.token.access_token

        url = urljoin(self.base_url, '/api/v1/auth/validate')
        data = {'token': token}

        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            result = response.json()

            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"令牌验证请求失败: {e}")
            return {'valid': False, 'message': f"验证请求失败: {str(e)}"}

    def refresh_token(self) -> bool:
        """
        刷新访问令牌

        Returns:
            bool: 刷新是否成功

        Raises:
            AuthenticationError: 刷新失败
        """
        if not self.token or not self.token.refresh_token:
            raise AuthenticationError("没有可用的刷新令牌")

        url = urljoin(self.base_url, '/api/v1/auth/refresh')
        data = {'refresh_token': self.token.refresh_token}

        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            result = response.json()

            if response.status_code == 200 and result.get('success'):
                # 更新令牌
                self.token = AuthToken(
                    access_token=result['access_token'],
                    refresh_token=result['refresh_token'],
                    expires_in=result.get('expires_in', 3600)
                )

                # 更新会话头部
                self.session.headers['Authorization'] = f"Bearer {self.token.access_token}"

                self.logger.info("令牌刷新成功")

                # 触发回调
                if self.on_token_refreshed:
                    self.on_token_refreshed(self.token)

                return True
            else:
                error_message = result.get('message', '刷新令牌失败')
                raise AuthenticationError(error_message, response.status_code)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"刷新令牌请求失败: {e}")
            raise AuthenticationError(f"网络请求失败: {str(e)}")

    def get_profile(self) -> Optional[UserProfile]:
        """
        获取用户档案

        Returns:
            UserProfile: 用户档案对象

        Raises:
            AuthenticationError: 获取失败
        """
        if not self.token:
            raise AuthenticationError("未登录")

        # 自动刷新即将过期的令牌
        if self.token.will_expire_soon:
            self.refresh_token()

        url = urljoin(self.base_url, '/api/v1/auth/profile')

        try:
            response = self.session.get(url, timeout=self.timeout)
            result = response.json()

            if response.status_code == 200 and result.get('success'):
                profile_data = result['user_profile']

                # 更新缓存的用户档案
                self.user_profile = UserProfile(
                    user_id=profile_data['user_id'],
                    username=profile_data['username'],
                    email=profile_data['email'],
                    role=profile_data['role'],
                    permissions=profile_data.get('permissions', []),
                    is_active=profile_data.get('is_active', True)
                )

                return self.user_profile
            else:
                error_message = result.get('message', '获取用户档案失败')
                raise AuthenticationError(error_message, response.status_code)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取用户档案请求失败: {e}")
            raise AuthenticationError(f"网络请求失败: {str(e)}")

    def make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送认证请求

        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数

        Returns:
            requests.Response: 响应对象

        Raises:
            AuthenticationError: 认证失败
            TokenExpiredError: 令牌过期
        """
        if not self.token:
            raise AuthenticationError("未登录")

        # 检查令牌是否即将过期
        if self.token.will_expire_soon:
            try:
                self.refresh_token()
            except AuthenticationError:
                # 刷新失败，可能需要重新登录
                self.token = None
                self.user_profile = None
                raise TokenExpiredError("令牌已过期，需要重新登录")

        # 确保URL是完整的
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)

        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)

            # 处理认证错误
            if response.status_code == 401:
                # 尝试刷新令牌
                try:
                    self.refresh_token()
                    # 重新发送请求
                    response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                except AuthenticationError:
                    raise TokenExpiredError("令牌已过期，需要重新登录")

            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"认证请求失败: {e}")
            raise AuthenticationError(f"网络请求失败: {str(e)}")

    def has_permission(self, permission: str) -> bool:
        """
        检查用户是否具有指定权限

        Args:
            permission: 权限字符串

        Returns:
            bool: 是否具有权限
        """
        if not self.user_profile or not self.user_profile.permissions:
            return False

        # 检查精确匹配
        if permission in self.user_profile.permissions:
            return True

        # 检查通配符权限
        for user_perm in self.user_profile.permissions:
            if user_perm.endswith(':*'):
                perm_prefix = user_perm[:-1]  # 去掉 '*'
                if permission.startswith(perm_prefix):
                    return True

        return False

    def check_health(self) -> Dict[str, Any]:
        """
        检查API健康状态

        Returns:
            dict: 健康状态
        """
        url = urljoin(self.base_url, '/api/v1/auth/health')

        try:
            start_time = time.time()
            response = self.session.get(url, timeout=self.timeout)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return {
                    'healthy': True,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'healthy': False,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except requests.exceptions.RequestException as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    @property
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.token is not None and not self.token.is_expired

    def close(self):
        """关闭客户端会话"""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncPerfect21AuthClient:
    """异步版本的Perfect21认证API客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.token: Optional[AuthToken] = None
        self.user_profile: Optional[UserProfile] = None
        self.session: Optional[aiohttp.ClientSession] = None

        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Perfect21-AsyncAuthClient/1.0.0',
                'Accept': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def login(self, username: str, password: str, remember_me: bool = False,
                   captcha_token: str = None) -> Dict[str, Any]:
        """异步登录"""
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用 async with 语句")

        url = urljoin(self.base_url, '/api/v1/auth/login')

        data = {
            'username': username,
            'password': password,
            'remember_me': remember_me,
            'device_fingerprint': self._get_device_fingerprint()
        }

        if captcha_token:
            data['captcha_token'] = captcha_token

        try:
            async with self.session.post(url, json=data) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    # 保存令牌
                    self.token = AuthToken(
                        access_token=result['access_token'],
                        refresh_token=result['refresh_token'],
                        expires_in=result.get('expires_in', 3600)
                    )

                    # 保存用户档案
                    if result.get('user_profile'):
                        profile_data = result['user_profile']
                        self.user_profile = UserProfile(
                            user_id=profile_data['user_id'],
                            username=profile_data['username'],
                            email=profile_data['email'],
                            role=profile_data['role'],
                            permissions=result.get('permissions', []),
                            is_active=profile_data.get('is_active', True)
                        )

                    # 更新会话头部
                    self.session.headers['Authorization'] = f"Bearer {self.token.access_token}"

                    return {
                        'success': True,
                        'message': '登录成功',
                        'user_profile': asdict(self.user_profile),
                        'token': asdict(self.token)
                    }
                else:
                    error_message = result.get('message', '登录失败')
                    raise AuthenticationError(error_message, response.status)

        except aiohttp.ClientError as e:
            self.logger.error(f"异步登录请求失败: {e}")
            raise AuthenticationError(f"网络请求失败: {str(e)}")

    def _get_device_fingerprint(self) -> str:
        """生成设备指纹（与同步版本相同）"""
        import platform
        import socket

        device_info = {
            'hostname': socket.gethostname(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }

        device_str = json.dumps(device_info, sort_keys=True)
        return hashlib.sha256(device_str.encode()).hexdigest()[:32]

    async def make_authenticated_request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """发送异步认证请求"""
        if not self.session:
            raise RuntimeError("客户端未初始化")

        if not self.token:
            raise AuthenticationError("未登录")

        # 检查令牌是否即将过期
        if self.token.will_expire_soon:
            await self.refresh_token()

        # 确保URL是完整的
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)

        return await self.session.request(method, url, **kwargs)

    async def refresh_token(self) -> bool:
        """异步刷新令牌"""
        if not self.session or not self.token or not self.token.refresh_token:
            raise AuthenticationError("没有可用的刷新令牌")

        url = urljoin(self.base_url, '/api/v1/auth/refresh')
        data = {'refresh_token': self.token.refresh_token}

        try:
            async with self.session.post(url, json=data) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    self.token = AuthToken(
                        access_token=result['access_token'],
                        refresh_token=result['refresh_token'],
                        expires_in=result.get('expires_in', 3600)
                    )

                    # 更新会话头部
                    self.session.headers['Authorization'] = f"Bearer {self.token.access_token}"

                    return True
                else:
                    error_message = result.get('message', '刷新令牌失败')
                    raise AuthenticationError(error_message, response.status)

        except aiohttp.ClientError as e:
            self.logger.error(f"异步刷新令牌请求失败: {e}")
            raise AuthenticationError(f"网络请求失败: {str(e)}")


# 便利函数
def create_auth_client(base_url: str, timeout: int = 30) -> Perfect21AuthClient:
    """创建认证客户端实例"""
    return Perfect21AuthClient(base_url, timeout)


def create_async_auth_client(base_url: str, timeout: int = 30) -> AsyncPerfect21AuthClient:
    """创建异步认证客户端实例"""
    return AsyncPerfect21AuthClient(base_url, timeout)


# 使用示例
if __name__ == '__main__':
    import logging

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 同步客户端示例
    print("🔐 Perfect21认证API客户端SDK示例")
    print("=" * 50)

    # 创建客户端
    client = create_auth_client('http://localhost:8080')

    try:
        # 登录
        login_result = client.login('testuser', 'testpass123')
        print(f"✅ 登录成功: {login_result['user_profile']['username']}")

        # 检查权限
        has_read = client.has_permission('user:read')
        print(f"📋 读取权限: {'✅' if has_read else '❌'}")

        # 获取档案
        profile = client.get_profile()
        print(f"👤 用户角色: {profile.role}")

        # 检查健康状态
        health = client.check_health()
        print(f"🏥 API健康: {'✅' if health['healthy'] else '❌'}")

        # 登出
        logout_result = client.logout()
        print(f"👋 {logout_result['message']}")

    except AuthenticationError as e:
        print(f"❌ 认证错误: {e}")
    except Exception as e:
        print(f"💥 其他错误: {e}")

    finally:
        client.close()

    print("\n✅ 客户端SDK演示完成")