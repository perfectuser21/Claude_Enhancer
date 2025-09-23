"""
Claude Enhancer 邮件服务
企业级邮件发送、模板管理和通知服务
"""

import asyncio
import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, BaseLoader
import redis.asyncio as redis
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from shared.messaging.publisher import MessagePublisher, MessageType
from shared.metrics.metrics import monitor_function


class EmailTemplate(BaseModel):
    """邮件模板"""

    template_id: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []


class EmailMessage(BaseModel):
    """邮件消息"""

    to_email: EmailStr
    to_name: Optional[str] = None
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    reply_to: Optional[str] = None
    priority: int = 5  # 1-10, 10最高


class EmailSendResult(BaseModel):
    """邮件发送结果"""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    delivery_time: Optional[float] = None


class EmailService:
    """邮件服务管理器"""

    def __init__(self):
        self.redis_client = None
        self.message_publisher = None
        self.smtp_config = settings.email_config
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME

        # 初始化模板引擎
        self.template_env = Environment(loader=BaseLoader(), autoescape=True)

        # 初始化Redis
        self._initialize_redis()

        # 邮件模板缓存
        self._templates = {}
        self._load_default_templates()

    def _initialize_redis(self):
        """初始化Redis连接"""
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, health_check_interval=30
        )

    async def set_message_publisher(self, publisher: MessagePublisher):
        """设置消息发布者"""
        self.message_publisher = publisher

    def _load_default_templates(self):
        """加载默认邮件模板"""
        self._templates = {
            "verification": EmailTemplate(
                template_id="verification",
                subject="验证您的邮箱地址 - {{ app_name }}",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>邮箱验证</title>
                    <style>
                        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                        .content { padding: 30px; background: #f8f9fa; }
                        .button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>{{ app_name }}</h1>
                        </div>
                        <div class="content">
                            <h2>您好，{{ first_name }}！</h2>
                            <p>感谢您注册{{ app_name }}。请点击下面的按钮验证您的邮箱地址：</p>
                            <p style="text-align: center; margin: 30px 0;">
                                <a href="{{ verification_url }}" class="button">验证邮箱</a>
                            </p>
                            <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
                            <p style="word-break: break-all; color: #007bff;">{{ verification_url }}</p>
                            <p>此链接将在{{ expiry_hours }}小时后过期。</p>
                        </div>
                        <div class="footer">
                            <p>此邮件由系统自动发送，请勿回复。</p>
                            <p>&copy; {{ current_year }} {{ app_name }}. 保留所有权利。</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content="""
                您好，{{ first_name }}！
                
                感谢您注册{{ app_name }}。请访问以下链接验证您的邮箱地址：
                
                {{ verification_url }}
                
                此链接将在{{ expiry_hours }}小时后过期。
                
                如有疑问，请联系我们的客服团队。
                
                {{ app_name }}团队
                """,
                variables=[
                    "first_name",
                    "app_name",
                    "verification_url",
                    "expiry_hours",
                    "current_year",
                ],
            ),
            "password_reset": EmailTemplate(
                template_id="password_reset",
                subject="重置您的密码 - {{ app_name }}",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>密码重置</title>
                    <style>
                        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                        .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
                        .content { padding: 30px; background: #f8f9fa; }
                        .button { display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 4px; }
                        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
                        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>{{ app_name }}</h1>
                        </div>
                        <div class="content">
                            <h2>您好，{{ first_name }}！</h2>
                            <p>我们收到了重置您密码的请求。如果这是您本人的操作，请点击下面的按钮重置密码：</p>
                            <p style="text-align: center; margin: 30px 0;">
                                <a href="{{ reset_url }}" class="button">重置密码</a>
                            </p>
                            <div class="warning">
                                <strong>安全提醒：</strong>
                                <ul>
                                    <li>此链接将在{{ expiry_hours }}小时后过期</li>
                                    <li>如果您没有请求重置密码，请忽略此邮件</li>
                                    <li>请不要与任何人分享此链接</li>
                                </ul>
                            </div>
                            <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
                            <p style="word-break: break-all; color: #dc3545;">{{ reset_url }}</p>
                        </div>
                        <div class="footer">
                            <p>此邮件由系统自动发送，请勿回复。</p>
                            <p>&copy; {{ current_year }} {{ app_name }}. 保留所有权利。</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                variables=[
                    "first_name",
                    "app_name",
                    "reset_url",
                    "expiry_hours",
                    "current_year",
                ],
            ),
            "security_alert": EmailTemplate(
                template_id="security_alert",
                subject="安全警告 - {{ app_name }}",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>安全警告</title>
                    <style>
                        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                        .header { background: #fd7e14; color: white; padding: 20px; text-align: center; }
                        .content { padding: 30px; background: #f8f9fa; }
                        .alert { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin: 20px 0; }
                        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🔒 {{ app_name }}</h1>
                        </div>
                        <div class="content">
                            <h2>您好，{{ first_name }}！</h2>
                            <div class="alert">
                                <strong>安全警告：</strong> {{ alert_message }}
                            </div>
                            <p><strong>事件详情：</strong></p>
                            <ul>
                                <li>时间：{{ event_time }}</li>
                                <li>IP地址：{{ ip_address }}</li>
                                <li>位置：{{ location }}</li>
                                <li>设备：{{ device_info }}</li>
                            </ul>
                            <p><strong>建议采取的措施：</strong></p>
                            <ul>
                                {% for action in recommended_actions %}
                                <li>{{ action }}</li>
                                {% endfor %}
                            </ul>
                            <p>如果这不是您的操作，请立即联系我们的客服团队。</p>
                        </div>
                        <div class="footer">
                            <p>此邮件由系统自动发送，请勿回复。</p>
                            <p>&copy; {{ current_year }} {{ app_name }}. 保留所有权利。</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                variables=[
                    "first_name",
                    "app_name",
                    "alert_message",
                    "event_time",
                    "ip_address",
                    "location",
                    "device_info",
                    "recommended_actions",
                    "current_year",
                ],
            ),
        }

    @monitor_function("email")
    async def send_verification_email(
        self, email: str, first_name: str, verification_token: str
    ) -> EmailSendResult:
        """发送邮箱验证邮件"""
        try:
            verification_url = f"{settings.FRONTEND_URL}{settings.FRONTEND_VERIFY_EMAIL_PATH}?token={verification_token}"

            variables = {
                "first_name": first_name,
                "app_name": settings.APP_NAME,
                "verification_url": verification_url,
                "expiry_hours": settings.EMAIL_VERIFICATION_TTL // 3600,
                "current_year": datetime.now().year,
            }

            return await self._send_template_email(
                template_id="verification",
                to_email=email,
                to_name=first_name,
                variables=variables,
                priority=8,
            )

        except Exception as e:
            return EmailSendResult(success=False, error=f"发送验证邮件失败: {str(e)}")

    @monitor_function("email")
    async def send_password_reset_email(
        self, email: str, first_name: str, reset_token: str
    ) -> EmailSendResult:
        """发送密码重置邮件"""
        try:
            reset_url = f"{settings.FRONTEND_URL}{settings.FRONTEND_RESET_PASSWORD_PATH}?token={reset_token}"

            variables = {
                "first_name": first_name,
                "app_name": settings.APP_NAME,
                "reset_url": reset_url,
                "expiry_hours": settings.EMAIL_RESET_PASSWORD_TTL // 3600,
                "current_year": datetime.now().year,
            }

            return await self._send_template_email(
                template_id="password_reset",
                to_email=email,
                to_name=first_name,
                variables=variables,
                priority=9,
            )

        except Exception as e:
            return EmailSendResult(success=False, error=f"发送密码重置邮件失败: {str(e)}")

    @monitor_function("email")
    async def send_security_alert_email(
        self, email: str, first_name: str, alert_type: str, details: Dict[str, Any]
    ) -> EmailSendResult:
        """发送安全警告邮件"""
        try:
            alert_messages = {
                "password_breach": "您的密码存在于已知泄露数据库中",
                "suspicious_login": "检测到可疑的登录活动",
                "account_locked": "您的账户已被锁定",
                "mfa_disabled": "多因子认证已被禁用",
                "password_changed": "您的密码已被修改",
            }

            recommended_actions = {
                "password_breach": ["立即更改密码", "启用多因子认证", "检查其他账户是否使用相同密码"],
                "suspicious_login": ["确认是否为本人操作", "更改密码", "启用多因子认证"],
                "account_locked": ["等待解锁时间到期", "联系客服", "确认登录环境安全"],
                "mfa_disabled": ["重新启用多因子认证", "检查账户安全设置", "更改密码"],
                "password_changed": ["确认是否为本人操作", "检查账户活动记录", "联系客服（如非本人操作）"],
            }

            variables = {
                "first_name": first_name,
                "app_name": settings.APP_NAME,
                "alert_message": alert_messages.get(alert_type, "检测到异常安全活动"),
                "event_time": details.get("timestamp", datetime.now().isoformat()),
                "ip_address": details.get("ip_address", "Unknown"),
                "location": details.get("location", "Unknown"),
                "device_info": details.get("device_info", "Unknown"),
                "recommended_actions": recommended_actions.get(alert_type, ["联系客服团队"]),
                "current_year": datetime.now().year,
            }

            return await self._send_template_email(
                template_id="security_alert",
                to_email=email,
                to_name=first_name,
                variables=variables,
                priority=10,
            )

        except Exception as e:
            return EmailSendResult(success=False, error=f"发送安全警告邮件失败: {str(e)}")

    @monitor_function("email")
    async def send_custom_email(self, message: EmailMessage) -> EmailSendResult:
        """发送自定义邮件"""
        try:
            start_time = datetime.now()

            # 检查发送频率限制
            rate_limit_check = await self._check_rate_limit(message.to_email)
            if not rate_limit_check["allowed"]:
                return EmailSendResult(
                    success=False, error=f"发送频率超限: {rate_limit_check['message']}"
                )

            # 发送邮件
            result = await self._send_smtp_email(message)

            # 计算发送时间
            delivery_time = (datetime.now() - start_time).total_seconds()
            result.delivery_time = delivery_time

            # 记录发送结果
            await self._log_email_send(message, result)

            return result

        except Exception as e:
            return EmailSendResult(success=False, error=f"发送邮件失败: {str(e)}")

    async def _send_template_email(
        self,
        template_id: str,
        to_email: str,
        to_name: str,
        variables: Dict[str, Any],
        priority: int = 5,
    ) -> EmailSendResult:
        """使用模板发送邮件"""
        if template_id not in self._templates:
            return EmailSendResult(success=False, error=f"模板不存在: {template_id}")

        template = self._templates[template_id]

        # 渲染模板
        subject = self.template_env.from_string(template.subject).render(**variables)
        html_content = self.template_env.from_string(template.html_content).render(
            **variables
        )
        text_content = None

        if template.text_content:
            text_content = self.template_env.from_string(template.text_content).render(
                **variables
            )

        # 创建邮件消息
        message = EmailMessage(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            priority=priority,
        )

        return await self.send_custom_email(message)

    async def _send_smtp_email(self, message: EmailMessage) -> EmailSendResult:
        """通过SMTP发送邮件"""
        if not self.smtp_config["enabled"]:
            return EmailSendResult(success=False, error="邮件服务未启用")

        try:
            # 创建邮件消息
            msg = MimeMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = f"{message.to_name or ''} <{message.to_email}>"

            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # 添加邮件内容
            if message.text_content:
                text_part = MimeText(message.text_content, "plain", "utf-8")
                msg.attach(text_part)

            if message.html_content:
                html_part = MimeText(message.html_content, "html", "utf-8")
                msg.attach(html_part)

            # 发送邮件
            await self._smtp_send(msg, message.to_email)

            return EmailSendResult(success=True, message_id=msg["Message-ID"])

        except Exception as e:
            return EmailSendResult(success=False, error=str(e))

    async def _smtp_send(self, message: MimeMultipart, to_email: str):
        """SMTP发送实现"""

        def send_sync():
            # 创建SMTP连接
            if self.smtp_config["smtp_tls"]:
                context = ssl.create_default_context()
                server = smtplib.SMTP(
                    self.smtp_config["smtp_host"], self.smtp_config["smtp_port"]
                )
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(
                    self.smtp_config["smtp_host"], self.smtp_config["smtp_port"]
                )

            # 登录
            if self.smtp_config["smtp_username"] and self.smtp_config["smtp_password"]:
                server.login(
                    self.smtp_config["smtp_username"], self.smtp_config["smtp_password"]
                )

            # 发送邮件
            server.send_message(message, to_addrs=[to_email])
            server.quit()

        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_sync)

    async def _check_rate_limit(self, email: str) -> Dict[str, Any]:
        """检查发送频率限制"""
        try:
            # 每小时限制
            hourly_key = (
                f"email_rate_limit:hourly:{email}:{datetime.now().strftime('%Y%m%d%H')}"
            )
            hourly_count = await self.redis_client.incr(hourly_key)
            await self.redis_client.expire(hourly_key, 3600)

            if hourly_count > 10:  # 每小时最多10封
                return {"allowed": False, "message": "每小时发送限制已达上限"}

            # 每日限制
            daily_key = (
                f"email_rate_limit:daily:{email}:{datetime.now().strftime('%Y%m%d')}"
            )
            daily_count = await self.redis_client.incr(daily_key)
            await self.redis_client.expire(daily_key, 86400)

            if daily_count > 50:  # 每日最多50封
                return {"allowed": False, "message": "每日发送限制已达上限"}

            return {
                "allowed": True,
                "hourly_remaining": 10 - hourly_count,
                "daily_remaining": 50 - daily_count,
            }

        except Exception:
            # 如果检查失败，允许发送
            return {"allowed": True}

    async def _log_email_send(self, message: EmailMessage, result: EmailSendResult):
        """记录邮件发送日志"""
        try:
            log_data = {
                "to_email": message.to_email,
                "subject": message.subject,
                "success": result.success,
                "error": result.error,
                "delivery_time": result.delivery_time,
                "timestamp": datetime.now().isoformat(),
                "priority": message.priority,
            }

            # 存储到Redis（保留7天）
            log_key = f"email_log:{datetime.now().strftime('%Y%m%d')}:{message.to_email}:{int(datetime.now().timestamp())}"
            await self.redis_client.setex(log_key, 604800, str(log_data))

            # 发布邮件发送事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.USER_LOGIN,  # 使用合适的消息类型
                    data={"event_type": "email_sent", "email_data": log_data},
                )

        except Exception:
            # 日志记录失败不应影响邮件发送
            pass

    @monitor_function("email")
    async def get_email_stats(
        self, email: str = None, date_range: int = 7
    ) -> Dict[str, Any]:
        """获取邮件发送统计"""
        try:
            stats = {
                "total_sent": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_delivery_time": 0.0,
            }

            # 构建查询模式
            if email:
                pattern = f"email_log:*:{email}:*"
            else:
                pattern = "email_log:*"

            # 获取指定日期范围的日志
            log_keys = await self.redis_client.keys(pattern)

            delivery_times = []
            for key in log_keys:
                # 检查日期范围
                date_str = key.split(":")[1]
                log_date = datetime.strptime(date_str, "%Y%m%d")
                if (datetime.now() - log_date).days > date_range:
                    continue

                log_data = await self.redis_client.get(key)
                if log_data:
                    log_info = eval(log_data)  # 在生产环境中应使用JSON
                    stats["total_sent"] += 1

                    if log_info.get("success"):
                        stats["successful"] += 1
                        if log_info.get("delivery_time"):
                            delivery_times.append(log_info["delivery_time"])
                    else:
                        stats["failed"] += 1

            # 计算统计数据
            if stats["total_sent"] > 0:
                stats["success_rate"] = stats["successful"] / stats["total_sent"]

            if delivery_times:
                stats["avg_delivery_time"] = sum(delivery_times) / len(delivery_times)

            return stats

        except Exception as e:
            raise RuntimeError(f"获取邮件统计失败: {e}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查Redis连接
            await self.redis_client.ping()

            # 检查SMTP配置
            if not self.smtp_config["enabled"]:
                return False

            return True

        except Exception:
            return False

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局邮件服务实例
email_service = EmailService()


# 提供给其他模块使用的函数
async def get_email_service() -> EmailService:
    """获取邮件服务实例"""
    return email_service
