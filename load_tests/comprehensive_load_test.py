#!/usr/bin/env python3
"""
Perfect21 Comprehensive Load Testing Suite
==========================================

This script provides multiple load testing scenarios using Locust framework.
It simulates realistic user behavior patterns and measures performance metrics.

Usage:
    python3 comprehensive_load_test.py --scenario=baseline
    python3 comprehensive_load_test.py --scenario=stress --users=1000
    python3 comprehensive_load_test.py --scenario=spike --duration=600
"""

import random
import json
import time
import argparse
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import logging

# Configure logging
setup_logging("INFO", None)
logger = logging.getLogger(__name__)

class Perfect21User(HttpUser):
    """Base user class for Perfect21 system testing"""
    wait_time = between(1, 3)

    def __init__(self, environment):
        super().__init__(environment)
        self.token = None
        self.user_id = None
        self.session_data = {}

    def on_start(self):
        """Initialize user session"""
        logger.info(f"Starting user session for {self.environment.host}")
        self.authenticate()

    def authenticate(self):
        """Authenticate user and get session token"""
        user_email = f"testuser_{random.randint(1, 10000)}@perfect21.test"

        # Register user if needed (for load testing)
        register_response = self.client.post("/api/auth/register", json={
            "email": user_email,
            "password": "TestPassword123!",
            "first_name": f"Test{random.randint(1, 1000)}",
            "last_name": "User"
        }, catch_response=True)

        # Login
        with self.client.post("/api/auth/login", json={
            "email": user_email,
            "password": "TestPassword123!"
        }, catch_response=True, name="auth_login") as response:

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")

                # Set authorization header for future requests
                self.client.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })

                response.success()
                logger.debug(f"User authenticated: {user_email}")
            else:
                response.failure(f"Authentication failed: {response.status_code}")
                logger.error(f"Authentication failed for {user_email}: {response.text}")

class BaselineLoadTest(Perfect21User):
    """Baseline performance test with normal user behavior"""
    wait_time = between(2, 5)

    @task(5)  # Weight: 5 - Most common operation
    def view_dashboard(self):
        """Load user dashboard - most frequent operation"""
        with self.client.get("/api/user/dashboard",
                           catch_response=True,
                           name="dashboard_load") as response:
            if response.elapsed.total_seconds() > 1:
                response.failure(f"Dashboard slow: {response.elapsed.total_seconds()}s")
            elif response.status_code == 200:
                response.success()

                # Parse dashboard data for follow-up requests
                try:
                    data = response.json()
                    self.session_data["dashboard"] = data
                except:
                    pass

    @task(3)  # Weight: 3 - Common read operations
    def view_profile(self):
        """View user profile information"""
        self.client.get("/api/user/profile", name="profile_view")

    @task(2)  # Weight: 2 - Settings and preferences
    def update_preferences(self):
        """Update user preferences"""
        preferences = {
            "theme": random.choice(["light", "dark", "auto"]),
            "language": random.choice(["en", "zh", "es", "fr"]),
            "notifications": {
                "email": random.choice([True, False]),
                "push": random.choice([True, False]),
                "sms": random.choice([True, False])
            },
            "timezone": random.choice(["UTC", "America/New_York", "Europe/London", "Asia/Shanghai"])
        }

        self.client.put("/api/user/preferences",
                       json=preferences,
                       name="preferences_update")

    @task(2)  # Weight: 2 - Data browsing
    def browse_data(self):
        """Browse application data with pagination"""
        page = random.randint(1, 5)
        limit = random.choice([10, 20, 50])
        sort_by = random.choice(["created_at", "updated_at", "name"])

        self.client.get(f"/api/data/browse",
                       params={
                           "page": page,
                           "limit": limit,
                           "sort_by": sort_by,
                           "order": "desc"
                       },
                       name="data_browse")

    @task(1)  # Weight: 1 - Search operations
    def search_content(self):
        """Search functionality test"""
        search_terms = ["test", "user", "data", "project", "report", "analysis"]
        query = random.choice(search_terms)

        self.client.get("/api/search",
                       params={"q": query, "limit": 20},
                       name="content_search")

class StressTest(Perfect21User):
    """High-load stress testing with aggressive patterns"""
    wait_time = between(0.1, 1)  # Much shorter wait times

    @task(8)  # Heavy load on authentication
    def rapid_requests(self):
        """Rapid API requests to stress the system"""
        endpoints = [
            "/api/user/dashboard",
            "/api/user/profile",
            "/api/user/settings",
            "/api/data/summary"
        ]

        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name="rapid_request")

    @task(3)  # Concurrent data modifications
    def concurrent_updates(self):
        """Concurrent update operations"""
        data = {
            "field1": f"value_{random.randint(1, 1000)}",
            "field2": random.choice(["A", "B", "C"]),
            "timestamp": datetime.now().isoformat()
        }

        self.client.post("/api/data/update",
                        json=data,
                        name="concurrent_update")

    @task(2)  # Database stress
    def heavy_queries(self):
        """Heavy database query operations"""
        # Complex analytics query
        self.client.post("/api/analytics/complex", json={
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "metrics": ["users", "sessions", "revenue", "conversions"],
            "group_by": ["day", "source", "device"],
            "filters": {
                "country": random.choice(["US", "UK", "DE", "FR", "JP"]),
                "device_type": random.choice(["desktop", "mobile", "tablet"])
            }
        }, name="heavy_analytics")

class SpikeTest(Perfect21User):
    """Spike test with sudden traffic increases"""
    wait_time = between(0.5, 2)

    @task(10)  # Very high frequency
    def spike_load(self):
        """Generate spike traffic"""
        # Simulate sudden high traffic
        endpoints = [
            "/api/user/dashboard",
            "/api/notifications/check",
            "/api/health/status"
        ]

        for endpoint in endpoints:
            self.client.get(endpoint, name="spike_request")
            time.sleep(0.1)  # Small delay between requests

class FileUploadTest(Perfect21User):
    """File upload performance testing"""
    wait_time = between(2, 4)

    @task(1)
    def upload_small_file(self):
        """Upload small files (< 1MB)"""
        file_content = "x" * (1024 * 512)  # 512KB
        files = {"file": ("small_test.txt", file_content, "text/plain")}

        with self.client.post("/api/files/upload",
                            files=files,
                            catch_response=True,
                            name="small_file_upload") as response:
            if response.elapsed.total_seconds() > 5:
                response.failure(f"Upload too slow: {response.elapsed.total_seconds()}s")
            elif response.status_code in [200, 201]:
                response.success()

    @task(1)
    def upload_large_file(self):
        """Upload large files (5-10MB)"""
        file_size = random.randint(5, 10) * 1024 * 1024  # 5-10MB
        file_content = "x" * file_size
        files = {"file": ("large_test.txt", file_content, "text/plain")}

        with self.client.post("/api/files/upload",
                            files=files,
                            catch_response=True,
                            name="large_file_upload",
                            timeout=30) as response:
            if response.elapsed.total_seconds() > 15:
                response.failure(f"Large upload too slow: {response.elapsed.total_seconds()}s")
            elif response.status_code in [200, 201]:
                response.success()

class EnduranceTest(Perfect21User):
    """Long-running endurance test"""
    wait_time = between(3, 8)

    @task(3)
    def normal_operations(self):
        """Normal user operations for endurance testing"""
        operations = [
            lambda: self.client.get("/api/user/dashboard"),
            lambda: self.client.get("/api/user/profile"),
            lambda: self.client.post("/api/user/activity", json={
                "action": "page_view",
                "page": "/dashboard",
                "timestamp": datetime.now().isoformat()
            })
        ]

        # Execute random operation
        operation = random.choice(operations)
        operation()

    @task(1)
    def memory_intensive(self):
        """Memory intensive operations for leak detection"""
        # Request large data sets
        self.client.get("/api/data/export",
                       params={"format": "json", "limit": 1000},
                       name="memory_intensive")

# Performance metrics collection
class PerformanceCollector:
    """Collect and analyze performance metrics during testing"""

    def __init__(self):
        self.metrics = {
            "response_times": [],
            "error_count": 0,
            "total_requests": 0,
            "start_time": time.time(),
            "errors_by_endpoint": {},
            "response_times_by_endpoint": {}
        }

    def record_request(self, request_type, name, response_time, response_length, response, context, exception, **kwargs):
        """Record request metrics"""
        self.metrics["total_requests"] += 1

        if exception:
            self.metrics["error_count"] += 1
            endpoint = name or "unknown"
            self.metrics["errors_by_endpoint"][endpoint] = self.metrics["errors_by_endpoint"].get(endpoint, 0) + 1
        else:
            self.metrics["response_times"].append(response_time)
            endpoint = name or "unknown"
            if endpoint not in self.metrics["response_times_by_endpoint"]:
                self.metrics["response_times_by_endpoint"][endpoint] = []
            self.metrics["response_times_by_endpoint"][endpoint].append(response_time)

    def calculate_percentiles(self, data, percentiles=[50, 95, 99]):
        """Calculate percentiles for response time data"""
        if not data:
            return {f"p{p}": 0 for p in percentiles}

        sorted_data = sorted(data)
        results = {}
        for p in percentiles:
            index = int(len(sorted_data) * p / 100)
            results[f"p{p}"] = sorted_data[min(index, len(sorted_data) - 1)]
        return results

    def generate_report(self):
        """Generate performance test report"""
        duration = time.time() - self.metrics["start_time"]

        overall_percentiles = self.calculate_percentiles(self.metrics["response_times"])

        report = {
            "test_duration": duration,
            "total_requests": self.metrics["total_requests"],
            "error_count": self.metrics["error_count"],
            "error_rate": self.metrics["error_count"] / max(self.metrics["total_requests"], 1),
            "requests_per_second": self.metrics["total_requests"] / duration,
            "overall_response_times": overall_percentiles,
            "endpoint_performance": {}
        }

        # Per-endpoint performance
        for endpoint, times in self.metrics["response_times_by_endpoint"].items():
            report["endpoint_performance"][endpoint] = {
                "request_count": len(times),
                "response_times": self.calculate_percentiles(times),
                "error_count": self.metrics["errors_by_endpoint"].get(endpoint, 0)
            }

        return report

def run_load_test(scenario, users=10, spawn_rate=2, duration=300, host="http://localhost:8000"):
    """Run load test with specified parameters"""

    # Map scenarios to user classes
    user_classes = {
        "baseline": BaselineLoadTest,
        "stress": StressTest,
        "spike": SpikeTest,
        "file_upload": FileUploadTest,
        "endurance": EnduranceTest
    }

    if scenario not in user_classes:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(user_classes.keys())}")

    # Set up environment
    env = Environment(user_classes=[user_classes[scenario]], host=host)

    # Set up performance collector
    collector = PerformanceCollector()
    env.events.request.add_listener(collector.record_request)

    # Start test
    logger.info(f"Starting {scenario} test with {users} users for {duration} seconds")
    env.create_local_runner()
    env.runner.start(users, spawn_rate=spawn_rate)

    # Run for specified duration
    time.sleep(duration)

    # Stop test
    env.runner.stop()

    # Generate report
    report = collector.generate_report()

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"performance_report_{scenario}_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Test completed. Report saved to: {report_file}")

    # Print summary
    print("\n" + "="*50)
    print(f"PERFORMANCE TEST SUMMARY - {scenario.upper()}")
    print("="*50)
    print(f"Duration: {report['test_duration']:.2f}s")
    print(f"Total Requests: {report['total_requests']}")
    print(f"Error Rate: {report['error_rate']:.2%}")
    print(f"Requests/sec: {report['requests_per_second']:.2f}")
    print(f"Response Times (ms):")
    print(f"  P50: {report['overall_response_times']['p50']:.2f}")
    print(f"  P95: {report['overall_response_times']['p95']:.2f}")
    print(f"  P99: {report['overall_response_times']['p99']:.2f}")
    print("="*50)

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perfect21 Load Testing Suite")
    parser.add_argument("--scenario", default="baseline",
                       choices=["baseline", "stress", "spike", "file_upload", "endurance"],
                       help="Test scenario to run")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", type=int, default=2, help="Users spawned per second")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host URL")

    args = parser.parse_args()

    try:
        report = run_load_test(
            scenario=args.scenario,
            users=args.users,
            spawn_rate=args.spawn_rate,
            duration=args.duration,
            host=args.host
        )

        # Exit with appropriate code
        if report['error_rate'] > 0.05:  # More than 5% errors
            exit(1)
        else:
            exit(0)

    except Exception as e:
        logger.error(f"Load test failed: {e}")
        exit(1)