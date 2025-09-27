"""
标签数据模型
管理任务标签和分类
"""

from typing import List, Optional
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .task import task_labels


class Label(BaseModel):
    """
    标签模型

    字段说明：
    - name: 标签名称
    - description: 标签描述
    - color: 标签颜色
    - is_system: 是否为系统标签
    - is_active: 是否激活
    - sort_order: 排序顺序
    """

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="标签名称"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="标签描述"
    )

    # 显示属性
    color: Mapped[str] = mapped_column(
        String(7), default="#6b7280", nullable=False, comment="标签颜色（HEX格式）"
    )

    # 状态属性
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否为系统标签"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )

    sort_order: Mapped[int] = mapped_column(default=0, nullable=False, comment="排序顺序")

    # 关系定义
    tasks: Mapped[List["Task"]] = relationship(
        "Task", secondary=task_labels, back_populates="labels", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Label(name={self.name}, color={self.color})>"

    @property
    def task_count(self) -> int:
        """使用此标签的任务数量"""
        return self.tasks.count()

    @property
    def is_deletable(self) -> bool:
        """是否可以删除（非系统标签且无关联任务）"""
        return not self.is_system and self.task_count == 0

    def can_delete(self) -> bool:
        """检查是否可以删除标签"""
        return self.is_deletable

    @classmethod
    def create_system_labels(cls) -> List["Label"]:
        """创建系统默认标签"""
        system_labels = [
            {
                "name": "bug",
                "description": "错误修复",
                "color": "#ef4444",
                "is_system": True,
                "sort_order": 1,
            },
            {
                "name": "feature",
                "description": "新功能",
                "color": "#22c55e",
                "is_system": True,
                "sort_order": 2,
            },
            {
                "name": "enhancement",
                "description": "功能改进",
                "color": "#3b82f6",
                "is_system": True,
                "sort_order": 3,
            },
            {
                "name": "documentation",
                "description": "文档相关",
                "color": "#8b5cf6",
                "is_system": True,
                "sort_order": 4,
            },
            {
                "name": "testing",
                "description": "测试相关",
                "color": "#f59e0b",
                "is_system": True,
                "sort_order": 5,
            },
            {
                "name": "urgent",
                "description": "紧急任务",
                "color": "#dc2626",
                "is_system": True,
                "sort_order": 6,
            },
        ]

        labels = []
        for label_data in system_labels:
            label = cls(**label_data)
            labels.append(label)

        return labels

    @classmethod
    def get_active_labels(cls):
        """获取所有激活的标签"""
        return (
            cls.query.filter_by(is_active=True).order_by(cls.sort_order, cls.name).all()
        )

    @classmethod
    def get_by_name(cls, name: str):
        """根据名称获取标签"""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def search_labels(cls, query: str):
        """搜索标签"""
        return (
            cls.query.filter(cls.name.ilike(f"%{query}%"), cls.is_active == True)
            .order_by(cls.sort_order, cls.name)
            .all()
        )
