"""
WebSocket实时通信模块
提供完整的WebSocket实时通信解决方案

包含功能：
- WebSocket连接管理
- 消息处理和事件分发
- 实时任务状态更新
- 用户在线状态管理
- 协作编辑支持
- 系统通知推送
- 自动重连和心跳保活
"""

from .manager import websocket_manager, WebSocketManager
from .handlers import websocket_handlers, WebSocketHandlers
from .events import (
    EventType,
    Priority,
    WebSocketMessage,
    MessageBuilder,
    TaskEvent,
    UserEvent,
    CollaborationEvent,
    NotificationEvent,
    EventFilter,
    EventTemplates,
)
from .server import (
    websocket_server,
    WebSocketServer,
    start_websocket_server,
    stop_websocket_server,
    broadcast_task_update,
    broadcast_user_status,
    send_notification_to_user,
    get_websocket_stats,
    get_online_users_for_api,
    get_room_info_for_api,
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude Enhancer Team"


# 模块级别的便捷函数
async def initialize_websocket_system(host: str = "localhost", port: int = 8765):
    """初始化WebSocket系统"""
    try:
        await start_websocket_server(host, port)
        return True
    except Exception as e:
        print(f"WebSocket系统初始化失败: {e}")
        return False


async def shutdown_websocket_system():
    """关闭WebSocket系统"""
    try:
        await stop_websocket_server()
        return True
    except Exception as e:
        print(f"WebSocket系统关闭失败: {e}")
        return False


def is_websocket_available():
    """检查WebSocket是否可用"""
    try:
        import websockets

        return True
    except ImportError:
        return False


# 导出主要接口
__all__ = [
    # 核心类
    "WebSocketManager",
    "WebSocketHandlers",
    "WebSocketServer",
    # 实例
    "websocket_manager",
    "websocket_handlers",
    "websocket_server",
    # 事件相关
    "EventType",
    "Priority",
    "WebSocketMessage",
    "MessageBuilder",
    "TaskEvent",
    "UserEvent",
    "CollaborationEvent",
    "NotificationEvent",
    "EventFilter",
    "EventTemplates",
    # 服务器控制
    "start_websocket_server",
    "stop_websocket_server",
    "initialize_websocket_system",
    "shutdown_websocket_system",
    # API集成
    "broadcast_task_update",
    "broadcast_user_status",
    "send_notification_to_user",
    "get_websocket_stats",
    "get_online_users_for_api",
    "get_room_info_for_api",
    # 工具函数
    "is_websocket_available",
]

# 模块使用示例
"""
使用示例：

1. 启动WebSocket服务器：
   await initialize_websocket_system("0.0.0.0", 8765)

2. 广播任务更新：
   await broadcast_task_update({
       'task_id': 'task_123',
       'title': '新任务',
       'status': 'in_progress',
       'project_id': 'project_456'
   })

3. 发送用户通知：
   await send_notification_to_user(
       'user_123',
       '任务提醒',
       '您有新的任务分配'
   )

4. 获取在线用户：
   users = get_online_users_for_api('project_456')

5. 关闭系统：
   await shutdown_websocket_system()
"""
