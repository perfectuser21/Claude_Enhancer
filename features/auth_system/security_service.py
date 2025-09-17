#!/usr/bin/env python3
"""
Perfect21安全服务
负责安全策略、防护机制和安全验证
"""

import os
import sys
import re
import time
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from modules.logger import log_info, log_error, log_warning

class SecurityService:
    """安全服务类"""

    def __init__(self):
        """初始化安全服务"""
        # 登录尝试限制
        self.login_attempts: Dict[str, List[datetime]] = {}
        self.max_attempts = 5  # 最大登录尝试次数
        self.lockout_duration = timedelta(minutes=15)  # 锁定时长

        # 密码策略
        self.password_min_length = 8
        self.password_require_uppercase = True
        self.password_require_lowercase = True
        self.password_require_digits = True
        self.password_require_special = True

        # 常见弱密码列表
        self.common_passwords = {
            '123456', 'password', '123456789', '12345678', '12345',
            'qwerty', 'abc123', 'password123', 'admin', 'letmein',
            'welcome', '123123', 'password1', '1234567890'
        }

        # 安全事件记录
        self.security_events: List[Dict[str, Any]] = []

        log_info("SecurityService初始化完成")

    def validate_password(self, password: str) -> Dict[str, Any]:
        """验证密码强度"""
        errors = []

        # 长度检查
        if len(password) < self.password_min_length:
            errors.append(f"密码长度不能少于{self.password_min_length}个字符")

        # 大写字母检查
        if self.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含至少一个大写字母")

        # 小写字母检查
        if self.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("密码必须包含至少一个小写字母")

        # 数字检查
        if self.password_require_digits and not re.search(r'\d', password):
            errors.append("密码必须包含至少一个数字")

        # 特殊字符检查
        if self.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含至少一个特殊字符")

        # 常见密码检查
        if password.lower() in self.common_passwords:
            errors.append("不能使用常见弱密码")

        # 重复字符检查
        if len(set(password)) < len(password) / 2:
            errors.append("密码不能包含过多重复字符")

        return {
            'valid': len(errors) == 0,
            'error': '; '.join(errors) if errors else None,
            'strength': self._calculate_password_strength(password)
        }

    def _calculate_password_strength(self, password: str) -> str:
        """计算密码强度"""
        score = 0

        # 长度加分
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1

        # 字符多样性加分
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1

        # 复杂性加分
        if len(set(password)) / len(password) > 0.7:
            score += 1

        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        elif score <= 6:
            return "strong"
        else:
            return "very_strong"

    def validate_email(self, email: str) -> Dict[str, Any]:
        """验证邮箱格式"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return {
                'valid': False,
                'error': '邮箱格式不正确'
            }

        # 检查邮箱长度
        if len(email) > 254:
            return {
                'valid': False,
                'error': '邮箱地址过长'
            }

        return {
            'valid': True,
            'error': None
        }

    def validate_username(self, username: str) -> Dict[str, Any]:
        """验证用户名格式"""
        errors = []

        # 长度检查
        if len(username) < 3:
            errors.append("用户名长度不能少于3个字符")
        elif len(username) > 30:
            errors.append("用户名长度不能超过30个字符")

        # 字符检查
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append("用户名只能包含字母、数字、下划线和短横线")

        # 开头检查
        if not re.match(r'^[a-zA-Z0-9]', username):
            errors.append("用户名必须以字母或数字开头")

        # 保留字检查
        reserved_words = {
            'admin', 'root', 'user', 'test', 'api', 'www',
            'ftp', 'mail', 'email', 'system', 'null', 'undefined'
        }
        if username.lower() in reserved_words:
            errors.append("用户名不能使用保留字")

        return {
            'valid': len(errors) == 0,
            'error': '; '.join(errors) if errors else None
        }

    def validate_registration(self, username: str, email: str,
                            password: str) -> Dict[str, Any]:
        """验证注册信息"""
        # 验证用户名
        username_validation = self.validate_username(username)
        if not username_validation['valid']:
            return username_validation

        # 验证邮箱
        email_validation = self.validate_email(email)
        if not email_validation['valid']:
            return email_validation

        # 验证密码
        password_validation = self.validate_password(password)
        if not password_validation['valid']:
            return password_validation

        return {
            'valid': True,
            'error': None
        }

    def check_login_attempts(self, identifier: str) -> bool:
        """检查登录尝试次数"""
        now = datetime.now()

        if identifier not in self.login_attempts:
            return True

        # 清理过期的尝试记录
        cutoff_time = now - self.lockout_duration
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if attempt > cutoff_time
        ]

        # 检查是否超过限制
        attempt_count = len(self.login_attempts[identifier])
        if attempt_count >= self.max_attempts:
            self._log_security_event('LOGIN_ATTEMPTS_EXCEEDED', {
                'identifier': identifier,
                'attempt_count': attempt_count
            })
            return False

        return True

    def record_failed_attempt(self, identifier: str):
        """记录失败的登录尝试"""
        now = datetime.now()

        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []

        self.login_attempts[identifier].append(now)

        self._log_security_event('FAILED_LOGIN_ATTEMPT', {
            'identifier': identifier,
            'timestamp': now.isoformat()
        })

        log_warning(f"登录失败尝试: {identifier}")

    def clear_failed_attempts(self, identifier: str):
        """清除失败的登录尝试记录"""
        if identifier in self.login_attempts:
            del self.login_attempts[identifier]

    def detect_suspicious_activity(self, user_id: str, activity_type: str,
                                 details: Dict[str, Any] = None) -> bool:
        """检测可疑活动"""
        suspicious_indicators = []

        # 这里可以添加更多的可疑活动检测逻辑
        # 例如：异常登录时间、异常IP地址、频繁操作等

        if suspicious_indicators:
            self._log_security_event('SUSPICIOUS_ACTIVITY', {
                'user_id': user_id,
                'activity_type': activity_type,
                'indicators': suspicious_indicators,
                'details': details
            })
            return True

        return False

    def validate_api_rate_limit(self, user_id: str, endpoint: str,
                              window_minutes: int = 1,
                              max_requests: int = 60) -> bool:
        """API速率限制验证"""
        # 简化实现，实际应用中建议使用Redis等缓存
        key = f"{user_id}:{endpoint}"
        now = datetime.now()

        # 这里应该实现具体的速率限制逻辑
        # 暂时返回True，表示通过验证
        return True

    def sanitize_input(self, input_str: str) -> str:
        """输入清理"""
        if not isinstance(input_str, str):
            return str(input_str)

        # 移除潜在危险字符
        sanitized = input_str.strip()

        # HTML转义
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        sanitized = sanitized.replace('&', '&amp;')

        return sanitized

    def validate_file_upload(self, filename: str, file_size: int,
                           file_content: bytes = None) -> Dict[str, Any]:
        """文件上传安全验证"""
        errors = []

        # 文件名检查
        if not filename or len(filename) > 255:
            errors.append("文件名无效或过长")

        # 文件扩展名检查
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx'}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            errors.append(f"不允许的文件类型: {file_ext}")

        # 文件大小检查
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            errors.append("文件大小超出限制")

        # 文件内容检查（如果提供）
        if file_content:
            # 检查文件头部是否匹配扩展名
            # 这里可以添加更多的文件内容验证逻辑
            pass

        return {
            'valid': len(errors) == 0,
            'error': '; '.join(errors) if errors else None
        }

    def generate_csrf_token(self, user_id: str) -> str:
        """生成CSRF令牌"""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return f"{token}:{timestamp}"

    def validate_csrf_token(self, token: str, user_id: str,
                           max_age: int = 3600) -> bool:
        """验证CSRF令牌"""
        try:
            token_hash, timestamp = token.split(':')
            token_time = int(timestamp)

            # 检查时间有效性
            if time.time() - token_time > max_age:
                return False

            # 重新计算令牌
            data = f"{user_id}:{timestamp}"
            expected_hash = hashlib.sha256(data.encode()).hexdigest()

            return token_hash == expected_hash

        except (ValueError, TypeError):
            return False

    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """记录安全事件"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }

        self.security_events.append(event)

        # 保持事件日志大小合理
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-500:]

        log_warning(f"安全事件: {event_type} - {details}")

    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取安全事件记录"""
        return self.security_events[-limit:]

    def get_security_stats(self) -> Dict[str, Any]:
        """获取安全统计信息"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > hour_ago
        ]

        daily_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > day_ago
        ]

        return {
            'total_events': len(self.security_events),
            'events_last_hour': len(recent_events),
            'events_last_day': len(daily_events),
            'locked_accounts': len(self.login_attempts),
            'password_policy': {
                'min_length': self.password_min_length,
                'require_uppercase': self.password_require_uppercase,
                'require_lowercase': self.password_require_lowercase,
                'require_digits': self.password_require_digits,
                'require_special': self.password_require_special
            }
        }

    def cleanup_old_events(self, max_age_days: int = 30):
        """清理旧的安全事件"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        self.security_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > cutoff_date
        ]

        log_info(f"清理了{max_age_days}天前的安全事件")

    def cleanup(self):
        """清理资源"""
        try:
            self.login_attempts.clear()
            self.security_events.clear()
            log_info("SecurityService清理完成")
        except Exception as e:
            log_error("SecurityService清理失败", e)