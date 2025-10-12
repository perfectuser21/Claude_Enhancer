"""
审计日志模型
============

定义系统审计相关的数据模型:
- AuditLog: 审计日志主表
- SecurityEvent: 安全事件表
- SystemLog: 系统日志表
"""

from datetime import datetime
from typing import Optional, Dict, Any
import enum
import json

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Index,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class AuditAction(enum.Enum):
    """审计操作枚举"""

    CREATE = "create"  # 创建
    READ = "read"  # 读取
    UPDATE = "update"  # 更新
    DELETE = "delete"  # 删除
    LOGIN = "login"  # 登录
    LOGOUT = "logout"  # 登出
    ACCESS = "access"  # 访问
    EXPORT = "export"  # 导出
    IMPORT = "import"  # 导入
    CONFIGURE = "configure"  # 配置


class AuditLevel(enum.Enum):
    """审计级别枚举"""

    DEBUG = "debug"  # 调试
    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


class EventType(enum.Enum):
    """安全事件类型"""

    LOGIN_SUCCESS = "login_success"  # 登录成功
    LOGIN_FAILURE = "login_failure"  # 登录失败
    LOGOUT = "logout"  # 登出
    PASSWORD_CHANGE = "password_change"  # 密码更改
    ACCOUNT_LOCKED = "account_locked"  # 账户锁定
    ACCOUNT_UNLOCKED = "account_unlocked"  # 账户解锁
    PERMISSION_DENIED = "permission_denied"  # 权限拒绝
    SUSPICIOUS_ACTIVITY = "suspicious_activity"  # 可疑活动
    DATA_BREACH = "data_breach"  # 数据泄露
    UNAUTHORIZED_ACCESS = "unauthorized_access"  # 未授权访问


class AuditLog(BaseModel):
    """
    审计日志主表
    ============

    记录系统中所有重要操作的审计日志:
    - 用户操作记录
    - 数据变更记录
    - 系统事件记录
    - 安全相关操作
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        # 创建索引 - 优化查询性能
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_level", "level"),
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_resource_type", "resource_type"),
        Index("idx_audit_logs_ip_address", "ip_address"),
        # 复合索引
        Index("idx_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_logs_resource_action", "resource_type", "action"),
        # 表注释
        {"comment": "审计日志表 - 记录系统所有重要操作的审计信息"},
    )

    # 操作主体
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作用户ID (系统操作时为NULL)",
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联会话ID",
    )

    # 操作信息
    action = Column(Enum(AuditAction), nullable=False, comment="操作类型")

    level = Column(
        Enum(AuditLevel), default=AuditLevel.INFO, nullable=False, comment="审计级别"
    )

    timestamp = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="操作时间戳",
    )

    # 资源信息
    resource_type = Column(String(100), nullable=False, comment="资源类型 (表名/模块名)")

    resource_id = Column(String(255), nullable=True, comment="资源ID")

    resource_name = Column(String(255), nullable=True, comment="资源名称")

    # 操作详情
    description = Column(Text, nullable=False, comment="操作描述")

    changes = Column(
        JSONB, nullable=True, comment="数据变更详情 (JSON格式: {before: {}, after: {}})"
    )

    # 请求信息
    request_method = Column(String(10), nullable=True, comment="HTTP请求方法")

    request_path = Column(String(500), nullable=True, comment="请求路径")

    request_params = Column(JSONB, nullable=True, comment="请求参数 (JSON格式)")

    # 网络信息
    ip_address = Column(INET, nullable=True, comment="客户端IP地址")

    user_agent = Column(Text, nullable=True, comment="用户代理字符串")

    # 结果信息
    success = Column(Boolean, default=True, nullable=False, comment="操作是否成功")

    error_message = Column(Text, nullable=True, comment="错误信息 (操作失败时)")

    response_time = Column(Integer, nullable=True, comment="响应时间 (毫秒)")

    # 扩展信息
    extra_metadata = Column(JSONB, nullable=True, comment="扩展元数据 (JSON格式)")

    # 关联关系
    user = relationship("User")
    session = relationship("Session")

    @classmethod
    def create_log(
        cls,
        action: AuditAction,
        resource_type: str,
        description: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        level: AuditLevel = AuditLevel.INFO,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        response_time: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """
        创建审计日志记录

        Args:
            action: 操作类型
            resource_type: 资源类型
            description: 操作描述
            user_id: 用户ID
            session_id: 会话ID
            resource_id: 资源ID
            resource_name: 资源名称
            level: 审计级别
            changes: 数据变更
            ip_address: IP地址
            user_agent: 用户代理
            request_method: 请求方法
            request_path: 请求路径
            request_params: 请求参数
            success: 是否成功
            error_message: 错误信息
            response_time: 响应时间
            extra_metadata: 扩展元数据

        Returns:
            新创建的审计日志对象
        """
        return cls(
            user_id=user_id,
            session_id=session_id,
            action=action,
            level=level,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            changes=changes,
            request_method=request_method,
            request_path=request_path,
            request_params=request_params,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            response_time=response_time,
            extra_metadata=extra_metadata,
            timestamp=datetime.utcnow(),
        )

    def add_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """
        添加字段变更记录

        Args:
            field: 字段名
            old_value: 原值
            new_value: 新值
        """
        if self.changes is None:
            self.changes = {"before": {}, "after": {}}

        self.changes["before"][field] = old_value
        self.changes["after"][field] = new_value

    @hybrid_property
    def duration_ms(self) -> Optional[int]:
        """获取操作耗时 (毫秒)"""
        return self.response_time

    def to_log_format(self) -> str:
        """转换为日志格式字符串"""
        log_data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action.value,
            "resource": f"{self.resource_type}:{self.resource_id}",
            "description": self.description,
            "ip": str(self.ip_address) if self.ip_address else None,
            "success": self.success,
        }

        if self.error_message:
            log_data["error"] = self.error_message

        if self.response_time:
            log_data["duration"] = f"{self.response_time}ms"

        return json.dumps(log_data, ensure_ascii=False)


class SecurityEvent(BaseModel):
    """
    安全事件表
    ===========

    专门记录安全相关的事件:
    - 登录异常
    - 权限违规
    - 可疑活动
    - 安全策略变更
    """

    __tablename__ = "security_events"
    __table_args__ = (
        Index("idx_security_events_user_id", "user_id"),
        Index("idx_security_events_event_type", "event_type"),
        Index("idx_security_events_timestamp", "timestamp"),
        Index("idx_security_events_severity", "severity"),
        Index("idx_security_events_resolved", "resolved"),
        {"comment": "安全事件表 - 记录系统安全相关事件"},
    )

    # 事件主体
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联用户ID",
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联会话ID",
    )

    # 事件信息
    event_type = Column(Enum(EventType), nullable=False, comment="事件类型")

    severity = Column(
        String(20),
        default="medium",
        nullable=False,
        comment="严重程度 (low/medium/high/critical)",
    )

    timestamp = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, comment="事件时间"
    )

    # 事件详情
    title = Column(String(255), nullable=False, comment="事件标题")

    description = Column(Text, nullable=False, comment="事件描述")

    details = Column(JSONB, nullable=True, comment="事件详细信息 (JSON格式)")

    # 网络信息
    ip_address = Column(INET, nullable=True, comment="来源IP地址")

    user_agent = Column(Text, nullable=True, comment="用户代理")

    # 处理状态
    resolved = Column(Boolean, default=False, nullable=False, comment="是否已处理")

    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="处理时间")

    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="处理人员ID",
    )

    resolution_notes = Column(Text, nullable=True, comment="处理备注")

    # 风险评估
    risk_score = Column(Integer, default=0, nullable=False, comment="风险评分 (0-100)")

    false_positive = Column(Boolean, default=False, nullable=False, comment="是否为误报")

    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("Session")
    resolver = relationship("User", foreign_keys=[resolved_by])

    @classmethod
    def create_event(
        cls,
        event_type: EventType,
        title: str,
        description: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        severity: str = "medium",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        risk_score: int = 0,
    ) -> "SecurityEvent":
        """创建安全事件"""
        return cls(
            event_type=event_type,
            title=title,
            description=description,
            user_id=user_id,
            session_id=session_id,
            severity=severity,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            risk_score=risk_score,
            timestamp=datetime.utcnow(),
        )

    def resolve(self, resolver_id: str, notes: str = None) -> None:
        """
        标记事件为已处理

        Args:
            resolver_id: 处理人员ID
            notes: 处理备注
        """
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolver_id
        self.resolution_notes = notes

    def mark_false_positive(self, resolver_id: str, notes: str = None) -> None:
        """
        标记为误报

        Args:
            resolver_id: 处理人员ID
            notes: 处理备注
        """
        self.false_positive = True
        self.resolve(resolver_id, notes)


class SystemLog(BaseModel):
    """
    系统日志表
    ===========

    记录系统级别的日志信息:
    - 应用启动/关闭
    - 配置变更
    - 系统错误
    - 性能监控
    """

    __tablename__ = "system_logs"
    __table_args__ = (
        Index("idx_system_logs_level", "level"),
        Index("idx_system_logs_timestamp", "timestamp"),
        Index("idx_system_logs_component", "component"),
        Index("idx_system_logs_correlation_id", "correlation_id"),
        {"comment": "系统日志表 - 记录系统级别的运行日志"},
    )

    # 日志基本信息
    level = Column(
        String(20), nullable=False, comment="日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)"
    )

    timestamp = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, comment="日志时间"
    )

    # 来源信息
    component = Column(String(100), nullable=False, comment="组件名称")

    module = Column(String(100), nullable=True, comment="模块名称")

    function = Column(String(100), nullable=True, comment="函数名称")

    # 日志内容
    message = Column(Text, nullable=False, comment="日志消息")

    details = Column(JSONB, nullable=True, comment="详细信息 (JSON格式)")

    # 追踪信息
    correlation_id = Column(String(255), nullable=True, comment="关联ID (用于追踪请求链路)")

    trace_id = Column(String(255), nullable=True, comment="追踪ID")

    span_id = Column(String(255), nullable=True, comment="跨度ID")

    # 异常信息
    exception_type = Column(String(255), nullable=True, comment="异常类型")

    exception_message = Column(Text, nullable=True, comment="异常消息")

    stack_trace = Column(Text, nullable=True, comment="堆栈跟踪")

    # 性能信息
    duration_ms = Column(BigInteger, nullable=True, comment="操作耗时 (毫秒)")

    memory_usage = Column(BigInteger, nullable=True, comment="内存使用量 (字节)")

    cpu_usage = Column(Integer, nullable=True, comment="CPU使用率 (百分比)")

    @classmethod
    def create_log(
        cls,
        level: str,
        component: str,
        message: str,
        module: Optional[str] = None,
        function: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        exception: Optional[Exception] = None,
        duration_ms: Optional[int] = None,
    ) -> "SystemLog":
        """创建系统日志"""
        log_entry = cls(
            level=level.upper(),
            component=component,
            module=module,
            function=function,
            message=message,
            details=details,
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
        )

        # 处理异常信息
        if exception:
            import traceback

            log_entry.exception_type = type(exception).__name__
            log_entry.exception_message = str(exception)
            log_entry.stack_trace = traceback.format_exc()

        return log_entry


# 导出模型
__all__ = [
    "AuditLog",
    "SecurityEvent",
    "SystemLog",
    "AuditAction",
    "AuditLevel",
    "EventType",
]
