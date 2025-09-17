#!/usr/bin/env python3
"""
认证系统存储层 - Repository模式
负责数据持久化和数据库操作
"""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func

from backend.auth.models import User, UserSession, AuditLog, UserStatus, UserRole
from backend.core.exceptions import DatabaseError, UserNotFoundError, ValidationError

class UserRepository:
    """用户数据仓库"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """创建新用户"""
        try:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                role=user_data.get('role', UserRole.USER),
                status=user_data.get('status', UserStatus.PENDING_VERIFICATION),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                timezone=user_data.get('timezone', 'UTC')
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            return user

        except IntegrityError as e:
            self.db.rollback()
            if 'username' in str(e):
                raise ValidationError("用户名已存在")
            elif 'email' in str(e):
                raise ValidationError("邮箱已存在")
            else:
                raise ValidationError("用户数据冲突")
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"创建用户失败: {str(e)}")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            return self.db.query(User).filter(
                and_(
                    User.username == username,
                    User.status != UserStatus.INACTIVE
                )
            ).first()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")

    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            return self.db.query(User).filter(
                and_(
                    User.email == email,
                    User.status != UserStatus.INACTIVE
                )
            ).first()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")

    def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        """根据标识符（用户名或邮箱）获取用户"""
        try:
            return self.db.query(User).filter(
                and_(
                    or_(
                        User.username == identifier,
                        User.email == identifier
                    ),
                    User.status != UserStatus.INACTIVE
                )
            ).first()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> User:
        """更新用户信息"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError("用户不存在")

            # 过滤允许更新的字段
            allowed_fields = {
                'username', 'email', 'password_hash', 'role', 'status',
                'first_name', 'last_name', 'avatar_url', 'timezone',
                'last_login_at', 'email_verified_at', 'password_changed_at',
                'failed_login_attempts', 'locked_until'
            }

            for field, value in update_data.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)

            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)

            return user

        except IntegrityError as e:
            self.db.rollback()
            if 'username' in str(e):
                raise ValidationError("用户名已存在")
            elif 'email' in str(e):
                raise ValidationError("邮箱已存在")
            else:
                raise ValidationError("用户数据冲突")
        except (UserNotFoundError, ValidationError):
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"更新用户失败: {str(e)}")

    def update_last_login(self, user_id: str) -> None:
        """更新用户最后登录时间"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                user.last_login_at = datetime.utcnow()
                user.failed_login_attempts = '0'  # 重置登录失败次数
                user.locked_until = None  # 清除锁定状态
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"更新最后登录时间失败: {str(e)}")

    def increment_failed_attempts(self, identifier: str) -> int:
        """增加失败登录次数"""
        try:
            user = self.get_user_by_identifier(identifier)
            if not user:
                return 0

            # 解析失败尝试记录
            attempts_data = json.loads(user.failed_login_attempts or '0')
            if isinstance(attempts_data, int):
                attempts_data = attempts_data + 1
            else:
                attempts_data = 1

            user.failed_login_attempts = str(attempts_data)

            # 如果失败次数过多，锁定账户
            if attempts_data >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)

            self.db.commit()
            return attempts_data

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"更新失败尝试次数失败: {str(e)}")

    def clear_failed_attempts(self, identifier: str) -> None:
        """清除失败登录次数"""
        try:
            user = self.get_user_by_identifier(identifier)
            if user:
                user.failed_login_attempts = '0'
                user.locked_until = None
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"清除失败尝试次数失败: {str(e)}")

    def is_user_locked(self, identifier: str) -> bool:
        """检查用户是否被锁定"""
        try:
            user = self.get_user_by_identifier(identifier)
            if not user or not user.locked_until:
                return False

            return datetime.utcnow() < user.locked_until
        except Exception:
            return False

    def verify_email(self, user_id: str) -> None:
        """验证用户邮箱"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                user.email_verified_at = datetime.utcnow()
                user.status = UserStatus.ACTIVE
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"验证邮箱失败: {str(e)}")

    def list_users(
        self,
        offset: int = 0,
        limit: int = 50,
        status_filter: Optional[UserStatus] = None,
        role_filter: Optional[UserRole] = None,
        search_query: Optional[str] = None
    ) -> tuple[List[User], int]:
        """获取用户列表"""
        try:
            query = self.db.query(User)

            # 状态筛选
            if status_filter:
                query = query.filter(User.status == status_filter)

            # 角色筛选
            if role_filter:
                query = query.filter(User.role == role_filter)

            # 搜索查询
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_pattern),
                        User.email.ilike(search_pattern),
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern)
                    )
                )

            # 总数
            total = query.count()

            # 分页和排序
            users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

            return users, total

        except Exception as e:
            raise DatabaseError(f"获取用户列表失败: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            user.status = UserStatus.INACTIVE
            user.updated_at = datetime.utcnow()
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"删除用户失败: {str(e)}")

class SessionRepository:
    """用户会话数据仓库"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_session(self, session_data: Dict[str, Any]) -> UserSession:
        """创建新会话"""
        try:
            session = UserSession(
                user_id=session_data['user_id'],
                access_token_jti=session_data['access_token_jti'],
                refresh_token_jti=session_data['refresh_token_jti'],
                expires_at=session_data['expires_at'],
                ip_address=session_data.get('ip_address'),
                user_agent=session_data.get('user_agent'),
                device_id=session_data.get('device_id')
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"创建会话失败: {str(e)}")

    def get_session_by_id(self, session_id: str) -> Optional[UserSession]:
        """根据ID获取会话"""
        try:
            return self.db.query(UserSession).filter(UserSession.id == session_id).first()
        except Exception as e:
            raise DatabaseError(f"获取会话失败: {str(e)}")

    def get_session_by_token_jti(self, jti: str, token_type: str = 'access') -> Optional[UserSession]:
        """根据令牌JTI获取会话"""
        try:
            if token_type == 'access':
                return self.db.query(UserSession).filter(
                    UserSession.access_token_jti == jti
                ).first()
            else:
                return self.db.query(UserSession).filter(
                    UserSession.refresh_token_jti == jti
                ).first()
        except Exception as e:
            raise DatabaseError(f"获取会话失败: {str(e)}")

    def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[UserSession]:
        """获取用户的所有会话"""
        try:
            query = self.db.query(UserSession).filter(UserSession.user_id == user_id)

            if active_only:
                query = query.filter(
                    and_(
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.utcnow()
                    )
                )

            return query.order_by(UserSession.created_at.desc()).all()

        except Exception as e:
            raise DatabaseError(f"获取用户会话失败: {str(e)}")

    def update_session_access(self, session_id: str) -> None:
        """更新会话访问时间"""
        try:
            session = self.get_session_by_id(session_id)
            if session:
                session.last_accessed_at = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"更新会话访问时间失败: {str(e)}")

    def revoke_session(self, session_id: str) -> bool:
        """撤销会话"""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return False

            session.is_active = False
            session.revoked_at = datetime.utcnow()
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"撤销会话失败: {str(e)}")

    def revoke_user_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> int:
        """撤销用户的所有会话"""
        try:
            query = self.db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )

            if exclude_session_id:
                query = query.filter(UserSession.id != exclude_session_id)

            sessions = query.all()

            revoked_count = 0
            for session in sessions:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                revoked_count += 1

            self.db.commit()
            return revoked_count

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"撤销用户会话失败: {str(e)}")

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            current_time = datetime.utcnow()

            expired_sessions = self.db.query(UserSession).filter(
                and_(
                    UserSession.expires_at < current_time,
                    UserSession.is_active == True
                )
            ).all()

            cleaned_count = 0
            for session in expired_sessions:
                session.is_active = False
                session.revoked_at = current_time
                cleaned_count += 1

            self.db.commit()
            return cleaned_count

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"清理过期会话失败: {str(e)}")

class AuditLogRepository:
    """审计日志数据仓库"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_log(self, log_data: Dict[str, Any]) -> AuditLog:
        """创建审计日志"""
        try:
            log = AuditLog(
                user_id=log_data.get('user_id'),
                event_type=log_data['event_type'],
                event_description=log_data.get('event_description'),
                ip_address=log_data.get('ip_address'),
                user_agent=log_data.get('user_agent'),
                success=log_data['success'],
                error_message=log_data.get('error_message'),
                metadata=log_data.get('metadata')
            )

            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)

            return log

        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"创建审计日志失败: {str(e)}")

    def get_user_logs(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 50,
        event_type: Optional[str] = None
    ) -> tuple[List[AuditLog], int]:
        """获取用户审计日志"""
        try:
            query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

            if event_type:
                query = query.filter(AuditLog.event_type == event_type)

            total = query.count()
            logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

            return logs, total

        except Exception as e:
            raise DatabaseError(f"获取用户审计日志失败: {str(e)}")

    def get_security_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: bool = False,
        limit: int = 100
    ) -> List[AuditLog]:
        """获取安全事件日志"""
        try:
            query = self.db.query(AuditLog).filter(
                AuditLog.event_type.in_(['login', 'failed_login', 'logout', 'password_change'])
            )

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)

            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            if success_only:
                query = query.filter(AuditLog.success == True)

            return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

        except Exception as e:
            raise DatabaseError(f"获取安全事件日志失败: {str(e)}")

    def get_failed_login_stats(self, hours: int = 24) -> Dict[str, int]:
        """获取失败登录统计"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)

            result = self.db.query(
                func.count(AuditLog.id).label('total_attempts'),
                func.count(func.distinct(AuditLog.ip_address)).label('unique_ips'),
                func.count(func.distinct(AuditLog.user_id)).label('affected_users')
            ).filter(
                and_(
                    AuditLog.event_type == 'failed_login',
                    AuditLog.created_at >= since_time
                )
            ).first()

            return {
                'total_attempts': result.total_attempts or 0,
                'unique_ips': result.unique_ips or 0,
                'affected_users': result.affected_users or 0
            }

        except Exception as e:
            raise DatabaseError(f"获取失败登录统计失败: {str(e)}")