#!/usr/bin/env python3
"""
Perfect21安全数据库访问层
提供参数化查询和SQL注入防护
"""

import sqlite3
import os
import sys
from typing import Dict, Any, Optional, List, Union, Set
from contextlib import contextmanager

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error, log_warning

class SecureQueryBuilder:
    """安全查询构建器 - 防止SQL注入"""

    # 允许的表名白名单
    ALLOWED_TABLES: Set[str] = {
        'users', 'user_sessions', 'user_activity_log',
        'system_config', 'operation_logs', 'api_stats'
    }

    # 允许的字段名白名单（按表分组）
    ALLOWED_FIELDS: Dict[str, Set[str]] = {
        'users': {
            'id', 'username', 'email', 'password_hash', 'salt', 'role',
            'status', 'created_at', 'last_login', 'email_verified',
            'verification_token', 'reset_token', 'reset_token_expires'
        },
        'user_sessions': {
            'id', 'user_id', 'session_token', 'device_info', 'ip_address',
            'created_at', 'expires_at', 'is_active'
        },
        'user_activity_log': {
            'id', 'user_id', 'action', 'details', 'ip_address',
            'user_agent', 'timestamp'
        },
        'system_config': {
            'key', 'value', 'description', 'created_at', 'updated_at'
        },
        'operation_logs': {
            'id', 'user_id', 'operation', 'details', 'ip_address',
            'user_agent', 'status', 'created_at'
        },
        'api_stats': {
            'id', 'endpoint', 'method', 'status_code', 'response_time',
            'user_id', 'ip_address', 'created_at'
        }
    }

    # 允许的操作符
    ALLOWED_OPERATORS: Set[str] = {
        '=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN', 'NOT IN', 'IS', 'IS NOT'
    }

    @classmethod
    def validate_table_name(cls, table_name: str) -> str:
        """验证表名"""
        if not table_name or table_name not in cls.ALLOWED_TABLES:
            raise ValueError(f"Invalid table name. Allowed: {', '.join(sorted(cls.ALLOWED_TABLES))}")
        return table_name

    @classmethod
    def validate_field_name(cls, table_name: str, field_name: str) -> str:
        """验证字段名"""
        table_name = cls.validate_table_name(table_name)

        if not field_name:
            raise ValueError("Field name cannot be empty")

        allowed_fields = cls.ALLOWED_FIELDS.get(table_name, set())
        if field_name not in allowed_fields:
            raise ValueError(f"Invalid field '{field_name}' for table '{table_name}'. "
                           f"Allowed: {', '.join(sorted(allowed_fields))}")
        return field_name

    @classmethod
    def validate_operator(cls, operator: str) -> str:
        """验证操作符"""
        operator = operator.upper().strip()
        if operator not in cls.ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator. Allowed: {', '.join(sorted(cls.ALLOWED_OPERATORS))}")
        return operator

    @classmethod
    def build_select_query(cls, table_name: str, fields: List[str] = None,
                          where_conditions: Dict[str, Any] = None,
                          order_by: str = None, order_direction: str = 'ASC',
                          limit: int = None, offset: int = None) -> tuple:
        """
        构建安全的SELECT查询

        Returns:
            tuple: (query_string, parameters)
        """
        # 验证表名
        table_name = cls.validate_table_name(table_name)

        # 验证字段
        if fields:
            validated_fields = []
            for field in fields:
                validated_fields.append(cls.validate_field_name(table_name, field))
            fields_str = ', '.join(validated_fields)
        else:
            fields_str = '*'

        # 构建基础查询
        query = f"SELECT {fields_str} FROM {table_name}"
        params = []

        # 添加WHERE条件
        if where_conditions:
            where_clauses = []
            for field, value in where_conditions.items():
                cls.validate_field_name(table_name, field)
                where_clauses.append(f"{field} = ?")
                params.append(value)

            if where_clauses:
                query += f" WHERE {' AND '.join(where_clauses)}"

        # 添加ORDER BY
        if order_by:
            order_by = cls.validate_field_name(table_name, order_by)
            order_direction = order_direction.upper()
            if order_direction not in ('ASC', 'DESC'):
                order_direction = 'ASC'
            query += f" ORDER BY {order_by} {order_direction}"

        # 添加LIMIT和OFFSET
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError("Limit must be a non-negative integer")
            query += " LIMIT ?"
            params.append(limit)

            if offset is not None:
                if not isinstance(offset, int) or offset < 0:
                    raise ValueError("Offset must be a non-negative integer")
                query += " OFFSET ?"
                params.append(offset)

        return query, tuple(params)

    @classmethod
    def build_insert_query(cls, table_name: str, data: Dict[str, Any]) -> tuple:
        """
        构建安全的INSERT查询

        Returns:
            tuple: (query_string, parameters)
        """
        table_name = cls.validate_table_name(table_name)

        if not data:
            raise ValueError("Insert data cannot be empty")

        # 验证字段
        validated_fields = []
        values = []
        for field, value in data.items():
            validated_field = cls.validate_field_name(table_name, field)
            validated_fields.append(validated_field)
            values.append(value)

        placeholders = ', '.join(['?' for _ in validated_fields])
        fields_str = ', '.join(validated_fields)

        query = f"INSERT INTO {table_name} ({fields_str}) VALUES ({placeholders})"

        return query, tuple(values)

    @classmethod
    def build_update_query(cls, table_name: str, data: Dict[str, Any],
                          where_conditions: Dict[str, Any]) -> tuple:
        """
        构建安全的UPDATE查询

        Returns:
            tuple: (query_string, parameters)
        """
        table_name = cls.validate_table_name(table_name)

        if not data:
            raise ValueError("Update data cannot be empty")

        if not where_conditions:
            raise ValueError("WHERE conditions are required for UPDATE")

        # 验证更新字段
        set_clauses = []
        params = []
        for field, value in data.items():
            validated_field = cls.validate_field_name(table_name, field)
            set_clauses.append(f"{validated_field} = ?")
            params.append(value)

        # 验证WHERE条件
        where_clauses = []
        for field, value in where_conditions.items():
            validated_field = cls.validate_field_name(table_name, field)
            where_clauses.append(f"{validated_field} = ?")
            params.append(value)

        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"

        return query, tuple(params)

    @classmethod
    def build_delete_query(cls, table_name: str, where_conditions: Dict[str, Any]) -> tuple:
        """
        构建安全的DELETE查询

        Returns:
            tuple: (query_string, parameters)
        """
        table_name = cls.validate_table_name(table_name)

        if not where_conditions:
            raise ValueError("WHERE conditions are required for DELETE")

        # 验证WHERE条件
        where_clauses = []
        params = []
        for field, value in where_conditions.items():
            validated_field = cls.validate_field_name(table_name, field)
            where_clauses.append(f"{validated_field} = ?")
            params.append(value)

        query = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"

        return query, tuple(params)


class SecureDatabase:
    """安全数据库访问类"""

    def __init__(self, db_path: str):
        """初始化安全数据库连接"""
        self.db_path = db_path
        self._conn = None
        log_info(f"SecureDatabase initialized: {db_path}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row

            # 启用安全设置
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")

            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            log_error("Database connection error", e)
            raise
        finally:
            if conn:
                conn.close()

    def execute_secure_query(self, query: str, params: tuple = None,
                           fetch_mode: str = 'all') -> Union[List[Dict], int, Optional[Dict]]:
        """
        执行安全的参数化查询

        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_mode: 'all', 'one', 'none'

        Returns:
            查询结果或影响行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch_mode == 'all':
                    result = cursor.fetchall()
                    return [dict(row) for row in result] if result else []
                elif fetch_mode == 'one':
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_mode == 'none':
                    conn.commit()
                    return cursor.rowcount
                else:
                    raise ValueError(f"Invalid fetch_mode: {fetch_mode}")

            except Exception as e:
                conn.rollback()
                log_error("Query execution error", e)
                log_error(f"Query: {query}")
                log_error(f"Params: {params}")
                raise

    def secure_select(self, table_name: str, fields: List[str] = None,
                     where_conditions: Dict[str, Any] = None,
                     order_by: str = None, order_direction: str = 'ASC',
                     limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """安全的SELECT操作"""
        query, params = SecureQueryBuilder.build_select_query(
            table_name, fields, where_conditions,
            order_by, order_direction, limit, offset
        )
        return self.execute_secure_query(query, params, 'all')

    def secure_insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """安全的INSERT操作"""
        query, params = SecureQueryBuilder.build_insert_query(table_name, data)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def secure_update(self, table_name: str, data: Dict[str, Any],
                     where_conditions: Dict[str, Any]) -> int:
        """安全的UPDATE操作"""
        query, params = SecureQueryBuilder.build_update_query(
            table_name, data, where_conditions
        )
        return self.execute_secure_query(query, params, 'none')

    def secure_delete(self, table_name: str, where_conditions: Dict[str, Any]) -> int:
        """安全的DELETE操作"""
        query, params = SecureQueryBuilder.build_delete_query(table_name, where_conditions)
        return self.execute_secure_query(query, params, 'none')

    def secure_search(self, table_name: str, search_fields: List[str],
                     search_query: str, additional_conditions: Dict[str, Any] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        安全的模糊搜索

        Args:
            table_name: 表名
            search_fields: 搜索字段列表
            search_query: 搜索关键词
            additional_conditions: 额外的精确匹配条件
            limit: 结果数量限制
        """
        table_name = SecureQueryBuilder.validate_table_name(table_name)

        # 验证搜索字段
        validated_fields = []
        for field in search_fields:
            validated_fields.append(SecureQueryBuilder.validate_field_name(table_name, field))

        # 构建搜索条件
        search_clauses = []
        params = []

        # 处理搜索关键词
        if search_query and search_query.strip():
            # 使用安全的LIKE模式
            from api.validators import SecurityValidator
            safe_pattern = SecurityValidator.create_safe_like_pattern(search_query.strip())

            field_clauses = []
            for field in validated_fields:
                field_clauses.append(f"{field} LIKE ?")
                params.append(safe_pattern)

            if field_clauses:
                search_clauses.append(f"({' OR '.join(field_clauses)})")

        # 添加额外条件
        if additional_conditions:
            for field, value in additional_conditions.items():
                validated_field = SecureQueryBuilder.validate_field_name(table_name, field)
                search_clauses.append(f"{validated_field} = ?")
                params.append(value)

        # 构建完整查询
        query = f"SELECT * FROM {table_name}"
        if search_clauses:
            query += f" WHERE {' AND '.join(search_clauses)}"

        query += f" LIMIT ?"
        params.append(limit)

        return self.execute_secure_query(query, tuple(params), 'all')


# 导出类
__all__ = ['SecureQueryBuilder', 'SecureDatabase']