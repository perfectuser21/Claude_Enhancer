#!/usr/bin/env python3
"""
数据库测试插件 - 用于数据库集成测试
提供数据库连接、事务管理、数据清理功能
"""

import os
import sqlite3
import tempfile
import pytest
from typing import Dict, Any, List, Optional
from pathlib import Path
from contextlib import contextmanager


class DatabaseTestManager:
    """数据库测试管理器"""
    
    def __init__(self, db_type: str = 'sqlite'):
        self.db_type = db_type
        self.test_db_path = None
        self.connection = None
        self.test_data_registry = {}
    
    def setup_test_database(self) -> str:
        """设置测试数据库"""
        if self.db_type == 'sqlite':
            # 创建临时SQLite数据库
            temp_dir = tempfile.gettempdir()
            self.test_db_path = os.path.join(temp_dir, f'test_perfect21_{os.getpid()}.db')
            
            self.connection = sqlite3.connect(self.test_db_path)
            self.connection.row_factory = sqlite3.Row  # 返回字典格式
            
            # 创建基本表结构
            self._create_test_schema()
            
            return self.test_db_path
        else:
            raise NotImplementedError(f"不支持的数据库类型: {self.db_type}")
    
    def _create_test_schema(self):
        """创建测试表结构"""
        cursor = self.connection.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME NULL,
                login_attempts INTEGER DEFAULT 0
            )
        ''')
        
        # 会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 登录日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                success BOOLEAN NOT NULL,
                attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT NULL
            )
        ''')
        
        # 速率限制表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address VARCHAR(45) NOT NULL,
                endpoint VARCHAR(255) NOT NULL,
                attempts INTEGER DEFAULT 1,
                window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ip_address, endpoint)
            )
        ''')
        
        self.connection.commit()
    
    def insert_test_data(self, table: str, data: List[Dict[str, Any]]) -> List[int]:
        """插入测试数据"""
        cursor = self.connection.cursor()
        inserted_ids = []
        
        for record in data:
            columns = ', '.join(record.keys())
            placeholders = ', '.join(['?' for _ in record])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, list(record.values()))
            inserted_ids.append(cursor.lastrowid)
            
            # 记录测试数据用于清理
            if table not in self.test_data_registry:
                self.test_data_registry[table] = []
            self.test_data_registry[table].append(cursor.lastrowid)
        
        self.connection.commit()
        return inserted_ids
    
    def get_test_user(self, email: str = "test@example.com") -> Dict[str, Any]:
        """获取测试用户"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_test_user(self, email: str = "test@example.com", password_hash: str = "hashed_password") -> int:
        """创建测试用户"""
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'is_active': 1,
            'login_attempts': 0
        }
        return self.insert_test_data('users', [user_data])[0]
    
    def create_test_session(self, user_id: int, token: str, expires_at: str) -> int:
        """创建测试会话"""
        session_data = {
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at,
            'ip_address': '127.0.0.1'
        }
        return self.insert_test_data('sessions', [session_data])[0]
    
    def log_login_attempt(self, email: str, ip_address: str, success: bool, error_message: str = None) -> int:
        """记录登录尝试"""
        log_data = {
            'email': email,
            'ip_address': ip_address,
            'success': success,
            'error_message': error_message
        }
        return self.insert_test_data('login_logs', [log_data])[0]
    
    def get_user_login_logs(self, email: str) -> List[Dict[str, Any]]:
        """获取用户登录日志"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM login_logs WHERE email = ? ORDER BY attempted_at DESC", (email,))
        return [dict(row) for row in cursor.fetchall()]
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        cursor = self.connection.cursor()
        try:
            cursor.execute('BEGIN TRANSACTION')
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
    
    def cleanup_test_data(self):
        """清理测试数据"""
        cursor = self.connection.cursor()
        
        # 清理所有记录的测试数据
        for table, ids in self.test_data_registry.items():
            if ids:
                placeholders = ','.join(['?' for _ in ids])
                cursor.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
        
        self.connection.commit()
        self.test_data_registry.clear()
    
    def reset_database(self):
        """重置数据库"""
        cursor = self.connection.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 清空所有表
        for table in tables:
            if table != 'sqlite_sequence':  # 保留系统表
                cursor.execute(f"DELETE FROM {table}")
        
        self.connection.commit()
        self.test_data_registry.clear()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
        
        # 删除临时数据库文件
        if self.test_db_path and os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass  # 忽略删除失败
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行SQL查询"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_table_count(self, table: str) -> int:
        """获取表记录数量"""
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        cursor = self.connection.cursor()
        
        stats = {
            'tables': {},
            'total_records': 0
        }
        
        # 获取所有表的记录数
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            if table != 'sqlite_sequence':
                count = self.get_table_count(table)
                stats['tables'][table] = count
                stats['total_records'] += count
        
        return stats


class DatabaseFixtures:
    """数据库测试数据夹具"""
    
    @staticmethod
    def get_sample_users() -> List[Dict[str, Any]]:
        """获取示例用户数据"""
        return [
            {
                'email': 'active@example.com',
                'password_hash': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
                'is_active': 1,
                'login_attempts': 0
            },
            {
                'email': 'locked@example.com',
                'password_hash': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
                'is_active': 0,
                'login_attempts': 5
            },
            {
                'email': 'newuser@example.com',
                'password_hash': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
                'is_active': 1,
                'login_attempts': 0
            }
        ]
    
    @staticmethod
    def get_sample_sessions() -> List[Dict[str, Any]]:
        """获取示例会话数据"""
        from datetime import datetime, timedelta
        
        return [
            {
                'user_id': 1,
                'token': 'session_token_1',
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                'ip_address': '192.168.1.100'
            },
            {
                'user_id': 2,
                'token': 'session_token_2',
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat(),
                'ip_address': '192.168.1.101'
            }
        ]
    
    @staticmethod
    def get_sample_login_logs() -> List[Dict[str, Any]]:
        """获取示例登录日志数据"""
        return [
            {
                'email': 'active@example.com',
                'ip_address': '192.168.1.100',
                'success': 1,
                'error_message': None
            },
            {
                'email': 'locked@example.com',
                'ip_address': '192.168.1.101',
                'success': 0,
                'error_message': 'Account locked'
            },
            {
                'email': 'nonexistent@example.com',
                'ip_address': '192.168.1.102',
                'success': 0,
                'error_message': 'User not found'
            }
        ]


@pytest.fixture(scope='function')
def test_db():
    """测试数据库夹具 - 函数级别的数据库"""
    db_manager = DatabaseTestManager('sqlite')
    db_manager.setup_test_database()
    
    yield db_manager
    
    db_manager.cleanup_test_data()
    db_manager.close()

@pytest.fixture(scope='session')
def session_test_db():
    """测试数据库夹具 - 会话级别的数据库"""
    db_manager = DatabaseTestManager('sqlite')
    db_manager.setup_test_database()
    
    yield db_manager
    
    db_manager.close()

@pytest.fixture
def db_fixtures():
    """数据库测试数据夹具"""
    return DatabaseFixtures()

@pytest.fixture(autouse=True)
def auto_cleanup_db(test_db):
    """自动清理数据库测试数据"""
    # 测试前不需要做什么
    yield
    # 测试后清理数据
    try:
        test_db.cleanup_test_data()
    except:
        pass  # 忽略清理错误


class DatabaseTestHelper:
    """数据库测试辅助类"""
    
    @staticmethod
    def assert_table_count(db_manager: DatabaseTestManager, table: str, expected_count: int):
        """断言表记录数量"""
        actual_count = db_manager.get_table_count(table)
        assert actual_count == expected_count, f"Table {table} has {actual_count} records, expected {expected_count}"
    
    @staticmethod
    def assert_record_exists(db_manager: DatabaseTestManager, table: str, conditions: Dict[str, Any]):
        """断言记录存在"""
        where_clause = ' AND '.join([f"{k} = ?" for k in conditions.keys()])
        query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
        
        cursor = db_manager.connection.cursor()
        cursor.execute(query, list(conditions.values()))
        count = cursor.fetchone()[0]
        
        assert count > 0, f"Record not found in {table} with conditions {conditions}"
    
    @staticmethod
    def assert_record_not_exists(db_manager: DatabaseTestManager, table: str, conditions: Dict[str, Any]):
        """断言记录不存在"""
        where_clause = ' AND '.join([f"{k} = ?" for k in conditions.keys()])
        query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
        
        cursor = db_manager.connection.cursor()
        cursor.execute(query, list(conditions.values()))
        count = cursor.fetchone()[0]
        
        assert count == 0, f"Record unexpectedly found in {table} with conditions {conditions}"
    
    @staticmethod
    def create_test_scenario(db_manager: DatabaseTestManager, scenario_name: str) -> Dict[str, Any]:
        """创建测试场景数据"""
        fixtures = DatabaseFixtures()
        scenario_data = {'created_ids': {}}
        
        if scenario_name == 'basic_auth':
            # 创建基本认证场景
            user_ids = db_manager.insert_test_data('users', fixtures.get_sample_users())
            session_ids = db_manager.insert_test_data('sessions', fixtures.get_sample_sessions())
            log_ids = db_manager.insert_test_data('login_logs', fixtures.get_sample_login_logs())
            
            scenario_data['created_ids'] = {
                'users': user_ids,
                'sessions': session_ids,
                'login_logs': log_ids
            }
        
        elif scenario_name == 'rate_limiting':
            # 创建速率限制场景
            rate_limit_data = [
                {'ip_address': '192.168.1.200', 'endpoint': '/api/login', 'attempts': 5},
                {'ip_address': '192.168.1.201', 'endpoint': '/api/login', 'attempts': 10},
                {'ip_address': '192.168.1.202', 'endpoint': '/api/login', 'attempts': 1}
            ]
            rate_limit_ids = db_manager.insert_test_data('rate_limits', rate_limit_data)
            scenario_data['created_ids'] = {'rate_limits': rate_limit_ids}
        
        return scenario_data


# Pytest 标记
def pytest_configure(config):
    """注册Pytest标记"""
    config.addinivalue_line(
        "markers", "database: mark test as database test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "transaction: mark test as transaction test"
    )
