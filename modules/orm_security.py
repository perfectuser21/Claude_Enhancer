#!/usr/bin/env python3
"""
Perfect21 ORM安全中间件
提供ORM级别的SQL注入防护和查询审计
"""

import re
import time
import hashlib
from typing import Any, Dict, List, Optional, Set, Callable
from functools import wraps
from datetime import datetime

from modules.logger import log_info, log_error, log_warning


class ORMSecurityMiddleware:
    """ORM安全中间件"""

    def __init__(self):
        """初始化安全中间件"""
        self.query_cache = {}
        self.threat_patterns = self._load_threat_patterns()
        self.query_audit_log = []
        self.blocked_queries = []

    def _load_threat_patterns(self) -> List[re.Pattern]:
        """加载威胁检测模式"""
        patterns = [
            # SQL注入关键词检测
            re.compile(r'\b(UNION\s+SELECT|DROP\s+TABLE|DELETE\s+FROM)\b', re.IGNORECASE),
            re.compile(r'\b(INSERT\s+INTO|UPDATE\s+SET|CREATE\s+TABLE)\b', re.IGNORECASE),
            re.compile(r'\b(EXEC\s*\(|EXECUTE\s*\(|xp_cmdshell)\b', re.IGNORECASE),
            re.compile(r'\b(sp_executesql|OPENROWSET|OPENDATASOURCE)\b', re.IGNORECASE),

            # 注释和字符串逃逸
            re.compile(r'(--|/\*|\*/|#)', re.IGNORECASE),
            re.compile(r"('\s*OR\s*'|'\s*AND\s*')", re.IGNORECASE),
            re.compile(r'(\bOR\s+\d+\s*=\s*\d+|\bAND\s+\d+\s*=\s*\d+)', re.IGNORECASE),

            # 函数注入
            re.compile(r'\b(CAST\s*\(|CONVERT\s*\(|SUBSTRING\s*\()', re.IGNORECASE),
            re.compile(r'\b(CHAR\s*\(|ASCII\s*\(|HEX\s*\()', re.IGNORECASE),

            # 时间盲注
            re.compile(r'\b(SLEEP\s*\(|WAITFOR\s+DELAY|BENCHMARK\s*\()', re.IGNORECASE),

            # 联合查询和子查询注入
            re.compile(r'\bUNION\s+(ALL\s+)?SELECT\b', re.IGNORECASE),
            re.compile(r'\)\s*UNION\s+', re.IGNORECASE),

            # 堆叠查询
            re.compile(r';\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)', re.IGNORECASE),
        ]
        return patterns

    def analyze_query_threat(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """分析查询威胁等级"""
        threat_score = 0
        detected_patterns = []

        # 检查查询字符串
        if query:
            for pattern in self.threat_patterns:
                matches = pattern.findall(query)
                if matches:
                    threat_score += len(matches) * 10
                    detected_patterns.extend(matches)

        # 检查参数
        if params:
            for param in params:
                if isinstance(param, str):
                    for pattern in self.threat_patterns:
                        matches = pattern.findall(param)
                        if matches:
                            threat_score += len(matches) * 5
                            detected_patterns.extend([f"param:{match}" for match in matches])

        # 威胁等级评估
        if threat_score >= 50:
            threat_level = "CRITICAL"
        elif threat_score >= 20:
            threat_level = "HIGH"
        elif threat_score >= 10:
            threat_level = "MEDIUM"
        elif threat_score > 0:
            threat_level = "LOW"
        else:
            threat_level = "SAFE"

        return {
            'threat_score': threat_score,
            'threat_level': threat_level,
            'detected_patterns': detected_patterns,
            'is_safe': threat_level in ['SAFE', 'LOW']
        }

    def validate_query_structure(self, query: str) -> bool:
        """验证查询结构合法性"""
        if not query or not isinstance(query, str):
            return False

        # 基本结构检查
        query_upper = query.upper().strip()

        # 允许的查询类型
        allowed_starts = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'ALTER', 'DROP', 'PRAGMA'
        ]

        if not any(query_upper.startswith(start) for start in allowed_starts):
            return False

        # 检查括号匹配
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens != close_parens:
            log_warning("查询语句括号不匹配")
            return False

        # 检查引号匹配
        single_quotes = query.count("'")
        double_quotes = query.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            log_warning("查询语句引号不匹配")
            return False

        return True

    def sanitize_query_params(self, params: tuple) -> tuple:
        """清理查询参数"""
        if not params:
            return params

        sanitized_params = []
        for param in params:
            if isinstance(param, str):
                # 移除危险字符
                sanitized = param.replace('\x00', '')  # 空字节
                sanitized = sanitized.replace('\x1a', '')  # 替换字符

                # 限制长度
                if len(sanitized) > 10000:
                    log_warning(f"参数长度过长，已截断: {len(sanitized)} -> 10000")
                    sanitized = sanitized[:10000]

                sanitized_params.append(sanitized)
            elif isinstance(param, (int, float, bool, type(None))):
                sanitized_params.append(param)
            else:
                # 其他类型转换为字符串并清理
                sanitized = str(param)[:1000]
                sanitized_params.append(sanitized)

        return tuple(sanitized_params)

    def audit_query(self, query: str, params: tuple = None,
                   execution_time: float = None, result_count: int = None):
        """查询审计日志"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'query_hash': hashlib.sha256(query.encode()).hexdigest()[:16],
            'query_type': query.strip().split()[0].upper() if query else 'UNKNOWN',
            'execution_time': execution_time,
            'result_count': result_count,
            'param_count': len(params) if params else 0,
        }

        # 威胁分析
        threat_analysis = self.analyze_query_threat(query, params)
        audit_entry.update(threat_analysis)

        # 记录审计日志
        self.query_audit_log.append(audit_entry)

        # 保持日志大小限制
        if len(self.query_audit_log) > 1000:
            self.query_audit_log = self.query_audit_log[-500:]

        # 高威胁查询特别记录
        if threat_analysis['threat_level'] in ['HIGH', 'CRITICAL']:
            log_warning(f"检测到高威胁查询: {threat_analysis}")
            self.blocked_queries.append({
                **audit_entry,
                'query_preview': query[:200] if query else '',
                'params_preview': str(params)[:200] if params else ''
            })

    def get_security_stats(self) -> Dict[str, Any]:
        """获取安全统计信息"""
        if not self.query_audit_log:
            return {
                'total_queries': 0,
                'threat_distribution': {},
                'blocked_queries': 0,
                'avg_execution_time': 0
            }

        # 威胁等级分布
        threat_distribution = {}
        total_time = 0
        time_count = 0

        for entry in self.query_audit_log:
            level = entry.get('threat_level', 'UNKNOWN')
            threat_distribution[level] = threat_distribution.get(level, 0) + 1

            if entry.get('execution_time'):
                total_time += entry['execution_time']
                time_count += 1

        return {
            'total_queries': len(self.query_audit_log),
            'threat_distribution': threat_distribution,
            'blocked_queries': len(self.blocked_queries),
            'avg_execution_time': total_time / time_count if time_count > 0 else 0,
            'recent_threats': [
                entry for entry in self.query_audit_log[-50:]
                if entry.get('threat_level') in ['HIGH', 'CRITICAL']
            ]
        }


def secure_query_decorator(middleware: ORMSecurityMiddleware):
    """安全查询装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # 提取查询和参数
            query = None
            params = None

            if len(args) >= 2:
                query = args[1] if isinstance(args[1], str) else None
                params = args[2] if len(args) >= 3 and isinstance(args[2], (tuple, list)) else None

            # 从kwargs中提取
            if not query:
                query = kwargs.get('query')
            if not params:
                params = kwargs.get('params')

            # 安全检查
            if query:
                # 结构验证
                if not middleware.validate_query_structure(query):
                    raise ValueError("查询结构不合法")

                # 威胁分析
                threat_analysis = middleware.analyze_query_threat(query, params)

                # 阻止高威胁查询
                if threat_analysis['threat_level'] == 'CRITICAL':
                    log_error(f"阻止CRITICAL威胁查询: {threat_analysis}")
                    raise SecurityError("检测到严重SQL注入威胁，查询已被阻止")

                if threat_analysis['threat_level'] == 'HIGH':
                    log_warning(f"检测到HIGH威胁查询: {threat_analysis}")

                # 参数清理
                if params:
                    params = middleware.sanitize_query_params(params)
                    # 更新args或kwargs中的参数
                    if len(args) >= 3:
                        args = list(args)
                        args[2] = params
                        args = tuple(args)
                    elif 'params' in kwargs:
                        kwargs['params'] = params

            try:
                # 执行原函数
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # 审计日志
                result_count = len(result) if isinstance(result, (list, tuple)) else None
                middleware.audit_query(query, params, execution_time, result_count)

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                middleware.audit_query(query, params, execution_time, None)
                raise

        return wrapper
    return decorator


class SecurityError(Exception):
    """安全异常"""
    pass


# 全局中间件实例
security_middleware = ORMSecurityMiddleware()

# 导出
__all__ = [
    'ORMSecurityMiddleware',
    'secure_query_decorator',
    'SecurityError',
    'security_middleware'
]