"""
Performance Optimization: Load Balancer
负载均衡器 - 高性能流量分发与负载均衡系统
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import random
import json
from contextlib import asynccontextmanager
import ssl

logger = logging.getLogger(__name__)

class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    HEALTH_BASED = "health_based"
    RESPONSE_TIME = "response_time"

class ServerStatus(Enum):
    """服务器状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    DRAINING = "draining"

@dataclass
class Server:
    """后端服务器"""
    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    status: ServerStatus = ServerStatus.HEALTHY
    health_check_url: str = "/health"
    health_check_interval: int = 30
    health_check_timeout: int = 5
    consecutive_failures: int = 0
    max_failures: int = 3
    last_health_check: Optional[datetime] = None
    response_times: List[float] = field(default_factory=list)
    avg_response_time: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.url}{self.health_check_url}"

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100

    def update_response_time(self, response_time: float):
        """更新响应时间"""
        self.response_times.append(response_time)
        # 只保留最近100次的响应时间
        if len(self.response_times) > 100:
            self.response_times.pop(0)

        self.avg_response_time = sum(self.response_times) / len(self.response_times)

@dataclass
class LoadBalancerConfig:
    """负载均衡器配置"""
    strategy: LoadBalanceStrategy = LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN
    health_check_enabled: bool = True
    health_check_interval: int = 30
    session_affinity: bool = False
    session_timeout: int = 3600  # 1小时
    max_retries: int = 3
    retry_delay: float = 0.1
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    connection_timeout: float = 10.0
    read_timeout: float = 30.0
    enable_ssl: bool = False
    ssl_verify: bool = True

class CircuitBreaker:
    """熔断器"""

    def __init__(self, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.threshold:
            self.state = "open"

    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        if self.state == "closed":
            return True

        if self.state == "open":
            if (datetime.now() - self.last_failure_time).seconds >= self.timeout:
                self.state = "half_open"
                return True
            return False

        if self.state == "half_open":
            return True

        return False

class LoadBalancer:
    """负载均衡器 - 企业级流量分发系统"""

    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: Dict[str, Server] = {}
        self.current_index = 0  # 用于轮询
        self.sessions: Dict[str, str] = {}  # 会话亲和性
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化负载均衡器"""
        try:
            pass  # Auto-fixed empty block
            # 启动健康检查
            if self.config.health_check_enabled:
                asyncio.create_task(self._health_check_loop())

            # 启动统计报告
            asyncio.create_task(self._stats_reporter())

            # 启动会话清理
            if self.config.session_affinity:
                asyncio.create_task(self._session_cleanup())

            logger.info(f"✅ 负载均衡器初始化成功 - 策略: {self.config.strategy.value}")

        except Exception as e:
            logger.error(f"❌ 负载均衡器初始化失败: {e}")
            raise

    async def add_server(self, server: Server):
        """添加后端服务器"""
        async with self._lock:
            self.servers[server.id] = server

            # 初始化熔断器
            if self.config.circuit_breaker_enabled:
                self.circuit_breakers[server.id] = CircuitBreaker(
                    threshold=self.config.circuit_breaker_threshold,
                    timeout=self.config.circuit_breaker_timeout
                )

            logger.info(f"✅ 添加服务器: {server.id} ({server.url})")

    async def remove_server(self, server_id: str):
        """移除后端服务器"""
        async with self._lock:
            if server_id in self.servers:
                del self.servers[server_id]
                if server_id in self.circuit_breakers:
                    del self.circuit_breakers[server_id]

                logger.info(f"🗑️ 移除服务器: {server_id}")

    async def set_server_weight(self, server_id: str, weight: int):
        """设置服务器权重"""
        if server_id in self.servers:
            self.servers[server_id].weight = weight
            logger.info(f"⚖️ 更新服务器权重: {server_id} -> {weight}")

    async def set_server_status(self, server_id: str, status: ServerStatus):
        """设置服务器状态"""
        if server_id in self.servers:
            self.servers[server_id].status = status
            logger.info(f"🔄 更新服务器状态: {server_id} -> {status.value}")

    async def select_server(self, client_ip: Optional[str] = None,
                          session_id: Optional[str] = None) -> Optional[Server]:
        """选择后端服务器"""
        healthy_servers = [
            server for server in self.servers.values()
            if server.status == ServerStatus.HEALTHY
        ]

        if not healthy_servers:
            logger.error("❌ 没有健康的后端服务器")
            return None

        # 会话亲和性
        if self.config.session_affinity and session_id:
            if session_id in self.sessions:
                server_id = self.sessions[session_id]
                if server_id in self.servers and self.servers[server_id].status == ServerStatus.HEALTHY:
                    return self.servers[server_id]

        # 根据策略选择服务器
        if self.config.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            server = await self._round_robin_select(healthy_servers)
        elif self.config.strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            server = await self._weighted_round_robin_select(healthy_servers)
        elif self.config.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            server = await self._least_connections_select(healthy_servers)
        elif self.config.strategy == LoadBalanceStrategy.WEIGHTED_LEAST_CONNECTIONS:
            server = await self._weighted_least_connections_select(healthy_servers)
        elif self.config.strategy == LoadBalanceStrategy.IP_HASH:
            server = await self._ip_hash_select(healthy_servers, client_ip)
        elif self.config.strategy == LoadBalanceStrategy.RANDOM:
            server = await self._random_select(healthy_servers)
        elif self.config.strategy == LoadBalanceStrategy.HEALTH_BASED:
            server = await self._health_based_select(healthy_servers)
        elif self.config.strategy == LoadBalanceStrategy.RESPONSE_TIME:
            server = await self._response_time_select(healthy_servers)
        else:
            server = await self._round_robin_select(healthy_servers)

        # 更新会话亲和性
        if self.config.session_affinity and session_id and server:
            self.sessions[session_id] = server.id

        return server

    async def _round_robin_select(self, servers: List[Server]) -> Server:
        """轮询选择"""
        self.current_index = (self.current_index + 1) % len(servers)
        return servers[self.current_index]

    async def _weighted_round_robin_select(self, servers: List[Server]) -> Server:
        """加权轮询选择"""
        total_weight = sum(server.weight for server in servers)
        if total_weight == 0:
            return await self._round_robin_select(servers)

        # 生成权重范围
        weight_ranges = []
        current_weight = 0
        for server in servers:
            weight_ranges.append((current_weight, current_weight + server.weight, server))
            current_weight += server.weight

        # 选择服务器
        target = (self.current_index * 7) % total_weight  # 使用素数避免模式
        self.current_index += 1

        for start, end, server in weight_ranges:
            if start <= target < end:
                return server

        return servers[0]  # fallback

    async def _least_connections_select(self, servers: List[Server]) -> Server:
        """最少连接选择"""
        return min(servers, key=lambda s: s.current_connections)

    async def _weighted_least_connections_select(self, servers: List[Server]) -> Server:
        """加权最少连接选择"""
        def connection_ratio(server):
            if server.weight == 0:
                return float('inf')
            return server.current_connections / server.weight

        return min(servers, key=connection_ratio)

    async def _ip_hash_select(self, servers: List[Server], client_ip: Optional[str]) -> Server:
        """IP哈希选择"""
        if not client_ip:
            return await self._round_robin_select(servers)

        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(servers)
        return servers[index]

    async def _random_select(self, servers: List[Server]) -> Server:
        """随机选择"""
        return random.choice(servers)

    async def _health_based_select(self, servers: List[Server]) -> Server:
        """基于健康度选择"""
        def health_score(server):
            # 综合成功率、连接数、响应时间计算健康度
            success_rate = server.success_rate
            connection_load = server.current_connections / server.max_connections
            response_time_score = 1000 / (server.avg_response_time + 1)  # 响应时间越低分数越高

            return success_rate * (1 - connection_load) * response_time_score

        return max(servers, key=health_score)

    async def _response_time_select(self, servers: List[Server]) -> Server:
        """基于响应时间选择"""
        return min(servers, key=lambda s: s.avg_response_time if s.avg_response_time > 0 else float('inf'))

    async def proxy_request(self, method: str, path: str,
                          headers: Optional[Dict[str, str]] = None,
                          data: Any = None,
                          client_ip: Optional[str] = None,
                          session_id: Optional[str] = None) -> Tuple[int, Dict[str, str], Any]:
        """代理请求到后端服务器"""
        start_time = time.time()
        self.stats['total_requests'] += 1

        for attempt in range(self.config.max_retries + 1):
            server = await self.select_server(client_ip, session_id)
            if not server:
                raise Exception("没有可用的后端服务器")

            # 检查熔断器
            if (self.config.circuit_breaker_enabled and
                server.id in self.circuit_breakers and
                not self.circuit_breakers[server.id].can_execute()):
                logger.warning(f"⚡ 熔断器开启，跳过服务器: {server.id}")
                continue

            try:
                pass  # Auto-fixed empty block
                # 增加连接计数
                server.current_connections += 1

                # 发送请求
                url = f"{server.url}{path}"
                timeout = aiohttp.ClientTimeout(
                    connect=self.config.connection_timeout,
                    total=self.config.read_timeout
                )

                ssl_context = None
                if self.config.enable_ssl:
                    ssl_context = ssl.create_default_context()
                    if not self.config.ssl_verify:
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        ssl=ssl_context
                    ) as response:
                        response_data = await response.read()
                        response_headers = dict(response.headers)
                        status_code = response.status

                # 记录成功
                request_time = time.time() - start_time
                server.update_response_time(request_time)
                server.total_requests += 1
                server.successful_requests += 1

                if self.config.circuit_breaker_enabled and server.id in self.circuit_breakers:
                    self.circuit_breakers[server.id].record_success()

                # 更新统计
                self.stats['successful_requests'] += 1
                self.stats['total_response_time'] += request_time
                self.stats['avg_response_time'] = (
                    self.stats['total_response_time'] / self.stats['successful_requests']
                )

                logger.debug(f"✅ 请求成功 - 服务器: {server.id}, 耗时: {request_time:.3f}s")

                return status_code, response_headers, response_data

            except Exception as e:
                pass  # Auto-fixed empty block
                # 记录失败
                server.total_requests += 1
                server.failed_requests += 1

                if self.config.circuit_breaker_enabled and server.id in self.circuit_breakers:
                    self.circuit_breakers[server.id].record_failure()

                logger.error(f"❌ 请求失败 - 服务器: {server.id}, 错误: {e}")

                if attempt == self.config.max_retries:
                    pass  # Auto-fixed empty block
                    # 最后一次重试也失败了
                    self.stats['failed_requests'] += 1
                    raise

                # 等待后重试
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

            finally:
                pass  # Auto-fixed empty block
                # 减少连接计数
                server.current_connections = max(0, server.current_connections - 1)

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # 并发检查所有服务器
                tasks = []
                for server in self.servers.values():
                    if server.status != ServerStatus.MAINTENANCE:
                        task = asyncio.create_task(self._check_server_health(server))
                        tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

            except Exception as e:
                logger.error(f"❌ 健康检查循环失败: {e}")

    async def _check_server_health(self, server: Server):
        """检查单个服务器健康状态"""
        try:
            timeout = aiohttp.ClientTimeout(total=server.health_check_timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(server.health_url) as response:
                    if response.status == 200:
                        pass  # Auto-fixed empty block
                        # 健康检查成功
                        server.consecutive_failures = 0
                        if server.status == ServerStatus.UNHEALTHY:
                            server.status = ServerStatus.HEALTHY
                            logger.info(f"✅ 服务器恢复健康: {server.id}")
                    else:
                        raise aiohttp.ClientError(f"HTTP {response.status}")

        except Exception as e:
            pass  # Auto-fixed empty block
            # 健康检查失败
            server.consecutive_failures += 1

            if server.consecutive_failures >= server.max_failures:
                if server.status == ServerStatus.HEALTHY:
                    server.status = ServerStatus.UNHEALTHY
                    logger.error(f"❌ 服务器标记为不健康: {server.id}, 连续失败: {server.consecutive_failures}")

            logger.debug(f"⚠️ 健康检查失败: {server.id}, 错误: {e}")

        finally:
            server.last_health_check = datetime.now()

    async def _stats_reporter(self):
        """统计报告"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟报告一次

                total_servers = len(self.servers)
                healthy_servers = len([s for s in self.servers.values() if s.status == ServerStatus.HEALTHY])

                success_rate = 0.0
                if self.stats['total_requests'] > 0:
                    success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100

                logger.info(
                    f"📊 负载均衡器统计 - "
                    f"健康服务器: {healthy_servers}/{total_servers}, "
                    f"总请求: {self.stats['total_requests']}, "
                    f"成功率: {success_rate:.2f}%, "
                    f"平均响应时间: {self.stats['avg_response_time']:.3f}s"
                )

                # 输出每个服务器的详细状态
                for server in self.servers.values():
                    logger.debug(
                        f"服务器 {server.id}: "
                        f"状态={server.status.value}, "
                        f"连接={server.current_connections}/{server.max_connections}, "
                        f"成功率={server.success_rate:.2f}%, "
                        f"平均响应时间={server.avg_response_time:.3f}s"
                    )

            except Exception as e:
                logger.error(f"❌ 统计报告失败: {e}")

    async def _session_cleanup(self):
        """会话清理"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次

                # 这里应该实现会话过期清理逻辑
                # 由于这是简化实现，暂时跳过

            except Exception as e:
                logger.error(f"❌ 会话清理失败: {e}")

    async def get_server_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        server_stats = {}

        for server_id, server in self.servers.items():
            server_stats[server_id] = {
                'status': server.status.value,
                'current_connections': server.current_connections,
                'max_connections': server.max_connections,
                'total_requests': server.total_requests,
                'successful_requests': server.successful_requests,
                'failed_requests': server.failed_requests,
                'success_rate': server.success_rate,
                'avg_response_time': server.avg_response_time,
                'weight': server.weight,
                'consecutive_failures': server.consecutive_failures,
                'last_health_check': server.last_health_check.isoformat() if server.last_health_check else None
            }

        return {
            'servers': server_stats,
            'global_stats': self.stats.copy(),
            'config': {
                'strategy': self.config.strategy.value,
                'health_check_enabled': self.config.health_check_enabled,
                'session_affinity': self.config.session_affinity,
                'circuit_breaker_enabled': self.config.circuit_breaker_enabled
            }
        }

    async def health_check(self) -> bool:
        """负载均衡器健康检查"""
        healthy_servers = [s for s in self.servers.values() if s.status == ServerStatus.HEALTHY]
        return len(healthy_servers) > 0

# 使用示例
async def example_usage():
    """负载均衡器使用示例"""
    # 配置负载均衡器
    config = LoadBalancerConfig(
        strategy=LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN,
        health_check_enabled=True,
        circuit_breaker_enabled=True,
        session_affinity=True
    )

    # 创建负载均衡器
    lb = LoadBalancer(config)
    await lb.initialize()

    # 添加后端服务器
    servers = [
        Server(id="server1", host="192.168.1.10", port=8080, weight=3),
        Server(id="server2", host="192.168.1.11", port=8080, weight=2),
        Server(id="server3", host="192.168.1.12", port=8080, weight=1),
    ]

    for server in servers:
        await lb.add_server(server)

    # 代理请求
    try:
        status, headers, data = await lb.proxy_request(
            method="GET",
            path="/api/users",
            client_ip="192.168.1.100",
            session_id="session123"
        )
    # print(f"Response: {status}, Data: {data}")
    except Exception as e:
        pass  # Auto-fixed empty block
    # print(f"Request failed: {e}")

    # 获取统计信息
    stats = await lb.get_server_stats()
    # print(f"Stats: {json.dumps(stats, indent=2)}")