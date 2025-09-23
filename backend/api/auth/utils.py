"""
Claude Enhancer 认证API工具函数
提供认证相关的实用工具和辅助函数
"""

import re
import hashlib
import secrets
import base64
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import ipaddress
import user_agents
from urllib.parse import quote
import qrcode
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class PasswordValidator:
    """密码强度验证器"""

    # 常见弱密码模式
    WEAK_PATTERNS = [
        "password",
        "pass123",
        "123456",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "root",
        "user",
        "guest",
    ]

    # 键盘模式
    KEYBOARD_PATTERNS = ["qwerty", "asdf", "zxcv", "1234", "abcd"]

    @classmethod
    def validate_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """
        验证密码强度

        Args:
            password: 待验证的密码

        Returns:
            (是否通过验证, 错误消息列表)
        """
        errors = []

        # 长度检查
        if len(password) < 12:
            errors.append("密码长度至少12位")
        elif len(password) > 128:
            errors.append("密码长度不能超过128位")

        # 字符类型检查
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>[]\\/-_+=~`' for c in password)

        if not has_upper:
            errors.append("密码必须包含大写字母")
        if not has_lower:
            errors.append("密码必须包含小写字母")
        if not has_digit:
            errors.append("密码必须包含数字")
        if not has_special:
            errors.append("密码必须包含特殊字符")

        # 重复字符检查
        if cls._has_repeated_chars(password):
            errors.append("密码不能包含过多重复字符")

        # 顺序字符检查
        if cls._has_sequential_chars(password):
            errors.append("密码不能包含连续的字符序列")

        # 弱密码模式检查
        password_lower = password.lower()
        for pattern in cls.WEAK_PATTERNS:
            if pattern in password_lower:
                errors.append(f"密码不能包含常见弱密码模式: {pattern}")

        # 键盘模式检查
        for pattern in cls.KEYBOARD_PATTERNS:
            if pattern in password_lower:
                errors.append(f"密码不能包含键盘模式: {pattern}")

        return len(errors) == 0, errors

    @staticmethod
    def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:
        """检查是否有过多重复字符"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i - 1]:
                count += 1
                if count > max_repeat:
                    return True
            else:
                count = 1
        return False

    @staticmethod
    def _has_sequential_chars(password: str, max_sequence: int = 3) -> bool:
        """检查是否有连续字符序列"""
        for i in range(len(password) - max_sequence + 1):
            # 检查递增序列
            is_ascending = True
            is_descending = True

            for j in range(1, max_sequence):
                if ord(password[i + j]) != ord(password[i + j - 1]) + 1:
                    is_ascending = False
                if ord(password[i + j]) != ord(password[i + j - 1]) - 1:
                    is_descending = False

            if is_ascending or is_descending:
                return True

        return False

    @classmethod
    def calculate_entropy(cls, password: str) -> float:
        """
        计算密码熵值

        Args:
            password: 密码

        Returns:
            密码熵值（bits）
        """
        charset_size = 0

        # 统计字符集大小
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in '!@#$%^&*(),.?":{}|<>[]\\/-_+=~`' for c in password):
            charset_size += 32

        # 计算熵值
        import math

        if charset_size > 0:
            entropy = len(password) * math.log2(charset_size)
        else:
            entropy = 0

        return entropy


class DeviceFingerprint:
    """设备指纹生成器"""

    @staticmethod
    def generate(request_headers: Dict[str, str], ip_address: str) -> str:
        """
        生成设备指纹

        Args:
            request_headers: 请求头
            ip_address: IP地址

        Returns:
            设备指纹哈希值
        """
        # 提取关键信息
        user_agent = request_headers.get("user-agent", "")
        accept_language = request_headers.get("accept-language", "")
        accept_encoding = request_headers.get("accept-encoding", "")
        accept = request_headers.get("accept", "")

        # 组合指纹信息
        fingerprint_data = "|".join(
            [user_agent, accept_language, accept_encoding, accept, ip_address]
        )

        # 生成哈希
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    @staticmethod
    def analyze_user_agent(user_agent: str) -> Dict[str, Any]:
        """
        分析User-Agent字符串

        Args:
            user_agent: User-Agent字符串

        Returns:
            设备信息字典
        """
        try:
            ua = user_agents.parse(user_agent)
            return {
                "browser": {
                    "family": ua.browser.family,
                    "version": ua.browser.version_string,
                },
                "os": {"family": ua.os.family, "version": ua.os.version_string},
                "device": {
                    "family": ua.device.family,
                    "brand": ua.device.brand,
                    "model": ua.device.model,
                },
                "is_mobile": ua.is_mobile,
                "is_tablet": ua.is_tablet,
                "is_pc": ua.is_pc,
                "is_bot": ua.is_bot,
            }
        except Exception as e:
            logger.warning(f"User-Agent解析失败: {e}")
            return {
                "browser": {"family": "Unknown", "version": ""},
                "os": {"family": "Unknown", "version": ""},
                "device": {"family": "Unknown", "brand": "", "model": ""},
                "is_mobile": False,
                "is_tablet": False,
                "is_pc": True,
                "is_bot": False,
            }


class SecurityAnalyzer:
    """安全分析器"""

    # 可疑IP范围（示例）
    SUSPICIOUS_IP_RANGES = [
        "127.0.0.0/8",  # 本地回环
        "10.0.0.0/8",  # 私有网络
        "172.16.0.0/12",  # 私有网络
        "192.168.0.0/16",  # 私有网络
    ]

    # 已知恶意User-Agent模式
    MALICIOUS_UA_PATTERNS = [
        r"sqlmap",
        r"nikto",
        r"nmap",
        r"masscan",
        r"python-requests",
        r"curl",
        r"wget",
    ]

    @classmethod
    def analyze_login_risk(
        cls,
        user_id: str,
        ip_address: str,
        user_agent: str,
        login_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        分析登录风险

        Args:
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User-Agent
            login_history: 登录历史

        Returns:
            风险分析结果
        """
        risk_score = 0
        risk_factors = []

        # IP地址风险分析
        ip_risk = cls._analyze_ip_risk(ip_address, login_history)
        risk_score += ip_risk["score"]
        risk_factors.extend(ip_risk["factors"])

        # 设备风险分析
        device_risk = cls._analyze_device_risk(user_agent, login_history)
        risk_score += device_risk["score"]
        risk_factors.extend(device_risk["factors"])

        # 时间模式分析
        time_risk = cls._analyze_time_pattern(login_history)
        risk_score += time_risk["score"]
        risk_factors.extend(time_risk["factors"])

        # 地理位置分析（如果有IP地理信息）
        geo_risk = cls._analyze_geographic_risk(ip_address, login_history)
        risk_score += geo_risk["score"]
        risk_factors.extend(geo_risk["factors"])

        # 确定风险等级
        if risk_score >= 80:
            risk_level = "HIGH"
        elif risk_score >= 50:
            risk_level = "MEDIUM"
        elif risk_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "requires_additional_verification": risk_score >= 50,
            "block_login": risk_score >= 90,
        }

    @classmethod
    def _analyze_ip_risk(
        cls, ip_address: str, login_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析IP地址风险"""
        risk_score = 0
        factors = []

        try:
            ip = ipaddress.ip_address(ip_address)

            # 检查是否为可疑IP范围
            for suspicious_range in cls.SUSPICIOUS_IP_RANGES:
                if ip in ipaddress.ip_network(suspicious_range):
                    risk_score += 20
                    factors.append(f"IP在可疑范围内: {suspicious_range}")
                    break

            # 检查IP使用频率
            recent_logins = [
                login
                for login in login_history
                if (datetime.utcnow() - login.get("timestamp", datetime.min)).days <= 30
            ]

            ip_usage = sum(
                1 for login in recent_logins if login.get("ip_address") == ip_address
            )
            total_recent = len(recent_logins)

            if total_recent > 0:
                ip_ratio = ip_usage / total_recent
                if ip_ratio < 0.1:  # 新IP地址
                    risk_score += 30
                    factors.append("新IP地址")
                elif ip_ratio > 0.8:  # 主要使用的IP
                    risk_score -= 10  # 降低风险

        except Exception as e:
            logger.warning(f"IP风险分析失败: {e}")
            risk_score += 10
            factors.append("IP地址格式异常")

        return {"score": risk_score, "factors": factors}

    @classmethod
    def _analyze_device_risk(
        cls, user_agent: str, login_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析设备风险"""
        risk_score = 0
        factors = []

        # 检查恶意User-Agent模式
        for pattern in cls.MALICIOUS_UA_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                risk_score += 50
                factors.append(f"可疑User-Agent模式: {pattern}")

        # 检查User-Agent变化
        recent_agents = [login.get("user_agent", "") for login in login_history[-10:]]

        if user_agent not in recent_agents and len(recent_agents) > 0:
            risk_score += 20
            factors.append("新设备/浏览器")

        # 检查空User-Agent
        if not user_agent.strip():
            risk_score += 30
            factors.append("空User-Agent")

        return {"score": risk_score, "factors": factors}

    @classmethod
    def _analyze_time_pattern(
        cls, login_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析时间模式风险"""
        risk_score = 0
        factors = []

        if not login_history:
            return {"score": 0, "factors": []}

        now = datetime.utcnow()

        # 检查登录频率
        recent_hour = [
            login
            for login in login_history
            if (now - login.get("timestamp", datetime.min)).total_seconds() < 3600
        ]

        if len(recent_hour) > 10:
            risk_score += 40
            factors.append("登录频率过高")

        # 检查异常时间登录
        hour = now.hour
        if hour < 6 or hour > 23:  # 深夜或凌晨
            risk_score += 15
            factors.append("异常时间登录")

        return {"score": risk_score, "factors": factors}

    @classmethod
    def _analyze_geographic_risk(
        cls, ip_address: str, login_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析地理位置风险"""
        # TODO: 实现IP地理位置查询和分析
        # 这里需要集成IP地理位置服务
        return {"score": 0, "factors": []}


class QRCodeGenerator:
    """二维码生成器"""

    @staticmethod
    def generate_totp_qr(
        secret: str,
        user_email: str,
        issuer: str = "Claude Enhancer",
        algorithm: str = "SHA1",
        digits: int = 6,
        period: int = 30,
    ) -> str:
        """
        生成TOTP二维码

        Args:
            secret: TOTP密钥
            user_email: 用户邮箱
            issuer: 发行者名称
            algorithm: 算法
            digits: 验证码位数
            period: 时间周期

        Returns:
            二维码的base64编码字符串
        """
        # 构建TOTP URI
        totp_uri = (
            f"otpauth://totp/{quote(issuer)}:{quote(user_email)}"
            f"?secret={secret}"
            f"&issuer={quote(issuer)}"
            f"&algorithm={algorithm}"
            f"&digits={digits}"
            f"&period={period}"
        )

        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # 创建图像
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"


class TokenUtils:
    """Token工具类"""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        生成安全随机Token

        Args:
            length: Token长度

        Returns:
            安全随机Token
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_backup_codes(count: int = 10, length: int = 8) -> List[str]:
        """
        生成备用恢复码

        Args:
            count: 生成数量
            length: 每个码的长度

        Returns:
            备用恢复码列表
        """
        codes = []
        for _ in range(count):
            # 生成数字码
            code = "".join(secrets.choice("0123456789") for _ in range(length))
            codes.append(code)
        return codes

    @staticmethod
    def mask_sensitive_data(
        data: str, mask_char: str = "*", visible_chars: int = 4
    ) -> str:
        """
        掩码敏感数据

        Args:
            data: 原始数据
            mask_char: 掩码字符
            visible_chars: 可见字符数

        Returns:
            掩码后的数据
        """
        if len(data) <= visible_chars * 2:
            return mask_char * len(data)

        visible_start = data[:visible_chars]
        visible_end = data[-visible_chars:]
        mask_length = len(data) - visible_chars * 2

        return f"{visible_start}{mask_char * mask_length}{visible_end}"


class EmailValidator:
    """邮箱验证器"""

    # 一次性邮箱域名列表（示例）
    DISPOSABLE_DOMAINS = {
        "10minutemail.com",
        "guerrillamail.com",
        "mailinator.com",
        "tempmail.org",
        "yopmail.com",
        "throwaway.email",
    }

    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, List[str]]:
        """
        验证邮箱地址

        Args:
            email: 邮箱地址

        Returns:
            (是否通过验证, 错误消息列表)
        """
        errors = []

        # 基本格式检查
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            errors.append("邮箱格式不正确")
            return False, errors

        # 长度检查
        if len(email) > 254:
            errors.append("邮箱地址过长")

        # 域名检查
        domain = email.split("@")[1].lower()

        # 检查一次性邮箱
        if domain in cls.DISPOSABLE_DOMAINS:
            errors.append("不允许使用一次性邮箱")

        # 检查域名长度
        if len(domain) > 253:
            errors.append("邮箱域名过长")

        return len(errors) == 0, errors

    @staticmethod
    def normalize_email(email: str) -> str:
        """
        标准化邮箱地址

        Args:
            email: 原始邮箱

        Returns:
            标准化后的邮箱
        """
        # 转换为小写
        email = email.lower().strip()

        # Gmail特殊处理（移除.和+别名）
        if email.endswith("@gmail.com"):
            local, domain = email.split("@")
            # 移除点号
            local = local.replace(".", "")
            # 移除+号及之后的内容
            if "+" in local:
                local = local.split("+")[0]
            email = f"{local}@{domain}"

        return email


class RateLimiter:
    """速率限制器（内存版本，生产环境应使用Redis）"""

    def __init__(self):
        self._requests = {}

    def is_allowed(
        self, key: str, limit: int, window: int, current_time: Optional[datetime] = None
    ) -> bool:
        """
        检查是否允许请求

        Args:
            key: 限制键（如IP地址）
            limit: 请求限制数量
            window: 时间窗口（秒）
            current_time: 当前时间

        Returns:
            是否允许请求
        """
        if current_time is None:
            current_time = datetime.utcnow()

        window_start = current_time - timedelta(seconds=window)

        # 清理过期记录
        if key in self._requests:
            self._requests[key] = [
                req_time for req_time in self._requests[key] if req_time > window_start
            ]
        else:
            self._requests[key] = []

        # 检查是否超过限制
        if len(self._requests[key]) >= limit:
            return False

        # 记录当前请求
        self._requests[key].append(current_time)
        return True

    def get_remaining(self, key: str, limit: int, window: int) -> int:
        """获取剩余请求次数"""
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window)

        if key in self._requests:
            current_count = len(
                [
                    req_time
                    for req_time in self._requests[key]
                    if req_time > window_start
                ]
            )
            return max(0, limit - current_count)

        return limit
