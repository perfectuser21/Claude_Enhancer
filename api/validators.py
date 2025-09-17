#!/usr/bin/env python3
"""
Perfect21 API输入验证器
提供全面的输入验证和清理功能
"""

import re
import html
import unicodedata
from typing import Optional, Any, Dict, Set
from pydantic import BaseModel, validator, Field
from email_validator import validate_email, EmailNotValidError

# 安全的正则表达式模式
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# 严格的字段白名单
ALLOWED_SORT_FIELDS: Set[str] = {
    'id', 'username', 'email', 'created_at', 'updated_at', 'status'
}

ALLOWED_SEARCH_FIELDS: Set[str] = {
    'username', 'email', 'name', 'description'
}

# 数据库字段名验证模式（只允许字母、数字、下划线）
FIELD_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{0,63}$')

# 危险字符检测（用于额外安全检查）
DANGEROUS_CHARS = {'\x00', '\x08', '\x09', '\x0a', '\x0d', '\x1a', '\x22', '\x27', '\x5c'}

# SQL关键字黑名单（仅作为额外检查，不是主要防护）
SQL_KEYWORDS = {
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'UNION', 'EXEC', 'EXECUTE', 'SCRIPT', 'DECLARE', 'CAST', 'CONVERT'
}

class SecurityValidator:
    """安全验证器 - 使用白名单和参数化查询防护"""

    @staticmethod
    def validate_database_field(field_name: str, allowed_fields: Set[str]) -> str:
        """验证数据库字段名（白名单方式）"""
        if not field_name:
            raise ValueError("Field name cannot be empty")

        # 标准化输入
        field_name = field_name.strip().lower()

        # 白名单验证
        if field_name not in allowed_fields:
            raise ValueError(f"Invalid field name. Allowed: {', '.join(sorted(allowed_fields))}")

        # 额外安全检查：字段名格式验证
        if not FIELD_NAME_PATTERN.match(field_name):
            raise ValueError("Invalid field name format")

        return field_name

    @staticmethod
    def validate_safe_string(value: str, max_length: int = 1000, allow_special_chars: bool = False) -> str:
        """验证安全字符串（严格白名单方式）"""
        if not value:
            return ""

        # Unicode标准化
        value = unicodedata.normalize('NFKC', value)

        # 长度限制
        if len(value) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")

        # 检查危险字符
        if any(char in DANGEROUS_CHARS for char in value):
            raise ValueError("Input contains dangerous characters")

        # 严格的字符验证
        if not allow_special_chars:
            # 只允许字母、数字、空格、基本标点
            allowed_pattern = re.compile(r'^[a-zA-Z0-9\s\-_@.]+$')
            if not allowed_pattern.match(value):
                raise ValueError("Input contains invalid characters")

        return value.strip()

    @staticmethod
    def sanitize_search_query(query: str, max_length: int = 200) -> str:
        """清理搜索查询（用于全文搜索）"""
        if not query:
            return ""

        # Unicode标准化
        query = unicodedata.normalize('NFKC', query)

        # 长度限制
        query = query[:max_length]

        # HTML转义
        query = html.escape(query)

        # 移除危险字符
        query = ''.join(char for char in query if char not in DANGEROUS_CHARS)

        # 移除SQL关键字（额外安全措施）
        words = query.upper().split()
        filtered_words = [word for word in words if word not in SQL_KEYWORDS]

        # 重新组合并清理空白
        result = ' '.join(filtered_words)
        result = ' '.join(result.split())  # 标准化空白

        return result.strip()

    @staticmethod
    def validate_sort_order(order: str) -> str:
        """验证排序方向"""
        if not order:
            return 'ASC'

        order = order.upper().strip()
        if order not in {'ASC', 'DESC'}:
            raise ValueError("Sort order must be 'ASC' or 'DESC'")

        return order

    @staticmethod
    def create_safe_like_pattern(pattern: str) -> str:
        """创建安全的LIKE模式（转义特殊字符）"""
        if not pattern:
            return ""

        # 转义SQL LIKE特殊字符
        pattern = pattern.replace('\\', '\\\\')
        pattern = pattern.replace('%', '\\%')
        pattern = pattern.replace('_', '\\_')
        pattern = pattern.replace('[', '\\[')

        return f"%{pattern}%"

class AuthRequest(BaseModel):
    """认证请求验证"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @validator('username')
    def validate_username(cls, v):
        """验证用户名（严格验证）"""
        # 基本格式验证
        if not USERNAME_PATTERN.match(v):
            raise ValueError('Username must be 3-50 characters and contain only letters, numbers, underscore, and hyphen')

        # 使用安全验证器
        try:
            v = SecurityValidator.validate_safe_string(v, max_length=50, allow_special_chars=False)
        except ValueError as e:
            raise ValueError(f'Invalid username: {str(e)}')

        # 检查保留用户名
        reserved_names = {'admin', 'root', 'system', 'perfect21', 'api', 'test', 'administrator'}
        if v.lower() in reserved_names:
            raise ValueError('Username is reserved')

        return v

    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters')

        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f'Password must not exceed {PASSWORD_MAX_LENGTH} characters')

        # 检查密码复杂度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and numbers')

        # 检查常见弱密码
        weak_passwords = ['password', '12345678', 'qwerty', 'admin123']
        if v.lower() in weak_passwords:
            raise ValueError('Password is too weak')

        return v

class RegisterRequest(AuthRequest):
    """注册请求验证"""
    email: str = Field(..., max_length=254)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('email')
    def validate_email(cls, v):
        """验证邮箱"""
        try:
            # 验证邮箱格式
            validation = validate_email(v)
            # 返回标准化的邮箱
            return validation.email
        except EmailNotValidError:
            raise ValueError('Invalid email format')

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """确认密码匹配"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class TokenRequest(BaseModel):
    """Token请求验证"""
    token: str = Field(..., min_length=10, max_length=2000)

    @validator('token')
    def validate_token(cls, v):
        """验证token格式（严格验证）"""
        # 基本格式检查
        if not v or len(v) < 10:
            raise ValueError('Invalid token format')

        # Token应该只包含安全字符（Base64/JWT格式）
        token_pattern = re.compile(r'^[A-Za-z0-9\-_\.]+$')
        if not token_pattern.match(v):
            raise ValueError('Token contains invalid characters')

        # 长度限制
        if len(v) > 2000:
            raise ValueError('Token too long')

        return v

class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., min_length=10, max_length=2000)

    @validator('refresh_token')
    def validate_refresh_token(cls, v):
        """验证refresh token（严格验证）"""
        if not v or len(v) < 10:
            raise ValueError('Invalid refresh token')

        # Token应该只包含安全字符（Base64/JWT格式）
        token_pattern = re.compile(r'^[A-Za-z0-9\-_\.]+$')
        if not token_pattern.match(v):
            raise ValueError('Refresh token contains invalid characters')

        # 长度限制
        if len(v) > 2000:
            raise ValueError('Refresh token too long')

        return v

class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: str = Field(..., max_length=254)

    @validator('email')
    def validate_email(cls, v):
        """验证邮箱"""
        try:
            validation = validate_email(v)
            return validation.email
        except EmailNotValidError:
            raise ValueError('Invalid email format')

class NewPasswordRequest(BaseModel):
    """新密码请求"""
    reset_token: str = Field(..., min_length=10, max_length=2000)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password_strength(cls, v):
        """验证新密码强度"""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters')

        # 密码复杂度检查
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and numbers')

        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """确认密码匹配"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, le=10000)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field(None, max_length=50)
    order: Optional[str] = Field('asc', regex='^(asc|desc)$')

    @validator('sort_by')
    def validate_sort_field(cls, v):
        """验证排序字段（严格白名单）"""
        if v:
            try:
                return SecurityValidator.validate_database_field(v, ALLOWED_SORT_FIELDS)
            except ValueError as e:
                raise ValueError(str(e))
        return v

class SearchParams(BaseModel):
    """搜索参数"""
    query: str = Field(..., min_length=1, max_length=200)
    fields: Optional[list] = Field(None, max_items=10)

    @validator('query')
    def validate_query(cls, v):
        """验证搜索查询（严格清理）"""
        try:
            return SecurityValidator.sanitize_search_query(v, max_length=200)
        except ValueError as e:
            raise ValueError(f'Invalid search query: {str(e)}')

    @validator('fields')
    def validate_fields(cls, v):
        """验证搜索字段（严格白名单）"""
        if v:
            validated_fields = []
            for field in v:
                try:
                    validated_field = SecurityValidator.validate_database_field(field, ALLOWED_SEARCH_FIELDS)
                    validated_fields.append(validated_field)
                except ValueError as e:
                    raise ValueError(f'Invalid search field "{field}": {str(e)}')
            return validated_fields
        return v

def validate_request_data(data: Dict[str, Any], max_size: int = 10000) -> Dict[str, Any]:
    """
    通用请求数据验证（严格安全验证）

    Args:
        data: 请求数据
        max_size: 最大数据大小

    Returns:
        验证和清理后的数据
    """
    # 检查数据大小
    import json
    try:
        data_str = json.dumps(data, ensure_ascii=False)
        if len(data_str.encode('utf-8')) > max_size:
            raise ValueError(f'Request data too large (max {max_size} bytes)')
    except (TypeError, ValueError) as e:
        raise ValueError(f'Invalid request data format: {str(e)}')

    # 递归验证和清理数据
    def clean_value(value, depth=0):
        # 防止深度嵌套攻击
        if depth > 10:
            raise ValueError('Request data nesting too deep')

        if isinstance(value, str):
            try:
                return SecurityValidator.validate_safe_string(value, max_length=1000, allow_special_chars=True)
            except ValueError:
                # 对于可能包含特殊字符的字符串，使用更宽松的清理
                return SecurityValidator.sanitize_search_query(value, max_length=1000)
        elif isinstance(value, dict):
            if len(value) > 100:  # 限制字典大小
                raise ValueError('Request object has too many fields')
            return {str(k)[:100]: clean_value(v, depth + 1) for k, v in value.items()}
        elif isinstance(value, list):
            if len(value) > 1000:  # 限制数组大小
                raise ValueError('Request array too large')
            return [clean_value(v, depth + 1) for v in value]
        elif isinstance(value, (int, float, bool, type(None))):
            return value
        else:
            # 其他类型转换为字符串并验证
            str_value = str(value)[:1000]
            return SecurityValidator.validate_safe_string(str_value, allow_special_chars=True)

    return clean_value(data)

# 导出常用验证器
__all__ = [
    'SecurityValidator',
    'AuthRequest',
    'RegisterRequest',
    'TokenRequest',
    'RefreshTokenRequest',
    'PasswordResetRequest',
    'NewPasswordRequest',
    'PaginationParams',
    'SearchParams',
    'validate_request_data'
]