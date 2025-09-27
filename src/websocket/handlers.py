"""
WebSocket消息处理器
处理各种WebSocket事件和业务逻辑
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .events import (
    EventType,
    WebSocketMessage,
    MessageBuilder,
    TaskEvent,
    UserEvent,
    CollaborationEvent,
    NotificationEvent,
)
from .manager import websocket_manager

logger = logging.getLogger(__name__)


class WebSocketHandlers:
    """WebSocket事件处理器集合"""

    def __init__(self):
        self.active_collaborations: Dict[
            str, Dict[str, Any]
        ] = {}  # document_id -> collaboration_data
        self.typing_users: Dict[
            str, Dict[str, datetime]
        ] = {}  # room_id -> {user_id: last_typing_time}

    async def setup_handlers(self):
        """设置事件处理器"""
        # 注册所有事件处理器
        websocket_manager.register_event_handler(
            EventType.CONNECT, self.handle_user_connect
        )
        websocket_manager.register_event_handler(
            EventType.DISCONNECT, self.handle_user_disconnect
        )
        websocket_manager.register_event_handler(
            EventType.TASK_CREATED, self.handle_task_created
        )
        websocket_manager.register_event_handler(
            EventType.TASK_UPDATED, self.handle_task_updated
        )
        websocket_manager.register_event_handler(
            EventType.TASK_STATUS_CHANGED, self.handle_task_status_changed
        )
        websocket_manager.register_event_handler(
            EventType.DOCUMENT_EDIT, self.handle_document_edit
        )
        websocket_manager.register_event_handler(
            EventType.USER_TYPING, self.handle_user_typing
        )
        websocket_manager.register_event_handler(
            EventType.COLLABORATION_START, self.handle_collaboration_start
        )
        websocket_manager.register_event_handler(
            EventType.COLLABORATION_END, self.handle_collaboration_end
        )

        logger.info("WebSocket事件处理器已设置完成")

    async def handle_user_connect(self, data: Dict[str, Any]):
        """处理用户连接事件"""
        user_id = data["user_id"]
        username = data["username"]
        metadata = data.get("metadata", {})

        logger.info(f"用户 {username}({user_id}) 已连接")

        # 广播用户上线通知
        user_event = UserEvent(user_id=user_id, username=username, status="online")

        online_msg = MessageBuilder.user_online(user_event)
        await websocket_manager.broadcast_to_all(online_msg, exclude_user=user_id)

        # 发送系统状态信息给新连接的用户
        await self.send_system_status(user_id)

    async def handle_user_disconnect(self, data: Dict[str, Any]):
        """处理用户断开连接事件"""
        user_id = data["user_id"]
        username = data["username"]

        logger.info(f"用户 {username}({user_id}) 已断开连接")

        # 广播用户下线通知
        user_event = UserEvent(user_id=user_id, username=username, status="offline")

        offline_msg = MessageBuilder.user_offline(user_event)
        await websocket_manager.broadcast_to_all(offline_msg, exclude_user=user_id)

        # 清理协作状态
        await self.cleanup_user_collaborations(user_id)

    async def handle_task_created(self, data: Dict[str, Any]):
        """处理任务创建事件"""
        message = data["message"]
        task_data = message.data

        logger.info(f"新任务创建: {task_data.get('title', 'Unknown')}")

        # 如果任务有项目ID，广播给项目成员
        project_id = task_data.get("project_id")
        if project_id:
            await websocket_manager.broadcast_to_room(project_id, message)

        # 如果任务有指派人，发送通知
        assignee_id = task_data.get("assignee_id")
        if assignee_id and assignee_id != data["user_id"]:
            notification = NotificationEvent(
                notification_id=f"task_assigned_{task_data.get('task_id')}",
                title="新任务分配",
                message=f"您收到了新任务: {task_data.get('title', '未知任务')}",
                type="info",
                target_user_id=assignee_id,
                action_url=f"/tasks/{task_data.get('task_id')}",
            )
            notify_msg = MessageBuilder.system_notification(notification, assignee_id)
            await websocket_manager.send_to_user(assignee_id, notify_msg)

    async def handle_task_updated(self, data: Dict[str, Any]):
        """处理任务更新事件"""
        message = data["message"]
        task_data = message.data

        logger.info(f"任务更新: {task_data.get('title', 'Unknown')}")

        # 广播给项目成员
        project_id = task_data.get("project_id")
        if project_id:
            await websocket_manager.broadcast_to_room(project_id, message)

        # 通知相关用户
        await self.notify_task_stakeholders(task_data, "任务已更新")

    async def handle_task_status_changed(self, data: Dict[str, Any]):
        """处理任务状态变更事件"""
        message = data["message"]
        task_data = message.data

        logger.info(
            f"任务状态变更: {task_data.get('task_id')} -> {task_data.get('new_status')}"
        )

        # 广播状态变更
        project_id = message.room_id
        if project_id:
            await websocket_manager.broadcast_to_room(project_id, message)

        # 发送状态变更通知
        notification = NotificationEvent(
            notification_id=f"status_change_{task_data.get('task_id')}",
            title="任务状态更新",
            message=f"任务状态从 '{task_data.get('old_status')}' 变更为 '{task_data.get('new_status')}'",
            type="info",
        )
        notify_msg = MessageBuilder.system_notification(notification)

        if project_id:
            await websocket_manager.broadcast_to_room(project_id, notify_msg)

    async def handle_document_edit(self, data: Dict[str, Any]):
        """处理文档编辑事件"""
        message = data["message"]
        edit_data = message.data
        user_id = data["user_id"]

        document_id = edit_data.get("document_id")
        logger.debug(f"文档编辑: {document_id} by {user_id}")

        # 广播编辑事件给文档的其他协作者
        await websocket_manager.broadcast_to_room(
            document_id, message, exclude_user=user_id
        )

        # 更新协作状态
        await self.update_collaboration_state(document_id, user_id, edit_data)

    async def handle_user_typing(self, data: Dict[str, Any]):
        """处理用户输入事件"""
        message = data["message"]
        user_id = data["user_id"]
        room_id = message.room_id

        if room_id:
            # 记录用户输入状态
            if room_id not in self.typing_users:
                self.typing_users[room_id] = {}

            self.typing_users[room_id][user_id] = datetime.utcnow()

            # 广播输入状态给房间其他成员
            await websocket_manager.broadcast_to_room(
                room_id, message, exclude_user=user_id
            )

            # 5秒后清理输入状态
            asyncio.create_task(self.clear_typing_status(room_id, user_id, 5))

    async def handle_collaboration_start(self, data: Dict[str, Any]):
        """处理协作开始事件"""
        message = data["message"]
        collab_data = message.data
        user_id = data["user_id"]

        document_id = collab_data.get("document_id")
        logger.info(f"开始协作编辑: {document_id} by {user_id}")

        # 初始化协作状态
        if document_id not in self.active_collaborations:
            self.active_collaborations[document_id] = {
                "participants": set(),
                "started_at": datetime.utcnow(),
                "document_version": collab_data.get("version", 0),
            }

        self.active_collaborations[document_id]["participants"].add(user_id)

        # 用户加入文档房间
        await websocket_manager.join_room(
            user_id, document_id, f"Document: {document_id}"
        )

        # 通知其他协作者
        await websocket_manager.broadcast_to_room(
            document_id, message, exclude_user=user_id
        )

    async def handle_collaboration_end(self, data: Dict[str, Any]):
        """处理协作结束事件"""
        message = data["message"]
        collab_data = message.data
        user_id = data["user_id"]

        document_id = collab_data.get("document_id")
        logger.info(f"结束协作编辑: {document_id} by {user_id}")

        # 用户离开文档房间
        await websocket_manager.leave_room(user_id, document_id)

        # 更新协作状态
        if document_id in self.active_collaborations:
            self.active_collaborations[document_id]["participants"].discard(user_id)

            # 如果没有参与者了，清理协作状态
            if not self.active_collaborations[document_id]["participants"]:
                del self.active_collaborations[document_id]
                logger.info(f"协作会话结束: {document_id}")

        # 通知其他协作者
        await websocket_manager.broadcast_to_room(
            document_id, message, exclude_user=user_id
        )

    async def send_system_status(self, user_id: str):
        """发送系统状态信息给用户"""
        try:
            # 获取在线用户列表
            online_users = websocket_manager.get_online_users()

            # 获取系统统计信息
            stats = websocket_manager.get_stats()

            # 创建系统状态消息
            status_data = {
                "online_users_count": len(online_users),
                "active_rooms": len(websocket_manager.rooms),
                "server_time": datetime.utcnow().isoformat(),
                "system_stats": stats,
            }

            status_msg = MessageBuilder.create_message(
                EventType.DATA_SYNC, status_data, user_id=user_id
            )

            await websocket_manager.send_to_user(user_id, status_msg)

        except Exception as e:
            logger.error(f"发送系统状态失败: {e}")

    async def notify_task_stakeholders(self, task_data: Dict[str, Any], message: str):
        """通知任务相关人员"""
        try:
            # 通知任务创建者
            creator_id = task_data.get("creator_id")
            if creator_id:
                await self.send_notification(creator_id, "任务更新", message)

            # 通知任务指派人
            assignee_id = task_data.get("assignee_id")
            if assignee_id and assignee_id != creator_id:
                await self.send_notification(assignee_id, "任务更新", message)

            # 通知项目成员（如果不是以上人员）
            project_id = task_data.get("project_id")
            if project_id:
                notification = NotificationEvent(
                    notification_id=f"task_update_{task_data.get('task_id')}",
                    title="项目任务更新",
                    message=f"{message}: {task_data.get('title', '未知任务')}",
                    type="info",
                    target_project_id=project_id,
                )
                notify_msg = MessageBuilder.system_notification(notification)
                await websocket_manager.broadcast_to_room(project_id, notify_msg)

        except Exception as e:
            logger.error(f"通知任务相关人员失败: {e}")

    async def send_notification(
        self, user_id: str, title: str, message: str, type: str = "info"
    ):
        """发送通知给用户"""
        try:
            notification = NotificationEvent(
                notification_id=f"notif_{user_id}_{datetime.utcnow().timestamp()}",
                title=title,
                message=message,
                type=type,
                target_user_id=user_id,
            )
            notify_msg = MessageBuilder.system_notification(notification, user_id)
            await websocket_manager.send_to_user(user_id, notify_msg)

        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    async def update_collaboration_state(
        self, document_id: str, user_id: str, edit_data: Dict[str, Any]
    ):
        """更新协作状态"""
        try:
            if document_id in self.active_collaborations:
                collab = self.active_collaborations[document_id]

                # 更新文档版本
                if "version" in edit_data:
                    collab["document_version"] = edit_data["version"]

                # 记录最后编辑时间
                collab["last_edit"] = datetime.utcnow()
                collab["last_editor"] = user_id

                logger.debug(f"协作状态已更新: {document_id}")

        except Exception as e:
            logger.error(f"更新协作状态失败: {e}")

    async def cleanup_user_collaborations(self, user_id: str):
        """清理用户的协作状态"""
        try:
            documents_to_cleanup = []

            # 找到用户参与的所有协作
            for document_id, collab in self.active_collaborations.items():
                if user_id in collab["participants"]:
                    collab["participants"].discard(user_id)

                    # 如果没有其他参与者，标记为需要清理
                    if not collab["participants"]:
                        documents_to_cleanup.append(document_id)

            # 清理空的协作会话
            for document_id in documents_to_cleanup:
                del self.active_collaborations[document_id]
                logger.info(f"清理协作会话: {document_id}")

        except Exception as e:
            logger.error(f"清理用户协作状态失败: {e}")

    async def clear_typing_status(self, room_id: str, user_id: str, delay: int):
        """延迟清理用户输入状态"""
        try:
            await asyncio.sleep(delay)

            if room_id in self.typing_users and user_id in self.typing_users[room_id]:
                # 检查是否超过了设定时间
                last_typing = self.typing_users[room_id][user_id]
                if (datetime.utcnow() - last_typing).seconds >= delay:
                    del self.typing_users[room_id][user_id]

                    # 如果房间没有人在输入，清理房间记录
                    if not self.typing_users[room_id]:
                        del self.typing_users[room_id]

                    # 广播停止输入状态
                    stop_typing_msg = MessageBuilder.create_message(
                        EventType.USER_TYPING,
                        {"user_id": user_id, "typing": False},
                        user_id=user_id,
                        room_id=room_id,
                    )
                    await websocket_manager.broadcast_to_room(
                        room_id, stop_typing_msg, exclude_user=user_id
                    )

        except Exception as e:
            logger.error(f"清理输入状态失败: {e}")

    def get_collaboration_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取协作信息"""
        if document_id not in self.active_collaborations:
            return None

        collab = self.active_collaborations[document_id]
        return {
            "document_id": document_id,
            "participants": list(collab["participants"]),
            "participant_count": len(collab["participants"]),
            "started_at": collab["started_at"].isoformat(),
            "document_version": collab.get("document_version", 0),
            "last_edit": collab.get("last_edit", {}).isoformat()
            if collab.get("last_edit")
            else None,
            "last_editor": collab.get("last_editor"),
        }

    def get_typing_users(self, room_id: str) -> List[str]:
        """获取正在输入的用户列表"""
        if room_id not in self.typing_users:
            return []

        # 清理超时的输入状态
        current_time = datetime.utcnow()
        active_users = []

        for user_id, last_typing in list(self.typing_users[room_id].items()):
            if (current_time - last_typing).seconds < 10:  # 10秒超时
                active_users.append(user_id)
            else:
                del self.typing_users[room_id][user_id]

        return active_users


# 全局处理器实例
websocket_handlers = WebSocketHandlers()


# 便捷的API函数
async def broadcast_task_event(
    event_type: EventType,
    task_data: Dict[str, Any],
    user_id: str,
    project_id: str = None,
):
    """广播任务事件"""
    task_event = TaskEvent(**task_data)

    if event_type == EventType.TASK_CREATED:
        message = MessageBuilder.task_created(task_event, user_id, project_id)
    elif event_type == EventType.TASK_UPDATED:
        message = MessageBuilder.task_updated(task_event, user_id, project_id)
    else:
        message = MessageBuilder.create_message(
            event_type, task_data, user_id, project_id
        )

    if project_id:
        await websocket_manager.broadcast_to_room(project_id, message)
    else:
        await websocket_manager.broadcast_to_all(message)


async def send_notification_to_user(
    user_id: str, title: str, message: str, type: str = "info"
):
    """发送通知给特定用户"""
    notification = NotificationEvent(
        notification_id=f"notif_{user_id}_{datetime.utcnow().timestamp()}",
        title=title,
        message=message,
        type=type,
        target_user_id=user_id,
    )
    notify_msg = MessageBuilder.system_notification(notification, user_id)
    await websocket_manager.send_to_user(user_id, notify_msg)


async def broadcast_user_status(
    user_id: str, username: str, status: str, project_id: str = None
):
    """广播用户状态变更"""
    user_event = UserEvent(user_id=user_id, username=username, status=status)

    if status == "online":
        message = MessageBuilder.user_online(user_event, project_id)
    else:
        message = MessageBuilder.user_offline(user_event, project_id)

    if project_id:
        await websocket_manager.broadcast_to_room(project_id, message)
    else:
        await websocket_manager.broadcast_to_all(message)
