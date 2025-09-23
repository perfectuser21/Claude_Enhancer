#!/usr/bin/env python3
"""
Mock Performance Test Server
模拟性能测试服务器 - 提供各种端点用于性能测试
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, Any, List
from aiohttp import web, ClientSession
import aiohttp_cors
import weakref
import psutil
from pathlib import Path

# 模拟数据
MOCK_USERS = []
MOCK_CACHE = {}
REQUEST_STATS = {
    'total_requests': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'database_queries': 0,
    'errors': 0
}

class MockDatabase:
    """模拟数据库"""

    def __init__(self):
        self.query_delay = 0.01  # 10ms基础查询延迟
        self.users = self._generate_mock_users(10000)

    def _generate_mock_users(self, count: int) -> List[Dict]:
        """生成模拟用户数据"""
        users = []
        for i in range(count):
            users.append({
                'id': i + 1,
                'name': f'User{i+1}',
                'email': f'user{i+1}@example.com',
                'created_at': '2024-01-01T00:00:00Z',
                'active': random.choice([True, False]),
                'score': random.randint(0, 1000)
            })
        return users

    async def get_user(self, user_id: int) -> Dict:
        """获取用户"""
        await asyncio.sleep(self.query_delay)
        REQUEST_STATS['database_queries'] += 1

        for user in self.users:
            if user['id'] == user_id:
                return user
        return None

    async def search_users(self, limit: int = 100, active_only: bool = False) -> List[Dict]:
        """搜索用户"""
        # 模拟复杂查询延迟
        await asyncio.sleep(self.query_delay * (limit / 10))
        REQUEST_STATS['database_queries'] += 1

        users = self.users[:limit]
        if active_only:
            users = [u for u in users if u['active']]

        return users

    async def get_analytics(self) -> Dict:
        """获取分析数据"""
        # 模拟复杂分析查询
        await asyncio.sleep(0.1)  # 100ms
        REQUEST_STATS['database_queries'] += 1

        return {
            'total_users': len(self.users),
            'active_users': len([u for u in self.users if u['active']]),
            'avg_score': sum(u['score'] for u in self.users) / len(self.users),
            'generated_at': datetime.now().isoformat()
        }

class MockCache:
    """模拟缓存"""

    def __init__(self):
        self.data = {}
        self.ttl = {}

    async def get(self, key: str) -> Any:
        """获取缓存"""
        await asyncio.sleep(0.001)  # 1ms延迟

        if key in self.data:
            # 检查TTL
            if key in self.ttl and time.time() > self.ttl[key]:
                del self.data[key]
                del self.ttl[key]
                REQUEST_STATS['cache_misses'] += 1
                return None

            REQUEST_STATS['cache_hits'] += 1
            return self.data[key]

        REQUEST_STATS['cache_misses'] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        await asyncio.sleep(0.001)  # 1ms延迟
        self.data[key] = value
        if ttl > 0:
            self.ttl[key] = time.time() + ttl

# 全局实例
db = MockDatabase()
cache = MockCache()

async def health_handler(request):
    """健康检查端点"""
    REQUEST_STATS['total_requests'] += 1

    return web.json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - request.app['start_time']
    })

async def status_handler(request):
    """状态端点"""
    REQUEST_STATS['total_requests'] += 1

    # 模拟少量处理延迟
    await asyncio.sleep(random.uniform(0.005, 0.015))

    return web.json_response({
        'service': 'perfect21-mock',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

async def metrics_handler(request):
    """指标端点"""
    REQUEST_STATS['total_requests'] += 1

    # 获取系统指标
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()

    metrics = {
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / 1024 / 1024
        },
        'application': REQUEST_STATS.copy(),
        'cache': {
            'hit_rate': (REQUEST_STATS['cache_hits'] / max(REQUEST_STATS['cache_hits'] + REQUEST_STATS['cache_misses'], 1)) * 100,
            'size': len(cache.data)
        },
        'timestamp': datetime.now().isoformat()
    }

    return web.json_response(metrics)

async def users_handler(request):
    """用户列表端点"""
    REQUEST_STATS['total_requests'] += 1

    # 检查缓存
    cache_key = f"users_list_{request.query.get('limit', 100)}_{request.query.get('active_only', False)}"
    cached_data = await cache.get(cache_key)

    if cached_data:
        return web.json_response(cached_data)

    # 从数据库获取
    limit = int(request.query.get('limit', 100))
    active_only = request.query.get('active_only', 'false').lower() == 'true'

    try:
        users = await db.search_users(limit=limit, active_only=active_only)

        response_data = {
            'users': users,
            'total': len(users),
            'limit': limit,
            'active_only': active_only,
            'timestamp': datetime.now().isoformat()
        }

        # 缓存结果
        await cache.set(cache_key, response_data, ttl=60)

        return web.json_response(response_data)

    except Exception as e:
        REQUEST_STATS['errors'] += 1
        return web.json_response({'error': str(e)}, status=500)

async def user_detail_handler(request):
    """用户详情端点"""
    REQUEST_STATS['total_requests'] += 1

    user_id = int(request.match_info['user_id'])
    cache_key = f"user_{user_id}"

    # 检查缓存
    cached_user = await cache.get(cache_key)
    if cached_user:
        return web.json_response(cached_user)

    # 从数据库获取
    try:
        user = await db.get_user(user_id)
        if user:
            # 缓存结果
            await cache.set(cache_key, user, ttl=300)
            return web.json_response(user)
        else:
            return web.json_response({'error': 'User not found'}, status=404)

    except Exception as e:
        REQUEST_STATS['errors'] += 1
        return web.json_response({'error': str(e)}, status=500)

async def analytics_handler(request):
    """分析数据端点"""
    REQUEST_STATS['total_requests'] += 1

    # 检查缓存
    cache_key = "analytics_data"
    cached_data = await cache.get(cache_key)

    if cached_data:
        return web.json_response(cached_data)

    # 生成分析数据（模拟重量级操作）
    try:
        analytics = await db.get_analytics()

        # 缓存结果
        await cache.set(cache_key, analytics, ttl=120)

        return web.json_response(analytics)

    except Exception as e:
        REQUEST_STATS['errors'] += 1
        return web.json_response({'error': str(e)}, status=500)

async def large_data_handler(request):
    """大数据端点 - 用于内存压力测试"""
    REQUEST_STATS['total_requests'] += 1

    # 生成大量数据
    size = int(request.query.get('size', 1000))

    try:
        # 模拟生成大数据
        await asyncio.sleep(0.1)  # 模拟处理时间

        large_data = {
            'data': [
                {
                    'id': i,
                    'value': f'data_item_{i}',
                    'metadata': {
                        'created': datetime.now().isoformat(),
                        'random_data': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=100))
                    }
                }
                for i in range(size)
            ],
            'size': size,
            'generated_at': datetime.now().isoformat()
        }

        return web.json_response(large_data)

    except Exception as e:
        REQUEST_STATS['errors'] += 1
        return web.json_response({'error': str(e)}, status=500)

async def slow_endpoint_handler(request):
    """慢端点 - 模拟慢查询"""
    REQUEST_STATS['total_requests'] += 1

    # 模拟慢操作
    delay = float(request.query.get('delay', 1.0))
    await asyncio.sleep(delay)

    return web.json_response({
        'message': f'Slow operation completed after {delay}s',
        'timestamp': datetime.now().isoformat()
    })

async def error_endpoint_handler(request):
    """错误端点 - 模拟错误"""
    REQUEST_STATS['total_requests'] += 1
    REQUEST_STATS['errors'] += 1

    error_type = request.query.get('type', 'generic')

    if error_type == 'timeout':
        await asyncio.sleep(5)  # 超时
        return web.json_response({'error': 'Operation timed out'}, status=408)
    elif error_type == 'server':
        return web.json_response({'error': 'Internal server error'}, status=500)
    elif error_type == 'forbidden':
        return web.json_response({'error': 'Access forbidden'}, status=403)
    else:
        return web.json_response({'error': 'Generic error'}, status=400)

async def config_handler(request):
    """配置端点"""
    REQUEST_STATS['total_requests'] += 1

    cache_key = "app_config"
    cached_config = await cache.get(cache_key)

    if cached_config:
        return web.json_response(cached_config)

    config = {
        'app_name': 'Claude Enhancer Mock Server',
        'version': '1.0.0',
        'environment': 'test',
        'features': {
            'caching': True,
            'analytics': True,
            'user_management': True
        },
        'limits': {
            'max_users_per_request': 1000,
            'cache_ttl': 300,
            'max_request_size': '10MB'
        },
        'updated_at': datetime.now().isoformat()
    }

    await cache.set(cache_key, config, ttl=600)
    return web.json_response(config)

async def search_handler(request):
    """搜索端点"""
    REQUEST_STATS['total_requests'] += 1

    query = request.query.get('q', '')
    limit = int(request.query.get('limit', 50))

    # 模拟搜索延迟
    await asyncio.sleep(0.05)

    # 简单搜索模拟
    results = []
    for user in db.users[:limit]:
        if query.lower() in user['name'].lower() or query.lower() in user['email'].lower():
            results.append(user)

    return web.json_response({
        'query': query,
        'results': results,
        'total': len(results),
        'limit': limit,
        'search_time_ms': 50
    })

async def reports_handler(request):
    """报告端点 - 模拟复杂报告生成"""
    REQUEST_STATS['total_requests'] += 1

    report_type = request.query.get('type', 'summary')

    # 模拟报告生成时间
    if report_type == 'detailed':
        await asyncio.sleep(0.5)  # 500ms
    else:
        await asyncio.sleep(0.1)  # 100ms

    report = {
        'type': report_type,
        'data': {
            'total_users': len(db.users),
            'active_users': len([u for u in db.users if u['active']]),
            'requests_today': REQUEST_STATS['total_requests'],
            'cache_performance': {
                'hit_rate': (REQUEST_STATS['cache_hits'] / max(REQUEST_STATS['cache_hits'] + REQUEST_STATS['cache_misses'], 1)) * 100,
                'total_hits': REQUEST_STATS['cache_hits'],
                'total_misses': REQUEST_STATS['cache_misses']
            }
        },
        'generated_at': datetime.now().isoformat(),
        'generation_time_ms': 500 if report_type == 'detailed' else 100
    }

    return web.json_response(report)

async def init_app():
    """初始化应用"""
    app = web.Application()

    # 设置启动时间
    app['start_time'] = time.time()

    # 设置CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # 添加路由
    routes = [
        web.get('/health', health_handler),
        web.get('/api/health', health_handler),
        web.get('/api/status', status_handler),
        web.get('/api/metrics', metrics_handler),
        web.get('/api/users', users_handler),
        web.get('/api/users/{user_id}', user_detail_handler),
        web.get('/api/users/search', search_handler),
        web.get('/api/analytics', analytics_handler),
        web.get('/api/reports', reports_handler),
        web.get('/api/data/large', large_data_handler),
        web.get('/api/slow', slow_endpoint_handler),
        web.get('/api/error', error_endpoint_handler),
        web.get('/api/config', config_handler),
    ]

    for route in routes:
        app.router.add_route(route.method, route.path, route.handler)
        cors.add(app.router._resources[-1])

    return app

async def main():
    """主函数"""
    print("🚀 启动Claude Enhancer模拟性能测试服务器")
    print("=" * 50)

    app = await init_app()

    # 创建服务器
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    # print("✅ 服务器已启动")
    # print("📍 访问地址: http://localhost:8080")
    # print("\n📋 可用端点:")
    # print("  GET /health - 健康检查")
    # print("  GET /api/health - API健康检查")
    # print("  GET /api/status - 服务状态")
    # print("  GET /api/metrics - 系统指标")
    # print("  GET /api/users?limit=100&active_only=true - 用户列表")
    # print("  GET /api/users/{user_id} - 用户详情")
    # print("  GET /api/users/search?q=query&limit=50 - 用户搜索")
    # print("  GET /api/analytics - 分析数据")
    # print("  GET /api/reports?type=summary|detailed - 报告")
    # print("  GET /api/data/large?size=1000 - 大数据(内存测试)")
    # print("  GET /api/slow?delay=1.0 - 慢端点")
    # print("  GET /api/error?type=server|timeout|forbidden - 错误端点")
    # print("  GET /api/config - 配置信息")
    # print("\n⏱️  服务器运行中，按 Ctrl+C 停止...")

    try:
        # 持续运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
    # print("\n🛑 停止服务器...")
    finally:
        await runner.cleanup()
    # print("✅ 服务器已停止")

if __name__ == "__main__":
    asyncio.run(main())