"""
🚀 Authentication Load & Performance Tests
==========================================

Comprehensive load testing and performance benchmarking for authentication system
Tests system behavior under various stress conditions - like performance engineering

Author: Performance Engineering Agent
"""

import pytest
import asyncio
import time
import statistics
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import concurrent.futures
import random
import psutil

from test_fixtures import TestDataGenerator, UserRole, TestScenario


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self):
        self.response_times = []
        self.throughput_data = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.cpu_samples = []
        self.memory_samples = []
        self.lock = threading.Lock()

    def record_operation(self, operation_time: float, success: bool):
        """Record a single operation"""
        with self.lock:
            self.response_times.append(operation_time * 1000)  # Convert to ms
            if success:
                self.success_count += 1
            else:
                self.error_count += 1

    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.end_time = time.time()

    def sample_system_resources(self):
        """Sample current system resource usage"""
        with self.lock:
            self.cpu_samples.append(psutil.cpu_percent(interval=0.1))
            memory_info = psutil.virtual_memory()
            self.memory_samples.append(memory_info.used / 1024 / 1024)  # MB

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics"""
        if not self.response_times:
            return {}

        total_operations = self.success_count + self.error_count
        duration = (
            (self.end_time - self.start_time)
            if self.end_time and self.start_time
            else 0
        )

        response_stats = {
            "min_ms": min(self.response_times),
            "max_ms": max(self.response_times),
            "mean_ms": statistics.mean(self.response_times),
            "median_ms": statistics.median(self.response_times),
            "std_dev_ms": statistics.stdev(self.response_times)
            if len(self.response_times) > 1
            else 0,
            "p95_ms": self._percentile(self.response_times, 95),
            "p99_ms": self._percentile(self.response_times, 99),
        }

        throughput_stats = {
            "total_operations": total_operations,
            "successful_operations": self.success_count,
            "failed_operations": self.error_count,
            "success_rate_percent": (self.success_count / total_operations * 100)
            if total_operations > 0
            else 0,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "duration_seconds": duration,
        }

        resource_stats = {
            "avg_cpu_percent": statistics.mean(self.cpu_samples)
            if self.cpu_samples
            else 0,
            "max_cpu_percent": max(self.cpu_samples) if self.cpu_samples else 0,
            "avg_memory_mb": statistics.mean(self.memory_samples)
            if self.memory_samples
            else 0,
            "max_memory_mb": max(self.memory_samples) if self.memory_samples else 0,
        }

        return {
            "response_times": response_stats,
            "throughput": throughput_stats,
            "system_resources": resource_stats,
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def print_summary(self, test_name: str):
        """Print performance summary"""
        stats = self.get_statistics()
        if not stats:
            # print(f"❌ {test_name}: No data collected")
            return

    # print(f"\n📊 {test_name} Performance Summary")
    # print("=" * 60)
    # print(f"Total Operations: {stats['throughput']['total_operations']}")
    # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
    # print(f"Duration: {stats['throughput']['duration_seconds']:.2f}s")
    # print(f"Throughput: {stats['throughput']['operations_per_second']:.1f} ops/sec")
    # print()
    # print("Response Times:")
    # print(f"  Average: {stats['response_times']['mean_ms']:.1f}ms")
    # print(f"  Median: {stats['response_times']['median_ms']:.1f}ms")
    # print(f"  P95: {stats['response_times']['p95_ms']:.1f}ms")
    # print(f"  P99: {stats['response_times']['p99_ms']:.1f}ms")
    # print(f"  Min/Max: {stats['response_times']['min_ms']:.1f}ms / {stats['response_times']['max_ms']:.1f}ms")
    # print()
    # print("System Resources:")
    # print(f"  Avg CPU: {stats['system_resources']['avg_cpu_percent']:.1f}%")
    # print(f"  Max CPU: {stats['system_resources']['max_cpu_percent']:.1f}%")
    # print(f"  Avg Memory: {stats['system_resources']['avg_memory_mb']:.1f}MB")
    # print(f"  Max Memory: {stats['system_resources']['max_memory_mb']:.1f}MB")
    # print("=" * 60)


class TestRegistrationPerformance:
    """Test user registration performance under various loads"""

    @pytest.mark.asyncio
    async def test_concurrent_registration_light_load(
        self, integrated_test_environment
    ):
        """⚡ Test concurrent user registration - Light Load (50 users)"""
        await self._test_concurrent_registrations(
            integrated_test_environment, 50, "Light Load"
        )

    @pytest.mark.asyncio
    async def test_concurrent_registration_medium_load(
        self, integrated_test_environment
    ):
        """⚡⚡ Test concurrent user registration - Medium Load (200 users)"""
        await self._test_concurrent_registrations(
            integrated_test_environment, 200, "Medium Load"
        )

    @pytest.mark.asyncio
    async def test_concurrent_registration_heavy_load(
        self, integrated_test_environment
    ):
        """⚡⚡⚡ Test concurrent user registration - Heavy Load (500 users)"""
        await self._test_concurrent_registrations(
            integrated_test_environment, 500, "Heavy Load"
        )

    async def _test_concurrent_registrations(
        self, env, user_count: int, load_type: str
    ):
        """Helper method for concurrent registration testing"""
        metrics = PerformanceMetrics()

        # Generate test users
        users = TestDataGenerator.generate_users_batch(
            user_count, UserRole.USER, TestScenario.HAPPY_PATH
        )

        async def register_single_user(user_index, user):
            """Register a single user and measure performance"""
            start_time = time.time()
            try:
                result = await env.register_user(user.to_dict())
                end_time = time.time()
                metrics.record_operation(
                    end_time - start_time, result.get("success", False)
                )

                # Sample system resources periodically
                if user_index % 10 == 0:
                    metrics.sample_system_resources()

                return result
            except Exception as e:
                end_time = time.time()
                metrics.record_operation(end_time - start_time, False)
                return {"success": False, "error": str(e)}

        # Execute concurrent registrations
        metrics.start_monitoring()

        # Use semaphore to limit concurrency and prevent overwhelming the system
        semaphore = asyncio.Semaphore(50)  # Max 50 concurrent operations

        async def register_with_semaphore(index, user):
            async with semaphore:
                return await register_single_user(index, user)

        tasks = [register_with_semaphore(i, user) for i, user in enumerate(users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics.stop_monitoring()

        # Analyze results
        successful_registrations = sum(
            1
            for result in results
            if isinstance(result, dict) and result.get("success", False)
        )

        # Performance assertions
        stats = metrics.get_statistics()
        assert successful_registrations >= user_count * 0.95  # 95% success rate
        assert stats["response_times"]["p95_ms"] < 2000  # P95 under 2 seconds
        assert stats["throughput"]["operations_per_second"] > 10  # At least 10 ops/sec

        # Print detailed metrics
        metrics.print_summary(f"Registration {load_type}")

    @pytest.mark.asyncio
    async def test_registration_with_email_delivery_load(
        self, integrated_test_environment
    ):
        """📧 Test registration performance including email delivery simulation"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        user_count = 100
        users = TestDataGenerator.generate_users_batch(
            user_count, UserRole.USER, TestScenario.HAPPY_PATH
        )

        async def register_user_with_email_delay(user):
            """Registration with simulated email delivery delay"""
            start_time = time.time()

            # Register user
            result = await env.register_user(user.to_dict())

            # Simulate email delivery processing time
            await asyncio.sleep(random.uniform(0.1, 0.3))  # 100-300ms delay

            end_time = time.time()
            metrics.record_operation(
                end_time - start_time, result.get("success", False)
            )
            return result

        metrics.start_monitoring()

        # Execute with limited concurrency to simulate real-world email constraints
        semaphore = asyncio.Semaphore(20)

        async def register_with_limit(user):
            async with semaphore:
                return await register_user_with_email_delay(user)

        tasks = [register_with_limit(user) for user in users]
        results = await asyncio.gather(*tasks)

        metrics.stop_monitoring()

        # Verify email delivery impact
        stats = metrics.get_statistics()
        successful_registrations = sum(1 for r in results if r.get("success", False))

        assert successful_registrations >= user_count * 0.90  # 90% success rate
        assert stats["response_times"]["mean_ms"] < 1000  # Average under 1 second
        assert stats["throughput"]["operations_per_second"] > 5  # At least 5 ops/sec

        metrics.print_summary("Registration with Email Delivery")


class TestLoginPerformance:
    """Test login performance under various loads"""

    @pytest.mark.asyncio
    async def test_concurrent_login_burst(self, integrated_test_environment):
        """🔐 Test concurrent login burst performance"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Setup: Create users first
        user_count = 100
        users = TestDataGenerator.generate_users_batch(
            user_count, UserRole.USER, TestScenario.HAPPY_PATH
        )

        # Pre-register all users
        for user in users:
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})

        async def perform_login(user):
            """Perform login and measure time"""
            start_time = time.time()
            try:
                result = await env.login_user(user.email, user.password)
                end_time = time.time()
                metrics.record_operation(
                    end_time - start_time, result.get("success", False)
                )
                return result
            except Exception as e:
                end_time = time.time()
                metrics.record_operation(end_time - start_time, False)
                return {"success": False, "error": str(e)}

        # Execute burst login test
        metrics.start_monitoring()

        login_tasks = [perform_login(user) for user in users]
        results = await asyncio.gather(*login_tasks, return_exceptions=True)

        metrics.stop_monitoring()

        # Analyze results
        successful_logins = sum(
            1
            for result in results
            if isinstance(result, dict) and result.get("success", False)
        )

        stats = metrics.get_statistics()
        assert successful_logins >= user_count * 0.95  # 95% success rate
        assert stats["response_times"]["p95_ms"] < 1000  # P95 under 1 second
        assert (
            stats["throughput"]["operations_per_second"] > 20
        )  # At least 20 logins/sec

        metrics.print_summary("Concurrent Login Burst")

    @pytest.mark.asyncio
    async def test_sustained_login_load(self, integrated_test_environment):
        """🔄 Test sustained login load over time"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Setup users
        users = TestDataGenerator.generate_users_batch(
            50, UserRole.USER, TestScenario.HAPPY_PATH
        )
        for user in users:
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})

        test_duration = 30  # 30 seconds
        target_rps = 10  # Target 10 requests per second

        async def sustained_login_worker():
            """Worker that performs sustained login operations"""
            end_time = time.time() + test_duration

            while time.time() < end_time:
                user = random.choice(users)
                start_time = time.time()

                try:
                    result = await env.login_user(user.email, user.password)
                    operation_time = time.time() - start_time
                    metrics.record_operation(
                        operation_time, result.get("success", False)
                    )

                    # Sample resources periodically
                    if random.random() < 0.1:  # 10% chance
                        metrics.sample_system_resources()

                except Exception as e:
                    operation_time = time.time() - start_time
                    metrics.record_operation(operation_time, False)

                # Control rate
                await asyncio.sleep(1.0 / target_rps)

        # Start sustained load test
        metrics.start_monitoring()

        # Run multiple workers for concurrent load
        workers = [sustained_login_worker() for _ in range(5)]
        await asyncio.gather(*workers)

        metrics.stop_monitoring()

        # Verify sustained performance
        stats = metrics.get_statistics()
        actual_rps = stats["throughput"]["operations_per_second"]

        assert stats["throughput"]["success_rate_percent"] > 95  # 95% success rate
        assert actual_rps > target_rps * 0.8  # At least 80% of target RPS
        assert stats["response_times"]["p95_ms"] < 500  # P95 under 500ms

        metrics.print_summary("Sustained Login Load")

    @pytest.mark.asyncio
    async def test_login_with_mfa_performance(
        self, integrated_test_environment, mock_sms_service
    ):
        """📱 Test login performance with MFA enabled"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Setup MFA-enabled users
        users = TestDataGenerator.generate_users_batch(
            20, UserRole.USER, TestScenario.HAPPY_PATH
        )
        for user in users:
            user_dict = user.to_dict()
            user_dict["phone"] = f"+1{random.randint(1000000000, 9999999999)}"
            await env.register_user(user_dict)
            await env.database.update_user(
                user.email,
                {"is_verified": True, "mfa_enabled": True, "phone": user_dict["phone"]},
            )

        async def mfa_login_flow(user):
            """Complete MFA login flow"""
            start_time = time.time()

            try:
                # Step 1: Initial login
                login_result = await env.login_user(user.email, user.password)
                if not login_result.get("success"):
                    return {"success": False, "step": "initial_login"}

                # Step 2: MFA challenge
                user_data = await env.database.get_user(user.email)
                phone = user_data.get("phone")
                mfa_code = f"{random.randint(100000, 999999)}"

                await mock_sms_service.send_verification_code(phone, mfa_code)

                # Step 3: MFA verification
                mfa_result = mock_sms_service.verify_code(phone, mfa_code)
                if not mfa_result.get("valid"):
                    return {"success": False, "step": "mfa_verification"}

                # Step 4: Final token generation
                final_token = env.jwt_service.generate_token(
                    user_id=str(hash(user.email)),
                    email=user.email,
                    permissions=["read", "write", "mfa_verified"],
                )

                end_time = time.time()
                metrics.record_operation(end_time - start_time, True)
                return {"success": True, "token": final_token}

            except Exception as e:
                end_time = time.time()
                metrics.record_operation(end_time - start_time, False)
                return {"success": False, "error": str(e)}

        # Execute MFA login test
        metrics.start_monitoring()

        mfa_tasks = [mfa_login_flow(user) for user in users]
        results = await asyncio.gather(*mfa_tasks, return_exceptions=True)

        metrics.stop_monitoring()

        # Analyze MFA performance
        successful_mfa_logins = sum(
            1
            for result in results
            if isinstance(result, dict) and result.get("success", False)
        )

        stats = metrics.get_statistics()
        assert successful_mfa_logins >= len(users) * 0.90  # 90% success rate for MFA
        assert (
            stats["response_times"]["p95_ms"] < 3000
        )  # P95 under 3 seconds (MFA adds overhead)

        metrics.print_summary("MFA Login Performance")


class TestTokenValidationPerformance:
    """Test JWT token validation performance"""

    @pytest.mark.asyncio
    async def test_high_frequency_token_validation(self, integrated_test_environment):
        """🎯 Test high-frequency token validation performance"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Setup: Create user and get token
        user = TestDataGenerator.generate_user()
        await env.register_user(user.to_dict())
        await env.database.update_user(user.email, {"is_verified": True})

        login_result = await env.login_user(user.email, user.password)
        token = login_result["token"]

        validation_count = 1000

        async def validate_token_batch():
            """Validate token in rapid succession"""
            for i in range(validation_count):
                start_time = time.time()

                try:
                    result = await env.verify_token(token)
                    end_time = time.time()
                    metrics.record_operation(
                        end_time - start_time, result.get("valid", False)
                    )

                    # Sample resources every 100 validations
                    if i % 100 == 0:
                        metrics.sample_system_resources()

                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(end_time - start_time, False)

        metrics.start_monitoring()
        await validate_token_batch()
        metrics.stop_monitoring()

        # Verify validation performance
        stats = metrics.get_statistics()
        assert (
            stats["throughput"]["success_rate_percent"] == 100
        )  # All validations should succeed
        assert stats["response_times"]["p95_ms"] < 10  # P95 under 10ms for validation
        assert (
            stats["throughput"]["operations_per_second"] > 100
        )  # At least 100 validations/sec

        metrics.print_summary("High-Frequency Token Validation")

    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self, integrated_test_environment):
        """🔄 Test concurrent token validation from multiple sessions"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Setup: Create multiple users and tokens
        users = TestDataGenerator.generate_users_batch(
            50, UserRole.USER, TestScenario.HAPPY_PATH
        )
        tokens = []

        for user in users:
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})
            login_result = await env.login_user(user.email, user.password)
            tokens.append(login_result["token"])

        validations_per_token = 20

        async def validate_token_concurrently(token):
            """Validate single token multiple times"""
            for _ in range(validations_per_token):
                start_time = time.time()

                try:
                    result = await env.verify_token(token)
                    end_time = time.time()
                    metrics.record_operation(
                        end_time - start_time, result.get("valid", False)
                    )
                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(end_time - start_time, False)

                await asyncio.sleep(0.01)  # Small delay between validations

        # Execute concurrent validation
        metrics.start_monitoring()

        validation_tasks = [validate_token_concurrently(token) for token in tokens]
        await asyncio.gather(*validation_tasks)

        metrics.stop_monitoring()

        # Verify concurrent validation performance
        expected_total_validations = len(tokens) * validations_per_token
        stats = metrics.get_statistics()

        assert stats["throughput"]["total_operations"] == expected_total_validations
        assert stats["throughput"]["success_rate_percent"] > 98  # 98% success rate
        assert stats["response_times"]["p95_ms"] < 50  # P95 under 50ms

        metrics.print_summary("Concurrent Token Validation")


class TestStressScenarios:
    """Test authentication system under extreme stress"""

    @pytest.mark.asyncio
    async def test_registration_flood_attack_simulation(
        self, integrated_test_environment
    ):
        """🌊 Simulate flood attack on registration endpoint"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Simulate flood attack with many invalid registrations
        attack_requests = 200
        invalid_users = []

        for i in range(attack_requests):
            # Generate various types of invalid data
            if i % 4 == 0:
                # Invalid email
                invalid_users.append(
                    {"email": f"invalid_email_{i}", "password": "ValidPass123!"}
                )
            elif i % 4 == 1:
                # Weak password
                invalid_users.append(
                    {"email": f"user{i}@example.com", "password": "weak"}
                )
            elif i % 4 == 2:
                # SQL injection attempt
                invalid_users.append(
                    {
                        "email": f"user{i}' OR '1'='1' --@example.com",
                        "password": "ValidPass123!",
                    }
                )
            else:
                # XSS attempt
                invalid_users.append(
                    {
                        "email": f"user{i}@example.com",
                        "password": "<script>alert('xss')</script>",
                    }
                )

        async def flood_registration(user_data):
            """Single flood request"""
            start_time = time.time()

            try:
                result = await env.register_user(user_data)
                end_time = time.time()
                # For flood attack, we expect failures
                metrics.record_operation(
                    end_time - start_time, not result.get("success", True)
                )
            except Exception:
                end_time = time.time()
                metrics.record_operation(
                    end_time - start_time, True
                )  # Exception is expected

        # Execute flood attack
        metrics.start_monitoring()

        flood_tasks = [flood_registration(user_data) for user_data in invalid_users]
        await asyncio.gather(*flood_tasks, return_exceptions=True)

        metrics.stop_monitoring()

        # Verify system resilience
        stats = metrics.get_statistics()
        # System should handle flood gracefully
        assert (
            stats["response_times"]["p95_ms"] < 5000
        )  # P95 under 5 seconds even under attack
        assert (
            stats["throughput"]["operations_per_second"] > 10
        )  # Maintain some throughput

        metrics.print_summary("Registration Flood Attack Simulation")

    @pytest.mark.asyncio
    async def test_memory_pressure_scenario(self, integrated_test_environment):
        """💾 Test system behavior under memory pressure"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Create many concurrent long-lived sessions
        session_count = 100
        users = TestDataGenerator.generate_users_batch(
            session_count, UserRole.USER, TestScenario.HAPPY_PATH
        )

        # Create all users
        for user in users:
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})

        async def create_long_lived_session(user):
            """Create session and perform multiple operations"""
            start_time = time.time()

            try:
                # Login
                login_result = await env.login_user(user.email, user.password)
                if not login_result.get("success"):
                    return False

                token = login_result["token"]

                # Perform multiple token validations (simulating API usage)
                for i in range(10):
                    validation_result = await env.verify_token(token)
                    if not validation_result.get("valid"):
                        return False

                    await asyncio.sleep(0.1)  # Small delay

                end_time = time.time()
                metrics.record_operation(end_time - start_time, True)
                return True

            except Exception:
                end_time = time.time()
                metrics.record_operation(end_time - start_time, False)
                return False

        # Monitor memory during test
        async def monitor_memory():
            """Monitor memory usage during test"""
            while metrics.start_time and not metrics.end_time:
                metrics.sample_system_resources()
                await asyncio.sleep(1)

        # Execute memory pressure test
        metrics.start_monitoring()

        # Start memory monitoring
        memory_monitor_task = asyncio.create_task(monitor_memory())

        # Create many concurrent sessions
        session_tasks = [create_long_lived_session(user) for user in users]
        results = await asyncio.gather(*session_tasks, return_exceptions=True)

        metrics.stop_monitoring()
        memory_monitor_task.cancel()

        # Analyze memory pressure impact
        successful_sessions = sum(1 for r in results if r is True)
        stats = metrics.get_statistics()

        assert successful_sessions >= session_count * 0.85  # 85% success under pressure
        assert (
            stats["system_resources"]["max_memory_mb"] < 1024
        )  # Keep memory under 1GB

        metrics.print_summary("Memory Pressure Scenario")

    @pytest.mark.asyncio
    async def test_cascading_failure_recovery(self, integrated_test_environment):
        """⚡ Test recovery from cascading failures"""
        env = integrated_test_environment
        metrics = PerformanceMetrics()

        # Setup users
        users = TestDataGenerator.generate_users_batch(
            50, UserRole.USER, TestScenario.HAPPY_PATH
        )
        for user in users:
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})

        # Simulate cascading failures
        failure_duration = 10  # 10 seconds of failures
        recovery_duration = 20  # 20 seconds of recovery

        async def simulate_service_degradation():
            """Simulate progressive service degradation"""
            test_start = time.time()

            while time.time() - test_start < failure_duration + recovery_duration:
                current_time = time.time() - test_start
                user = random.choice(users)

                start_op_time = time.time()

                try:
                    # Simulate different failure rates over time
                    if current_time < failure_duration:
                        # During failure period - high failure rate
                        if random.random() < 0.7:  # 70% failure rate
                            raise Exception("Simulated service failure")

                    # Normal operation or recovery
                    result = await env.login_user(user.email, user.password)
                    end_op_time = time.time()
                    metrics.record_operation(
                        end_op_time - start_op_time, result.get("success", False)
                    )

                except Exception:
                    end_op_time = time.time()
                    metrics.record_operation(end_op_time - start_op_time, False)

                await asyncio.sleep(0.2)  # 200ms between operations

        # Execute cascading failure test
        metrics.start_monitoring()

        # Run multiple workers to simulate load during failures
        workers = [simulate_service_degradation() for _ in range(5)]
        await asyncio.gather(*workers, return_exceptions=True)

        metrics.stop_monitoring()

        # Verify recovery behavior
        stats = metrics.get_statistics()
        # Overall success rate should be reasonable despite failures
        assert (
            stats["throughput"]["success_rate_percent"] > 40
        )  # At least 40% success during degradation
        assert (
            stats["response_times"]["p95_ms"] < 10000
        )  # P95 under 10 seconds even during failures

        metrics.print_summary("Cascading Failure Recovery")


if __name__ == "__main__":
    # print("🚀 Running Load & Performance Tests")
    # print("=" * 50)

    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            "--durations=15",
            "-m",
            "not slow",  # Skip slow tests by default
        ]
    )
