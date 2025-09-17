import time
#!/usr/bin/env python3
"""
Perfect21 RBAC权限管理器
实现基于角色的访问控制(Role-Based Access Control)
"""

import os
import sys
import yaml
import re
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import unquote
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from modules.logger import log_info, log_error, log_warning
from modules.cache import cache_manager

class PermissionResult(Enum):
    """权限检查结果"""
    GRANTED = "granted"
    DENIED = "denied" 
    FORBIDDEN = "forbidden"
    UNAUTHORIZED = "unauthorized"

@dataclass
class AccessContext:
    """访问上下文"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Set[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = set()

@dataclass
class EndpointConfig:
    """端点配置"""
    path: str
    methods: List[str]
    auth_required: bool = True
    permissions: List[str] = None
    roles: List[str] = None
    resource_check: Optional[str] = None
    rate_limit: Optional[Dict] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.roles is None:
            self.roles = []

class RBACManager:
    """RBAC权限管理器"""
    
    def __init__(self, config_path: str = None):
        """初始化RBAC管理器"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "permissions_config.yaml"
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        self.roles = self._build_role_hierarchy()
        self.endpoints = self._build_endpoint_map()
        
        # 编译路径匹配正则
        self._compile_path_patterns()
        
        log_info("RBAC管理器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载权限配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 验证配置格式
            self._validate_config(config)
            
            log_info(f"权限配置加载成功: {self.config_path}")
            return config
            
        except Exception as e:
            log_error(f"权限配置加载失败: {self.config_path}", e)
            # 返回默认配置
            return self._get_default_config()
    
    def _validate_config(self, config: Dict[str, Any]):
        """验证配置格式"""
        required_sections = ['roles', 'endpoints']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"配置文件缺少必需部分: {section}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'roles': {
                'guest': {'permissions': []},
                'user': {'permissions': ['auth:profile:read']},
                'admin': {'permissions': ['auth:*']}
            },
            'endpoints': {
                'public': [
                    {'path': '/', 'methods': ['GET'], 'auth_required': False},
                    {'path': '/health', 'methods': ['GET'], 'auth_required': False}
                ]
            }
        }
    
    def _build_role_hierarchy(self) -> Dict[str, Dict]:
        """构建角色层次结构"""
        roles = {}
        
        for role_name, role_config in self.config['roles'].items():
            # 解析继承关系
            inherits = role_config.get('inherits', [])
            permissions = set(role_config.get('permissions', []))
            
            # 递归收集继承的权限
            all_permissions = self._collect_inherited_permissions(
                role_name, inherits, permissions
            )
            
            roles[role_name] = {
                'description': role_config.get('description', ''),
                'inherits': inherits,
                'permissions': all_permissions
            }
        
        return roles
    
    def _collect_inherited_permissions(self, role_name: str, 
                                     inherits: List[str], 
                                     permissions: Set[str]) -> Set[str]:
        """递归收集继承的权限"""
        all_permissions = permissions.copy()
        
        for parent_role in inherits:
            if parent_role in self.config['roles']:
                parent_config = self.config['roles'][parent_role]
                parent_inherits = parent_config.get('inherits', [])
                parent_permissions = set(parent_config.get('permissions', []))
                
                # 递归收集父角色权限
                inherited_permissions = self._collect_inherited_permissions(
                    parent_role, parent_inherits, parent_permissions
                )
                all_permissions.update(inherited_permissions)
        
        return all_permissions
    
    def _build_endpoint_map(self) -> Dict[str, List[EndpointConfig]]:
        """构建端点映射"""
        endpoints = {}
        
        for category, endpoint_list in self.config['endpoints'].items():
            endpoints[category] = []
            
            for endpoint_config in endpoint_list:
                config = EndpointConfig(**endpoint_config)
                endpoints[category].append(config)
        
        return endpoints
    
    def _compile_path_patterns(self):
        """编译路径匹配模式"""
        self.path_patterns = {}
        
        for category, endpoint_list in self.endpoints.items():
            self.path_patterns[category] = []
            
            for endpoint in endpoint_list:
                # 将路径参数转换为正则表达式
                pattern = self._path_to_regex(endpoint.path)
                compiled_pattern = re.compile(pattern)
                
                self.path_patterns[category].append({
                    'pattern': compiled_pattern,
                    'original_path': endpoint.path,
                    'config': endpoint
                })
    
    def _path_to_regex(self, path: str) -> str:
        """将路径转换为正则表达式"""
        # 转义特殊字符
        escaped = re.escape(path)
        
        # 替换路径参数 {param} -> (?P<param>[^/]+)
        pattern = re.sub(
            r'\\{([^}]+)\\}', 
            r'(?P<\1>[^/]+)', 
            escaped
        )
        
        # 添加开始和结束锚点
        return f'^{pattern}/?$'
    
    def normalize_path(self, path: str) -> str:
        """标准化路径"""
        try:
            # URL解码
            path = unquote(path)
            
            # 移除多余的斜杠
            path = re.sub(r'/+', '/', path)
            
            # 移除路径遍历
            path = re.sub(r'/\.\.?(?=/|$)', '', path)
            
            # 移除尾部斜杠(除了根路径)
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')
            
            # 检查路径长度
            max_length = self.config.get('path_matching', {}).get('max_path_length', 2048)
            if len(path) > max_length:
                log_warning(f"路径长度超过限制: {len(path)} > {max_length}")
                return None
            
            return path
            
        except Exception as e:
            log_error("路径标准化失败", e)
            return None
    
    def find_endpoint_config(self, path: str, method: str) -> Optional[EndpointConfig]:
        """查找端点配置"""
        normalized_path = self.normalize_path(path)
        if not normalized_path:
            return None
        
        # 按优先级搜索端点配置
        search_order = ['auth', 'users', 'system', 'public']
        
        for category in search_order:
            if category not in self.path_patterns:
                continue
            
            for pattern_info in self.path_patterns[category]:
                if pattern_info['pattern'].match(normalized_path):
                    config = pattern_info['config']
                    if method.upper() in [m.upper() for m in config.methods]:
                        return config
        
        return None
    
    def check_permission(self, context: AccessContext, 
                        path: str, method: str) -> Tuple[PermissionResult, str]:
        """检查权限"""
        try:
            # 查找端点配置
            endpoint_config = self.find_endpoint_config(path, method)
            if not endpoint_config:
                log_warning(f"未找到端点配置: {method} {path}")
                return PermissionResult.FORBIDDEN, "端点不存在或不允许访问"
            
            # 公开端点无需认证
            if not endpoint_config.auth_required:
                return PermissionResult.GRANTED, "公开端点"
            
            # 检查认证状态
            if not context.user_id or not context.role:
                return PermissionResult.UNAUTHORIZED, "需要认证"
            
            # 检查角色权限
            if endpoint_config.roles:
                if context.role not in endpoint_config.roles:
                    log_warning(f"角色权限不足: {context.role} not in {endpoint_config.roles}")
                    return PermissionResult.FORBIDDEN, "角色权限不足"
            
            # 检查具体权限
            if endpoint_config.permissions:
                if not self._has_permissions(context, endpoint_config.permissions):
                    log_warning(f"权限不足: {context.permissions} vs {endpoint_config.permissions}")
                    return PermissionResult.FORBIDDEN, "权限不足"
            
            # 记录成功访问
            self._audit_access(context, path, method, True, "访问granted")
            
            return PermissionResult.GRANTED, "权限检查通过"
            
        except Exception as e:
            log_error("权限检查失败", e)
            return PermissionResult.FORBIDDEN, "权限检查过程中发生错误"
    
    def _has_permissions(self, context: AccessContext, 
                        required_permissions: List[str]) -> bool:
        """检查是否具有所需权限"""
        user_permissions = self.get_user_permissions(context.role)
        
        for required_perm in required_permissions:
            if not self._check_single_permission(user_permissions, required_perm):
                return False
        
        return True
    
    def _check_single_permission(self, user_permissions: Set[str], 
                                required_perm: str) -> bool:
        """检查单个权限"""
        # 直接匹配
        if required_perm in user_permissions:
            return True
        
        # 通配符匹配
        for user_perm in user_permissions:
            if user_perm.endswith('*'):
                prefix = user_perm[:-1]
                if required_perm.startswith(prefix):
                    return True
        
        return False
    
    def get_user_permissions(self, role: str) -> Set[str]:
        """获取用户权限"""
        if role not in self.roles:
            log_warning(f"未知角色: {role}")
            return set()
        
        return self.roles[role]['permissions']
    
    def is_public_endpoint(self, path: str, method: str) -> bool:
        """检查是否为公开端点"""
        endpoint_config = self.find_endpoint_config(path, method)
        return endpoint_config and not endpoint_config.auth_required
    
    def get_endpoint_rate_limit(self, path: str, method: str) -> Optional[Dict]:
        """获取端点限流配置"""
        endpoint_config = self.find_endpoint_config(path, method)
        return endpoint_config.rate_limit if endpoint_config else None
    
    def _audit_access(self, context: AccessContext, path: str, 
                     method: str, granted: bool, reason: str):
        """审计访问记录"""
        try:
            audit_config = self.config.get('audit', {})
            if not audit_config.get('enabled', False):
                return
            
            should_log = False
            if granted and audit_config.get('log_access_granted', False):
                should_log = True
            elif not granted and audit_config.get('log_access_denied', True):
                should_log = True
            
            if should_log:
                audit_record = {
                    'timestamp': int(time.time()),
                    'user_id': context.user_id,
                    'username': context.username,
                    'role': context.role,
                    'path': path,
                    'method': method,
                    'granted': granted,
                    'reason': reason,
                    'ip_address': context.ip_address,
                    'user_agent': context.user_agent
                }
                
                # 记录到缓存中(实际项目中应该记录到数据库)
                audit_key = f"audit:access:{int(time.time())}"
                cache_manager.set(audit_key, audit_record, ttl=7776000)  # 90天
                
                log_info(f"访问审计: {method} {path} - {granted} - {reason}")
                
        except Exception as e:
            log_error("访问审计失败", e)
    
    def validate_role(self, role: str) -> bool:
        """验证角色是否有效"""
        return role in self.roles
    
    def get_role_info(self, role: str) -> Optional[Dict]:
        """获取角色信息"""
        return self.roles.get(role)
    
    def reload_config(self):
        """重新加载配置"""
        try:
            self.config = self._load_config()
            self.roles = self._build_role_hierarchy()
            self.endpoints = self._build_endpoint_map()
            self._compile_path_patterns()
            
            log_info("RBAC配置重新加载成功")
            return True
            
        except Exception as e:
            log_error("RBAC配置重新加载失败", e)
            return False

# 全局RBAC管理器实例
_rbac_manager = None

def get_rbac_manager() -> RBACManager:
    """获取全局RBAC管理器实例"""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager

# 装饰器支持
def require_permission(permissions: List[str], roles: List[str] = None):
    """权限装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 这里应该从请求上下文中获取用户信息
            # 实际实现需要结合具体的Web框架
            pass
        return wrapper
    return decorator

def require_role(roles: List[str]):
    """角色装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 实际实现需要结合具体的Web框架
            pass
        return wrapper
    return decorator
