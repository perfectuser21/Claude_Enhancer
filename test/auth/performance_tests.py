"""
⚡ Authentication Performance Tests
===================================

Load testing and performance benchmarking for authentication system
Tests system behavior under various load conditions - like stress-testing infrastructure

Author: Performance Engineering Agent
"""

import pytest
import asyncio
import aiohttp
import time
import statistics
import psutil
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import json
import random
import string


# Performance Test Configuration
class PerformanceConfig:
    """Configuration for performance tests"""

    # Load Test Parameters
    CONCURRENT_USERS_LIGHT = 50  # Light load
    CONCURRENT_USERS_MEDIUM = 200  # Medium load
    CONCURRENT_USERS_HEAVY = 500  # Heavy load
    CONCURRENT_USERS_STRESS = 1000  # Stress test

    # Performance Thresholds (milliseconds)
    REGISTRATION_THRESHOLD_MS = 1000  # Registration should complete within 1s
    LOGIN_THRESHOLD_MS = 500  # Login should complete within 500ms
    TOKEN_VALIDATION_THRESHOLD_MS = 100  # Token validation within 100ms
    PROTECTED_ENDPOINT_THRESHOLD_MS = 200  # Protected endpoints within 200ms

    # Throughput Targets
    MIN_REQUESTS_PER_SECOND = 100  # Minimum RPS
    TARGET_REQUESTS_PER_SECOND = 500  # Target RPS

    # Resource Limits
    MAX_CPU_USAGE_PERCENT = 80  # Maximum CPU usage
    MAX_MEMORY_USAGE_MB = 512  # Maximum memory usage

    # Test Duration
    LOAD_TEST_DURATION_SECONDS = 60  # Load test duration
    STRESS_TEST_DURATION_SECONDS = 120  # Stress test duration


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.cpu_usage = []
        self.memory_usage = []

    def add_response_time(self, response_time_ms: float, success: bool = True):
        """Add response time measurement"""
        self.response_times.append(response_time_ms)
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

    def collect_system_metrics(self):
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()

        self.cpu_usage.append(cpu_percent)
        self.memory_usage.append(memory_info.used / 1024 / 1024)  # MB

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        if not self.response_times:
            return {}

        total_requests = self.success_count + self.error_count
        duration_seconds = (
            (self.end_time - self.start_time)
            if self.end_time and self.start_time
            else 0
        )

        return {
            "response_times": {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "mean_ms": statistics.mean(self.response_times),
                "median_ms": statistics.median(self.response_times),
                "p95_ms": self._percentile(self.response_times, 95),
                "p99_ms": self._percentile(self.response_times, 99),
            },
            "throughput": {
                "total_requests": total_requests,
                "successful_requests": self.success_count,
                "failed_requests": self.error_count,
                "success_rate_percent": (self.success_count / total_requests * 100)
                if total_requests > 0
                else 0,
                "requests_per_second": total_requests / duration_seconds
                if duration_seconds > 0
                else 0,
            },
            "system_resources": {
                "avg_cpu_percent": statistics.mean(self.cpu_usage)
                if self.cpu_usage
                else 0,
                "max_cpu_percent": max(self.cpu_usage) if self.cpu_usage else 0,
                "avg_memory_mb": statistics.mean(self.memory_usage)
                if self.memory_usage
                else 0,
                "max_memory_mb": max(self.memory_usage) if self.memory_usage else 0,
            },
            "duration_seconds": duration_seconds,
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Mock Authentication Service for Performance Testing
class PerformanceTestService:
    """High-performance mock service for load testing"""

    def __init__(self):
        self.users = {}  # In-memory user storage for speed
        self.sessions = {}  # In-memory session storage
        self.jwt_secret = "performance_test_secret"
        self.request_count = 0
        self.lock = threading.Lock()

    async def register_user(self, email: str, password: str) -> Tuple[bool, float]:
        """Register user and return (success, response_time_ms)"""
        start_time = time.time()

        try:
            with self.lock:
                self.request_count += 1

                if email in self.users:
                    return False, (time.time() - start_time) * 1000

                # Simulate password hashing delay
                await asyncio.sleep(0.01)  # 10ms simulated hashing time

                self.users[email] = {
                    "password_hash": f"hash_{password}",
                    "id": len(self.users) + 1,
                    "created_at": datetime.utcnow(),
                    "is_active": True,
                    "failed_attempts": 0,
                }

                return True, (time.time() - start_time) * 1000

        except Exception:
            return False, (time.time() - start_time) * 1000

    async def login_user(self, email: str, password: str) -> Tuple[bool, str, float]:
        """Login user and return (success, token, response_time_ms)"""
        start_time = time.time()

        try:
            with self.lock:
                self.request_count += 1

                user = self.users.get(email)
                if not user or user["password_hash"] != f"hash_{password}":
                    pass  # Auto-fixed empty block
                    # Simulate password verification delay
                    await asyncio.sleep(0.005)  # 5ms delay for failed auth
                    return False, "", (time.time() - start_time) * 1000

                # Generate token (simplified)
                token = f"token_{email}_{time.time()}"
                self.sessions[token] = {
                    "user_email": email,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=24),
                }

                return True, token, (time.time() - start_time) * 1000

        except Exception:
            return False, "", (time.time() - start_time) * 1000

    async def validate_token(self, token: str) -> Tuple[bool, float]:
        """Validate token and return (success, response_time_ms)"""
        start_time = time.time()

        try:
            with self.lock:
                self.request_count += 1

                session = self.sessions.get(token)
                if not session:
                    return False, (time.time() - start_time) * 1000

                # Check expiration
                if session["expires_at"] < datetime.utcnow():
                    del self.sessions[token]
                    return False, (time.time() - start_time) * 1000

                return True, (time.time() - start_time) * 1000

        except Exception:
            return False, (time.time() - start_time) * 1000

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self.lock:
            return {
                "total_users": len(self.users),
                "active_sessions": len(self.sessions),
                "total_requests": self.request_count,
            }


# Test Fixtures
@pytest.fixture
async def performance_service():
    """Provide performance test service"""
    return PerformanceTestService()


@pytest.fixture
def performance_config():
    """Provide performance configuration"""
    return PerformanceConfig()


# ============================================================================
# PERFORMANCE TESTS - USER REGISTRATION
# ============================================================================


class TestRegistrationPerformance:
    """Test registration performance under various loads"""

    @pytest.mark.asyncio
    async def test_registration_response_time(self, performance_service):
        """⏱️ Test single user registration response time"""
        email = "test@example.com"
        password = "TestPassword123!"

        success, response_time = await performance_service.register_user(
            email, password
        )

        assert success is True
        assert response_time < PerformanceConfig.REGISTRATION_THRESHOLD_MS

    @pytest.mark.asyncio
    async def test_concurrent_registrations_light_load(
        self, performance_service, performance_config
    ):
        """⚡ Test concurrent registrations - light load"""
        await self._test_concurrent_registrations(
            performance_service, performance_config.CONCURRENT_USERS_LIGHT, "light_load"
        )

    @pytest.mark.asyncio
    async def test_concurrent_registrations_medium_load(
        self, performance_service, performance_config
    ):
        """⚡⚡ Test concurrent registrations - medium load"""
        await self._test_concurrent_registrations(
            performance_service,
            performance_config.CONCURRENT_USERS_MEDIUM,
            "medium_load",
        )

    @pytest.mark.asyncio
    async def test_concurrent_registrations_heavy_load(
        self, performance_service, performance_config
    ):
        """⚡⚡⚡ Test concurrent registrations - heavy load"""
        await self._test_concurrent_registrations(
            performance_service, performance_config.CONCURRENT_USERS_HEAVY, "heavy_load"
        )

    async def _test_concurrent_registrations(
        self, service, concurrent_users: int, load_type: str
    ):
        """Helper method for concurrent registration testing"""
        metrics = PerformanceMetrics()

        async def register_single_user(user_index):
            email = f"user{user_index}_{load_type}@example.com"
            password = f"Password{user_index}123!"

            success, response_time = await service.register_user(email, password)
            metrics.add_response_time(response_time, success)

            if user_index % 10 == 0:  # Collect system metrics periodically
                metrics.collect_system_metrics()

            return success

        # Start monitoring
        metrics.start_monitoring()

        # Execute concurrent registrations
        tasks = [register_single_user(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Stop monitoring
        metrics.stop_monitoring()

        # Analyze results
        successful_registrations = sum(1 for result in results if result is True)
        stats = metrics.calculate_statistics()

        # Assertions
        assert successful_registrations == concurrent_users
        assert (
            stats["response_times"]["p95_ms"]
            < PerformanceConfig.REGISTRATION_THRESHOLD_MS * 2
        )
        assert stats["throughput"]["success_rate_percent"] > 95

        # Log performance metrics

    # print(f"\n📊 Registration Performance - {load_type.upper()}")
    # print(f"Users: {concurrent_users}")
    # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
    # print(f"Avg Response Time: {stats['response_times']['mean_ms']:.1f}ms")
    # print(f"P95 Response Time: {stats['response_times']['p95_ms']:.1f}ms")
    # print(f"Throughput: {stats['throughput']['requests_per_second']:.1f} req/s")


# ============================================================================
# PERFORMANCE TESTS - USER LOGIN
# ============================================================================


class TestLoginPerformance:
    """Test login performance under various loads"""

    @pytest.mark.asyncio
    async def test_login_response_time(self, performance_service):
        """⏱️ Test single user login response time"""
        email = "logintest@example.com"
        password = "TestPassword123!"

        # Register user first
        await performance_service.register_user(email, password)

        # Test login
        success, token, response_time = await performance_service.login_user(
            email, password
        )

        assert success is True
        assert token != ""
        assert response_time < PerformanceConfig.LOGIN_THRESHOLD_MS

    @pytest.mark.asyncio
    async def test_concurrent_logins_performance(self, performance_service):
        """⚡ Test concurrent login performance"""
        num_users = PerformanceConfig.CONCURRENT_USERS_MEDIUM
        metrics = PerformanceMetrics()

        # Setup: Create test users
        setup_tasks = []
        for i in range(num_users):
            email = f"loginuser{i}@example.com"
            password = f"LoginPassword{i}123!"
            setup_tasks.append(performance_service.register_user(email, password))

        await asyncio.gather(*setup_tasks)

        async def login_single_user(user_index):
            email = f"loginuser{user_index}@example.com"
            password = f"LoginPassword{user_index}123!"

            success, token, response_time = await performance_service.login_user(
                email, password
            )
            metrics.add_response_time(response_time, success)

            if user_index % 20 == 0:
                metrics.collect_system_metrics()

            return success, token

        # Execute concurrent logins
        metrics.start_monitoring()

        tasks = [login_single_user(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics.stop_monitoring()

        # Analyze results
        successful_logins = sum(
            1 for result in results if isinstance(result, tuple) and result[0] is True
        )
        stats = metrics.calculate_statistics()

        # Assertions
        assert successful_logins == num_users
        assert (
            stats["response_times"]["p95_ms"] < PerformanceConfig.LOGIN_THRESHOLD_MS * 2
        )
        assert stats["throughput"]["success_rate_percent"] > 98

    # print(f"\n🔐 Login Performance Analysis")
    # print(f"Concurrent Users: {num_users}")
    # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
    # print(f"Avg Response Time: {stats['response_times']['mean_ms']:.1f}ms")
    # print(f"P95 Response Time: {stats['response_times']['p95_ms']:.1f}ms")
    # print(f"Throughput: {stats['throughput']['requests_per_second']:.1f} req/s")


# ============================================================================
# PERFORMANCE TESTS - TOKEN VALIDATION
# ============================================================================


class TestTokenValidationPerformance:
    """Test token validation performance - critical for API performance"""

    @pytest.mark.asyncio
    async def test_token_validation_response_time(self, performance_service):
        """⏱️ Test single token validation response time"""
        email = "tokentest@example.com"
        password = "TestPassword123!"

        # Setup: Register and login to get token
        await performance_service.register_user(email, password)
        success, token, _ = await performance_service.login_user(email, password)

        # Test token validation
        valid, response_time = await performance_service.validate_token(token)

        assert valid is True
        assert response_time < PerformanceConfig.TOKEN_VALIDATION_THRESHOLD_MS

    @pytest.mark.asyncio
    async def test_high_frequency_token_validation(self, performance_service):
        """🔥 Test high-frequency token validation (simulating API calls)"""
        email = "highfreq@example.com"
        password = "TestPassword123!"

        # Setup: Register and login to get token
        await performance_service.register_user(email, password)
        success, token, _ = await performance_service.login_user(email, password)

        metrics = PerformanceMetrics()

        async def validate_token_repeatedly(iterations: int):
            for i in range(iterations):
                valid, response_time = await performance_service.validate_token(token)
                metrics.add_response_time(response_time, valid)

                if i % 100 == 0:
                    metrics.collect_system_metrics()

        # Test with 1000 rapid validations
        metrics.start_monitoring()
        await validate_token_repeatedly(1000)
        metrics.stop_monitoring()

        stats = metrics.calculate_statistics()

        # Assertions
        assert stats["throughput"]["success_rate_percent"] == 100
        assert (
            stats["response_times"]["p95_ms"]
            < PerformanceConfig.TOKEN_VALIDATION_THRESHOLD_MS
        )
        assert (
            stats["throughput"]["requests_per_second"]
            > PerformanceConfig.MIN_REQUESTS_PER_SECOND
        )

    # print(f"\n🎯 Token Validation Performance")
    # print(f"Validations: 1000")
    # print(f"Avg Response Time: {stats['response_times']['mean_ms']:.2f}ms")
    # print(f"P95 Response Time: {stats['response_times']['p95_ms']:.2f}ms")
    # print(f"Throughput: {stats['throughput']['requests_per_second']:.1f} validations/s")

    @pytest.mark.asyncio
    async def test_concurrent_token_validations(self, performance_service):
        """⚡ Test concurrent token validations from multiple sessions"""
        num_sessions = 100
        validations_per_session = 50

        # Setup: Create multiple user sessions
        tokens = []
        for i in range(num_sessions):
            email = f"concurrent{i}@example.com"
            password = f"Password{i}123!"

            await performance_service.register_user(email, password)
            success, token, _ = await performance_service.login_user(email, password)
            if success:
                tokens.append(token)

        metrics = PerformanceMetrics()

        async def validate_session_tokens(session_tokens):
            for token in session_tokens:
                for _ in range(validations_per_session):
                    valid, response_time = await performance_service.validate_token(
                        token
                    )
                    metrics.add_response_time(response_time, valid)

        # Execute concurrent validations
        metrics.start_monitoring()

        # Split tokens into batches for concurrent processing
        batch_size = 10
        tasks = []
        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i : i + batch_size]
            tasks.append(validate_session_tokens(batch_tokens))

        await asyncio.gather(*tasks)
        metrics.stop_monitoring()

        stats = metrics.calculate_statistics()

        # Assertions
        expected_validations = len(tokens) * validations_per_session
        assert stats["throughput"]["total_requests"] == expected_validations
        assert stats["throughput"]["success_rate_percent"] > 99
        assert (
            stats["response_times"]["p95_ms"]
            < PerformanceConfig.TOKEN_VALIDATION_THRESHOLD_MS * 1.5
        )

    # print(f"\n🚀 Concurrent Token Validation")
    # print(f"Sessions: {len(tokens)}")
    # print(f"Total Validations: {expected_validations}")
    # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
    # print(f"Throughput: {stats['throughput']['requests_per_second']:.1f} validations/s")


# ============================================================================
# PERFORMANCE TESTS - STRESS TESTING
# ============================================================================


class TestStressScenarios:
    """Stress testing authentication system at limits"""

    @pytest.mark.asyncio
    async def test_maximum_concurrent_users(self, performance_service):
        """💥 Test system at maximum concurrent user capacity"""
        max_users = PerformanceConfig.CONCURRENT_USERS_STRESS
        metrics = PerformanceMetrics()

        async def stress_test_user(user_index):
            email = f"stress{user_index}@example.com"
            password = f"StressPassword{user_index}123!"

            # Registration
            reg_success, reg_time = await performance_service.register_user(
                email, password
            )
            if reg_success:
                metrics.add_response_time(reg_time, True)

                # Login
                login_success, token, login_time = await performance_service.login_user(
                    email, password
                )
                if login_success:
                    metrics.add_response_time(login_time, True)

                    # Multiple token validations
                    for _ in range(10):
                        valid, val_time = await performance_service.validate_token(
                            token
                        )
                        metrics.add_response_time(val_time, valid)

            if user_index % 50 == 0:
                metrics.collect_system_metrics()

        # Execute stress test
        metrics.start_monitoring()

        # Process users in smaller batches to avoid overwhelming the system
        batch_size = 100
        for i in range(0, max_users, batch_size):
            batch_end = min(i + batch_size, max_users)
            batch_tasks = [stress_test_user(j) for j in range(i, batch_end)]
            await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Small delay between batches
            await asyncio.sleep(0.1)

        metrics.stop_monitoring()

        stats = metrics.calculate_statistics()
        service_stats = performance_service.get_stats()

        # Verify system handled the load
        assert service_stats["total_users"] > max_users * 0.9  # At least 90% success
        assert (
            stats["throughput"]["success_rate_percent"] > 85
        )  # At least 85% success rate

    # print(f"\n💥 Stress Test Results")
    # print(f"Target Users: {max_users}")
    # print(f"Created Users: {service_stats['total_users']}")
    # print(f"Active Sessions: {service_stats['active_sessions']}")
    # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
    # print(f"Max CPU Usage: {stats['system_resources']['max_cpu_percent']:.1f}%")
    # print(f"Max Memory Usage: {stats['system_resources']['max_memory_mb']:.1f}MB")

    @pytest.mark.asyncio
    async def test_sustained_load_endurance(self, performance_service):
        """🏃‍♂️ Test sustained load over extended period"""
        duration_seconds = 30  # Reduced for testing
        concurrent_users = 50

        metrics = PerformanceMetrics()
        stop_event = asyncio.Event()

        async def sustained_user_activity(user_id):
            email = f"endurance{user_id}@example.com"
            password = f"EndurancePassword{user_id}123!"

            # Initial registration and login
            await performance_service.register_user(email, password)
            success, token, _ = await performance_service.login_user(email, password)

            if not success:
                return

            # Sustained activity
            while not stop_event.is_set():
                pass  # Auto-fixed empty block
                # Validate token
                valid, response_time = await performance_service.validate_token(token)
                metrics.add_response_time(response_time, valid)

                # Random delay between requests (1-3 seconds)
                await asyncio.sleep(random.uniform(1, 3))

        # Start sustained load
        metrics.start_monitoring()

        # Start all users
        tasks = [sustained_user_activity(i) for i in range(concurrent_users)]
        user_tasks = asyncio.gather(*tasks, return_exceptions=True)

        # Run for specified duration
        await asyncio.sleep(duration_seconds)
        stop_event.set()

        # Wait for tasks to complete
        await user_tasks
        metrics.stop_monitoring()

        stats = metrics.calculate_statistics()
        service_stats = performance_service.get_stats()

        # Verify system maintained performance
        assert stats["throughput"]["success_rate_percent"] > 95
        assert (
            stats["response_times"]["p95_ms"]
            < PerformanceConfig.TOKEN_VALIDATION_THRESHOLD_MS * 2
        )

    # print(f"\n🏃‍♂️ Endurance Test Results")
    # print(f"Duration: {duration_seconds}s")
    # print(f"Concurrent Users: {concurrent_users}")
    # print(f"Total Requests: {stats['throughput']['total_requests']}")
    # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
    # print(f"Avg Response Time: {stats['response_times']['mean_ms']:.1f}ms")
    # print(f"System Stability: {'STABLE' if stats['throughput']['success_rate_percent'] > 95 else 'UNSTABLE'}")


# ============================================================================
# PERFORMANCE BENCHMARKING AND REPORTING
# ============================================================================


class TestPerformanceBenchmarks:
    """Comprehensive performance benchmarking"""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow_benchmark(self, performance_service):
        """📊 Benchmark complete authentication flow"""
        num_users = 200
        metrics = PerformanceMetrics()

        async def complete_auth_flow(user_index):
            email = f"benchmark{user_index}@example.com"
            password = f"BenchmarkPassword{user_index}123!"

            flow_start = time.time()

            # 1. Registration
            reg_success, reg_time = await performance_service.register_user(
                email, password
            )
            if not reg_success:
                return False

            # 2. Login
            login_success, token, login_time = await performance_service.login_user(
                email, password
            )
            if not login_success:
                return False

            # 3. Multiple API calls (simulated with token validations)
            api_call_times = []
            for _ in range(5):
                valid, val_time = await performance_service.validate_token(token)
                api_call_times.append(val_time)
                if not valid:
                    return False

            flow_end = time.time()
            total_flow_time = (flow_end - flow_start) * 1000

            metrics.add_response_time(total_flow_time, True)
            return True

        # Execute benchmark
        metrics.start_monitoring()

        tasks = [complete_auth_flow(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics.stop_monitoring()

        successful_flows = sum(1 for result in results if result is True)
        stats = metrics.calculate_statistics()

        # Generate benchmark report
        # print(f"\n📊 AUTHENTICATION SYSTEM BENCHMARK REPORT")
        # print("=" * 60)
        # print(f"Test Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        # print(f"Users Tested: {num_users}")
        # print(f"Successful Flows: {successful_flows}")
        # print(f"Success Rate: {stats['throughput']['success_rate_percent']:.1f}%")
        # print()
        # print("PERFORMANCE METRICS:")
        # print(f"  Complete Flow Time (avg): {stats['response_times']['mean_ms']:.1f}ms")
        # print(f"  Complete Flow Time (p95): {stats['response_times']['p95_ms']:.1f}ms")
        # print(f"  Complete Flow Time (p99): {stats['response_times']['p99_ms']:.1f}ms")
        # print(f"  Throughput: {stats['throughput']['requests_per_second']:.1f} flows/s")
        # print()
        # print("SYSTEM RESOURCES:")
        # print(f"  Avg CPU Usage: {stats['system_resources']['avg_cpu_percent']:.1f}%")
        # print(f"  Max CPU Usage: {stats['system_resources']['max_cpu_percent']:.1f}%")
        # print(f"  Avg Memory Usage: {stats['system_resources']['avg_memory_mb']:.1f}MB")
        # print(f"  Max Memory Usage: {stats['system_resources']['max_memory_mb']:.1f}MB")
        # print()

        # Performance Rating
        rating = self._calculate_performance_rating(stats)
        # print(f"PERFORMANCE RATING: {rating}")
        # print("=" * 60)

        # Assertions
        assert successful_flows >= num_users * 0.95  # 95% success rate
        assert stats["response_times"]["p95_ms"] < 3000  # Complete flow under 3s

    def _calculate_performance_rating(self, stats: Dict[str, Any]) -> str:
        """Calculate overall performance rating"""
        score = 0

        # Response time scoring (30 points)
        p95_time = stats["response_times"]["p95_ms"]
        if p95_time < 1000:
            score += 30
        elif p95_time < 2000:
            score += 20
        elif p95_time < 3000:
            score += 10

        # Success rate scoring (40 points)
        success_rate = stats["throughput"]["success_rate_percent"]
        if success_rate >= 99:
            score += 40
        elif success_rate >= 95:
            score += 30
        elif success_rate >= 90:
            score += 20
        elif success_rate >= 85:
            score += 10

        # Throughput scoring (20 points)
        rps = stats["throughput"]["requests_per_second"]
        if rps >= 100:
            score += 20
        elif rps >= 50:
            score += 15
        elif rps >= 25:
            score += 10
        elif rps >= 10:
            score += 5

        # Resource usage scoring (10 points)
        cpu_usage = stats["system_resources"]["max_cpu_percent"]
        if cpu_usage < 50:
            score += 10
        elif cpu_usage < 70:
            score += 7
        elif cpu_usage < 85:
            score += 5

        # Convert to letter grade
        if score >= 90:
            return f"A+ (Excellent) - Score: {score}/100"
        elif score >= 80:
            return f"A (Very Good) - Score: {score}/100"
        elif score >= 70:
            return f"B (Good) - Score: {score}/100"
        elif score >= 60:
            return f"C (Acceptable) - Score: {score}/100"
        else:
            return f"F (Poor) - Score: {score}/100"


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    # print("⚡ Running Authentication Performance Tests")
    # print("=" * 50)

    # Run performance tests
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            "-m",
            "not slow",  # Skip slow tests by default
            "--durations=5",
        ]
    )
