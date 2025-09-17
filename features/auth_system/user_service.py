#!/usr/bin/env python3
"""
Perfect21用户服务
负责用户数据的CRUD操作和密码管理
"""

import os
import sys
import sqlite3
import hashlib
import secrets
import bcrypt
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from modules.logger import log_info, log_error
from modules.secure_db import SecureDatabase

class UserService:
    """用户服务类 - 使用安全数据库访问层"""

    def __init__(self, db_path: str):
        """初始化用户服务"""
        self.db_path = db_path
        self._conn = None
        self.secure_db = SecureDatabase(db_path)
        log_info("UserService初始化完成（安全模式）")

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                salt VARCHAR(32) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                status VARCHAR(20) DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                email_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(255),
                reset_token VARCHAR(255),
                reset_token_expires DATETIME
            )
        ''')

        # 用户会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(255) NOT NULL,
                device_info TEXT,
                ip_address VARCHAR(45),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        # 用户操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                details TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        log_info("用户数据表初始化完成")

    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """使用bcrypt哈希密码"""
        # bcrypt会自动生成和处理salt，不需要单独的salt参数
        password_bytes = password.encode('utf-8')
        salt_bytes = bcrypt.gensalt(rounds=12)  # 使用12轮加密，平衡安全性和性能
        password_hash = bcrypt.hashpw(password_bytes, salt_bytes)

        # 返回hash和salt（bcrypt将salt包含在hash中）
        return password_hash.decode('utf-8'), salt_bytes.decode('utf-8')

    def create_user(self, username: str, email: str, password: str,
                   role: str = "user") -> str:
        """创建用户（安全插入）"""
        try:
            # 生成密码哈希
            password_hash, salt = self._hash_password(password)

            # 使用安全插入
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'salt': salt,
                'role': role
            }

            user_id = self.secure_db.secure_insert('users', user_data)

            # 记录操作日志
            self.log_user_activity(str(user_id), 'REGISTER', f'User registered: {username}')

            log_info(f"用户创建成功: {username} (ID: {user_id})")
            return str(user_id)

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                log_error("用户创建失败：用户名或邮箱已存在", e)
                raise ValueError("用户名或邮箱已存在")
            else:
                log_error("用户创建失败", e)
                raise

    def user_exists(self, username: str, email: str) -> bool:
        """检查用户是否存在（安全查询）"""
        try:
            # 使用安全查询构建器
            from modules.secure_db import SecureQueryBuilder

            # 分别检查用户名和邮箱
            username_result = self.secure_db.secure_select(
                'users', ['id'], {'username': username}
            )

            email_result = self.secure_db.secure_select(
                'users', ['id'], {'email': email}
            )

            return len(username_result) > 0 or len(email_result) > 0

        except Exception as e:
            log_error("检查用户存在性失败", e)
            raise

    def find_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        """根据用户名或邮箱查找用户（安全查询）"""
        try:
            # 先尝试按用户名查找
            username_result = self.secure_db.secure_select(
                'users', None, {'username': identifier}
            )

            if username_result:
                return username_result[0]

            # 再尝试按邮箱查找
            email_result = self.secure_db.secure_select(
                'users', None, {'email': identifier}
            )

            if email_result:
                return email_result[0]

            return None

        except Exception as e:
            log_error("查找用户失败", e)
            raise

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户（安全查询）"""
        try:
            result = self.secure_db.secure_select(
                'users', None, {'id': user_id}
            )
            return result[0] if result else None

        except Exception as e:
            log_error("根据ID获取用户失败", e)
            raise

    def verify_password(self, user_id: str, password: str) -> bool:
        """使用bcrypt验证密码（安全查询）"""
        try:
            result = self.secure_db.secure_select(
                'users', ['password_hash'], {'id': user_id}
            )

            if not result:
                return False

            row = result[0]
            stored_hash = row['password_hash']

            # 使用bcrypt验证密码
            password_bytes = password.encode('utf-8')
            stored_hash_bytes = stored_hash.encode('utf-8')

            return bcrypt.checkpw(password_bytes, stored_hash_bytes)

        except Exception as e:
            log_error("密码验证失败", e)
            return False

    def update_password(self, user_id: str, new_password: str):
        """使用bcrypt更新用户密码（安全更新）"""
        try:
            password_hash, salt = self._hash_password(new_password)

            update_data = {
                'password_hash': password_hash,
                'salt': salt  # bcrypt中salt包含在hash中，但保持数据库结构兼容性
            }

            rows_affected = self.secure_db.secure_update(
                'users', update_data, {'id': user_id}
            )

            if rows_affected == 0:
                raise ValueError("用户不存在")

            # 记录操作日志
            self.log_user_activity(user_id, 'PASSWORD_CHANGE', 'Password changed with bcrypt')

            log_info(f"用户密码更新成功（bcrypt）: user_id={user_id}")

        except Exception as e:
            log_error("更新密码失败", e)
            raise

    def update_last_login(self, user_id: str):
        """更新最后登录时间（安全更新）"""
        try:
            # SQLite中CURRENT_TIMESTAMP需要特殊处理
            from datetime import datetime
            current_time = datetime.now().isoformat()

            update_data = {'last_login': current_time}

            rows_affected = self.secure_db.secure_update(
                'users', update_data, {'id': user_id}
            )

            if rows_affected == 0:
                log_warning(f"更新最后登录时间失败：用户不存在 user_id={user_id}")
                return

            # 记录操作日志
            self.log_user_activity(user_id, 'LOGIN', 'User logged in')

        except Exception as e:
            log_error("更新最后登录时间失败", e)

    def update_user(self, user_id: str, **kwargs):
        """更新用户信息（安全更新）"""
        try:
            # 白名单验证允许的字段
            allowed_fields = {'username', 'email', 'role', 'status'}
            update_data = {}

            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_data[field] = value
                else:
                    log_warning(f"忽略不允许的字段: {field}")

            if not update_data:
                log_info("没有有效的更新字段")
                return

            rows_affected = self.secure_db.secure_update(
                'users', update_data, {'id': user_id}
            )

            if rows_affected == 0:
                raise ValueError("用户不存在")

            # 记录操作日志
            self.log_user_activity(
                user_id,
                'PROFILE_UPDATE',
                f'Updated fields: {list(update_data.keys())}'
            )

            log_info(f"用户信息更新成功: user_id={user_id}")

        except Exception as e:
            log_error("更新用户信息失败", e)
            raise

    def set_verification_token(self, user_id: str, token: str):
        """设置邮箱验证令牌"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET verification_token = ?
            WHERE id = ?
        ''', (token, user_id))

        conn.commit()

    def verify_email(self, token: str) -> bool:
        """验证邮箱"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET email_verified = TRUE, verification_token = NULL
            WHERE verification_token = ?
        ''', (token,))

        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False

    def set_reset_token(self, user_id: str, token: str, expires_at: datetime):
        """设置密码重置令牌"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET reset_token = ?, reset_token_expires = ?
            WHERE id = ?
        ''', (token, expires_at, user_id))

        conn.commit()

    def verify_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证重置令牌"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users
            WHERE reset_token = ? AND reset_token_expires > CURRENT_TIMESTAMP
        ''', (token,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def clear_reset_token(self, user_id: str):
        """清除重置令牌"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET reset_token = NULL, reset_token_expires = NULL
            WHERE id = ?
        ''', (user_id,))

        conn.commit()

    def log_user_activity(self, user_id: str, action: str, details: str = None,
                         ip_address: str = None, user_agent: str = None):
        """记录用户活动日志（安全插入）"""
        try:
            activity_data = {
                'user_id': user_id,
                'action': action,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent
            }

            self.secure_db.secure_insert('user_activity_log', activity_data)

        except Exception as e:
            # 日志记录失败不应该影响主要业务流程
            log_error("记录用户活动日志失败", e)

    def get_user_activity(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户活动记录（安全查询）"""
        try:
            return self.secure_db.secure_select(
                'user_activity_log',
                None,
                {'user_id': user_id},
                order_by='timestamp',
                order_direction='DESC',
                limit=limit
            )

        except Exception as e:
            log_error("获取用户活动记录失败", e)
            return []

    def create_session(self, user_id: str, session_token: str,
                      expires_at: datetime, device_info: str = None,
                      ip_address: str = None) -> str:
        """创建用户会话"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_sessions
            (user_id, session_token, device_info, ip_address, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, device_info, ip_address, expires_at))

        session_id = cursor.lastrowid
        conn.commit()

        return str(session_id)

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM user_sessions
            WHERE session_token = ? AND is_active = TRUE AND expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def revoke_session(self, session_token: str):
        """撤销会话"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE user_sessions
            SET is_active = FALSE
            WHERE session_token = ?
        ''', (session_token,))

        conn.commit()

    def revoke_user_sessions(self, user_id: str):
        """撤销用户所有会话"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE user_sessions
            SET is_active = FALSE
            WHERE user_id = ?
        ''', (user_id,))

        conn.commit()

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM user_sessions
            WHERE expires_at < CURRENT_TIMESTAMP
        ''')

        deleted_count = cursor.rowcount
        conn.commit()

        log_info(f"清理过期会话: {deleted_count}个")

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """根据角色获取用户列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE role = ?', (role,))

        return [dict(row) for row in cursor.fetchall()]

    def cleanup(self):
        """清理资源"""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
        except Exception as e:
            log_error("UserService清理失败", e)