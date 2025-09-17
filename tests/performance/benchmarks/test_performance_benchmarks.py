#!/usr/bin/env python3
"""
Performance benchmarks for Perfect21
Target: Performance testing and optimization insights
"""

import pytest
import time
import asyncio
import threading
import multiprocessing
import psutil
import os
import json
import statistics
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main.perfect21 import Perfect21Core
from features.parallel_executor import ParallelExecutor
from modules.cache import Cache
from modules.database import Database


class PerformanceMonitor:
    """Monitor system performance during tests"""

    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
        self.initial_cpu_percent = self.process.cpu_percent()
        self.start_time = time.time()

    def get_metrics(self):
        """Get current performance metrics"""
        current_memory = self.process.memory_info().rss
        memory_delta = current_memory - self.initial_memory
        cpu_percent = self.process.cpu_percent()
        elapsed_time = time.time() - self.start_time

        return {
            'memory_usage_mb': current_memory / (1024 * 1024),
            'memory_delta_mb': memory_delta / (1024 * 1024),
            'cpu_percent': cpu_percent,
            'elapsed_time': elapsed_time
        }


@pytest.mark.performance
class TestCorePerformance:
    """Test core component performance"""

    def test_perfect21_core_initialization_performance(self):
        """Test Perfect21Core initialization performance"""
        start_time = time.time()
        monitor = PerformanceMonitor()

        # Initialize core
        core = Perfect21Core()

        end_time = time.time()
        metrics = monitor.get_metrics()

        initialization_time = end_time - start_time

        # Assertions
        assert initialization_time < 2.0  # Should initialize within 2 seconds
        assert metrics['memory_delta_mb'] < 100  # Should not use more than 100MB
        assert metrics['cpu_percent'] < 90  # Should not peg CPU

    def test_agent_loading_performance(self):
        """Test agent loading performance"""
        monitor = PerformanceMonitor()
        core = Perfect21Core()

        start_time = time.time()

        # Load multiple agents
        agent_names = [
            'project-manager', 'business-analyst', 'technical-writer',
            'api-designer', 'backend-architect', 'database-specialist',
            'frontend-specialist', 'test-engineer', 'security-auditor'
        ]

        loaded_agents = []
        for agent_name in agent_names:
            try:
                agent = core.get_agent(agent_name)
                loaded_agents.append(agent)
            except:
                # Some agents might not be available
                pass

        end_time = time.time()
        metrics = monitor.get_metrics()

        loading_time = end_time - start_time
        time_per_agent = loading_time / len(agent_names) if agent_names else 0

        # Assertions
        assert time_per_agent < 0.5  # Less than 500ms per agent
        assert metrics['memory_delta_mb'] < 200  # Reasonable memory usage

    def test_task_execution_performance(self):
        """Test task execution performance"""
        monitor = PerformanceMonitor()

        # Mock agents for consistent performance testing
        mock_agents = {}
        for i in range(10):
            mock_agent = MagicMock()
            mock_agent.execute.return_value = {
                'success': True,
                'output': f'Mock output {i}',
                'execution_time': 0.1
            }
            mock_agents[f'agent_{i}'] = mock_agent

        with patch('main.perfect21.Perfect21Core.get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents.get(name, MagicMock())

            core = Perfect21Core()

            start_time = time.time()

            # Execute multiple tasks
            results = []
            for i in range(50):
                result = core.execute_task(f'agent_{i % 10}', f'Task {i}')
                results.append(result)

            end_time = time.time()
            metrics = monitor.get_metrics()

            execution_time = end_time - start_time
            time_per_task = execution_time / 50

            # Assertions
            assert time_per_task < 0.1  # Less than 100ms per task
            assert len(results) == 50
            assert metrics['memory_delta_mb'] < 50  # Reasonable memory growth

    def test_memory_efficiency(self):
        """Test memory efficiency under load"""
        monitor = PerformanceMonitor()
        core = Perfect21Core()

        memory_samples = []

        # Create and destroy many objects
        for cycle in range(10):
            objects = []

            # Create objects
            for i in range(100):
                obj = {
                    'id': i,
                    'data': 'x' * 1000,  # 1KB string
                    'nested': {'values': list(range(100))}
                }
                objects.append(obj)

            # Sample memory
            memory_samples.append(monitor.get_metrics()['memory_usage_mb'])

            # Cleanup
            del objects

            # Force garbage collection
            import gc
            gc.collect()

        # Memory should not grow significantly over cycles
        memory_growth = memory_samples[-1] - memory_samples[0]
        assert memory_growth < 50  # Less than 50MB growth

        # Memory should be relatively stable
        memory_variance = statistics.variance(memory_samples)
        assert memory_variance < 100  # Low variance indicates stability

    def test_concurrent_access_performance(self):
        """Test performance under concurrent access"""
        core = Perfect21Core()
        results = []
        errors = []

        def worker_task(worker_id):
            try:
                start_time = time.time()
                for i in range(10):
                    # Simulate work
                    time.sleep(0.01)
                    result = f"Worker {worker_id} task {i} completed"
                    results.append(result)
                end_time = time.time()
                return end_time - start_time
            except Exception as e:
                errors.append(str(e))

        # Run concurrent workers
        threads = []
        start_time = time.time()

        for worker_id in range(5):
            thread = threading.Thread(target=worker_task, args=(worker_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Assertions
        assert len(errors) == 0  # No errors should occur
        assert len(results) == 50  # All tasks completed
        assert total_time < 5.0  # Should complete within reasonable time


@pytest.mark.performance
class TestParallelExecutorPerformance:
    """Test parallel executor performance"""

    @pytest.fixture
    def parallel_executor(self):
        """Create parallel executor for testing"""
        return ParallelExecutor(max_workers=4)

    def test_parallel_vs_sequential_performance(self, parallel_executor):
        """Compare parallel vs sequential execution performance"""
        def mock_task(task_id):
            # Simulate work
            time.sleep(0.1)
            return f"Task {task_id} completed"

        tasks = [('task', i) for i in range(20)]

        # Sequential execution
        start_time = time.time()
        sequential_results = []
        for task_type, task_id in tasks:
            result = mock_task(task_id)
            sequential_results.append(result)
        sequential_time = time.time() - start_time

        # Parallel execution
        start_time = time.time()
        parallel_results = parallel_executor.execute_parallel(
            [(mock_task, (task_id,)) for _, task_id in tasks]
        )
        parallel_time = time.time() - start_time

        # Assertions
        assert len(parallel_results) == len(sequential_results)
        assert parallel_time < sequential_time * 0.8  # At least 20% faster
        assert parallel_time < sequential_time / 2  # Should be significantly faster

    def test_parallel_executor_scalability(self, parallel_executor):
        """Test parallel executor scalability"""
        def cpu_intensive_task(n):
            # CPU intensive task
            result = 0
            for i in range(n * 1000):
                result += i ** 2
            return result

        # Test different task counts
        task_counts = [1, 5, 10, 20, 50]
        execution_times = []

        for task_count in task_counts:
            tasks = [(cpu_intensive_task, (100,)) for _ in range(task_count)]

            start_time = time.time()
            results = parallel_executor.execute_parallel(tasks)
            execution_time = time.time() - start_time

            execution_times.append(execution_time)

            assert len(results) == task_count

        # Execution time should scale sub-linearly (due to parallelization)
        # Time for 50 tasks should be less than 50x time for 1 task
        time_ratio = execution_times[-1] / execution_times[0]
        task_ratio = task_counts[-1] / task_counts[0]

        assert time_ratio < task_ratio * 0.7  # Should be significantly more efficient

    def test_parallel_executor_memory_usage(self, parallel_executor):
        """Test parallel executor memory usage"""
        monitor = PerformanceMonitor()

        def memory_intensive_task(size):
            # Create large data structure
            data = ['x' * 1000 for _ in range(size)]
            return len(data)

        initial_memory = monitor.get_metrics()['memory_usage_mb']

        # Execute memory intensive tasks
        tasks = [(memory_intensive_task, (100,)) for _ in range(10)]
        results = parallel_executor.execute_parallel(tasks)

        peak_memory = monitor.get_metrics()['memory_usage_mb']
        memory_delta = peak_memory - initial_memory

        # Clean up and measure final memory
        del results
        import gc
        gc.collect()

        final_memory = monitor.get_metrics()['memory_usage_mb']
        memory_cleanup = peak_memory - final_memory

        # Assertions
        assert memory_delta < 500  # Should not use excessive memory
        assert memory_cleanup > memory_delta * 0.5  # Should clean up at least 50%


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database performance"""

    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database"""
        db_path = tmp_path / "test_performance.db"
        db = Database(str(db_path))
        db.initialize()
        return db

    def test_database_insert_performance(self, test_db):
        """Test database insert performance"""
        monitor = PerformanceMonitor()

        # Prepare test data
        test_records = []
        for i in range(1000):
            test_records.append({
                'id': i,
                'name': f'Record {i}',
                'data': f'Data for record {i}' * 10,
                'value': i * 1.5
            })

        start_time = time.time()

        # Insert records
        for record in test_records:
            test_db.insert('test_table', record)

        insert_time = time.time() - start_time
        metrics = monitor.get_metrics()

        # Assertions
        insert_time_per_record = insert_time / len(test_records)
        assert insert_time_per_record < 0.01  # Less than 10ms per record
        assert insert_time < 10.0  # Total insert time under 10 seconds

    def test_database_query_performance(self, test_db):
        """Test database query performance"""
        # Setup test data
        for i in range(1000):
            test_db.insert('test_table', {
                'id': i,
                'category': f'category_{i % 10}',
                'value': i * 2,
                'active': i % 2 == 0
            })

        # Test different query types
        query_tests = [
            ('SELECT * FROM test_table LIMIT 100', 'simple_select'),
            ('SELECT * FROM test_table WHERE category = "category_5"', 'filtered_select'),
            ('SELECT category, COUNT(*) FROM test_table GROUP BY category', 'aggregation'),
            ('SELECT * FROM test_table WHERE value > 500 AND active = 1', 'complex_filter')
        ]

        for query, test_name in query_tests:
            start_time = time.time()
            results = test_db.execute_query(query)
            query_time = time.time() - start_time

            # Queries should execute quickly
            assert query_time < 1.0  # Less than 1 second
            assert results is not None

    def test_database_bulk_operations(self, test_db):
        """Test database bulk operations performance"""
        monitor = PerformanceMonitor()

        # Prepare bulk data
        bulk_data = []
        for i in range(5000):
            bulk_data.append({
                'id': i,
                'bulk_field': f'bulk_value_{i}',
                'timestamp': time.time()
            })

        start_time = time.time()

        # Bulk insert
        test_db.bulk_insert('bulk_test_table', bulk_data)

        bulk_time = time.time() - start_time
        metrics = monitor.get_metrics()

        # Bulk operations should be efficient
        time_per_record = bulk_time / len(bulk_data)
        assert time_per_record < 0.001  # Less than 1ms per record in bulk
        assert bulk_time < 5.0  # Total bulk time under 5 seconds


@pytest.mark.performance
class TestCachePerformance:
    """Test cache performance"""

    @pytest.fixture
    def cache(self):
        """Create cache for testing"""
        return Cache(max_size=10000)

    def test_cache_read_write_performance(self, cache):
        """Test cache read/write performance"""
        monitor = PerformanceMonitor()

        # Test data
        test_data = {f'key_{i}': f'value_{i}' * 100 for i in range(1000)}

        # Write performance test
        start_time = time.time()
        for key, value in test_data.items():
            cache.set(key, value)
        write_time = time.time() - start_time

        # Read performance test
        start_time = time.time()
        for key in test_data.keys():
            value = cache.get(key)
            assert value is not None
        read_time = time.time() - start_time

        metrics = monitor.get_metrics()

        # Assertions
        write_time_per_item = write_time / len(test_data)
        read_time_per_item = read_time / len(test_data)

        assert write_time_per_item < 0.001  # Less than 1ms per write
        assert read_time_per_item < 0.0005  # Less than 0.5ms per read

    def test_cache_eviction_performance(self, cache):
        """Test cache eviction performance"""
        # Fill cache beyond capacity
        for i in range(15000):  # More than max_size
            cache.set(f'key_{i}', f'value_{i}' * 100)

        # Cache should handle eviction efficiently
        assert cache.size() <= cache.max_size
        assert cache.size() > 0

    def test_cache_concurrent_access(self, cache):
        """Test cache performance under concurrent access"""
        errors = []
        results = []

        def cache_worker(worker_id):
            try:
                for i in range(100):
                    key = f'worker_{worker_id}_key_{i}'
                    value = f'worker_{worker_id}_value_{i}'

                    # Write
                    cache.set(key, value)

                    # Read
                    retrieved = cache.get(key)
                    if retrieved == value:
                        results.append(f'{worker_id}_{i}_success')

            except Exception as e:
                errors.append(str(e))

        # Run concurrent workers
        threads = []
        start_time = time.time()

        for worker_id in range(10):
            thread = threading.Thread(target=cache_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        concurrent_time = time.time() - start_time

        # Assertions
        assert len(errors) == 0  # No errors should occur
        assert len(results) == 1000  # All operations should succeed
        assert concurrent_time < 5.0  # Should complete within reasonable time


@pytest.mark.performance
class TestAsyncPerformance:
    """Test async operation performance"""

    @pytest.mark.asyncio
    async def test_async_task_execution_performance(self):
        """Test async task execution performance"""
        async def async_task(task_id):
            await asyncio.sleep(0.01)  # Simulate async work
            return f'Async task {task_id} completed'

        start_time = time.time()

        # Execute many async tasks concurrently
        tasks = [async_task(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        execution_time = time.time() - start_time

        # Assertions
        assert len(results) == 100
        assert execution_time < 2.0  # Should complete much faster than sequential
        assert all('completed' in result for result in results)

    @pytest.mark.asyncio
    async def test_async_vs_sync_performance(self):
        """Compare async vs sync performance"""
        def sync_io_task(task_id):
            time.sleep(0.01)  # Simulate I/O
            return f'Sync task {task_id} completed'

        async def async_io_task(task_id):
            await asyncio.sleep(0.01)  # Simulate async I/O
            return f'Async task {task_id} completed'

        task_count = 50

        # Sync execution
        start_time = time.time()
        sync_results = [sync_io_task(i) for i in range(task_count)]
        sync_time = time.time() - start_time

        # Async execution
        start_time = time.time()
        async_tasks = [async_io_task(i) for i in range(task_count)]
        async_results = await asyncio.gather(*async_tasks)
        async_time = time.time() - start_time

        # Assertions
        assert len(sync_results) == len(async_results)
        assert async_time < sync_time * 0.3  # Async should be much faster

    @pytest.mark.asyncio
    async def test_async_memory_efficiency(self):
        """Test async memory efficiency"""
        monitor = PerformanceMonitor()
        initial_memory = monitor.get_metrics()['memory_usage_mb']

        async def memory_task(size):
            data = ['x' * 1000 for _ in range(size)]
            await asyncio.sleep(0.001)
            return len(data)

        # Create many concurrent async tasks
        tasks = [memory_task(10) for _ in range(1000)]
        results = await asyncio.gather(*tasks)

        peak_memory = monitor.get_metrics()['memory_usage_mb']
        memory_delta = peak_memory - initial_memory

        # Cleanup
        del results
        del tasks
        import gc
        gc.collect()

        final_memory = monitor.get_metrics()['memory_usage_mb']

        # Assertions
        assert len(results) == 1000
        assert memory_delta < 200  # Should not use excessive memory
        assert final_memory < peak_memory  # Should clean up memory


@pytest.mark.performance
class TestLoadTesting:
    """Load testing scenarios"""

    def test_system_under_sustained_load(self):
        """Test system performance under sustained load"""
        monitor = PerformanceMonitor()
        core = Perfect21Core()

        # Mock agent for consistent testing
        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            'success': True,
            'output': 'Load test task completed',
            'execution_time': 0.05
        }

        with patch.object(core, 'get_agent', return_value=mock_agent):
            start_time = time.time()
            successful_tasks = 0
            failed_tasks = 0

            # Run sustained load for a period
            while time.time() - start_time < 10:  # 10 seconds of load
                try:
                    result = core.execute_task('test_agent', 'Load test task')
                    if result.get('success'):
                        successful_tasks += 1
                    else:
                        failed_tasks += 1
                except Exception:
                    failed_tasks += 1

                # Small delay to prevent overwhelming
                time.sleep(0.01)

            total_time = time.time() - start_time
            final_metrics = monitor.get_metrics()

            # Calculate throughput
            total_tasks = successful_tasks + failed_tasks
            throughput = total_tasks / total_time

            # Assertions
            assert successful_tasks > 0
            assert throughput > 10  # At least 10 tasks per second
            assert successful_tasks / total_tasks > 0.95  # 95% success rate
            assert final_metrics['memory_delta_mb'] < 100  # Controlled memory growth

    def test_burst_load_handling(self):
        """Test system handling of burst loads"""
        monitor = PerformanceMonitor()

        def burst_worker(worker_id, task_count):
            results = []
            for i in range(task_count):
                # Simulate burst of work
                result = f'Burst worker {worker_id} task {i}'
                results.append(result)
                time.sleep(0.001)  # Minimal delay
            return results

        # Create burst load
        start_time = time.time()
        threads = []

        for worker_id in range(20):  # 20 concurrent workers
            thread = threading.Thread(
                target=burst_worker,
                args=(worker_id, 25)  # 25 tasks each
            )
            threads.append(thread)
            thread.start()

        # Wait for burst to complete
        for thread in threads:
            thread.join()

        burst_time = time.time() - start_time
        metrics = monitor.get_metrics()

        # Assertions
        assert burst_time < 5.0  # Should handle burst within 5 seconds
        assert metrics['memory_delta_mb'] < 150  # Reasonable memory usage
        assert metrics['cpu_percent'] < 95  # Should not max out CPU

    def test_resource_cleanup_under_load(self):
        """Test resource cleanup under load"""
        import gc
        import weakref

        created_objects = []
        weak_refs = []

        # Create and destroy objects under load
        for cycle in range(50):
            # Create objects
            objects = []
            for i in range(100):
                obj = {
                    'id': i,
                    'data': 'x' * 1000,
                    'cycle': cycle
                }
                objects.append(obj)
                weak_refs.append(weakref.ref(obj))

            created_objects.append(objects)

            # Periodically cleanup
            if cycle % 10 == 0:
                # Remove old objects
                if len(created_objects) > 10:
                    del created_objects[0]
                    gc.collect()

        # Force final cleanup
        del created_objects
        gc.collect()

        # Check if objects were properly cleaned up
        alive_objects = sum(1 for ref in weak_refs if ref() is not None)
        total_objects = len(weak_refs)
        cleanup_ratio = 1 - (alive_objects / total_objects)

        # Most objects should be cleaned up
        assert cleanup_ratio > 0.8  # At least 80% cleanup


if __name__ == "__main__":
    pytest.main([__file__, "-v"])