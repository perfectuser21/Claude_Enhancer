"""
Base SQLAlchemy configuration and utilities for todo data models.
Production-ready base classes with advanced features.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models with common functionality."""

    # Common fields that most models will have
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        Args:
            exclude: Set of field names to exclude from output

        Returns:
            Dictionary representation of the model
        """
        exclude = exclude or set()
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Handle UUID serialization
                if hasattr(value, '__str__'):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value

        return result

    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[set] = None) -> None:
        """Update model instance from dictionary.

        Args:
            data: Dictionary with field values to update
            exclude: Set of field names to exclude from update
        """
        exclude = exclude or {'id', 'created_at'}

        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Create the base class for backward compatibility
SQLAlchemyBase = declarative_base()