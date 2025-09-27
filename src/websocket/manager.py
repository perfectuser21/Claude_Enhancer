"""
WebSocket连接管理器
负责管理WebSocket连接、房间和消息分发
"""

import asyncio
import logging
from typing import Dict, Set, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import weakref
from collections import defaultdict

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    # 如果没有安装websockets，提供Mock类型
    class WebSocketServerProtocol:
        pass


from .events import WebSocketMessage, EventType, MessageBuilder, EventFilter, Priority


logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """WebSocket连接信息"""

    websocket: WebSocketServerProtocol
    user_id: str
    username: str
    connected_at: datetime
    last_heartbeat: datetime
    rooms: Set[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if not self.rooms:
            self.rooms = set()
        if not self.metadata:
            self.metadata = {}

    @property
    def is_alive(self) -> bool:
        """检查连接是否活跃"""
        return (datetime.utcnow() - self.last_heartbeat) < timedelta(minutes=2)

    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.utcnow()


class Room:
    """房间管理类"""

    def __init__(self, room_id: str, name: str = None):
        self.room_id = room_id
        self.name = name or room_id
        self.connections: Set[str] = set()  # user_id集合
        self.created_at = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}

    def add_user(self, user_id: str):
        """添加用户到房间"""
        self.connections.add(user_id)

    def remove_user(self, user_id: str):
        """从房间移除用户"""
        self.connections.discard(user_id)

    @property
    def user_count(self) -> int:
        """房间用户数量"""
        return len(self.connections)

    @property
    def is_empty(self) -> bool:
        """房间是否为空"""
        return len(self.connections) == 0


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.connections: Dict[str, Connection] = {}  # user_id -> Connection
        self.rooms: Dict[str, Room] = {}  # room_id -> Room
        self.user_websockets: Dict[
            str, WebSocketServerProtocol
        ] = {}  # user_id -> websocket
        self.message_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "rooms_created": 0,
        }
        self._cleanup_task: Optional[asyncio.Task] = None
        self._broadcast_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动管理器"""
        logger.info("启动WebSocket管理器")
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_connections())
        self._broadcast_task = asyncio.create_task(self._process_broadcast_queue())

    async def stop(self):
        """停止管理器"""
        logger.info("停止WebSocket管理器")
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._broadcast_task:
            self._broadcast_task.cancel()

        # 关闭所有连接
        for connection in list(self.connections.values()):
            await self.disconnect_user(connection.user_id)

    async def connect_user(
        self,
        websocket: WebSocketServerProtocol,
        user_id: str,
        username: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """连接用户"""
        try:
            # 如果用户已经连接，先断开旧连接
            if user_id in self.connections:
                await self.disconnect_user(user_id)

            connection = Connection(
                websocket=websocket,
                user_id=user_id,
                username=username,
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                rooms=set(),
                metadata=metadata or {},
            )

            self.connections[user_id] = connection
            self.user_websockets[user_id] = websocket

            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)

            logger.info(f"用户 {username}({user_id}) 已连接")

            # 发送欢迎消息
            welcome_msg = MessageBuilder.create_message(
                EventType.CONNECT,
                {"message": f"欢迎 {username}!", "user_id": user_id},
                user_id=user_id,
            )
            await self.send_to_user(user_id, welcome_msg)

            # 触发用户上线事件
            await self._trigger_event_handlers(
                EventType.CONNECT,
                {"user_id": user_id, "username": username, "metadata": metadata},
            )

            return True

        except Exception as e:
            logger.error(f"连接用户失败: {e}")
            return False

    async def disconnect_user(self, user_id: str):
        """断开用户连接"""
        if user_id not in self.connections:
            return

        connection = self.connections[user_id]

        try:
            # 从所有房间移除用户
            for room_id in list(connection.rooms):
                await self.leave_room(user_id, room_id)

            # 关闭WebSocket连接
            if not connection.websocket.closed:
                await connection.websocket.close()

        except Exception as e:
            logger.error(f"断开连接时出错: {e}")

        finally:
            # 清理连接记录
            del self.connections[user_id]
            self.user_websockets.pop(user_id, None)

            self.stats["active_connections"] = len(self.connections)

            logger.info(f"用户 {connection.username}({user_id}) 已断开连接")

            # 触发用户下线事件
            await self._trigger_event_handlers(
                EventType.DISCONNECT,
                {"user_id": user_id, "username": connection.username},
            )

    async def join_room(
        self, user_id: str, room_id: str, room_name: str = None
    ) -> bool:
        """用户加入房间"""
        if user_id not in self.connections:
            logger.warning(f"用户 {user_id} 不存在，无法加入房间")
            return False

        # 创建房间（如果不存在）
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id, room_name)
            self.stats["rooms_created"] += 1
            logger.info(f"创建房间: {room_id}")

        # 用户加入房间
        self.connections[user_id].rooms.add(room_id)
        self.rooms[room_id].add_user(user_id)

        logger.info(f"用户 {user_id} 加入房间 {room_id}")

        # 通知房间内其他用户
        join_msg = MessageBuilder.create_message(
            EventType.USER_JOIN_PROJECT,
            {
                "user_id": user_id,
                "username": self.connections[user_id].username,
                "room_id": room_id,
                "room_name": room_name,
            },
            user_id=user_id,
            room_id=room_id,
        )
        await self.broadcast_to_room(room_id, join_msg, exclude_user=user_id)

        return True

    async def leave_room(self, user_id: str, room_id: str) -> bool:
        """用户离开房间"""
        if user_id not in self.connections:
            return False

        if room_id not in self.rooms:
            return False

        # 用户离开房间
        self.connections[user_id].rooms.discard(room_id)
        self.rooms[room_id].remove_user(user_id)

        logger.info(f"用户 {user_id} 离开房间 {room_id}")

        # 通知房间内其他用户
        leave_msg = MessageBuilder.create_message(
            EventType.USER_LEAVE_PROJECT,
            {
                "user_id": user_id,
                "username": self.connections[user_id].username,
                "room_id": room_id,
            },
            user_id=user_id,
            room_id=room_id,
        )
        await self.broadcast_to_room(room_id, leave_msg, exclude_user=user_id)

        # 如果房间为空，删除房间
        if self.rooms[room_id].is_empty:
            del self.rooms[room_id]
            logger.info(f"删除空房间: {room_id}")

        return True

    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> bool:
        """发送消息给特定用户"""
        if user_id not in self.connections:
            logger.warning(f"用户 {user_id} 不在线，无法发送消息")
            return False

        try:
            websocket = self.connections[user_id].websocket
            if websocket.closed:
                logger.warning(f"用户 {user_id} 的连接已关闭")
                await self.disconnect_user(user_id)
                return False

            await websocket.send(message.to_json())
            self.stats["messages_sent"] += 1
            return True

        except Exception as e:
            logger.error(f"发送消息给用户 {user_id} 失败: {e}")
            await self.disconnect_user(user_id)
            return False

    async def broadcast_to_room(
        self, room_id: str, message: WebSocketMessage, exclude_user: str = None
    ) -> int:
        """向房间广播消息"""
        if room_id not in self.rooms:
            logger.warning(f"房间 {room_id} 不存在")
            return 0

        success_count = 0
        room = self.rooms[room_id]

        for user_id in list(room.connections):
            if exclude_user and user_id == exclude_user:
                continue

            if await self.send_to_user(user_id, message):
                success_count += 1

        logger.debug(f"向房间 {room_id} 广播消息，成功发送给 {success_count} 个用户")
        return success_count

    async def broadcast_to_all(
        self, message: WebSocketMessage, exclude_user: str = None
    ) -> int:
        """向所有在线用户广播消息"""
        success_count = 0

        for user_id in list(self.connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue

            if await self.send_to_user(user_id, message):
                success_count += 1

        logger.debug(f"向所有用户广播消息，成功发送给 {success_count} 个用户")
        return success_count

    async def queue_broadcast(
        self, message: WebSocketMessage, target_type: str, target_id: str = None
    ):
        """将消息加入广播队列"""
        await self.broadcast_queue.put(
            {
                "message": message,
                "target_type": target_type,  # 'user', 'room', 'all'
                "target_id": target_id,
            }
        )

    async def handle_message(self, user_id: str, raw_message: str):
        """处理接收到的消息"""
        try:
            message = WebSocketMessage.from_json(raw_message)
            self.stats["messages_received"] += 1

            # 更新心跳
            if user_id in self.connections:
                self.connections[user_id].update_heartbeat()

            # 处理心跳消息
            if message.type == EventType.HEARTBEAT:
                await self._handle_heartbeat(user_id, message)
                return

            # 触发事件处理器
            await self._trigger_event_handlers(
                message.type,
                {"user_id": user_id, "message": message, "raw_data": message.data},
            )

            logger.debug(f"处理来自用户 {user_id} 的消息: {message.type.value}")

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            error_msg = MessageBuilder.error(f"消息处理失败: {str(e)}", user_id=user_id)
            await self.send_to_user(user_id, error_msg)

    def register_event_handler(self, event_type: EventType, handler: Callable):
        """注册事件处理器"""
        self.message_handlers[event_type].append(handler)
        logger.debug(f"注册事件处理器: {event_type.value}")

    def get_online_users(self, room_id: str = None) -> List[Dict[str, Any]]:
        """获取在线用户列表"""
        if room_id:
            if room_id not in self.rooms:
                return []
            user_ids = self.rooms[room_id].connections
        else:
            user_ids = self.connections.keys()

        users = []
        for user_id in user_ids:
            if user_id in self.connections:
                conn = self.connections[user_id]
                users.append(
                    {
                        "user_id": user_id,
                        "username": conn.username,
                        "connected_at": conn.connected_at.isoformat(),
                        "last_heartbeat": conn.last_heartbeat.isoformat(),
                        "rooms": list(conn.rooms),
                        "metadata": conn.metadata,
                    }
                )

        return users

    def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取房间信息"""
        if room_id not in self.rooms:
            return None

        room = self.rooms[room_id]
        return {
            "room_id": room_id,
            "name": room.name,
            "user_count": room.user_count,
            "users": list(room.connections),
            "created_at": room.created_at.isoformat(),
            "metadata": room.metadata,
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "rooms_count": len(self.rooms),
            "total_users_in_rooms": sum(
                room.user_count for room in self.rooms.values()
            ),
        }

    async def _handle_heartbeat(self, user_id: str, message: WebSocketMessage):
        """处理心跳消息"""
        if user_id in self.connections:
            self.connections[user_id].update_heartbeat()

            # 回复心跳确认
            heartbeat_ack = MessageBuilder.create_message(
                EventType.HEARTBEAT,
                {"ack": True, "server_time": datetime.utcnow().isoformat()},
                user_id=user_id,
            )
            await self.send_to_user(user_id, heartbeat_ack)

    async def _trigger_event_handlers(
        self, event_type: EventType, data: Dict[str, Any]
    ):
        """触发事件处理器"""
        if event_type in self.message_handlers:
            for handler in self.message_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {e}")

    async def _cleanup_inactive_connections(self):
        """清理非活跃连接"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次

                inactive_users = []
                for user_id, connection in self.connections.items():
                    if not connection.is_alive:
                        inactive_users.append(user_id)

                for user_id in inactive_users:
                    logger.info(f"清理非活跃连接: {user_id}")
                    await self.disconnect_user(user_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理连接时出错: {e}")

    async def _process_broadcast_queue(self):
        """处理广播队列"""
        while True:
            try:
                broadcast_item = await self.broadcast_queue.get()
                message = broadcast_item["message"]
                target_type = broadcast_item["target_type"]
                target_id = broadcast_item["target_id"]

                if target_type == "user":
                    await self.send_to_user(target_id, message)
                elif target_type == "room":
                    await self.broadcast_to_room(target_id, message)
                elif target_type == "all":
                    await self.broadcast_to_all(message)

                self.broadcast_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"处理广播队列时出错: {e}")


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()
