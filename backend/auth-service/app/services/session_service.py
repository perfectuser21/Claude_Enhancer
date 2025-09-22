"""
Perfect21 会话管理服务
企业级会话管理、追踪和安全控制
"""

import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
import json
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from shared.messaging.publisher import MessagePublisher, MessageType
from shared.metrics.metrics import monitor_function

class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPICIOUS = "suspicious"

class SessionType(Enum):
    """会话类型"""
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    DESKTOP = "desktop"

@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    user_id: str
    device_fingerprint: str
    ip_address: str
    user_agent: str
    session_type: SessionType
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    status: SessionStatus
    location: Optional[Dict[str, Any]] = None
    security_flags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionValidationResult(BaseModel):
    """会话验证结果"""
    is_valid: bool
    session_info: Optional[SessionInfo] = None
    warnings: List[str] = []
    security_alerts: List[str] = []
    should_refresh: bool = False
    should_terminate: bool = False

class SessionActivity(BaseModel):
    """会话活动记录"""
    session_id: str
    activity_type: str
    timestamp: datetime
    ip_address: str
    endpoint: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionService:
    """会话管理服务"""

    def __init__(self):
        self.redis_client = None
        self.message_publisher = None
        self.session_ttl = settings.SESSION_TTL
        self.max_sessions_per_user = settings.SESSION_MAX_PER_USER
        self.cleanup_interval = settings.SESSION_CLEANUP_INTERVAL
        
        # 初始化Redis
        self._initialize_redis()
        
        # 启动清理任务
        self._cleanup_task = None

    def _initialize_redis(self):
        """初始化Redis连接"""
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            health_check_interval=30
        )

    async def set_message_publisher(self, publisher: MessagePublisher):
        """设置消息发布者"""
        self.message_publisher = publisher
        
        # 启动清理任务
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    @monitor_function("session")
    async def create_session(self, user_id: str, device_info: Dict[str, Any], 
                           ip_address: str, session_type: SessionType = SessionType.WEB) -> SessionInfo:
        """创建新会话"""
        try:
            # 生成会话ID
            session_id = f"session_{secrets.token_urlsafe(32)}"
            
            # 生成设备指纹
            device_fingerprint = self._generate_device_fingerprint(device_info)
            
            # 检查并清理过期会话
            await self._cleanup_user_sessions(user_id)
            
            # 检查会话数量限制
            user_sessions = await self._get_user_active_sessions(user_id)
            if len(user_sessions) >= self.max_sessions_per_user:
                # 终止最旧的会话
                oldest_session = min(user_sessions, key=lambda s: s.last_activity_at)
                await self.terminate_session(oldest_session.session_id, "session_limit_exceeded")
            
            # 创建会话信息
            current_time = datetime.utcnow()
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                user_agent=device_info.get('user_agent', ''),
                session_type=session_type,
                created_at=current_time,
                last_activity_at=current_time,
                expires_at=current_time + timedelta(seconds=self.session_ttl),
                status=SessionStatus.ACTIVE,
                location=await self._get_location_info(ip_address),
                security_flags=[],
                metadata=device_info
            )
            
            # 存储会话
            await self._store_session(session_info)
            
            # 记录会话创建事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.USER_LOGIN,
                    data={
                        "event_type": "session_created",
                        "session_id": session_id,
                        "user_id": user_id,
                        "ip_address": ip_address,
                        "device_fingerprint": device_fingerprint,
                        "session_type": session_type.value,
                        "timestamp": current_time.isoformat()
                    },
                    user_id=user_id
                )
            
            return session_info
            
        except Exception as e:
            raise RuntimeError(f"创建会话失败: {e}")

    @monitor_function("session")
    async def validate_session(self, session_id: str, current_ip: str = None, 
                             user_agent: str = None) -> SessionValidationResult:
        """验证会话"""
        try:
            # 获取会话信息
            session_info = await self._get_session(session_id)
            
            if not session_info:
                return SessionValidationResult(
                    is_valid=False,
                    warnings=["会话不存在"]
                )
            
            warnings = []
            security_alerts = []
            should_refresh = False
            should_terminate = False
            
            # 检查会话状态
            if session_info.status != SessionStatus.ACTIVE:
                return SessionValidationResult(
                    is_valid=False,
                    session_info=session_info,
                    warnings=[f"会话状态异常: {session_info.status.value}"]
                )
            
            # 检查过期时间
            current_time = datetime.utcnow()
            if current_time > session_info.expires_at:
                await self.terminate_session(session_id, "expired")
                return SessionValidationResult(
                    is_valid=False,
                    session_info=session_info,
                    warnings=["会话已过期"]
                )
            
            # 安全检查
            # 1. IP地址变化检查
            if current_ip and current_ip != session_info.ip_address:
                security_alerts.append(f"IP地址变化: {session_info.ip_address} -> {current_ip}")
                
                # 检查IP变化是否可疑
                if await self._is_suspicious_ip_change(session_info.ip_address, current_ip):
                    should_terminate = True
                    security_alerts.append("可疑的IP地址变化")
            
            # 2. 设备指纹检查
            if user_agent:
                current_fingerprint = self._generate_device_fingerprint({'user_agent': user_agent})
                if current_fingerprint != session_info.device_fingerprint:
                    security_alerts.append("设备指纹不匹配")
                    should_terminate = True
            
            # 3. 会话劫持检查
            hijack_risk = await self._check_session_hijacking(session_info, current_ip, user_agent)
            if hijack_risk['is_suspicious']:
                security_alerts.extend(hijack_risk['indicators'])
                if hijack_risk['severity'] == 'high':
                    should_terminate = True
            
            # 4. 活动时间检查
            inactive_duration = current_time - session_info.last_activity_at
            if inactive_duration.total_seconds() > self.session_ttl / 2:
                should_refresh = True
                warnings.append("会话即将过期，建议刷新")
            
            # 如果需要终止会话
            if should_terminate:
                await self.terminate_session(session_id, "security_violation")
                
                # 发送安全警报
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.SECURITY_ALERT,
                        data={
                            "user_id": session_info.user_id,
                            "alert_type": "session_security_violation",
                            "severity": "high",
                            "description": "会话安全违规，已自动终止",
                            "session_id": session_id,
                            "security_alerts": security_alerts,
                            "current_ip": current_ip
                        },
                        user_id=session_info.user_id,
                        priority=8
                    )
                
                return SessionValidationResult(
                    is_valid=False,
                    session_info=session_info,
                    security_alerts=security_alerts,
                    should_terminate=True
                )
            
            # 更新会话活动时间
            if current_ip:
                await self._update_session_activity(session_id, current_ip, user_agent)
            
            return SessionValidationResult(
                is_valid=True,
                session_info=session_info,
                warnings=warnings,
                security_alerts=security_alerts,
                should_refresh=should_refresh
            )
            
        except Exception as e:
            raise RuntimeError(f"会话验证失败: {e}")

    @monitor_function("session")
    async def refresh_session(self, session_id: str) -> SessionInfo:
        """刷新会话"""
        try:
            session_info = await self._get_session(session_id)
            if not session_info:
                raise ValueError("会话不存在")
            
            if session_info.status != SessionStatus.ACTIVE:
                raise ValueError("会话状态异常，无法刷新")
            
            # 延长过期时间
            current_time = datetime.utcnow()
            session_info.expires_at = current_time + timedelta(seconds=self.session_ttl)
            session_info.last_activity_at = current_time
            
            # 更新存储
            await self._store_session(session_info)
            
            # 记录刷新事件
            await self._record_session_activity(
                session_id=session_id,
                activity_type="session_refreshed",
                ip_address=session_info.ip_address
            )
            
            return session_info
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"会话刷新失败: {e}")

    @monitor_function("session")
    async def terminate_session(self, session_id: str, reason: str = "user_logout"):
        """终止会话"""
        try:
            session_info = await self._get_session(session_id)
            if not session_info:
                return  # 会话不存在，认为已终止
            
            # 更新会话状态
            session_info.status = SessionStatus.TERMINATED
            await self._store_session(session_info)
            
            # 从活跃会话列表中移除
            await self._remove_from_active_sessions(session_info.user_id, session_id)
            
            # 记录终止事件
            await self._record_session_activity(
                session_id=session_id,
                activity_type="session_terminated",
                ip_address=session_info.ip_address,
                metadata={"reason": reason}
            )
            
            # 发布会话终止事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.USER_LOGIN,
                    data={
                        "event_type": "session_terminated",
                        "session_id": session_id,
                        "user_id": session_info.user_id,
                        "reason": reason,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    user_id=session_info.user_id
                )
            
        except Exception as e:
            raise RuntimeError(f"终止会话失败: {e}")

    @monitor_function("session")
    async def terminate_all_user_sessions(self, user_id: str, reason: str = "security_measure",
                                        exclude_session: str = None) -> int:
        """终止用户所有会话"""
        try:
            user_sessions = await self._get_user_active_sessions(user_id)
            terminated_count = 0
            
            for session_info in user_sessions:
                if exclude_session and session_info.session_id == exclude_session:
                    continue
                
                await self.terminate_session(session_info.session_id, reason)
                terminated_count += 1
            
            # 发布批量终止事件
            if self.message_publisher and terminated_count > 0:
                await self.message_publisher.publish_message(
                    message_type=MessageType.SECURITY_ALERT,
                    data={
                        "user_id": user_id,
                        "alert_type": "bulk_session_termination",
                        "severity": "medium",
                        "description": f"用户所有会话已终止: {reason}",
                        "terminated_count": terminated_count,
                        "excluded_session": exclude_session
                    },
                    user_id=user_id
                )
            
            return terminated_count
            
        except Exception as e:
            raise RuntimeError(f"批量终止会话失败: {e}")

    @monitor_function("session")
    async def get_user_sessions(self, user_id: str, include_terminated: bool = False) -> List[SessionInfo]:
        """获取用户会话列表"""
        try:
            if include_terminated:
                # 获取所有会话（包括已终止的）
                session_keys = await self.redis_client.keys(f"session_history:{user_id}:*")
                sessions = []
                
                for key in session_keys:
                    session_data = await self.redis_client.get(key)
                    if session_data:
                        session_dict = json.loads(session_data)
                        sessions.append(self._dict_to_session_info(session_dict))
                
                return sorted(sessions, key=lambda s: s.last_activity_at, reverse=True)
            else:
                # 只获取活跃会话
                return await self._get_user_active_sessions(user_id)
                
        except Exception as e:
            raise RuntimeError(f"获取用户会话失败: {e}")

    @monitor_function("session")
    async def record_activity(self, session_id: str, activity_type: str, 
                            ip_address: str, endpoint: str = None, 
                            metadata: Dict[str, Any] = None):
        """记录会话活动"""
        try:
            # 验证会话存在且有效
            session_info = await self._get_session(session_id)
            if not session_info or session_info.status != SessionStatus.ACTIVE:
                return
            
            # 更新最后活动时间
            await self._update_session_activity(session_id, ip_address)
            
            # 记录具体活动
            await self._record_session_activity(
                session_id=session_id,
                activity_type=activity_type,
                ip_address=ip_address,
                endpoint=endpoint,
                metadata=metadata
            )
            
        except Exception as e:
            # 活动记录失败不应影响主要业务流程
            pass

    def _generate_device_fingerprint(self, device_info: Dict[str, Any]) -> str:
        """生成设备指纹"""
        import hashlib
        
        fingerprint_data = {
            "user_agent": device_info.get("user_agent", ""),
            "screen_resolution": device_info.get("screen_resolution", ""),
            "timezone": device_info.get("timezone", ""),
            "language": device_info.get("language", ""),
            "platform": device_info.get("platform", "")
        }
        
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    async def _store_session(self, session_info: SessionInfo):
        """存储会话信息"""
        # 转换为字典
        session_dict = asdict(session_info)
        session_dict['created_at'] = session_info.created_at.isoformat()
        session_dict['last_activity_at'] = session_info.last_activity_at.isoformat()
        session_dict['expires_at'] = session_info.expires_at.isoformat()
        session_dict['status'] = session_info.status.value
        session_dict['session_type'] = session_info.session_type.value
        
        # 存储到Redis
        session_key = f"session:{session_info.session_id}"
        await self.redis_client.setex(
            session_key,
            self.session_ttl + 3600,  # 额外1小时用于清理
            json.dumps(session_dict)
        )
        
        # 添加到用户活跃会话集合
        if session_info.status == SessionStatus.ACTIVE:
            user_sessions_key = f"user_sessions:{session_info.user_id}"
            await self.redis_client.sadd(user_sessions_key, session_info.session_id)
            await self.redis_client.expire(user_sessions_key, self.session_ttl + 3600)
        
        # 存储会话历史（用于审计）
        history_key = f"session_history:{session_info.user_id}:{session_info.session_id}"
        await self.redis_client.setex(
            history_key,
            86400 * 30,  # 保留30天
            json.dumps(session_dict)
        )

    async def _get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        session_key = f"session:{session_id}"
        session_data = await self.redis_client.get(session_key)
        
        if not session_data:
            return None
        
        try:
            session_dict = json.loads(session_data)
            return self._dict_to_session_info(session_dict)
        except (json.JSONDecodeError, KeyError):
            return None

    def _dict_to_session_info(self, session_dict: Dict[str, Any]) -> SessionInfo:
        """将字典转换为SessionInfo对象"""
        return SessionInfo(
            session_id=session_dict['session_id'],
            user_id=session_dict['user_id'],
            device_fingerprint=session_dict['device_fingerprint'],
            ip_address=session_dict['ip_address'],
            user_agent=session_dict['user_agent'],
            session_type=SessionType(session_dict['session_type']),
            created_at=datetime.fromisoformat(session_dict['created_at']),
            last_activity_at=datetime.fromisoformat(session_dict['last_activity_at']),
            expires_at=datetime.fromisoformat(session_dict['expires_at']),
            status=SessionStatus(session_dict['status']),
            location=session_dict.get('location'),
            security_flags=session_dict.get('security_flags', []),
            metadata=session_dict.get('metadata', {})
        )

    async def _get_user_active_sessions(self, user_id: str) -> List[SessionInfo]:
        """获取用户活跃会话"""
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self.redis_client.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session_info = await self._get_session(session_id)
            if session_info and session_info.status == SessionStatus.ACTIVE:
                sessions.append(session_info)
        
        return sorted(sessions, key=lambda s: s.last_activity_at, reverse=True)

    async def _update_session_activity(self, session_id: str, ip_address: str, 
                                     user_agent: str = None):
        """更新会话活动时间"""
        session_info = await self._get_session(session_id)
        if session_info:
            session_info.last_activity_at = datetime.utcnow()
            if ip_address:
                session_info.ip_address = ip_address
            if user_agent:
                session_info.user_agent = user_agent
            
            await self._store_session(session_info)

    async def _remove_from_active_sessions(self, user_id: str, session_id: str):
        """从活跃会话集合中移除"""
        user_sessions_key = f"user_sessions:{user_id}"
        await self.redis_client.srem(user_sessions_key, session_id)

    async def _record_session_activity(self, session_id: str, activity_type: str, 
                                     ip_address: str, endpoint: str = None, 
                                     user_agent: str = None, request_id: str = None,
                                     metadata: Dict[str, Any] = None):
        """记录会话活动"""
        activity = SessionActivity(
            session_id=session_id,
            activity_type=activity_type,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            endpoint=endpoint,
            user_agent=user_agent,
            request_id=request_id,
            metadata=metadata or {}
        )
        
        # 存储活动记录（保留7天）
        activity_key = f"session_activity:{session_id}:{int(activity.timestamp.timestamp())}"
        await self.redis_client.setex(
            activity_key,
            86400 * 7,  # 7天
            activity.json()
        )

    async def _cleanup_user_sessions(self, user_id: str):
        """清理用户过期会话"""
        user_sessions = await self._get_user_active_sessions(user_id)
        current_time = datetime.utcnow()
        
        for session_info in user_sessions:
            if current_time > session_info.expires_at:
                await self.terminate_session(session_info.session_id, "expired")

    async def _get_location_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """获取IP地址位置信息（简化实现）"""
        # 这里应该集成IP地理位置服务
        # 为了演示，返回简化的位置信息
        if ip_address.startswith('192.168.') or ip_address.startswith('10.') or ip_address.startswith('127.'):
            return {"country": "CN", "city": "Local", "is_local": True}
        
        return {"country": "Unknown", "city": "Unknown", "is_local": False}

    async def _is_suspicious_ip_change(self, old_ip: str, new_ip: str) -> bool:
        """检查IP变化是否可疑"""
        # 简化的可疑IP检查逻辑
        old_location = await self._get_location_info(old_ip)
        new_location = await self._get_location_info(new_ip)
        
        # 如果从本地IP变为远程IP，或国家发生变化，认为可疑
        if (old_location.get('is_local') and not new_location.get('is_local')) or \
           (old_location.get('country') != new_location.get('country')):
            return True
        
        return False

    async def _check_session_hijacking(self, session_info: SessionInfo, 
                                     current_ip: str, user_agent: str) -> Dict[str, Any]:
        """检查会话劫持风险"""
        indicators = []
        severity = 'low'
        
        # 检查多个风险指标
        risk_score = 0
        
        # 1. IP地址变化
        if current_ip and current_ip != session_info.ip_address:
            indicators.append('IP地址变化')
            risk_score += 30
        
        # 2. User-Agent变化
        if user_agent and user_agent != session_info.user_agent:
            indicators.append('User-Agent变化')
            risk_score += 20
        
        # 3. 异常活动模式（简化检查）
        activity_pattern = await self._analyze_activity_pattern(session_info.session_id)
        if activity_pattern['is_unusual']:
            indicators.append('异常活动模式')
            risk_score += 25
        
        # 4. 地理位置跳跃
        if current_ip:
            location_jump = await self._check_location_jump(
                session_info.ip_address, 
                current_ip, 
                session_info.last_activity_at
            )
            if location_jump['is_impossible']:
                indicators.append('不可能的地理位置跳跃')
                risk_score += 50
        
        # 确定严重程度
        if risk_score >= 70:
            severity = 'high'
        elif risk_score >= 40:
            severity = 'medium'
        
        return {
            'is_suspicious': risk_score >= 40,
            'severity': severity,
            'risk_score': risk_score,
            'indicators': indicators
        }

    async def _analyze_activity_pattern(self, session_id: str) -> Dict[str, Any]:
        """分析会话活动模式"""
        # 简化的活动模式分析
        activity_keys = await self.redis_client.keys(f"session_activity:{session_id}:*")
        
        if len(activity_keys) < 3:
            return {'is_unusual': False}
        
        # 检查活动频率
        recent_activities = len([k for k in activity_keys if 
                               int(k.split(':')[-1]) > (datetime.utcnow().timestamp() - 300)])
        
        # 如果5分钟内有超过20个活动，认为异常
        return {'is_unusual': recent_activities > 20}

    async def _check_location_jump(self, old_ip: str, new_ip: str, 
                                 last_activity: datetime) -> Dict[str, Any]:
        """检查地理位置跳跃是否合理"""
        # 简化的地理位置跳跃检查
        old_location = await self._get_location_info(old_ip)
        new_location = await self._get_location_info(new_ip)
        
        # 如果都是本地IP，不算跳跃
        if old_location.get('is_local') and new_location.get('is_local'):
            return {'is_impossible': False}
        
        # 简化检查：如果国家不同且时间间隔小于1小时，认为不可能
        time_diff = datetime.utcnow() - last_activity
        if (old_location.get('country') != new_location.get('country') and 
            time_diff.total_seconds() < 3600):
            return {'is_impossible': True}
        
        return {'is_impossible': False}

    async def _periodic_cleanup(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # 获取所有会话键
                session_keys = await self.redis_client.keys("session:*")
                current_time = datetime.utcnow()
                
                cleanup_count = 0
                for key in session_keys:
                    session_data = await self.redis_client.get(key)
                    if session_data:
                        try:
                            session_dict = json.loads(session_data)
                            expires_at = datetime.fromisoformat(session_dict['expires_at'])
                            
                            if current_time > expires_at:
                                session_id = session_dict['session_id']
                                await self.terminate_session(session_id, "expired")
                                cleanup_count += 1
                        except (json.JSONDecodeError, KeyError, ValueError):
                            # 删除损坏的会话数据
                            await self.redis_client.delete(key)
                            cleanup_count += 1
                
                if cleanup_count > 0:
    # print(f"清理了 {cleanup_count} 个过期会话")
                    
            except Exception as e:
    # print(f"会话清理任务错误: {e}")
                await asyncio.sleep(60)  # 错误时等待1分钟后重试

    async def close(self):
        """关闭服务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()

# 全局会话服务实例
session_service = SessionService()

# 提供给其他模块使用的函数
async def get_session_service() -> SessionService:
    """获取会话服务实例"""
    return session_service