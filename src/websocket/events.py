"""
WebSocket事件定义模块
定义所有WebSocket事件类型和消息格式
"""

from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json


class EventType(Enum):
    """WebSocket事件类型枚举"""

    # 连接管理事件
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"

    # 任务状态事件
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ASSIGNED = "task_assigned"

    # 用户状态事件
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    USER_TYPING = "user_typing"
    USER_JOIN_PROJECT = "user_join_project"
    USER_LEAVE_PROJECT = "user_leave_project"

    # 协作编辑事件
    COLLABORATION_START = "collaboration_start"
    COLLABORATION_END = "collaboration_end"
    DOCUMENT_EDIT = "document_edit"
    CURSOR_POSITION = "cursor_position"

    # 系统通知事件
    SYSTEM_NOTIFICATION = "system_notification"
    PROJECT_NOTIFICATION = "project_notification"
    TEAM_NOTIFICATION = "team_notification"

    # 实时同步事件
    DATA_SYNC = "data_sync"
    CACHE_INVALIDATE = "cache_invalidate"

    # 错误事件
    ERROR = "error"
    AUTHENTICATION_ERROR = "auth_error"


class Priority(Enum):
    """消息优先级"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class WebSocketMessage:
    """标准WebSocket消息格式"""

    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str
    user_id: Optional[str] = None
    room_id: Optional[str] = None
    priority: Priority = Priority.NORMAL
    requires_ack: bool = False

    def to_json(self) -> str:
        """转换为JSON字符串"""
        data = asdict(self)
        data["type"] = self.type.value
        data["priority"] = self.priority.value
        data["timestamp"] = self.timestamp.isoformat()
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """从JSON字符串创建消息"""
        data = json.loads(json_str)
        data["type"] = EventType(data["type"])
        data["priority"] = Priority(data["priority"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class TaskEvent:
    """任务相关事件数据"""

    task_id: str
    title: str
    status: str
    assignee_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list] = None
    progress: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserEvent:
    """用户相关事件数据"""

    user_id: str
    username: str
    status: str
    last_seen: Optional[str] = None
    current_project: Optional[str] = None
    avatar_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CollaborationEvent:
    """协作编辑事件数据"""

    document_id: str
    user_id: str
    action: str  # 'insert', 'delete', 'update'
    position: int
    content: str
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationEvent:
    """通知事件数据"""

    notification_id: str
    title: str
    message: str
    type: str  # 'info', 'success', 'warning', 'error'
    target_user_id: Optional[str] = None
    target_project_id: Optional[str] = None
    action_url: Optional[str] = None
    auto_dismiss: bool = True
    dismiss_timeout: int = 5000  # 毫秒

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MessageBuilder:
    """WebSocket消息构建器"""

    @staticmethod
    def create_message(
        event_type: EventType,
        data: Dict[str, Any],
        user_id: str = None,
        room_id: str = None,
        priority: Priority = Priority.NORMAL,
        requires_ack: bool = False,
    ) -> WebSocketMessage:
        """创建标准WebSocket消息"""
        import uuid

        return WebSocketMessage(
            type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            message_id=str(uuid.uuid4()),
            user_id=user_id,
            room_id=room_id,
            priority=priority,
            requires_ack=requires_ack,
        )

    @staticmethod
    def task_created(
        task_event: TaskEvent, user_id: str, project_id: str = None
    ) -> WebSocketMessage:
        """创建任务创建事件"""
        return MessageBuilder.create_message(
            EventType.TASK_CREATED,
            task_event.to_dict(),
            user_id=user_id,
            room_id=project_id,
        )

    @staticmethod
    def task_updated(
        task_event: TaskEvent, user_id: str, project_id: str = None
    ) -> WebSocketMessage:
        """创建任务更新事件"""
        return MessageBuilder.create_message(
            EventType.TASK_UPDATED,
            task_event.to_dict(),
            user_id=user_id,
            room_id=project_id,
        )

    @staticmethod
    def task_status_changed(
        task_id: str,
        old_status: str,
        new_status: str,
        user_id: str,
        project_id: str = None,
    ) -> WebSocketMessage:
        """创建任务状态变更事件"""
        data = {
            "task_id": task_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": user_id,
        }
        return MessageBuilder.create_message(
            EventType.TASK_STATUS_CHANGED,
            data,
            user_id=user_id,
            room_id=project_id,
            priority=Priority.HIGH,
        )

    @staticmethod
    def user_online(user_event: UserEvent, project_id: str = None) -> WebSocketMessage:
        """创建用户上线事件"""
        return MessageBuilder.create_message(
            EventType.USER_ONLINE,
            user_event.to_dict(),
            user_id=user_event.user_id,
            room_id=project_id,
        )

    @staticmethod
    def user_offline(user_event: UserEvent, project_id: str = None) -> WebSocketMessage:
        """创建用户下线事件"""
        return MessageBuilder.create_message(
            EventType.USER_OFFLINE,
            user_event.to_dict(),
            user_id=user_event.user_id,
            room_id=project_id,
        )

    @staticmethod
    def collaboration_edit(
        collab_event: CollaborationEvent, user_id: str
    ) -> WebSocketMessage:
        """创建协作编辑事件"""
        return MessageBuilder.create_message(
            EventType.DOCUMENT_EDIT,
            collab_event.to_dict(),
            user_id=user_id,
            room_id=collab_event.document_id,
            priority=Priority.HIGH,
        )

    @staticmethod
    def system_notification(
        notification: NotificationEvent, user_id: str = None
    ) -> WebSocketMessage:
        """创建系统通知事件"""
        return MessageBuilder.create_message(
            EventType.SYSTEM_NOTIFICATION,
            notification.to_dict(),
            user_id=user_id,
            priority=Priority.NORMAL,
        )

    @staticmethod
    def heartbeat(user_id: str) -> WebSocketMessage:
        """创建心跳事件"""
        return MessageBuilder.create_message(
            EventType.HEARTBEAT,
            {"timestamp": datetime.utcnow().isoformat()},
            user_id=user_id,
        )

    @staticmethod
    def error(
        error_message: str, error_code: str = None, user_id: str = None
    ) -> WebSocketMessage:
        """创建错误事件"""
        data = {"message": error_message, "code": error_code or "UNKNOWN_ERROR"}
        return MessageBuilder.create_message(
            EventType.ERROR, data, user_id=user_id, priority=Priority.URGENT
        )


class EventFilter:
    """事件过滤器"""

    @staticmethod
    def should_broadcast_to_room(event_type: EventType, room_id: str) -> bool:
        """判断事件是否应该广播到房间"""
        room_events = {
            EventType.TASK_CREATED,
            EventType.TASK_UPDATED,
            EventType.TASK_DELETED,
            EventType.TASK_STATUS_CHANGED,
            EventType.USER_ONLINE,
            EventType.USER_OFFLINE,
            EventType.DOCUMENT_EDIT,
            EventType.PROJECT_NOTIFICATION,
        }
        return event_type in room_events and room_id is not None

    @staticmethod
    def should_send_to_user(event_type: EventType, user_id: str) -> bool:
        """判断事件是否应该发送给特定用户"""
        user_events = {
            EventType.SYSTEM_NOTIFICATION,
            EventType.TASK_ASSIGNED,
            EventType.AUTHENTICATION_ERROR,
            EventType.ERROR,
        }
        return event_type in user_events and user_id is not None

    @staticmethod
    def get_event_priority(event_type: EventType) -> Priority:
        """获取事件的默认优先级"""
        priority_map = {
            EventType.ERROR: Priority.URGENT,
            EventType.AUTHENTICATION_ERROR: Priority.URGENT,
            EventType.TASK_STATUS_CHANGED: Priority.HIGH,
            EventType.DOCUMENT_EDIT: Priority.HIGH,
            EventType.SYSTEM_NOTIFICATION: Priority.NORMAL,
            EventType.USER_ONLINE: Priority.LOW,
            EventType.USER_OFFLINE: Priority.LOW,
            EventType.HEARTBEAT: Priority.LOW,
        }
        return priority_map.get(event_type, Priority.NORMAL)


# 常用事件模板
class EventTemplates:
    """常用事件模板"""

    @staticmethod
    def welcome_message(user_id: str, username: str) -> WebSocketMessage:
        """欢迎消息"""
        notification = NotificationEvent(
            notification_id=f"welcome_{user_id}",
            title="欢迎",
            message=f"欢迎 {username}! 您已成功连接到实时系统。",
            type="success",
        )
        return MessageBuilder.system_notification(notification, user_id)

    @staticmethod
    def project_join_notification(
        user_id: str, username: str, project_name: str
    ) -> WebSocketMessage:
        """项目加入通知"""
        notification = NotificationEvent(
            notification_id=f"join_{user_id}_{project_name}",
            title="项目加入",
            message=f"{username} 加入了项目 {project_name}",
            type="info",
        )
        return MessageBuilder.system_notification(notification)

    @staticmethod
    def task_deadline_reminder(
        task_id: str, task_title: str, user_id: str
    ) -> WebSocketMessage:
        """任务截止日期提醒"""
        notification = NotificationEvent(
            notification_id=f"deadline_{task_id}",
            title="截止日期提醒",
            message=f"任务 '{task_title}' 即将到达截止日期",
            type="warning",
            target_user_id=user_id,
            action_url=f"/tasks/{task_id}",
        )
        return MessageBuilder.system_notification(notification, user_id)
