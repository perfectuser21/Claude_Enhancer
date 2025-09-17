#!/usr/bin/env python3
"""
Perfect21 数据库性能测试
测试工作流状态持久化、查询性能和并发访问
"""

import os
import sys
import time
import sqlite3
import json
import statistics
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

@dataclass
class DatabaseMetrics:
    """数据库性能指标"""
    operation_type: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    operations_per_second: float
    concurrent_connections: int
    test_duration: float

class DatabasePerformanceTester:
    """数据库性能测试器"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or ".perfect21/test_performance.db"
        Path(self.db_path).parent.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        self.setup_test_database()

    def setup_test_database(self):
        """设置测试数据库结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 工作流表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

            # 阶段表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    stage_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_mode TEXT NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
                )
            ''')

            # 任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    stage_name TEXT NOT NULL,
                    task_id TEXT UNIQUE NOT NULL,
                    agent_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
                )
            ''')

            # 执行日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
                )
            ''')

            # 性能指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_id ON workflows(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_state ON workflows(state)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stages_workflow ON stages(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_workflow ON execution_logs(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON execution_logs(timestamp)')

            conn.commit()

    def run_comprehensive_database_tests(self) -> Dict[str, Any]:
        """运行全面的数据库性能测试"""
        print("🗄️  开始数据库性能测试")
        print("=" * 60)

        test_results = {}

        # 1. 插入性能测试
        test_results['insert_performance'] = self.test_insert_performance()

        # 2. 查询性能测试
        test_results['query_performance'] = self.test_query_performance()

        # 3. 更新性能测试
        test_results['update_performance'] = self.test_update_performance()

        # 4. 并发访问测试
        test_results['concurrent_access'] = self.test_concurrent_access()

        # 5. 大数据量性能测试
        test_results['large_dataset_performance'] = self.test_large_dataset_performance()

        # 6. 事务性能测试
        test_results['transaction_performance'] = self.test_transaction_performance()

        # 7. 索引效率测试
        test_results['index_efficiency'] = self.test_index_efficiency()

        # 编译测试报告
        final_report = self.compile_database_performance_report(test_results)

        return final_report

    def test_insert_performance(self) -> DatabaseMetrics:
        """测试插入性能"""
        print("\n📝 1. 插入性能测试")
        print("-" * 30)

        operation_count = 1000
        response_times = []
        successful_ops = 0
        failed_ops = 0

        start_time = time.time()

        for i in range(operation_count):
            op_start = time.time()

            try:
                workflow_data = self._generate_test_workflow_data(f"insert_test_{i}")
                self._insert_workflow_with_stages(workflow_data)

                op_time = time.time() - op_start
                response_times.append(op_time)
                successful_ops += 1

                if i % 100 == 0:
                    print(f"已插入 {i} 个工作流...")

            except Exception as e:
                failed_ops += 1
                self.logger.error(f"插入操作失败: {e}")

        total_time = time.time() - start_time

        metrics = DatabaseMetrics(
            operation_type="INSERT",
            total_operations=operation_count,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            operations_per_second=successful_ops / total_time,
            concurrent_connections=1,
            test_duration=total_time
        )

        print(f"✅ 插入测试完成: {successful_ops}/{operation_count} 成功, "
              f"{metrics.operations_per_second:.1f} ops/s, "
              f"平均响应时间: {metrics.avg_response_time:.3f}s")

        return metrics

    def test_query_performance(self) -> DatabaseMetrics:
        """测试查询性能"""
        print("\n🔍 2. 查询性能测试")
        print("-" * 30)

        # 确保有足够的测试数据
        self._ensure_test_data(500)

        query_count = 1000
        response_times = []
        successful_ops = 0
        failed_ops = 0

        queries = [
            "SELECT * FROM workflows WHERE state = 'running'",
            "SELECT * FROM workflows WHERE created_at > datetime('now', '-1 day')",
            "SELECT w.*, COUNT(s.id) as stage_count FROM workflows w LEFT JOIN stages s ON w.workflow_id = s.workflow_id GROUP BY w.id",
            "SELECT * FROM tasks WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 10",
            "SELECT workflow_id, COUNT(*) as task_count FROM tasks GROUP BY workflow_id HAVING task_count > 5"
        ]

        start_time = time.time()

        for i in range(query_count):
            query = queries[i % len(queries)]
            op_start = time.time()

            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    results = cursor.fetchall()

                op_time = time.time() - op_start
                response_times.append(op_time)
                successful_ops += 1

                if i % 200 == 0:
                    print(f"已执行 {i} 个查询...")

            except Exception as e:
                failed_ops += 1
                self.logger.error(f"查询操作失败: {e}")

        total_time = time.time() - start_time

        metrics = DatabaseMetrics(
            operation_type="SELECT",
            total_operations=query_count,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            operations_per_second=successful_ops / total_time,
            concurrent_connections=1,
            test_duration=total_time
        )

        print(f"✅ 查询测试完成: {successful_ops}/{query_count} 成功, "
              f"{metrics.operations_per_second:.1f} ops/s, "
              f"平均响应时间: {metrics.avg_response_time:.3f}s")

        return metrics

    def test_update_performance(self) -> DatabaseMetrics:
        """测试更新性能"""
        print("\n✏️  3. 更新性能测试")
        print("-" * 30)

        # 确保有足够的测试数据
        workflow_ids = self._ensure_test_data(200)

        update_count = 500
        response_times = []
        successful_ops = 0
        failed_ops = 0

        start_time = time.time()

        for i in range(update_count):
            workflow_id = workflow_ids[i % len(workflow_ids)]
            op_start = time.time()

            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # 更新工作流状态
                    new_state = ['running', 'completed', 'failed'][i % 3]
                    cursor.execute(
                        "UPDATE workflows SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE workflow_id = ?",
                        (new_state, workflow_id)
                    )

                    # 更新相关任务状态
                    cursor.execute(
                        "UPDATE tasks SET status = ? WHERE workflow_id = ?",
                        (new_state, workflow_id)
                    )

                    conn.commit()

                op_time = time.time() - op_start
                response_times.append(op_time)
                successful_ops += 1

                if i % 100 == 0:
                    print(f"已更新 {i} 个工作流...")

            except Exception as e:
                failed_ops += 1
                self.logger.error(f"更新操作失败: {e}")

        total_time = time.time() - start_time

        metrics = DatabaseMetrics(
            operation_type="UPDATE",
            total_operations=update_count,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            operations_per_second=successful_ops / total_time,
            concurrent_connections=1,
            test_duration=total_time
        )

        print(f"✅ 更新测试完成: {successful_ops}/{update_count} 成功, "
              f"{metrics.operations_per_second:.1f} ops/s, "
              f"平均响应时间: {metrics.avg_response_time:.3f}s")

        return metrics

    def test_concurrent_access(self) -> DatabaseMetrics:
        """测试并发访问性能"""
        print("\n🚀 4. 并发访问测试")
        print("-" * 30)

        concurrent_users = 10
        operations_per_user = 50
        total_operations = concurrent_users * operations_per_user

        # 确保有足够的测试数据
        workflow_ids = self._ensure_test_data(100)

        response_times = []
        successful_ops = 0
        failed_ops = 0
        lock = threading.Lock()

        def concurrent_worker(worker_id: int):
            """并发工作线程"""
            nonlocal successful_ops, failed_ops

            worker_successful = 0
            worker_failed = 0
            worker_times = []

            for i in range(operations_per_user):
                operation_type = i % 4  # 4种操作类型
                op_start = time.time()

                try:
                    if operation_type == 0:  # 插入
                        workflow_data = self._generate_test_workflow_data(f"concurrent_{worker_id}_{i}")
                        self._insert_workflow_with_stages(workflow_data)

                    elif operation_type == 1:  # 查询
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM workflows WHERE state = 'running' LIMIT 10")
                            results = cursor.fetchall()

                    elif operation_type == 2:  # 更新
                        workflow_id = workflow_ids[i % len(workflow_ids)]
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE workflows SET updated_at = CURRENT_TIMESTAMP WHERE workflow_id = ?",
                                (workflow_id,)
                            )
                            conn.commit()

                    else:  # 删除和重新插入
                        workflow_id = workflow_ids[i % len(workflow_ids)]
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM tasks WHERE workflow_id = ?", (workflow_id,))
                            cursor.execute("DELETE FROM stages WHERE workflow_id = ?", (workflow_id,))
                            cursor.execute("DELETE FROM workflows WHERE workflow_id = ?", (workflow_id,))
                            conn.commit()

                    op_time = time.time() - op_start
                    worker_times.append(op_time)
                    worker_successful += 1

                except Exception as e:
                    worker_failed += 1
                    self.logger.error(f"Worker {worker_id} 操作失败: {e}")

            with lock:
                successful_ops += worker_successful
                failed_ops += worker_failed
                response_times.extend(worker_times)

        print(f"启动 {concurrent_users} 个并发用户，每用户 {operations_per_user} 操作...")

        start_time = time.time()

        # 启动并发线程
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(concurrent_worker, i) for i in range(concurrent_users)]
            concurrent.futures.wait(futures)

        total_time = time.time() - start_time

        metrics = DatabaseMetrics(
            operation_type="CONCURRENT_MIXED",
            total_operations=total_operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            operations_per_second=successful_ops / total_time,
            concurrent_connections=concurrent_users,
            test_duration=total_time
        )

        print(f"✅ 并发测试完成: {successful_ops}/{total_operations} 成功, "
              f"{metrics.operations_per_second:.1f} ops/s, "
              f"平均响应时间: {metrics.avg_response_time:.3f}s")

        return metrics

    def test_large_dataset_performance(self) -> DatabaseMetrics:
        """测试大数据量性能"""
        print("\n📊 5. 大数据量性能测试")
        print("-" * 30)

        # 创建大量测试数据
        large_dataset_size = 5000
        print(f"创建 {large_dataset_size} 个工作流的大数据集...")

        workflow_ids = self._ensure_test_data(large_dataset_size)

        # 测试复杂查询性能
        complex_queries = [
            """
            SELECT w.workflow_id, w.name, w.state,
                   COUNT(DISTINCT s.stage_name) as stage_count,
                   COUNT(t.id) as task_count,
                   AVG(CASE WHEN t.completed_at IS NOT NULL AND t.started_at IS NOT NULL
                       THEN (julianday(t.completed_at) - julianday(t.started_at)) * 24 * 3600
                       ELSE NULL END) as avg_task_duration
            FROM workflows w
            LEFT JOIN stages s ON w.workflow_id = s.workflow_id
            LEFT JOIN tasks t ON w.workflow_id = t.workflow_id
            GROUP BY w.workflow_id, w.name, w.state
            HAVING task_count > 0
            ORDER BY avg_task_duration DESC
            LIMIT 50
            """,

            """
            SELECT DATE(created_at) as date,
                   COUNT(*) as workflows_created,
                   SUM(CASE WHEN state = 'completed' THEN 1 ELSE 0 END) as completed_count,
                   AVG(CASE WHEN completed_at IS NOT NULL
                       THEN (julianday(completed_at) - julianday(created_at)) * 24 * 3600
                       ELSE NULL END) as avg_completion_time
            FROM workflows
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,

            """
            SELECT agent_name,
                   COUNT(*) as total_tasks,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                   AVG(retry_count) as avg_retries
            FROM tasks
            GROUP BY agent_name
            HAVING total_tasks > 10
            ORDER BY completed_tasks DESC
            """
        ]

        response_times = []
        successful_ops = 0
        failed_ops = 0

        start_time = time.time()

        for i, query in enumerate(complex_queries):
            for run in range(10):  # 每个查询运行10次
                op_start = time.time()

                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(query)
                        results = cursor.fetchall()

                    op_time = time.time() - op_start
                    response_times.append(op_time)
                    successful_ops += 1

                    print(f"查询 {i+1}, 运行 {run+1}: {op_time:.3f}s, {len(results)} 行结果")

                except Exception as e:
                    failed_ops += 1
                    self.logger.error(f"大数据查询失败: {e}")

        total_time = time.time() - start_time

        metrics = DatabaseMetrics(
            operation_type="LARGE_DATASET_QUERY",
            total_operations=len(complex_queries) * 10,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            operations_per_second=successful_ops / total_time,
            concurrent_connections=1,
            test_duration=total_time
        )

        print(f"✅ 大数据量测试完成: {successful_ops}/{len(complex_queries) * 10} 成功, "
              f"平均响应时间: {metrics.avg_response_time:.3f}s")

        return metrics

    def test_transaction_performance(self) -> DatabaseMetrics:
        """测试事务性能"""
        print("\n💾 6. 事务性能测试")
        print("-" * 30)

        transaction_count = 200
        response_times = []
        successful_ops = 0
        failed_ops = 0

        start_time = time.time()

        for i in range(transaction_count):
            op_start = time.time()

            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # 开始事务
                    cursor.execute("BEGIN TRANSACTION")

                    # 创建完整的工作流数据（多表操作）
                    workflow_data = self._generate_test_workflow_data(f"transaction_test_{i}")

                    # 插入工作流
                    cursor.execute(
                        "INSERT INTO workflows (workflow_id, name, state, config) VALUES (?, ?, ?, ?)",
                        (workflow_data['workflow_id'], workflow_data['name'],
                         workflow_data['state'], json.dumps(workflow_data['config']))
                    )

                    # 插入阶段
                    for stage in workflow_data['stages']:
                        cursor.execute(
                            "INSERT INTO stages (workflow_id, stage_name, status, execution_mode) VALUES (?, ?, ?, ?)",
                            (workflow_data['workflow_id'], stage['name'], stage['status'], stage['execution_mode'])
                        )

                    # 插入任务
                    for task in workflow_data['tasks']:
                        cursor.execute(
                            "INSERT INTO tasks (workflow_id, stage_name, task_id, agent_name, description, status, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (workflow_data['workflow_id'], task['stage_name'], task['task_id'],
                             task['agent_name'], task['description'], task['status'], task['priority'])
                        )

                    # 插入执行日志
                    cursor.execute(
                        "INSERT INTO execution_logs (workflow_id, event_type, event_data) VALUES (?, ?, ?)",
                        (workflow_data['workflow_id'], 'workflow_created', json.dumps({'test': True}))
                    )

                    # 提交事务
                    cursor.execute("COMMIT")

                op_time = time.time() - op_start
                response_times.append(op_time)
                successful_ops += 1

                if i % 50 == 0:
                    print(f"已完成 {i} 个事务...")

            except Exception as e:
                failed_ops += 1
                self.logger.error(f"事务操作失败: {e}")
                # 回滚事务
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.rollback()
                except:
                    pass

        total_time = time.time() - start_time

        metrics = DatabaseMetrics(
            operation_type="TRANSACTION",
            total_operations=transaction_count,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            operations_per_second=successful_ops / total_time,
            concurrent_connections=1,
            test_duration=total_time
        )

        print(f"✅ 事务测试完成: {successful_ops}/{transaction_count} 成功, "
              f"{metrics.operations_per_second:.1f} ops/s, "
              f"平均响应时间: {metrics.avg_response_time:.3f}s")

        return metrics

    def test_index_efficiency(self) -> Dict[str, Any]:
        """测试索引效率"""
        print("\n🗂️  7. 索引效率测试")
        print("-" * 30)

        # 确保有足够的测试数据
        self._ensure_test_data(1000)

        test_queries = [
            ("workflow_id索引", "SELECT * FROM workflows WHERE workflow_id = 'test_workflow_500'"),
            ("state索引", "SELECT * FROM workflows WHERE state = 'running'"),
            ("无索引查询", "SELECT * FROM workflows WHERE name LIKE '%test%'"),
            ("JOIN查询", """
                SELECT w.*, COUNT(t.id) as task_count
                FROM workflows w
                LEFT JOIN tasks t ON w.workflow_id = t.workflow_id
                GROUP BY w.id
            """),
            ("复合条件", "SELECT * FROM tasks WHERE workflow_id LIKE 'test_%' AND status = 'completed'")
        ]

        results = {}

        for test_name, query in test_queries:
            print(f"测试: {test_name}")

            # 执行查询多次取平均值
            execution_times = []

            for _ in range(20):
                start_time = time.time()

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    results_data = cursor.fetchall()

                execution_time = time.time() - start_time
                execution_times.append(execution_time)

            avg_time = statistics.mean(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)

            results[test_name] = {
                'avg_execution_time': avg_time,
                'max_execution_time': max_time,
                'min_execution_time': min_time,
                'result_count': len(results_data),
                'query': query
            }

            print(f"  平均执行时间: {avg_time:.3f}s, 结果数量: {len(results_data)}")

        return results

    def _generate_test_workflow_data(self, workflow_id: str) -> Dict[str, Any]:
        """生成测试工作流数据"""
        agents = ['backend-architect', 'frontend-specialist', 'database-specialist',
                 'test-engineer', 'security-auditor', 'devops-engineer']

        stages = []
        tasks = []

        # 生成阶段和任务
        for i, stage_name in enumerate(['analysis', 'design', 'implementation', 'testing']):
            stages.append({
                'name': stage_name,
                'status': ['created', 'running', 'completed'][i % 3],
                'execution_mode': 'parallel' if i % 2 == 0 else 'sequential'
            })

            # 为每个阶段生成任务
            for j, agent in enumerate(agents[:3]):  # 每阶段3个任务
                task_id = f"{workflow_id}_{stage_name}_{agent}"
                tasks.append({
                    'task_id': task_id,
                    'stage_name': stage_name,
                    'agent_name': agent,
                    'description': f'{agent} task for {stage_name}',
                    'status': ['created', 'running', 'completed', 'failed'][j % 4],
                    'priority': j + 1
                })

        return {
            'workflow_id': workflow_id,
            'name': f'Test Workflow {workflow_id}',
            'state': ['created', 'running', 'completed', 'failed'][len(workflow_id) % 4],
            'config': {
                'test': True,
                'complexity': 'medium',
                'agents_count': len(agents)
            },
            'stages': stages,
            'tasks': tasks
        }

    def _insert_workflow_with_stages(self, workflow_data: Dict[str, Any]):
        """插入完整的工作流数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 插入工作流
            cursor.execute(
                "INSERT INTO workflows (workflow_id, name, state, config) VALUES (?, ?, ?, ?)",
                (workflow_data['workflow_id'], workflow_data['name'],
                 workflow_data['state'], json.dumps(workflow_data['config']))
            )

            # 插入阶段
            for stage in workflow_data['stages']:
                cursor.execute(
                    "INSERT INTO stages (workflow_id, stage_name, status, execution_mode) VALUES (?, ?, ?, ?)",
                    (workflow_data['workflow_id'], stage['name'], stage['status'], stage['execution_mode'])
                )

            # 插入任务
            for task in workflow_data['tasks']:
                cursor.execute(
                    "INSERT INTO tasks (workflow_id, stage_name, task_id, agent_name, description, status, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (workflow_data['workflow_id'], task['stage_name'], task['task_id'],
                     task['agent_name'], task['description'], task['status'], task['priority'])
                )

            conn.commit()

    def _ensure_test_data(self, min_count: int) -> List[str]:
        """确保有足够的测试数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM workflows")
            current_count = cursor.fetchone()[0]

        workflow_ids = []

        if current_count < min_count:
            needed = min_count - current_count
            print(f"创建 {needed} 个测试工作流...")

            for i in range(needed):
                workflow_id = f"test_workflow_{current_count + i}"
                workflow_data = self._generate_test_workflow_data(workflow_id)
                self._insert_workflow_with_stages(workflow_data)
                workflow_ids.append(workflow_id)

        # 获取所有工作流ID
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT workflow_id FROM workflows LIMIT ?", (min_count,))
            workflow_ids.extend([row[0] for row in cursor.fetchall()])

        return workflow_ids

    def compile_database_performance_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """编译数据库性能测试报告"""
        print("\n📋 正在生成数据库性能测试报告...")

        # 计算数据库统计信息
        db_stats = self._get_database_statistics()

        report = {
            'test_summary': {
                'test_date': datetime.now().isoformat(),
                'database_path': self.db_path,
                'database_size_mb': os.path.getsize(self.db_path) / 1024 / 1024 if os.path.exists(self.db_path) else 0,
                'total_records': db_stats['total_records']
            },
            'performance_metrics': test_results,
            'database_statistics': db_stats,
            'performance_summary': self._calculate_performance_summary(test_results),
            'recommendations': self._generate_database_recommendations(test_results)
        }

        # 保存报告
        self._save_database_report(report)

        return report

    def _get_database_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 表记录数统计
            tables = ['workflows', 'stages', 'tasks', 'execution_logs', 'performance_metrics']
            total_records = 0

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[f'{table}_count'] = count
                total_records += count

            stats['total_records'] = total_records

            # 数据库文件大小
            if os.path.exists(self.db_path):
                stats['database_size_bytes'] = os.path.getsize(self.db_path)
                stats['database_size_mb'] = stats['database_size_bytes'] / 1024 / 1024

        return stats

    def _calculate_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """计算性能摘要"""
        summary = {}

        # 提取数字指标
        for test_name, result in results.items():
            if isinstance(result, DatabaseMetrics):
                summary[test_name] = {
                    'operations_per_second': result.operations_per_second,
                    'avg_response_time': result.avg_response_time,
                    'success_rate': result.successful_operations / result.total_operations if result.total_operations > 0 else 0
                }

        # 计算整体评分
        if summary:
            avg_ops_per_sec = statistics.mean([s['operations_per_second'] for s in summary.values()])
            avg_response_time = statistics.mean([s['avg_response_time'] for s in summary.values()])
            avg_success_rate = statistics.mean([s['success_rate'] for s in summary.values()])

            summary['overall'] = {
                'avg_operations_per_second': avg_ops_per_sec,
                'avg_response_time': avg_response_time,
                'avg_success_rate': avg_success_rate,
                'performance_score': min(100, int(avg_ops_per_sec * 10 + (1 - avg_response_time) * 50 + avg_success_rate * 40))
            }

        return summary

    def _generate_database_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成数据库优化建议"""
        recommendations = []

        # 基于测试结果生成建议
        for test_name, result in results.items():
            if isinstance(result, DatabaseMetrics):
                if result.avg_response_time > 0.1:  # 100ms
                    recommendations.append(f"{test_name}: 响应时间较高，考虑优化查询或添加索引")

                if result.operations_per_second < 100:
                    recommendations.append(f"{test_name}: 吞吐量较低，检查数据库配置和硬件性能")

                if result.failed_operations > 0:
                    recommendations.append(f"{test_name}: 存在失败操作，检查错误处理和数据一致性")

        # 通用建议
        recommendations.extend([
            "定期执行VACUUM操作以优化数据库文件",
            "考虑实现连接池以提高并发性能",
            "监控数据库大小和查询性能趋势",
            "实现数据归档策略以控制数据库增长"
        ])

        return recommendations

    def _save_database_report(self, report: Dict[str, Any]):
        """保存数据库性能报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确保结果目录存在
        results_dir = Path("tests/performance/results")
        results_dir.mkdir(exist_ok=True)

        # 保存JSON报告
        json_filename = results_dir / f"database_performance_report_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        # 生成文本摘要
        text_filename = results_dir / f"database_performance_summary_{timestamp}.txt"
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write("Perfect21 数据库性能测试报告\n")
            f.write("=" * 50 + "\n\n")

            # 测试摘要
            summary = report['test_summary']
            f.write(f"测试日期: {summary['test_date']}\n")
            f.write(f"数据库大小: {summary['database_size_mb']:.2f}MB\n")
            f.write(f"总记录数: {summary['total_records']}\n\n")

            # 性能指标
            perf_summary = report['performance_summary']
            if 'overall' in perf_summary:
                overall = perf_summary['overall']
                f.write("整体性能指标:\n")
                f.write("-" * 20 + "\n")
                f.write(f"平均操作/秒: {overall['avg_operations_per_second']:.1f}\n")
                f.write(f"平均响应时间: {overall['avg_response_time']:.3f}s\n")
                f.write(f"平均成功率: {overall['avg_success_rate']:.1%}\n")
                f.write(f"性能评分: {overall['performance_score']}/100\n\n")

            # 优化建议
            f.write("优化建议:\n")
            f.write("-" * 20 + "\n")
            for i, rec in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")

        print(f"\n📄 数据库性能报告已保存:")
        print(f"  • 详细报告: {json_filename}")
        print(f"  • 摘要报告: {text_filename}")

def main():
    """主函数：运行数据库性能测试"""
    print("🗄️  启动Perfect21数据库性能测试")

    tester = DatabasePerformanceTester()

    try:
        # 运行完整的数据库性能测试
        final_report = tester.run_comprehensive_database_tests()

        print("\n✅ 数据库性能测试完成！")

        # 显示摘要
        if 'performance_summary' in final_report and 'overall' in final_report['performance_summary']:
            overall = final_report['performance_summary']['overall']
            print(f"📊 整体性能评分: {overall['performance_score']}/100")
            print(f"💫 平均操作/秒: {overall['avg_operations_per_second']:.1f}")
            print(f"⏱️  平均响应时间: {overall['avg_response_time']:.3f}s")

        return final_report

    except Exception as e:
        print(f"❌ 数据库性能测试失败: {e}")
        raise

if __name__ == "__main__":
    main()