"""
Performance Optimization: Async Background Processor
异步后台处理器 - 高性能异步任务处理系统
"""

import asyncio
import aiohttp
import smtplib
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import json
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aio_pika
from contextlib import asynccontextmanager
import time
import uuid

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """异步任务"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    error: Optional[str] = None
    result: Any = None


@dataclass
class ProcessorConfig:
    """异步处理器配置"""

    max_workers: int = 10
    max_queue_size: int = 1000
    worker_timeout: float = 300.0  # 5分钟
    health_check_interval: float = 30.0
    stats_report_interval: float = 60.0
    cleanup_interval: float = 3600.0  # 1小时
    task_retention_hours: int = 24

    # 邮件配置
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    email_from: str = "noreply@perfect21.com"

    # 消息队列配置
    rabbitmq_url: str = "amqp://localhost"

    # 外部API配置
    api_timeout: float = 30.0
    api_retries: int = 3


class AsyncProcessor:
    """异步后台处理器 - 企业级异步任务处理系统"""

    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.tasks: Dict[str, Task] = {}
        self.pending_queue = asyncio.PriorityQueue(maxsize=config.max_queue_size)
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "retried_tasks": 0,
            "avg_processing_time": 0.0,
            "active_workers": 0,
        }
        self._lock = asyncio.Lock()
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

    async def initialize(self):
        """初始化异步处理器"""
        try:
            # 初始化RabbitMQ连接
            await self._setup_rabbitmq()

            # 启动工作进程
            await self._start_workers()

            # 启动后台任务
            asyncio.create_task(self._health_monitor())
            asyncio.create_task(self._stats_reporter())
            asyncio.create_task(self._cleanup_completed_tasks())

            self.running = True
            logger.info(f"✅ 异步处理器初始化成功 - 工作进程数: {self.config.max_workers}")

        except Exception as e:
            logger.error(f"❌ 异步处理器初始化失败: {e}")
            raise

    async def _setup_rabbitmq(self):
        """设置RabbitMQ连接"""
        try:
            self.rabbitmq_connection = await aio_pika.connect_robust(
                self.config.rabbitmq_url
            )
            self.rabbitmq_channel = await self.rabbitmq_connection.channel()

            # 声明队列
            await self.rabbitmq_channel.declare_queue(
                "perfect21.notifications", durable=True
            )
            await self.rabbitmq_channel.declare_queue("perfect21.emails", durable=True)
            await self.rabbitmq_channel.declare_queue(
                "perfect21.webhooks", durable=True
            )

            logger.info("✅ RabbitMQ连接建立成功")

        except Exception as e:
            logger.warning(f"⚠️ RabbitMQ连接失败，将使用内存队列: {e}")

    async def _start_workers(self):
        """启动工作进程"""
        for i in range(self.config.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

    async def _worker(self, worker_name: str):
        """工作进程"""
        logger.info(f"🔧 工作进程启动: {worker_name}")

        while self.running:
            try:
                # 获取任务（按优先级）
                priority, task = await asyncio.wait_for(
                    self.pending_queue.get(), timeout=1.0
                )

                self.stats["active_workers"] += 1

                # 处理任务
                await self._process_task(task, worker_name)

                self.pending_queue.task_done()
                self.stats["active_workers"] -= 1

            except asyncio.TimeoutError:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"❌ 工作进程 {worker_name} 错误: {e}")
                self.stats["active_workers"] -= 1
                await asyncio.sleep(1)

    async def _process_task(self, task: Task, worker_name: str):
        """处理单个任务"""
        start_time = time.time()
        task.started_at = datetime.now()
        task.status = TaskStatus.PROCESSING

        logger.debug(f"🔄 开始处理任务: {task.name} (ID: {task.id}) - 工作进程: {worker_name}")

        try:
            # 执行任务（带超时）
            if task.timeout:
                task.result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs), timeout=task.timeout
                )
            else:
                task.result = await task.func(*task.args, **task.kwargs)

            # 任务完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            processing_time = time.time() - start_time
            self.stats["completed_tasks"] += 1

            # 更新平均处理时间
            total_completed = self.stats["completed_tasks"]
            self.stats["avg_processing_time"] = (
                self.stats["avg_processing_time"] * (total_completed - 1)
                + processing_time
            ) / total_completed

            logger.debug(f"✅ 任务完成: {task.name} - 耗时: {processing_time:.2f}s")

        except asyncio.TimeoutError:
            # 任务超时
            task.error = f"Task timeout after {task.timeout}s"
            await self._handle_task_failure(task, start_time)

        except Exception as e:
            # 任务执行失败
            task.error = f"{type(e).__name__}: {str(e)}"
            await self._handle_task_failure(task, start_time)

    async def _handle_task_failure(self, task: Task, start_time: float):
        """处理任务失败"""
        processing_time = time.time() - start_time

        logger.error(f"❌ 任务失败: {task.name} - 错误: {task.error}")

        # 检查是否需要重试
        if task.retries < task.max_retries:
            task.retries += 1
            task.status = TaskStatus.RETRYING

            # 延迟后重新入队
            delay = task.retry_delay * (2 ** (task.retries - 1))  # 指数退避
            logger.info(f"🔄 任务重试: {task.name} - 第{task.retries}次重试，延迟{delay}s")

            asyncio.create_task(self._schedule_retry(task, delay))
            self.stats["retried_tasks"] += 1

        else:
            # 重试次数用尽，标记为失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.stats["failed_tasks"] += 1

            logger.error(f"💀 任务最终失败: {task.name} - 已重试{task.retries}次")

    async def _schedule_retry(self, task: Task, delay: float):
        """安排任务重试"""
        await asyncio.sleep(delay)
        task.status = TaskStatus.PENDING
        await self.add_task(task, overwrite=True)

    async def add_task(self, task: Task, overwrite: bool = False) -> str:
        """添加任务到队列"""
        async with self._lock:
            if not overwrite and task.id in self.tasks:
                raise ValueError(f"任务ID已存在: {task.id}")

            self.tasks[task.id] = task

            # 添加到优先级队列（优先级值越大，优先级越高）
            priority = -task.priority.value  # 负值使得高优先级在前
            await self.pending_queue.put((priority, task))

            self.stats["total_tasks"] += 1

            logger.debug(
                f"📝 任务已入队: {task.name} (ID: {task.id}, 优先级: {task.priority.name})"
            )

            return task.id

    async def submit_email_task(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """提交邮件发送任务"""
        task = Task(
            name=f"send_email",
            func=self._send_email,
            args=(to_emails, subject, body, is_html),
            priority=priority,
            timeout=30.0,
        )
        return await self.add_task(task)

    async def submit_notification_task(
        self,
        user_id: str,
        message: str,
        notification_type: str = "info",
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """提交通知任务"""
        task = Task(
            name=f"send_notification",
            func=self._send_notification,
            args=(user_id, message, notification_type),
            priority=priority,
            timeout=10.0,
        )
        return await self.add_task(task)

    async def submit_webhook_task(
        self,
        url: str,
        payload: dict,
        headers: Optional[dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """提交Webhook调用任务"""
        task = Task(
            name=f"webhook",
            func=self._call_webhook,
            args=(url, payload, headers or {}),
            priority=priority,
            timeout=self.config.api_timeout,
            max_retries=self.config.api_retries,
        )
        return await self.add_task(task)

    async def submit_custom_task(
        self,
        func: Callable,
        *args,
        name: str = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """提交自定义任务"""
        task = Task(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
        )
        return await self.add_task(task)

    async def _send_email(
        self, to_emails: List[str], subject: str, body: str, is_html: bool = False
    ):
        """发送邮件"""
        try:
            # 创建邮件消息
            msg = (
                MIMEMultipart("alternative")
                if is_html
                else MIMEText(body, "plain", "utf-8")
            )
            msg["Subject"] = subject
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(to_emails)

            if is_html:
                text_part = MIMEText(body, "plain", "utf-8")
                html_part = MIMEText(body, "html", "utf-8")
                msg.attach(text_part)
                msg.attach(html_part)

            # 发送邮件
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()

                if self.config.smtp_username:
                    server.login(self.config.smtp_username, self.config.smtp_password)

                server.send_message(msg)

            logger.info(f"📧 邮件发送成功 - 收件人: {', '.join(to_emails)}")

        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {e}")
            raise

    async def _send_notification(
        self, user_id: str, message: str, notification_type: str
    ):
        """发送通知"""
        try:
            notification_data = {
                "user_id": user_id,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.now().isoformat(),
                "id": str(uuid.uuid4()),
            }

            # 发送到消息队列
            if self.rabbitmq_channel:
                await self.rabbitmq_channel.default_exchange.publish(
                    aio_pika.Message(
                        json.dumps(notification_data).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key="perfect21.notifications",
                )

            logger.info(f"🔔 通知发送成功 - 用户: {user_id}, 类型: {notification_type}")

        except Exception as e:
            logger.error(f"❌ 通知发送失败: {e}")
            raise

    async def _call_webhook(self, url: str, payload: dict, headers: dict):
        """调用Webhook"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.api_timeout)
            ) as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Perfect21-AsyncProcessor/1.0",
                        **headers,
                    },
                ) as response:
                    response_text = await response.text()

                    if response.status >= 400:
                        raise aiohttp.ClientError(
                            f"HTTP {response.status}: {response_text}"
                        )

                    logger.info(f"🌐 Webhook调用成功 - URL: {url}, 状态: {response.status}")
                    return response_text

        except Exception as e:
            logger.error(f"❌ Webhook调用失败: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            logger.info(f"🚫 任务已取消: {task.name} (ID: {task_id})")
            return True
        return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_size": self.pending_queue.qsize(),
            "max_queue_size": self.config.max_queue_size,
            "active_workers": self.stats["active_workers"],
            "max_workers": self.config.max_workers,
            "total_tasks": len(self.tasks),
            "stats": self.stats.copy(),
        }

    async def _health_monitor(self):
        """健康监控"""
        while self.running:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # 检查工作进程健康状态
                dead_workers = [w for w in self.workers if w.done()]
                if dead_workers:
                    logger.warning(f"⚠️ 发现{len(dead_workers)}个已停止的工作进程，正在重启...")

                    # 移除已停止的工作进程
                    for worker in dead_workers:
                        self.workers.remove(worker)

                    # 启动新的工作进程
                    for i in range(len(dead_workers)):
                        worker_name = f"worker-{len(self.workers)}"
                        new_worker = asyncio.create_task(self._worker(worker_name))
                        self.workers.append(new_worker)

                # 检查队列健康状态
                queue_size = self.pending_queue.qsize()
                if queue_size > self.config.max_queue_size * 0.8:
                    logger.warning(
                        f"⚠️ 队列接近满载: {queue_size}/{self.config.max_queue_size}"
                    )

            except Exception as e:
                logger.error(f"❌ 健康监控失败: {e}")

    async def _stats_reporter(self):
        """统计报告"""
        while self.running:
            try:
                await asyncio.sleep(self.config.stats_report_interval)

                status = await self.get_queue_status()
                logger.info(
                    f"📊 处理器状态 - "
                    f"队列: {status['queue_size']}/{status['max_queue_size']}, "
                    f"活跃工作进程: {status['active_workers']}/{status['max_workers']}, "
                    f"完成任务: {self.stats['completed_tasks']}, "
                    f"失败任务: {self.stats['failed_tasks']}, "
                    f"平均处理时间: {self.stats['avg_processing_time']:.2f}s"
                )

            except Exception as e:
                logger.error(f"❌ 统计报告失败: {e}")

    async def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        while self.running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)

                cutoff_time = datetime.now() - timedelta(
                    hours=self.config.task_retention_hours
                )
                tasks_to_remove = []

                for task_id, task in self.tasks.items():
                    if (
                        task.completed_at
                        and task.completed_at < cutoff_time
                        and task.status
                        in [
                            TaskStatus.COMPLETED,
                            TaskStatus.FAILED,
                            TaskStatus.CANCELLED,
                        ]
                    ):
                        tasks_to_remove.append(task_id)

                for task_id in tasks_to_remove:
                    del self.tasks[task_id]

                if tasks_to_remove:
                    logger.info(f"🧹 清理已完成任务: {len(tasks_to_remove)}个")

            except Exception as e:
                logger.error(f"❌ 任务清理失败: {e}")

    async def health_check(self) -> bool:
        """健康检查"""
        return (
            self.running
            and len([w for w in self.workers if not w.done()]) > 0
            and self.pending_queue.qsize() < self.config.max_queue_size
        )

    async def shutdown(self):
        """关闭处理器"""
        logger.info("🛑 正在关闭异步处理器...")

        self.running = False

        # 等待队列中的任务完成
        if not self.pending_queue.empty():
            logger.info(f"⏳ 等待队列中的{self.pending_queue.qsize()}个任务完成...")
            await self.pending_queue.join()

        # 取消所有工作进程
        for worker in self.workers:
            worker.cancel()

        # 等待工作进程停止
        await asyncio.gather(*self.workers, return_exceptions=True)

        # 关闭RabbitMQ连接
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()

        logger.info("✅ 异步处理器已关闭")


def async_task(
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: Optional[float] = None,
    max_retries: int = 3,
):
    """异步任务装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, processor: AsyncProcessor = None, **kwargs):
            if processor:
                return await processor.submit_custom_task(
                    func,
                    *args,
                    name=func.__name__,
                    priority=priority,
                    timeout=timeout,
                    max_retries=max_retries,
                    **kwargs,
                )
            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


# 使用示例
@async_task(priority=TaskPriority.HIGH, timeout=60.0)
async def process_user_registration(user_id: str, email: str):
    """处理用户注册（异步任务）"""
    # 发送欢迎邮件
    # 创建用户目录
    # 初始化用户设置
    await asyncio.sleep(1)  # 模拟处理时间
    return f"用户 {user_id} 注册处理完成"


@async_task(priority=TaskPriority.NORMAL)
async def generate_report(report_type: str, params: dict):
    """生成报告（异步任务）"""
    # 查询数据
    # 生成报告
    # 保存文件
    await asyncio.sleep(5)  # 模拟处理时间
    return f"报告 {report_type} 生成完成"
