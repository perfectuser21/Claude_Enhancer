"""
Performance Optimization: Database Query Optimizer
数据库查询优化器 - 企业级数据库性能优化系统
"""

import asyncio
import asyncpg
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
import json
import hashlib
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型"""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"


@dataclass
class QueryStats:
    """查询统计信息"""

    query_hash: str
    query_type: QueryType
    avg_duration: float = 0.0
    max_duration: float = 0.0
    min_duration: float = float("inf")
    total_executions: int = 0
    total_duration: float = 0.0
    last_executed: Optional[datetime] = None
    slow_threshold_exceeded: int = 0
    error_count: int = 0
    cached_hits: int = 0


@dataclass
class DatabaseConfig:
    """数据库配置"""

    url: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    slow_query_threshold: float = 1.0  # 1秒
    enable_query_cache: bool = True
    query_cache_ttl: int = 300  # 5分钟
    enable_prepared_statements: bool = True
    statement_cache_size: int = 100


class DatabaseOptimizer:
    """数据库性能优化器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.query_stats: Dict[str, QueryStats] = {}
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.prepared_statements: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                self.config.url,
                min_size=1,
                max_size=self.config.pool_size,
                command_timeout=self.config.pool_timeout,
                server_settings={
                    "application_name": "claude-enhancer_optimizer",
                    "tcp_keepalives_idle": "300",
                    "tcp_keepalives_interval": "30",
                    "tcp_keepalives_count": "3",
                },
            )

            # 预热连接池
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")

            logger.info(f"✅ 数据库优化器初始化成功 - 连接池大小: {self.config.pool_size}")

            # 启动后台任务
            asyncio.create_task(self._periodic_optimization())
            asyncio.create_task(self._cache_cleanup())
            asyncio.create_task(self._stats_aggregation())

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise

    def _hash_query(self, query: str, params: tuple = None) -> str:
        """生成查询哈希"""
        query_normalized = " ".join(query.split())  # 标准化空格
        if params:
            query_with_params = f"{query_normalized}:{str(params)}"
        else:
            query_with_params = query_normalized
        return hashlib.md5(query_with_params.encode()).hexdigest()[:16]

    def _detect_query_type(self, query: str) -> QueryType:
        """检测查询类型"""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            if any(
                agg in query_upper
                for agg in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN(", "GROUP BY"]
            ):
                return QueryType.AGGREGATE
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        else:
            return QueryType.SELECT

    async def execute_optimized(
        self, query: str, *args, fetch_type: str = "all"
    ) -> Any:
        """执行优化的查询"""
        start_time = time.time()
        query_hash = self._hash_query(query, args)
        query_type = self._detect_query_type(query)

        # 检查查询缓存（仅对SELECT查询）
        if (
            self.config.enable_query_cache
            and query_type in [QueryType.SELECT, QueryType.AGGREGATE]
            and query_hash in self.query_cache
        ):
            cached_result, cache_time = self.query_cache[query_hash]
            if datetime.now() - cache_time < timedelta(
                seconds=self.config.query_cache_ttl
            ):
                # 更新统计
                await self._update_stats(query_hash, query_type, 0.001, cached=True)
                logger.debug(f"🎯 查询缓存命中: {query_hash}")
                return cached_result
            else:
                # 缓存过期，删除
                del self.query_cache[query_hash]

        try:
            # 执行查询
            async with self.pool.acquire() as conn:
                if fetch_type == "all":
                    result = await conn.fetch(query, *args)
                elif fetch_type == "one":
                    result = await conn.fetchrow(query, *args)
                elif fetch_type == "val":
                    result = await conn.fetchval(query, *args)
                elif fetch_type == "execute":
                    result = await conn.execute(query, *args)
                else:
                    result = await conn.fetch(query, *args)

            # 计算执行时间
            duration = time.time() - start_time

            # 缓存SELECT查询结果
            if (
                self.config.enable_query_cache
                and query_type in [QueryType.SELECT, QueryType.AGGREGATE]
                and duration < self.config.slow_query_threshold
            ):  # 只缓存快速查询
                self.query_cache[query_hash] = (result, datetime.now())

            # 更新统计
            await self._update_stats(query_hash, query_type, duration)

            # 慢查询日志
            if duration > self.config.slow_query_threshold:
                logger.warning(
                    f"🐌 慢查询检测 - 耗时: {duration:.3f}s, "
                    f"类型: {query_type.value}, "
                    f"查询: {query[:100]}..."
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            await self._update_stats(query_hash, query_type, duration, error=True)
            logger.error(f"❌ 查询执行失败: {e}, 查询: {query[:100]}...")
            raise

    async def _update_stats(
        self,
        query_hash: str,
        query_type: QueryType,
        duration: float,
        cached: bool = False,
        error: bool = False,
    ):
        """更新查询统计"""
        async with self._lock:
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = QueryStats(
                    query_hash=query_hash, query_type=query_type
                )

            stats = self.query_stats[query_hash]

            if error:
                stats.error_count += 1
                return

            if cached:
                stats.cached_hits += 1
                return

            stats.total_executions += 1
            stats.total_duration += duration
            stats.avg_duration = stats.total_duration / stats.total_executions
            stats.max_duration = max(stats.max_duration, duration)
            stats.min_duration = min(stats.min_duration, duration)
            stats.last_executed = datetime.now()

            if duration > self.config.slow_query_threshold:
                stats.slow_threshold_exceeded += 1

    async def execute_batch_optimized(
        self, query: str, params_list: List[tuple]
    ) -> List[Any]:
        """批量执行优化查询"""
        if not params_list:
            return []

        start_time = time.time()
        query_type = self._detect_query_type(query)

        try:
            # 使用executemany优化批量操作
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    if query_type == QueryType.INSERT:
                        # 批量插入优化
                        results = await conn.executemany(query, params_list)
                    else:
                        # 其他类型查询
                        results = []
                        for params in params_list:
                            result = await conn.fetch(query, *params)
                            results.append(result)

            duration = time.time() - start_time

            logger.info(
                f"📦 批量查询完成 - "
                f"类型: {query_type.value}, "
                f"数量: {len(params_list)}, "
                f"耗时: {duration:.3f}s"
            )

            return results

        except Exception as e:
            logger.error(f"❌ 批量查询失败: {e}")
            raise

    async def execute_with_connection_optimization(
        self, queries: List[Tuple[str, tuple]]
    ) -> List[Any]:
        """在单个连接中执行多个查询（减少连接开销）"""
        start_time = time.time()
        results = []

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for query, params in queries:
                        result = await conn.fetch(query, *params)
                        results.append(result)

            duration = time.time() - start_time

            logger.debug(
                f"🔗 连接优化查询完成 - " f"查询数: {len(queries)}, " f"耗时: {duration:.3f}s"
            )

            return results

        except Exception as e:
            logger.error(f"❌ 连接优化查询失败: {e}")
            raise

    async def analyze_table_performance(self, table_name: str) -> Dict[str, Any]:
        """分析表性能"""
        analysis = {}

        try:
            async with self.pool.acquire() as conn:
                # 表大小分析
                size_query = """
                    SELECT
                        pg_size_pretty(pg_total_relation_size($1)) as total_size,
                        pg_size_pretty(pg_relation_size($1)) as table_size,
                        pg_size_pretty(pg_indexes_size($1)) as indexes_size
                """
                size_result = await conn.fetchrow(size_query, table_name)
                analysis["size"] = dict(size_result) if size_result else {}

                # 索引使用分析
                index_query = """
                    SELECT
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE relname = $1
                """
                index_results = await conn.fetch(index_query, table_name)
                analysis["indexes"] = [dict(row) for row in index_results]

                # 表统计信息
                stats_query = """
                    SELECT
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_tup_hot_upd,
                        n_live_tup,
                        n_dead_tup
                    FROM pg_stat_user_tables
                    WHERE relname = $1
                """
                stats_result = await conn.fetchrow(stats_query, table_name)
                analysis["stats"] = dict(stats_result) if stats_result else {}

                # 建议优化
                suggestions = []
                if stats_result:
                    # 检查是否需要VACUUM
                    if stats_result["n_dead_tup"] > stats_result["n_live_tup"] * 0.1:
                        suggestions.append("建议执行VACUUM清理死元组")

                    # 检查索引效率
                    if stats_result["seq_scan"] > stats_result["idx_scan"] * 2:
                        suggestions.append("考虑添加索引以减少顺序扫描")

                analysis["suggestions"] = suggestions

        except Exception as e:
            logger.error(f"❌ 表性能分析失败: {e}")
            analysis["error"] = str(e)

        return analysis

    async def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        slow_queries = []

        for query_hash, stats in self.query_stats.items():
            if stats.slow_threshold_exceeded > 0:
                slow_queries.append(
                    {
                        "query_hash": query_hash,
                        "query_type": stats.query_type.value,
                        "avg_duration": stats.avg_duration,
                        "max_duration": stats.max_duration,
                        "total_executions": stats.total_executions,
                        "slow_count": stats.slow_threshold_exceeded,
                        "error_count": stats.error_count,
                        "last_executed": stats.last_executed.isoformat()
                        if stats.last_executed
                        else None,
                    }
                )

        # 按平均执行时间排序
        slow_queries.sort(key=lambda x: x["avg_duration"], reverse=True)
        return slow_queries[:limit]

    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {
            "total_queries": len(self.query_stats),
            "cache_hit_rate": 0.0,
            "avg_query_time": 0.0,
            "slow_query_count": 0,
            "error_rate": 0.0,
            "cache_size": len(self.query_cache),
        }

        if self.query_stats:
            total_executions = sum(
                qs.total_executions for qs in self.query_stats.values()
            )
            total_cached_hits = sum(qs.cached_hits for qs in self.query_stats.values())
            total_duration = sum(qs.total_duration for qs in self.query_stats.values())
            total_errors = sum(qs.error_count for qs in self.query_stats.values())
            slow_queries = sum(
                1 for qs in self.query_stats.values() if qs.slow_threshold_exceeded > 0
            )

            if total_executions > 0:
                stats["cache_hit_rate"] = (
                    total_cached_hits / (total_executions + total_cached_hits)
                ) * 100
                stats["avg_query_time"] = total_duration / total_executions
                stats["error_rate"] = (total_errors / total_executions) * 100

            stats["slow_query_count"] = slow_queries

        return stats

    async def _periodic_optimization(self):
        """定期优化任务"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时执行一次

                # 分析数据库性能
                await self._analyze_and_optimize()

                # 清理统计信息（保留最近24小时）
                await self._cleanup_old_stats()

            except Exception as e:
                logger.error(f"❌ 定期优化任务失败: {e}")

    async def _analyze_and_optimize(self):
        """分析并优化数据库"""
        try:
            async with self.pool.acquire() as conn:
                # 获取数据库统计信息
                db_stats = await conn.fetch(
                    """
                    SELECT
                        datname,
                        numbackends,
                        xact_commit,
                        xact_rollback,
                        blks_read,
                        blks_hit,
                        tup_returned,
                        tup_fetched,
                        tup_inserted,
                        tup_updated,
                        tup_deleted
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """
                )

                if db_stats:
                    stats = dict(db_stats[0])
                    buffer_hit_ratio = (
                        (stats["blks_hit"] / (stats["blks_hit"] + stats["blks_read"]))
                        * 100
                        if (stats["blks_hit"] + stats["blks_read"]) > 0
                        else 0
                    )

                    logger.info(
                        f"📊 数据库性能分析 - "
                        f"缓冲区命中率: {buffer_hit_ratio:.2f}%, "
                        f"活跃连接: {stats['numbackends']}, "
                        f"提交事务: {stats['xact_commit']}, "
                        f"回滚事务: {stats['xact_rollback']}"
                    )

                    # 如果缓冲区命中率低于95%，建议增加shared_buffers
                    if buffer_hit_ratio < 95:
                        logger.warning("⚠️ 缓冲区命中率较低，建议增加shared_buffers配置")

        except Exception as e:
            logger.error(f"❌ 数据库分析失败: {e}")

    async def _cache_cleanup(self):
        """清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次

                now = datetime.now()
                expired_keys = []

                for key, (_, cache_time) in self.query_cache.items():
                    if now - cache_time > timedelta(
                        seconds=self.config.query_cache_ttl
                    ):
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.query_cache[key]

                if expired_keys:
                    logger.debug(f"🧹 清理过期查询缓存: {len(expired_keys)}个")

            except Exception as e:
                logger.error(f"❌ 缓存清理失败: {e}")

    async def _cleanup_old_stats(self):
        """清理旧统计数据"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_stats = []

            for query_hash, stats in self.query_stats.items():
                if stats.last_executed and stats.last_executed < cutoff_time:
                    old_stats.append(query_hash)

            for query_hash in old_stats:
                del self.query_stats[query_hash]

            if old_stats:
                logger.debug(f"🧹 清理旧查询统计: {len(old_stats)}个")

        except Exception as e:
            logger.error(f"❌ 统计清理失败: {e}")

    async def _stats_aggregation(self):
        """统计信息聚合"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟聚合一次

                stats = await self.get_database_stats()

                if stats["total_queries"] > 0:
                    logger.info(
                        f"📈 数据库性能摘要 - "
                        f"查询总数: {stats['total_queries']}, "
                        f"缓存命中率: {stats['cache_hit_rate']:.2f}%, "
                        f"平均查询时间: {stats['avg_query_time']:.3f}s, "
                        f"慢查询数: {stats['slow_query_count']}, "
                        f"错误率: {stats['error_rate']:.2f}%"
                    )

            except Exception as e:
                logger.error(f"❌ 统计聚合失败: {e}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                return True
        except:
            return False

    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("📴 数据库连接池已关闭")


def optimized_query(cache_ttl: int = 300, batch_size: Optional[int] = None):
    """查询优化装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取数据库优化器实例
            optimizer = getattr(wrapper, "_optimizer", None)
            if not optimizer:
                return await func(*args, **kwargs)

            # 执行优化查询
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 使用示例
@optimized_query(cache_ttl=600)
async def get_user_by_id(user_id: int, optimizer: DatabaseOptimizer):
    """获取用户信息（优化版本）"""
    query = "SELECT * FROM users WHERE id = $1"
    return await optimizer.execute_optimized(query, user_id, fetch_type="one")


@optimized_query(batch_size=100)
async def bulk_insert_logs(logs: List[dict], optimizer: DatabaseOptimizer):
    """批量插入日志（优化版本）"""
    query = "INSERT INTO logs (level, message, timestamp) VALUES ($1, $2, $3)"
    params_list = [(log["level"], log["message"], log["timestamp"]) for log in logs]
    return await optimizer.execute_batch_optimized(query, params_list)
