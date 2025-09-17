#!/usr/bin/env python3
"""
Audit Logger - Perfect21 Audit Logging System
完整的审计日志系统，支持合规性要求和安全审计
"""

import json
import time
import hashlib
import threading
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os
import gzip
from pathlib import Path
import queue

class AuditEventType(Enum):
    """审计事件类型"""
    # 用户操作
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_ACTION = "user_action"

    # 系统操作
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"

    # 数据操作
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"

    # 安全事件
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECURITY_VIOLATION = "security_violation"

    # Agent操作
    AGENT_EXECUTION = "agent_execution"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"

    # Git操作
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"

    # API操作
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"

class AuditLevel(Enum):
    """审计级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    event_type: AuditEventType
    level: AuditLevel
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    details: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    checksum: Optional[str] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.metadata is None:
            self.metadata = {}
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """计算事件校验和"""
        # 创建用于校验的数据（不包括checksum本身）
        data = {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'level': self.level.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'source_ip': self.source_ip,
            'user_agent': self.user_agent,
            'resource': self.resource,
            'action': self.action,
            'result': self.result,
            'details': self.details,
            'metadata': self.metadata
        }

        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def verify_checksum(self) -> bool:
        """验证校验和"""
        original_checksum = self.checksum
        self.checksum = None
        calculated_checksum = self._calculate_checksum()
        self.checksum = original_checksum
        return original_checksum == calculated_checksum

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['level'] = self.level.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

class AuditFilter:
    """审计过滤器"""

    def __init__(self,
                 event_types: List[AuditEventType] = None,
                 levels: List[AuditLevel] = None,
                 users: List[str] = None,
                 resources: List[str] = None,
                 time_range: tuple = None):
        self.event_types = event_types
        self.levels = levels
        self.users = users
        self.resources = resources
        self.time_range = time_range

    def matches(self, event: AuditEvent) -> bool:
        """检查事件是否匹配过滤条件"""
        if self.event_types and event.event_type not in self.event_types:
            return False

        if self.levels and event.level not in self.levels:
            return False

        if self.users and event.user_id not in self.users:
            return False

        if self.resources and event.resource not in self.resources:
            return False

        if self.time_range:
            start_time, end_time = self.time_range
            if event.timestamp < start_time or event.timestamp > end_time:
                return False

        return True

class AuditStorage:
    """审计存储接口"""

    def store(self, event: AuditEvent):
        """存储审计事件"""
        raise NotImplementedError

    def query(self, filter_obj: AuditFilter = None, limit: int = 100) -> List[AuditEvent]:
        """查询审计事件"""
        raise NotImplementedError

    def archive(self, before_date: datetime) -> int:
        """归档旧事件"""
        raise NotImplementedError

class FileAuditStorage(AuditStorage):
    """文件审计存储"""

    def __init__(self, base_dir: str = "logs/audit", max_file_size: int = 100*1024*1024):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self.current_file = None
        self.current_size = 0
        self._lock = threading.Lock()

    def store(self, event: AuditEvent):
        """存储到文件"""
        with self._lock:
            self._ensure_current_file()

            log_line = event.to_json() + '\n'

            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
                f.flush()
                os.fsync(f.fileno())  # 确保写入磁盘

            self.current_size += len(log_line.encode('utf-8'))

            # 检查是否需要轮转文件
            if self.current_size >= self.max_file_size:
                self._rotate_file()

    def _ensure_current_file(self):
        """确保当前文件存在"""
        if not self.current_file or not self.current_file.exists():
            today = datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.now().strftime('%H%M%S')
            self.current_file = self.base_dir / f"audit-{today}-{timestamp}.jsonl"
            self.current_size = 0

    def _rotate_file(self):
        """轮转文件"""
        if self.current_file and self.current_file.exists():
            # 压缩当前文件
            compressed_file = self.current_file.with_suffix('.jsonl.gz')
            with open(self.current_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)

            # 删除原文件
            self.current_file.unlink()

        # 创建新文件
        self.current_file = None
        self.current_size = 0
        self._ensure_current_file()

    def query(self, filter_obj: AuditFilter = None, limit: int = 100) -> List[AuditEvent]:
        """查询审计事件"""
        events = []

        # 获取所有审计文件
        audit_files = sorted(self.base_dir.glob("audit-*.jsonl*"), reverse=True)

        for file_path in audit_files:
            if len(events) >= limit:
                break

            try:
                # 处理压缩和非压缩文件
                if file_path.suffix == '.gz':
                    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                        lines = f.readlines()
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                for line in reversed(lines):
                    if len(events) >= limit:
                        break

                    try:
                        data = json.loads(line.strip())
                        event = self._dict_to_event(data)

                        if not filter_obj or filter_obj.matches(event):
                            events.append(event)

                    except (json.JSONDecodeError, KeyError) as e:
                        logging.warning(f"Failed to parse audit log line: {e}")

            except Exception as e:
                logging.error(f"Failed to read audit file {file_path}: {e}")

        return events

    def _dict_to_event(self, data: Dict[str, Any]) -> AuditEvent:
        """将字典转换为AuditEvent"""
        return AuditEvent(
            event_id=data['event_id'],
            event_type=AuditEventType(data['event_type']),
            level=AuditLevel(data['level']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            source_ip=data.get('source_ip'),
            user_agent=data.get('user_agent'),
            resource=data.get('resource'),
            action=data.get('action'),
            result=data.get('result'),
            details=data.get('details', {}),
            metadata=data.get('metadata', {}),
            checksum=data.get('checksum')
        )

    def archive(self, before_date: datetime) -> int:
        """归档旧文件"""
        archived_count = 0
        archive_dir = self.base_dir / "archived"
        archive_dir.mkdir(exist_ok=True)

        for file_path in self.base_dir.glob("audit-*.jsonl*"):
            # 从文件名提取日期
            try:
                date_str = file_path.name.split('-')[1]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')

                if file_date < before_date:
                    # 移动到归档目录
                    archive_path = archive_dir / file_path.name
                    file_path.rename(archive_path)
                    archived_count += 1

            except (IndexError, ValueError) as e:
                logging.warning(f"Failed to parse date from file {file_path}: {e}")

        return archived_count

class Perfect21AuditLogger:
    """Perfect21审计日志器"""

    def __init__(self, storage: AuditStorage = None):
        self.storage = storage or FileAuditStorage()
        self.event_queue = queue.Queue()
        self.running = False
        self._processor_thread = None
        self._session_id = self._generate_session_id()

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def _generate_event_id(self) -> str:
        """生成事件ID"""
        import uuid
        return str(uuid.uuid4())

    def start(self):
        """启动审计日志器"""
        if self.running:
            return

        self.running = True
        self._processor_thread = threading.Thread(target=self._process_events, daemon=True)
        self._processor_thread.start()

        # 记录系统启动事件
        self.log_system_event(
            AuditEventType.SYSTEM_START,
            action="audit_logger_start",
            details={"session_id": self._session_id}
        )

        logging.info("Audit logger started")

    def stop(self):
        """停止审计日志器"""
        if not self.running:
            return

        # 记录系统停止事件
        self.log_system_event(
            AuditEventType.SYSTEM_STOP,
            action="audit_logger_stop",
            details={"session_id": self._session_id}
        )

        self.running = False
        if self._processor_thread:
            self._processor_thread.join(timeout=5)

        logging.info("Audit logger stopped")

    def _process_events(self):
        """处理事件队列"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self.storage.store(event)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing audit event: {e}")

    def log_event(self, event: AuditEvent):
        """记录审计事件"""
        self.event_queue.put(event)

    def log_user_event(self,
                       event_type: AuditEventType,
                       user_id: str,
                       action: str,
                       resource: str = None,
                       result: str = "success",
                       details: Dict[str, Any] = None,
                       source_ip: str = None,
                       user_agent: str = None,
                       level: AuditLevel = AuditLevel.INFO):
        """记录用户事件"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            level=level,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=self._session_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            metadata={"component": "user_interface"}
        )
        self.log_event(event)

    def log_system_event(self,
                         event_type: AuditEventType,
                         action: str,
                         resource: str = None,
                         result: str = "success",
                         details: Dict[str, Any] = None,
                         level: AuditLevel = AuditLevel.INFO):
        """记录系统事件"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            level=level,
            timestamp=datetime.now(),
            session_id=self._session_id,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            metadata={"component": "system"}
        )
        self.log_event(event)

    def log_api_event(self,
                      method: str,
                      endpoint: str,
                      status_code: int,
                      user_id: str = None,
                      source_ip: str = None,
                      user_agent: str = None,
                      request_data: Dict[str, Any] = None,
                      response_data: Dict[str, Any] = None,
                      duration: float = None):
        """记录API事件"""
        result = "success" if 200 <= status_code < 400 else "error"
        level = AuditLevel.INFO if result == "success" else AuditLevel.WARNING

        details = {
            "method": method,
            "status_code": status_code,
            "duration_ms": duration * 1000 if duration else None
        }

        if request_data:
            details["request_data"] = request_data
        if response_data:
            details["response_data"] = response_data

        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.API_REQUEST,
            level=level,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=self._session_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource=endpoint,
            action=method,
            result=result,
            details=details,
            metadata={"component": "api"}
        )
        self.log_event(event)

    def log_agent_execution(self,
                           agent_name: str,
                           task: str,
                           result: str,
                           duration: float = None,
                           user_id: str = None,
                           details: Dict[str, Any] = None):
        """记录Agent执行事件"""
        level = AuditLevel.INFO if result == "success" else AuditLevel.WARNING

        event_details = {
            "task": task,
            "duration_seconds": duration
        }
        if details:
            event_details.update(details)

        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.AGENT_EXECUTION,
            level=level,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=self._session_id,
            resource=agent_name,
            action="execute",
            result=result,
            details=event_details,
            metadata={"component": "agent"}
        )
        self.log_event(event)

    def log_git_operation(self,
                         operation: str,
                         result: str,
                         user_id: str = None,
                         repository: str = None,
                         branch: str = None,
                         commit_hash: str = None,
                         details: Dict[str, Any] = None):
        """记录Git操作事件"""
        event_type = {
            'commit': AuditEventType.GIT_COMMIT,
            'push': AuditEventType.GIT_PUSH,
            'pull': AuditEventType.GIT_PULL
        }.get(operation, AuditEventType.USER_ACTION)

        level = AuditLevel.INFO if result == "success" else AuditLevel.WARNING

        event_details = {
            "repository": repository,
            "branch": branch,
            "commit_hash": commit_hash
        }
        if details:
            event_details.update(details)

        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            level=level,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=self._session_id,
            resource=repository,
            action=operation,
            result=result,
            details=event_details,
            metadata={"component": "git"}
        )
        self.log_event(event)

    def log_security_event(self,
                          event_type: AuditEventType,
                          action: str,
                          result: str,
                          user_id: str = None,
                          source_ip: str = None,
                          details: Dict[str, Any] = None,
                          level: AuditLevel = AuditLevel.WARNING):
        """记录安全事件"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            level=level,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=self._session_id,
            source_ip=source_ip,
            action=action,
            result=result,
            details=details or {},
            metadata={"component": "security"}
        )
        self.log_event(event)

    def query_events(self,
                     event_types: List[AuditEventType] = None,
                     levels: List[AuditLevel] = None,
                     users: List[str] = None,
                     resources: List[str] = None,
                     time_range: tuple = None,
                     limit: int = 100) -> List[AuditEvent]:
        """查询审计事件"""
        filter_obj = AuditFilter(
            event_types=event_types,
            levels=levels,
            users=users,
            resources=resources,
            time_range=time_range
        )
        return self.storage.query(filter_obj, limit)

    def get_audit_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取审计摘要"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        events = self.query_events(time_range=(start_time, end_time), limit=10000)

        # 统计分析
        total_events = len(events)
        event_type_counts = {}
        level_counts = {}
        user_counts = {}
        component_counts = {}

        for event in events:
            # 事件类型统计
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            # 级别统计
            level = event.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

            # 用户统计
            if event.user_id:
                user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1

            # 组件统计
            component = event.metadata.get('component', 'unknown')
            component_counts[component] = component_counts.get(component, 0) + 1

        return {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': hours
            },
            'total_events': total_events,
            'event_types': event_type_counts,
            'levels': level_counts,
            'top_users': dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'components': component_counts
        }

    def archive_old_events(self, days: int = 90) -> int:
        """归档旧事件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return self.storage.archive(cutoff_date)

# 全局审计日志器实例
audit_logger = Perfect21AuditLogger()

# 便捷函数
def log_user_login(user_id: str, source_ip: str = None, user_agent: str = None, success: bool = True):
    """记录用户登录"""
    result = "success" if success else "failure"
    level = AuditLevel.INFO if success else AuditLevel.WARNING

    audit_logger.log_user_event(
        AuditEventType.USER_LOGIN,
        user_id=user_id,
        action="login",
        result=result,
        source_ip=source_ip,
        user_agent=user_agent,
        level=level
    )

def log_api_request(method: str, endpoint: str, status_code: int, user_id: str = None, **kwargs):
    """记录API请求"""
    audit_logger.log_api_event(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        user_id=user_id,
        **kwargs
    )

def log_agent_execution(agent_name: str, task: str, success: bool, duration: float = None, **kwargs):
    """记录Agent执行"""
    result = "success" if success else "failure"
    audit_logger.log_agent_execution(
        agent_name=agent_name,
        task=task,
        result=result,
        duration=duration,
        **kwargs
    )

def log_security_violation(action: str, user_id: str = None, source_ip: str = None, details: Dict[str, Any] = None):
    """记录安全违规"""
    audit_logger.log_security_event(
        AuditEventType.SECURITY_VIOLATION,
        action=action,
        result="blocked",
        user_id=user_id,
        source_ip=source_ip,
        details=details,
        level=AuditLevel.CRITICAL
    )

def start_audit_logging():
    """启动审计日志"""
    audit_logger.start()

def get_audit_summary(hours: int = 24) -> Dict[str, Any]:
    """获取审计摘要"""
    return audit_logger.get_audit_summary(hours)

def query_audit_events(**kwargs) -> List[AuditEvent]:
    """查询审计事件"""
    return audit_logger.query_events(**kwargs)