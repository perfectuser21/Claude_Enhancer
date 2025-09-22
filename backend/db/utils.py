"""
数据库工具函数
==============

提供数据库操作的工具函数:
- 查询优化
- 分页查询
- 批量操作
- 数据导入导出
- 性能监控
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from datetime import datetime, timedelta
import time
import csv
import json

from sqlalchemy import (
    select,
    update,
    delete,
    func,
    text,
    inspect,
    Column,
    Table,
    MetaData,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import Select
from sqlalchemy.engine import Result

from ..models.base import BaseModel
from .session import transaction, async_transaction, readonly_transaction

# 配置日志
logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    查询优化器
    ==========

    提供查询性能优化的工具方法
    """

    @staticmethod
    def analyze_query(session: Session, query: Union[Query, Select]) -> Dict[str, Any]:
        """
        分析查询执行计划

        Args:
            session: 数据库会话
            query: 查询对象

        Returns:
            执行计划分析结果
        """
        try:
            # 获取查询语句
            if hasattr(query, "statement"):
                statement = query.statement
            else:
                statement = query

            # 执行EXPLAIN ANALYZE
            explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {statement}")
            result = session.execute(explain_query)
            plan = result.scalar()

            # 解析执行计划
            plan_data = json.loads(plan)[0]
            execution_plan = plan_data.get("Plan", {})

            return {
                "total_cost": execution_plan.get("Total Cost"),
                "actual_time": execution_plan.get("Actual Total Time"),
                "rows": execution_plan.get("Actual Rows"),
                "node_type": execution_plan.get("Node Type"),
                "shared_hit_blocks": plan_data.get("Planning", {}).get(
                    "Shared Hit Blocks", 0
                ),
                "shared_read_blocks": plan_data.get("Planning", {}).get(
                    "Shared Read Blocks", 0
                ),
                "execution_time": plan_data.get("Execution Time"),
                "planning_time": plan_data.get("Planning Time"),
                "full_plan": plan_data,
            }

        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            return {}

    @staticmethod
    def suggest_indexes(session: Session, model: Type[BaseModel]) -> List[str]:
        """
        建议索引

        Args:
            session: 数据库会话
            model: 模型类

        Returns:
            索引建议列表
        """
        suggestions = []
        table_name = model.__tablename__

        try:
            # 获取表结构
            inspector = inspect(session.bind)
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            # 检查外键索引
            for fk in foreign_keys:
                fk_columns = fk["constrained_columns"]
                if not any(
                    set(fk_columns).issubset(set(idx["column_names"]))
                    for idx in indexes
                ):
                    index_name = f"idx_{table_name}_{'_'.join(fk_columns)}"
                    suggestions.append(
                        f"CREATE INDEX {index_name} ON {table_name} ({', '.join(fk_columns)});"
                    )

            # 检查常用查询字段
            common_query_fields = ["created_at", "updated_at", "status", "is_deleted"]
            for field in common_query_fields:
                if any(col["name"] == field for col in columns):
                    if not any(field in idx["column_names"] for idx in indexes):
                        index_name = f"idx_{table_name}_{field}"
                        suggestions.append(
                            f"CREATE INDEX {index_name} ON {table_name} ({field});"
                        )

            return suggestions

        except Exception as e:
            logger.error(f"索引建议生成失败: {e}")
            return []


class PaginationHelper:
    """
    分页助手
    ========

    提供分页查询的便捷方法
    """

    @staticmethod
    def paginate_query(
        query: Union[Query, Select],
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        分页查询

        Args:
            query: 查询对象
            page: 页码 (从1开始)
            per_page: 每页数量
            max_per_page: 最大每页数量

        Returns:
            (数据列表, 分页信息)
        """
        # 参数验证
        page = max(1, page)
        per_page = min(max(1, per_page), max_per_page)

        # 计算偏移量
        offset = (page - 1) * per_page

        # 获取总数
        if hasattr(query, "count"):
            total = query.count()
        else:
            # 对于Select对象，需要包装成count查询
            count_query = select(func.count()).select_from(query.alias())
            total = query.session.execute(count_query).scalar()

        # 获取数据
        items = query.offset(offset).limit(per_page).all()

        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages

        pagination_info = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
        }

        return items, pagination_info

    @staticmethod
    async def async_paginate_query(
        session: AsyncSession,
        query: Select,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        异步分页查询

        Args:
            session: 异步会话
            query: 查询对象
            page: 页码
            per_page: 每页数量
            max_per_page: 最大每页数量

        Returns:
            (数据列表, 分页信息)
        """
        # 参数验证
        page = max(1, page)
        per_page = min(max(1, per_page), max_per_page)

        # 计算偏移量
        offset = (page - 1) * per_page

        # 获取总数
        count_query = select(func.count()).select_from(query.alias())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # 获取数据
        data_query = query.offset(offset).limit(per_page)
        data_result = await session.execute(data_query)
        items = data_result.scalars().all()

        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages

        pagination_info = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
        }

        return items, pagination_info


class BulkOperator:
    """
    批量操作器
    ==========

    提供高效的批量数据操作
    """

    @staticmethod
    def bulk_insert(
        session: Session,
        model: Type[BaseModel],
        data_list: List[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> int:
        """
        批量插入

        Args:
            session: 数据库会话
            model: 模型类
            data_list: 数据字典列表
            batch_size: 批处理大小

        Returns:
            插入的记录数
        """
        if not data_list:
            return 0

        total_inserted = 0

        try:
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i : i + batch_size]

                # 添加默认字段
                for item in batch:
                    if "created_at" not in item:
                        item["created_at"] = datetime.utcnow()
                    if "updated_at" not in item:
                        item["updated_at"] = datetime.utcnow()

                # 批量插入
                result = session.execute(model.__table__.insert(), batch)

                total_inserted += result.rowcount
                session.flush()

                logger.debug(f"批量插入 {len(batch)} 条记录到 {model.__tablename__}")

            return total_inserted

        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            raise

    @staticmethod
    async def async_bulk_insert(
        session: AsyncSession,
        model: Type[BaseModel],
        data_list: List[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> int:
        """
        异步批量插入

        Args:
            session: 异步数据库会话
            model: 模型类
            data_list: 数据字典列表
            batch_size: 批处理大小

        Returns:
            插入的记录数
        """
        if not data_list:
            return 0

        total_inserted = 0

        try:
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i : i + batch_size]

                # 添加默认字段
                for item in batch:
                    if "created_at" not in item:
                        item["created_at"] = datetime.utcnow()
                    if "updated_at" not in item:
                        item["updated_at"] = datetime.utcnow()

                # 批量插入
                result = await session.execute(model.__table__.insert(), batch)

                total_inserted += result.rowcount
                await session.flush()

                logger.debug(f"异步批量插入 {len(batch)} 条记录到 {model.__tablename__}")

            return total_inserted

        except Exception as e:
            logger.error(f"异步批量插入失败: {e}")
            raise

    @staticmethod
    def bulk_update(
        session: Session,
        model: Type[BaseModel],
        updates: List[Dict[str, Any]],
        id_field: str = "id",
    ) -> int:
        """
        批量更新

        Args:
            session: 数据库会话
            model: 模型类
            updates: 更新数据列表 (必须包含id_field)
            id_field: ID字段名

        Returns:
            更新的记录数
        """
        if not updates:
            return 0

        try:
            # 添加更新时间
            for item in updates:
                item["updated_at"] = datetime.utcnow()

            # 执行批量更新
            result = session.execute(update(model.__table__), updates)

            return result.rowcount

        except Exception as e:
            logger.error(f"批量更新失败: {e}")
            raise

    @staticmethod
    def bulk_delete(
        session: Session,
        model: Type[BaseModel],
        ids: List[Any],
        id_field: str = "id",
        soft_delete: bool = True,
    ) -> int:
        """
        批量删除

        Args:
            session: 数据库会话
            model: 模型类
            ids: ID列表
            id_field: ID字段名
            soft_delete: 是否软删除

        Returns:
            删除的记录数
        """
        if not ids:
            return 0

        try:
            if soft_delete and hasattr(model, "is_deleted"):
                # 软删除
                result = session.execute(
                    update(model.__table__)
                    .where(getattr(model.__table__.c, id_field).in_(ids))
                    .values(
                        is_deleted=True,
                        deleted_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
            else:
                # 硬删除
                result = session.execute(
                    delete(model.__table__).where(
                        getattr(model.__table__.c, id_field).in_(ids)
                    )
                )

            return result.rowcount

        except Exception as e:
            logger.error(f"批量删除失败: {e}")
            raise


class DataExporter:
    """
    数据导出器
    ==========

    支持多种格式的数据导出
    """

    @staticmethod
    def export_to_csv(
        session: Session,
        query: Union[Query, Select],
        filename: str,
        headers: Optional[List[str]] = None,
    ) -> str:
        """
        导出到CSV文件

        Args:
            session: 数据库会话
            query: 查询对象
            filename: 文件名
            headers: 列标题

        Returns:
            导出的文件路径
        """
        try:
            # 执行查询
            if hasattr(query, "all"):
                results = query.all()
            else:
                results = session.execute(query).fetchall()

            if not results:
                logger.warning("查询结果为空，跳过导出")
                return filename

            # 写入CSV文件
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # 写入标题
                if headers:
                    writer.writerow(headers)
                elif hasattr(results[0], "_fields"):
                    writer.writerow(results[0]._fields)
                elif hasattr(results[0], "__dict__"):
                    writer.writerow(results[0].__dict__.keys())

                # 写入数据
                for row in results:
                    if hasattr(row, "_asdict"):
                        writer.writerow(row._asdict().values())
                    elif hasattr(row, "__dict__"):
                        writer.writerow(row.__dict__.values())
                    else:
                        writer.writerow(row)

            logger.info(f"成功导出 {len(results)} 条记录到 {filename}")
            return filename

        except Exception as e:
            logger.error(f"CSV导出失败: {e}")
            raise

    @staticmethod
    def export_to_json(
        session: Session, query: Union[Query, Select], filename: str, indent: int = 2
    ) -> str:
        """
        导出到JSON文件

        Args:
            session: 数据库会话
            query: 查询对象
            filename: 文件名
            indent: JSON缩进

        Returns:
            导出的文件路径
        """
        try:
            # 执行查询
            if hasattr(query, "all"):
                results = query.all()
            else:
                results = session.execute(query).fetchall()

            # 转换为字典列表
            data = []
            for row in results:
                if hasattr(row, "to_dict"):
                    data.append(row.to_dict())
                elif hasattr(row, "_asdict"):
                    data.append(row._asdict())
                elif hasattr(row, "__dict__"):
                    row_dict = {
                        k: v for k, v in row.__dict__.items() if not k.startswith("_")
                    }
                    data.append(row_dict)
                else:
                    data.append(str(row))

            # 写入JSON文件
            with open(filename, "w", encoding="utf-8") as jsonfile:
                json.dump(
                    data, jsonfile, indent=indent, ensure_ascii=False, default=str
                )

            logger.info(f"成功导出 {len(data)} 条记录到 {filename}")
            return filename

        except Exception as e:
            logger.error(f"JSON导出失败: {e}")
            raise


class PerformanceMonitor:
    """
    性能监控器
    ==========

    监控数据库操作的性能指标
    """

    def __init__(self):
        self.metrics = {
            "query_count": 0,
            "total_time": 0,
            "slow_queries": [],
            "error_count": 0,
        }

    def record_query(
        self, query: str, execution_time: float, error: Optional[Exception] = None
    ):
        """
        记录查询指标

        Args:
            query: 查询语句
            execution_time: 执行时间 (秒)
            error: 错误信息
        """
        self.metrics["query_count"] += 1
        self.metrics["total_time"] += execution_time

        if error:
            self.metrics["error_count"] += 1
            logger.error(f"查询执行失败: {error}")

        # 记录慢查询 (超过1秒)
        if execution_time > 1.0:
            self.metrics["slow_queries"].append(
                {
                    "query": query[:200] + "..." if len(query) > 200 else query,
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            logger.warning(f"慢查询检测: {execution_time:.3f}s - {query[:100]}...")

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            性能指标字典
        """
        avg_time = (
            self.metrics["total_time"] / self.metrics["query_count"]
            if self.metrics["query_count"] > 0
            else 0
        )

        return {
            **self.metrics,
            "average_time": avg_time,
            "slow_query_count": len(self.metrics["slow_queries"]),
            "error_rate": (
                self.metrics["error_count"] / self.metrics["query_count"]
                if self.metrics["query_count"] > 0
                else 0
            ),
        }

    def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            "query_count": 0,
            "total_time": 0,
            "slow_queries": [],
            "error_count": 0,
        }


# 创建全局性能监控器
performance_monitor = PerformanceMonitor()


# 导出公共接口
__all__ = [
    "QueryOptimizer",
    "PaginationHelper",
    "BulkOperator",
    "DataExporter",
    "PerformanceMonitor",
    "performance_monitor",
]
