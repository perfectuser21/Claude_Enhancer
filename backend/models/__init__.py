"""
数据访问层 - ORM模型包
===========================

这个包包含所有的SQLAlchemy ORM模型定义:
- Base: 所有模型的基类
- User: 用户模型
- Session: 会话模型
- AuditLog: 审计日志模型

使用示例:
    from backend.models import User, Session

    # 创建用户
    user = User(username="john_doe", email="john@example.com")

    # 查询用户
    user = session.query(User).filter_by(username="john_doe").first()
"""

from .base import Base, TimestampMixin, SoftDeleteMixin
from .user import User
from .session import Session
from .audit import AuditLog

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "Session",
    "AuditLog",
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Perfect21 Team"
__description__ = "SQLAlchemy ORM模型层 - 提供完整的数据模型定义"
