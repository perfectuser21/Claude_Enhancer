"""
API路由包
=========

包含所有API路由定义
"""

from .auth import router as auth_router
from .tasks import router as tasks_router
from .projects import router as projects_router
from .dashboard import router as dashboard_router
from .notifications import router as notifications_router

__all__ = [
    "auth_router",
    "tasks_router",
    "projects_router",
    "dashboard_router",
    "notifications_router",
]
