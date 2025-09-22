"""
数据模型基类
=============

提供所有ORM模型的基础功能:
- 基础模型类 (Base)
- 时间戳混入 (TimestampMixin)
- 软删除混入 (SoftDeleteMixin)
- 通用查询方法
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

# 创建基础模型类
Base = declarative_base()


class TimestampMixin:
    """时间戳混入类 - 自动管理创建和更新时间"""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class SoftDeleteMixin:
    """软删除混入类 - 支持逻辑删除"""

    deleted_at = Column(
        DateTime(timezone=True), nullable=True, comment="删除时间 (NULL表示未删除)"
    )

    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除")

    def soft_delete(self):
        """执行软删除"""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = True

    def restore(self):
        """恢复已删除的记录"""
        self.deleted_at = None
        self.is_deleted = False


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    基础模型类
    ===========

    所有业务模型的基类，提供:
    - UUID主键
    - 时间戳管理
    - 软删除功能
    - 通用查询方法
    - 序列化方法
    """

    __abstract__ = True

    # 使用UUID作为主键
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="主键ID",
    )

    # 版本号 (用于乐观锁)
    version = Column(Integer, default=1, nullable=False, comment="版本号 (乐观锁)")

    @declared_attr
    def __tablename__(cls):
        """自动生成表名 - 类名转下划线格式"""
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        转换为字典格式

        Args:
            exclude: 要排除的字段列表

        Returns:
            字典格式的模型数据
        """
        exclude = exclude or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)

                # 处理特殊类型
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value

        return result

    def update_from_dict(
        self, data: Dict[str, Any], exclude: Optional[List[str]] = None
    ):
        """
        从字典更新模型数据

        Args:
            data: 要更新的数据字典
            exclude: 要排除的字段列表
        """
        exclude = exclude or ["id", "created_at", "updated_at"]

        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_table_comment(cls) -> str:
        """获取表注释"""
        return getattr(cls.__table__, "comment", cls.__name__)

    def __repr__(self):
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class AuditMixin:
    """审计混入类 - 记录操作信息"""

    created_by = Column(UUID(as_uuid=True), nullable=True, comment="创建者ID")

    updated_by = Column(UUID(as_uuid=True), nullable=True, comment="更新者ID")

    operation_type = Column(
        String(20), nullable=True, comment="操作类型 (CREATE/UPDATE/DELETE)"
    )

    operation_reason = Column(Text, nullable=True, comment="操作原因")


# 导出基类
__all__ = ["Base", "BaseModel", "TimestampMixin", "SoftDeleteMixin", "AuditMixin"]
