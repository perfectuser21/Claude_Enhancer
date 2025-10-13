"""
安全防护模块
实现防暴力破解、IP封禁、安全监控等功能
包含完整的安全防护机制和威胁检测
"""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    """威胁等级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """安全事件类型"""

    FAILED_LOGIN = "failed_login"
    SUCCESSFUL_LOGIN = "successful_login"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    IP_BLOCKED = "ip_blocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    TOKEN_ABUSE = "token_abuse"
    PASSWORD_ATTACK = "password_attack"
    ACCOUNT_LOCKOUT = "account_lockout"


@dataclass
class SecurityEvent:
    """安全事件"""

    event_type: SecurityEventType
    timestamp: datetime
    ip_address: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    threat_level: ThreatLevel = ThreatLevel.LOW


class BruteForceProtection:
    """暴力破解防护"""

    def __init__(
        self,
        max_attempts: int = 5,
        window_minutes: int = 15,
        lockout_minutes: int = 30,
        progressive_delay: bool = True,
    ):
        """
        初始化暴力破解防护

        Args:
            max_attempts: 最大尝试次数
            window_minutes: 时间窗口（分钟）
            lockout_minutes: 锁定时间（分钟）
            progressive_delay: 是否启用渐进延迟
        """
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.lockout_minutes = lockout_minutes
        self.progressive_delay = progressive_delay

        # 失败尝试记录: {identifier: [timestamps]}
        self.failed_attempts = defaultdict(list)

        # 锁定记录: {identifier: lockout_until}
        self.lockouts = {}

        # IP级别限制: {ip: [timestamps]}
        self.ip_attempts = defaultdict(list)

        # 用户级别限制: {user_id: [timestamps]}
        self.user_attempts = defaultdict(list)

    def is_locked(self, identifier: str) -> bool:
        """检查是否被锁定"""
        if identifier not in self.lockouts:
            return False

        lockout_until = self.lockouts[identifier]
        if datetime.utcnow() >= lockout_until:
            pass  # Auto-fixed empty block
            # 锁定时间已过，移除锁定
            del self.lockouts[identifier]
            return False

        return True

    def get_lockout_time(self, identifier: str) -> Optional[datetime]:
        """获取锁定截止时间"""
        return self.lockouts.get(identifier)

    def record_failed_attempt(
        self, identifier: str, ip_address: str = None, user_id: int = None
    ) -> Dict[str, Any]:
        """
        记录失败尝试

        Args:
            identifier: 标识符（用户名、邮箱等）
            ip_address: IP地址
            user_id: 用户ID

        Returns:
            Dict: 防护状态信息
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)

        # 清理过期记录
        self._cleanup_expired_attempts(identifier, window_start)

        # 记录新的失败尝试
        self.failed_attempts[identifier].append(now)

        # 记录IP级别尝试
        if ip_address:
            self._cleanup_expired_attempts(f"ip_{ip_address}", window_start, is_ip=True)
            self.ip_attempts[ip_address].append(now)

        # 记录用户级别尝试
        if user_id:
            self._cleanup_expired_attempts(
                f"user_{user_id}", window_start, is_user=True
            )
            self.user_attempts[user_id].append(now)

        # 检查是否需要锁定
        attempts_count = len(self.failed_attempts[identifier])
        ip_attempts_count = (
            len(self.ip_attempts.get(ip_address, [])) if ip_address else 0
        )
        user_attempts_count = len(self.user_attempts.get(user_id, [])) if user_id else 0

        lockout_applied = False
        lockout_reason = ""

        # 检查标识符级别限制
        if attempts_count >= self.max_attempts:
            lockout_until = now + timedelta(minutes=self.lockout_minutes)
            self.lockouts[identifier] = lockout_until
            lockout_applied = True
            lockout_reason = f"identifier_{identifier}"

        # 检查IP级别限制（更严格）
        if ip_address and ip_attempts_count >= self.max_attempts * 2:
            lockout_until = now + timedelta(minutes=self.lockout_minutes * 2)
            self.lockouts[f"ip_{ip_address}"] = lockout_until
            lockout_applied = True
            lockout_reason = f"ip_{ip_address}"

        # 检查用户级别限制
        if user_id and user_attempts_count >= self.max_attempts:
            lockout_until = now + timedelta(minutes=self.lockout_minutes)
            self.lockouts[f"user_{user_id}"] = lockout_until
            lockout_applied = True
            lockout_reason = f"user_{user_id}"

        return {
            "locked": lockout_applied,
            "lockout_reason": lockout_reason,
            "attempts_count": attempts_count,
            "max_attempts": self.max_attempts,
            "time_window_minutes": self.window_minutes,
            "lockout_minutes": self.lockout_minutes,
            "lockout_until": self.lockouts.get(lockout_reason)
            if lockout_applied
            else None,
            "next_attempt_delay": self._calculate_delay(attempts_count)
            if self.progressive_delay
            else 0,
        }

    def record_successful_attempt(
        self, identifier: str, ip_address: str = None, user_id: int = None
    ):
        """记录成功尝试（清除失败记录）"""
        # 清除失败尝试记录
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]

        if ip_address and ip_address in self.ip_attempts:
            del self.ip_attempts[ip_address]

        if user_id and user_id in self.user_attempts:
            del self.user_attempts[user_id]

        # 移除相关锁定
        self.lockouts.pop(identifier, None)
        if ip_address:
            self.lockouts.pop(f"ip_{ip_address}", None)
        if user_id:
            self.lockouts.pop(f"user_{user_id}", None)

    def get_remaining_attempts(self, identifier: str) -> int:
        """获取剩余尝试次数"""
        if self.is_locked(identifier):
            return 0

        attempts_count = len(self.failed_attempts.get(identifier, []))
        return max(0, self.max_attempts - attempts_count)

    def _cleanup_expired_attempts(
        self,
        identifier: str,
        window_start: datetime,
        is_ip: bool = False,
        is_user: bool = False,
    ):
        """清理过期的失败尝试记录"""
        if is_ip:
            ip = identifier.replace("ip_", "")
            if ip in self.ip_attempts:
                self.ip_attempts[ip] = [
                    attempt
                    for attempt in self.ip_attempts[ip]
                    if attempt > window_start
                ]
        elif is_user:
            user_id = int(identifier.replace("user_", ""))
            if user_id in self.user_attempts:
                self.user_attempts[user_id] = [
                    attempt
                    for attempt in self.user_attempts[user_id]
                    if attempt > window_start
                ]
        else:
            if identifier in self.failed_attempts:
                self.failed_attempts[identifier] = [
                    attempt
                    for attempt in self.failed_attempts[identifier]
                    if attempt > window_start
                ]

    def _calculate_delay(self, attempts_count: int) -> float:
        """计算渐进延迟时间（秒）"""
        if attempts_count <= 1:
            return 0

        # 指数退避算法
        delay = min(2 ** (attempts_count - 2), 60)  # 最大60秒
        return delay

    def get_protection_stats(self) -> Dict[str, Any]:
        """获取防护统计信息"""
        now = datetime.utcnow()
        active_lockouts = {
            identifier: lockout_time
            for identifier, lockout_time in self.lockouts.items()
            if lockout_time > now
        }

        return {
            "active_lockouts": len(active_lockouts),
            "total_failed_attempts": sum(
                len(attempts) for attempts in self.failed_attempts.values()
            ),
            "unique_identifiers_with_failures": len(self.failed_attempts),
            "ip_addresses_with_failures": len(self.ip_attempts),
            "users_with_failures": len(self.user_attempts),
            "lockout_details": {
                identifier: lockout_time.isoformat()
                for identifier, lockout_time in active_lockouts.items()
            },
        }


class IPBlocklist:
    """IP黑名单管理"""

    def __init__(self):
        self.permanent_blocks: Set[str] = set()
        self.temporary_blocks: Dict[str, datetime] = {}
        self.suspicious_ips: Dict[str, List[datetime]] = defaultdict(list)

    def add_permanent_block(self, ip_address: str, reason: str = ""):
        """添加永久封禁IP"""
        self.permanent_blocks.add(ip_address)
        self._log_block_event(ip_address, "permanent", reason)

    def add_temporary_block(
        self, ip_address: str, duration_minutes: int = 60, reason: str = ""
    ):
        """添加临时封禁IP"""
        until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.temporary_blocks[ip_address] = until
        self._log_block_event(ip_address, f"temporary_{duration_minutes}min", reason)

    def is_blocked(self, ip_address: str) -> bool:
        """检查IP是否被封禁"""
        # 检查永久封禁
        if ip_address in self.permanent_blocks:
            return True

        # 检查临时封禁
        if ip_address in self.temporary_blocks:
            if datetime.utcnow() < self.temporary_blocks[ip_address]:
                return True
            else:
                pass  # Auto-fixed empty block
                # 临时封禁已过期，移除
                del self.temporary_blocks[ip_address]

        return False

    def remove_block(self, ip_address: str) -> bool:
        """移除IP封禁"""
        removed = False

        if ip_address in self.permanent_blocks:
            self.permanent_blocks.remove(ip_address)
            removed = True

        if ip_address in self.temporary_blocks:
            del self.temporary_blocks[ip_address]
            removed = True

        return removed

    def mark_suspicious(self, ip_address: str):
        """标记IP为可疑"""
        now = datetime.utcnow()
        self.suspicious_ips[ip_address].append(now)

        # 清理24小时前的记录
        cutoff = now - timedelta(hours=24)
        self.suspicious_ips[ip_address] = [
            timestamp
            for timestamp in self.suspicious_ips[ip_address]
            if timestamp > cutoff
        ]

    def get_block_info(self, ip_address: str) -> Dict[str, Any]:
        """获取IP封禁信息"""
        info = {
            "ip_address": ip_address,
            "is_blocked": self.is_blocked(ip_address),
            "permanent_block": ip_address in self.permanent_blocks,
            "temporary_block": False,
            "temporary_until": None,
            "suspicious_activity_count": len(self.suspicious_ips.get(ip_address, [])),
        }

        if ip_address in self.temporary_blocks:
            info["temporary_block"] = True
            info["temporary_until"] = self.temporary_blocks[ip_address].isoformat()

        return info

    def cleanup_expired_blocks(self) -> int:
        """清理过期的临时封禁"""
        now = datetime.utcnow()
        expired_ips = [
            ip for ip, until in self.temporary_blocks.items() if until <= now
        ]

        for ip in expired_ips:
            del self.temporary_blocks[ip]

        return len(expired_ips)

    def _log_block_event(self, ip_address: str, block_type: str, reason: str):
        """记录封禁事件"""
        print(f"IP_BLOCK: {ip_address} blocked ({block_type}) - {reason}")


class SecurityMonitor:
    """安全监控"""

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: deque = deque(maxlen=max_events)
        self.threat_patterns = {
            "rapid_requests": {"threshold": 50, "window_seconds": 60},
            "multiple_user_agents": {"threshold": 5, "window_minutes": 10},
            "geographic_anomaly": {"enabled": False},  # 需要地理位置数据
            "credential_stuffing": {"threshold": 10, "window_minutes": 5},
        }

    def record_event(self, event: SecurityEvent):
        """记录安全事件"""
        self.events.append(event)
        self._analyze_threats(event)

    def _analyze_threats(self, event: SecurityEvent):
        """分析威胁模式"""
        # 检测快速请求
        if self._detect_rapid_requests(event):
            self._escalate_threat(event, ThreatLevel.HIGH, "Rapid requests detected")

        # 检测多用户代理
        if self._detect_multiple_user_agents(event):
            self._escalate_threat(
                event, ThreatLevel.MEDIUM, "Multiple user agents from same IP"
            )

        # 检测凭据填充攻击
        if self._detect_credential_stuffing(event):
            self._escalate_threat(
                event, ThreatLevel.HIGH, "Credential stuffing attack detected"
            )

    def _detect_rapid_requests(self, current_event: SecurityEvent) -> bool:
        """检测快速请求攻击"""
        config = self.threat_patterns["rapid_requests"]
        cutoff = current_event.timestamp - timedelta(seconds=config["window_seconds"])

        same_ip_events = [
            event
            for event in self.events
            if event.ip_address == current_event.ip_address and event.timestamp > cutoff
        ]

        return len(same_ip_events) > config["threshold"]

    def _detect_multiple_user_agents(self, current_event: SecurityEvent) -> bool:
        """检测多用户代理"""
        config = self.threat_patterns["multiple_user_agents"]
        cutoff = current_event.timestamp - timedelta(minutes=config["window_minutes"])

        same_ip_events = [
            event
            for event in self.events
            if event.ip_address == current_event.ip_address
            and event.timestamp > cutoff
            and event.details
            and "user_agent" in event.details
        ]

        unique_user_agents = set(
            event.details["user_agent"] for event in same_ip_events
        )

        return len(unique_user_agents) > config["threshold"]

    def _detect_credential_stuffing(self, current_event: SecurityEvent) -> bool:
        """检测凭据填充攻击"""
        if current_event.event_type != SecurityEventType.FAILED_LOGIN:
            return False

        config = self.threat_patterns["credential_stuffing"]
        cutoff = current_event.timestamp - timedelta(minutes=config["window_minutes"])

        # 检查短时间内来自同一IP的多个不同用户名登录失败
        same_ip_failed_logins = [
            event
            for event in self.events
            if event.ip_address == current_event.ip_address
            and event.event_type == SecurityEventType.FAILED_LOGIN
            and event.timestamp > cutoff
            and event.username
        ]

        unique_usernames = set(event.username for event in same_ip_failed_logins)
        return len(unique_usernames) > config["threshold"]

    def _escalate_threat(
        self, event: SecurityEvent, threat_level: ThreatLevel, reason: str
    ):
        """提升威胁等级"""
        escalated_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            timestamp=datetime.utcnow(),
            ip_address=event.ip_address,
            user_id=event.user_id,
            username=event.username,
            details={
                "original_event": event.event_type.value,
                "escalation_reason": reason,
                "threat_level": threat_level.value,
            },
            threat_level=threat_level,
        )

        self.record_event(escalated_event)
        print(
            f"THREAT_ESCALATION: {reason} - {threat_level.value} - IP: {event.ip_address}"
        )

    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取安全摘要"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_events = [event for event in self.events if event.timestamp > cutoff]

        event_counts = defaultdict(int)
        threat_levels = defaultdict(int)
        top_ips = defaultdict(int)

        for event in recent_events:
            event_counts[event.event_type.value] += 1
            threat_levels[event.threat_level.value] += 1
            top_ips[event.ip_address] += 1

        return {
            "time_period_hours": hours,
            "total_events": len(recent_events),
            "event_types": dict(event_counts),
            "threat_levels": dict(threat_levels),
            "top_ips": dict(
                sorted(top_ips.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "high_threat_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type.value,
                    "ip": event.ip_address,
                    "threat_level": event.threat_level.value,
                    "details": event.details,
                }
                for event in recent_events
                if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
            ],
        }


class TokenRefreshManager:
    """令牌刷新管理器"""

    def __init__(self, max_refresh_per_hour: int = 10):
        self.max_refresh_per_hour = max_refresh_per_hour
        self.refresh_history: Dict[int, List[datetime]] = defaultdict(list)

    def can_refresh(self, user_id: int) -> bool:
        """检查是否可以刷新令牌"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # 清理过期记录
        self.refresh_history[user_id] = [
            timestamp
            for timestamp in self.refresh_history[user_id]
            if timestamp > hour_ago
        ]

        return len(self.refresh_history[user_id]) < self.max_refresh_per_hour

    def record_refresh(self, user_id: int):
        """记录令牌刷新"""
        self.refresh_history[user_id].append(datetime.utcnow())

    def get_refresh_stats(self, user_id: int) -> Dict[str, Any]:
        """获取刷新统计"""
        hour_refreshes = len(self.refresh_history.get(user_id, []))
        return {
            "refreshes_last_hour": hour_refreshes,
            "max_per_hour": self.max_refresh_per_hour,
            "remaining": max(0, self.max_refresh_per_hour - hour_refreshes),
        }


# 全局安全组件实例
brute_force_protection = BruteForceProtection()
ip_blocklist = IPBlocklist()
security_monitor = SecurityMonitor()
token_refresh_manager = TokenRefreshManager()


class SecurityManager:
    """安全管理器 - 整合所有安全组件"""

    def __init__(self):
        self.brute_force = brute_force_protection
        self.ip_blocklist = ip_blocklist
        self.monitor = security_monitor
        self.token_refresh = token_refresh_manager

    def validate_login_attempt(
        self, identifier: str, ip_address: str, user_id: int = None
    ) -> Dict[str, Any]:
        """验证登录尝试"""
        # 检查IP是否被封禁
        if self.ip_blocklist.is_blocked(ip_address):
            return {
                "allowed": False,
                "reason": "IP address is blocked",
                "code": "IP_BLOCKED",
            }

        # 检查暴力破解防护
        if self.brute_force.is_locked(identifier):
            lockout_time = self.brute_force.get_lockout_time(identifier)
            return {
                "allowed": False,
                "reason": "Account temporarily locked due to too many failed attempts",
                "code": "ACCOUNT_LOCKED",
                "lockout_until": lockout_time.isoformat() if lockout_time else None,
            }

        return {"allowed": True}

    def handle_failed_login(
        self,
        identifier: str,
        ip_address: str,
        user_id: int = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """处理登录失败"""
        # 记录失败尝试
        result = self.brute_force.record_failed_attempt(identifier, ip_address, user_id)

        # 记录安全事件
        event = SecurityEvent(
            event_type=SecurityEventType.FAILED_LOGIN,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_id=user_id,
            username=identifier,
            details={"user_agent": user_agent} if user_agent else None,
        )
        self.monitor.record_event(event)

        # 如果被锁定，考虑临时封禁IP
        if result["locked"]:
            if result["attempts_count"] >= self.brute_force.max_attempts * 2:
                self.ip_blocklist.add_temporary_block(
                    ip_address, 60, "Multiple failed login attempts"
                )

        return result

    def handle_successful_login(
        self, identifier: str, ip_address: str, user_id: int, user_agent: str = None
    ):
        """处理登录成功"""
        # 清除失败记录
        self.brute_force.record_successful_attempt(identifier, ip_address, user_id)

        # 记录安全事件
        event = SecurityEvent(
            event_type=SecurityEventType.SUCCESSFUL_LOGIN,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_id=user_id,
            username=identifier,
            details={"user_agent": user_agent} if user_agent else None,
        )
        self.monitor.record_event(event)

    def validate_token_refresh(self, user_id: int) -> Dict[str, Any]:
        """验证令牌刷新请求"""
        if not self.token_refresh.can_refresh(user_id):
            return {
                "allowed": False,
                "reason": "Too many refresh requests",
                "code": "REFRESH_LIMIT_EXCEEDED",
            }

        return {"allowed": True}

    def record_token_refresh(self, user_id: int):
        """记录令牌刷新"""
        self.token_refresh.record_refresh(user_id)

    def get_security_status(self) -> Dict[str, Any]:
        """获取整体安全状态"""
        return {
            "brute_force_protection": self.brute_force.get_protection_stats(),
            "ip_blocks": {
                "permanent_blocks": len(self.ip_blocklist.permanent_blocks),
                "temporary_blocks": len(self.ip_blocklist.temporary_blocks),
            },
            "security_summary": self.monitor.get_security_summary(),
            "timestamp": datetime.utcnow().isoformat(),
        }


# 全局安全管理器实例
security_manager = SecurityManager()
