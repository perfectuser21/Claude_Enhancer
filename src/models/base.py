"""
基础数据模型定义
包含所有模型的通用字段和方法
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    """
    所有数据模型的基类
    提供通用字段：id, created_at, updated_at
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名，使用类名的下划线形式"""
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    # 主键ID - 使用UUID字符串格式
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, comment="主键ID"
    )

    # 创建时间 - 自动设置
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    # 更新时间 - 自动更新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典格式"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update(self, **kwargs) -> None:
        """批量更新模型属性"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """模型的字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"
