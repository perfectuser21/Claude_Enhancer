"""
依赖注入管理
============

提供FastAPI依赖注入功能，包括：
- 用户认证依赖
- 权限检查依赖
- 服务层依赖
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from src.core.config import get_settings
from src.core.database import get_db
from src.auth.auth import get_current_user_from_token
from src.task_management.services import (
    TaskService,
    ProjectService,
    NotificationService,
)

# 配置
settings = get_settings()

# HTTP Bearer认证
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    获取当前用户
    ============

    从JWT Token中解析用户信息
    """
    try:
        # 解码JWT Token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库获取用户
    user = get_current_user_from_token(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    """
    获取当前活跃用户
    ===============

    确保用户账户是激活状态
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户账户已被禁用")
    return current_user


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """获取任务服务实例"""
    return TaskService(db)


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """获取项目服务实例"""
    return ProjectService(db)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """获取通知服务实例"""
    return NotificationService(db)


def setup_dependencies():
    """设置依赖注入配置"""
    # 这里可以添加一些依赖初始化逻辑
    pass
