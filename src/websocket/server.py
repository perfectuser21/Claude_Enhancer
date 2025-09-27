"""
WebSocket服务器启动模块
负责启动WebSocket服务器并与现有后端集成
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from urllib.parse import parse_qs

try:
    import websockets
    from websockets.server import WebSocketServerProtocol, serve
    from websockets.exceptions import ConnectionClosed, WebSocketException
except ImportError:
    print("警告: 未安装websockets库，WebSocket功能将不可用")
    print("请运行: pip install websockets")
    websockets = None

from .manager import websocket_manager
from .handlers import websocket_handlers
from .events import EventType, MessageBuilder


logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket服务器类"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.is_running = False

    async def start(self):
        """启动WebSocket服务器"""
        if not websockets:
            logger.error("无法启动WebSocket服务器: websockets库未安装")
            return

        try:
            # 启动WebSocket管理器
            await websocket_manager.start()

            # 设置事件处理器
            await websocket_handlers.setup_handlers()

            # 启动WebSocket服务器
            logger.info(f"启动WebSocket服务器 {self.host}:{self.port}")

            self.server = await serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            )

            self.is_running = True
            logger.info(f"WebSocket服务器已启动，监听 ws://{self.host}:{self.port}")

        except Exception as e:
            logger.error(f"启动WebSocket服务器失败: {e}")
            raise

    async def stop(self):
        """停止WebSocket服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        await websocket_manager.stop()
        self.is_running = False
        logger.info("WebSocket服务器已停止")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"新的WebSocket连接: {client_info}")

        user_id = None
        username = None

        try:
            # 解析连接参数
            query_params = parse_qs(websocket.query_string)
            user_id = query_params.get("user_id", [None])[0]
            username = query_params.get("username", [None])[0]

            if not user_id or not username:
                logger.warning(f"连接缺少必要参数: {client_info}")
                await websocket.close(code=4000, reason="Missing user_id or username")
                return

            # 验证用户身份（这里可以添加更严格的验证）
            if not await self.authenticate_user(user_id, username):
                logger.warning(f"用户身份验证失败: {user_id}")
                await websocket.close(code=4001, reason="Authentication failed")
                return

            # 连接用户到管理器
            success = await websocket_manager.connect_user(
                websocket,
                user_id,
                username,
                {
                    "ip": websocket.remote_address[0],
                    "user_agent": websocket.request_headers.get("User-Agent", ""),
                    "connected_at": asyncio.get_event_loop().time(),
                },
            )

            if not success:
                logger.error(f"连接用户失败: {user_id}")
                await websocket.close(code=4002, reason="Failed to connect user")
                return

            logger.info(f"用户 {username}({user_id}) 已连接")

            # 监听消息
            async for message in websocket:
                try:
                    await websocket_manager.handle_message(user_id, message)
                except json.JSONDecodeError:
                    logger.warning(f"收到无效JSON消息: {user_id}")
                    error_msg = MessageBuilder.error("无效的消息格式", "INVALID_JSON", user_id)
                    await websocket_manager.send_to_user(user_id, error_msg)
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    error_msg = MessageBuilder.error(
                        f"服务器错误: {str(e)}", "SERVER_ERROR", user_id
                    )
                    await websocket_manager.send_to_user(user_id, error_msg)

        except ConnectionClosed:
            logger.info(f"连接已关闭: {client_info}")
        except WebSocketException as e:
            logger.warning(f"WebSocket异常: {client_info} - {e}")
        except Exception as e:
            logger.error(f"处理客户端时出错: {client_info} - {e}")
        finally:
            # 清理连接
            if user_id:
                await websocket_manager.disconnect_user(user_id)
                logger.info(f"用户 {user_id} 连接已清理")

    async def authenticate_user(self, user_id: str, username: str) -> bool:
        """验证用户身份"""
        # 这里应该集成现有的认证系统
        # 可以检查JWT token、session等
        try:
            # 示例：简单的用户ID和用户名验证
            if not user_id or not username:
                return False

            # 可以添加更多验证逻辑，例如：
            # - 检查用户是否存在
            # - 验证JWT token
            # - 检查用户权限
            # - 验证IP白名单等

            # 目前简单验证非空即可
            return len(user_id.strip()) > 0 and len(username.strip()) > 0

        except Exception as e:
            logger.error(f"用户身份验证时出错: {e}")
            return False


# 全局WebSocket服务器实例
websocket_server = WebSocketServer()


# 便捷的启动函数
async def start_websocket_server(host: str = "localhost", port: int = 8765):
    """启动WebSocket服务器"""
    global websocket_server
    websocket_server = WebSocketServer(host, port)
    await websocket_server.start()


async def stop_websocket_server():
    """停止WebSocket服务器"""
    if websocket_server:
        await websocket_server.stop()


# 与现有后端API集成的工具函数
async def broadcast_task_update(
    task_data: Dict[str, Any], event_type: str = "task_updated"
):
    """从后端API广播任务更新"""
    try:
        if not websocket_manager.connections:
            return

        # 根据事件类型创建消息
        event_type_enum = getattr(EventType, event_type.upper(), EventType.TASK_UPDATED)

        message = MessageBuilder.create_message(
            event_type_enum,
            task_data,
            user_id=task_data.get("updated_by"),
            room_id=task_data.get("project_id"),
        )

        # 广播到相关房间或所有用户
        project_id = task_data.get("project_id")
        if project_id:
            await websocket_manager.broadcast_to_room(project_id, message)
        else:
            await websocket_manager.broadcast_to_all(message)

        logger.info(f"已广播任务更新: {task_data.get('task_id', 'unknown')}")

    except Exception as e:
        logger.error(f"广播任务更新失败: {e}")


async def broadcast_user_status(
    user_id: str, username: str, status: str, project_id: str = None
):
    """从后端API广播用户状态更新"""
    try:
        if not websocket_manager.connections:
            return

        user_data = {
            "user_id": user_id,
            "username": username,
            "status": status,
            "timestamp": asyncio.get_event_loop().time(),
        }

        event_type = (
            EventType.USER_ONLINE if status == "online" else EventType.USER_OFFLINE
        )

        message = MessageBuilder.create_message(
            event_type, user_data, user_id=user_id, room_id=project_id
        )

        if project_id:
            await websocket_manager.broadcast_to_room(project_id, message)
        else:
            await websocket_manager.broadcast_to_all(message)

        logger.info(f"已广播用户状态: {username} -> {status}")

    except Exception as e:
        logger.error(f"广播用户状态失败: {e}")


async def send_notification_to_user(
    user_id: str, title: str, message: str, notification_type: str = "info"
):
    """从后端API发送通知给特定用户"""
    try:
        notification_data = {
            "notification_id": f"api_notif_{asyncio.get_event_loop().time()}",
            "title": title,
            "message": message,
            "type": notification_type,
            "target_user_id": user_id,
            "auto_dismiss": True,
            "dismiss_timeout": 5000,
        }

        notify_msg = MessageBuilder.create_message(
            EventType.SYSTEM_NOTIFICATION, notification_data, user_id=user_id
        )

        await websocket_manager.send_to_user(user_id, notify_msg)
        logger.info(f"已发送通知给用户 {user_id}: {title}")

    except Exception as e:
        logger.error(f"发送通知失败: {e}")


def get_websocket_stats() -> Dict[str, Any]:
    """获取WebSocket服务器统计信息"""
    if not websocket_server.is_running:
        return {"status": "stopped"}

    stats = websocket_manager.get_stats()
    stats.update(
        {
            "status": "running",
            "server_host": websocket_server.host,
            "server_port": websocket_server.port,
        }
    )

    return stats


def get_online_users_for_api(room_id: str = None) -> list:
    """为API提供在线用户列表"""
    return websocket_manager.get_online_users(room_id)


def get_room_info_for_api(room_id: str) -> Optional[Dict[str, Any]]:
    """为API提供房间信息"""
    return websocket_manager.get_room_info(room_id)


# Flask/FastAPI集成示例
async def integrate_with_flask_socketio():
    """与Flask-SocketIO集成的示例"""
    # 这里可以添加与现有Flask后端的集成逻辑
    pass


async def integrate_with_fastapi():
    """与FastAPI集成的示例"""
    # 这里可以添加与现有FastAPI后端的集成逻辑
    pass


if __name__ == "__main__":
    # 独立运行WebSocket服务器
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket服务器")
    parser.add_argument("--host", default="localhost", help="服务器主机")
    parser.add_argument("--port", type=int, default=8765, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    async def main():
        try:
            await start_websocket_server(args.host, args.port)
            logger.info("WebSocket服务器正在运行，按Ctrl+C停止...")
            # 保持服务器运行
            await asyncio.Future()  # 永远等待
        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在关闭服务器...")
            await stop_websocket_server()

    asyncio.run(main())
