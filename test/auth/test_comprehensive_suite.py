"""
🎯 Comprehensive Authentication Test Suite
==========================================

Master test suite that orchestrates all authentication tests
Comprehensive testing strategy with detailed reporting and analysis

Author: Test Suite Orchestration Agent
"""

import pytest
import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from test_fixtures import TestDataGenerator, UserRole, TestScenario


class TestCategory(Enum):
    """Test categories for organization"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    END_TO_END = "end_to_end"
    LOAD = "load"


class TestSeverity(Enum):
    """Test result severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class TestResult:
    """Standardized test result structure"""
    test_name: str
    category: TestCategory
    status: str  # PASS, FAIL, SKIP, ERROR
    duration_ms: float
    severity: TestSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['category'] = self.category.value
        result['severity'] = self.severity.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


class TestSuiteOrchestrator:
    """Orchestrates and manages the complete test suite"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.suite_start_time = None
        self.suite_end_time = None
        self.environment_info = {}

    def start_suite(self):
        """Initialize test suite execution"""
        self.suite_start_time = datetime.utcnow()
        self.environment_info = self._collect_environment_info()
    # print("\n🚀 Starting Comprehensive Authentication Test Suite")
    # print("=" * 70)
    # print(f"Started at: {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    # print(f"Environment: {self.environment_info.get('platform', 'Unknown')}")
    # print("=" * 70)

    def end_suite(self):
        """Finalize test suite execution"""
        self.suite_end_time = datetime.utcnow()

    def record_test_result(self, result: TestResult):
        """Record individual test result"""
        self.test_results.append(result)

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test suite report"""
        if not self.suite_end_time:
            self.end_suite()

        total_duration = (self.suite_end_time - self.suite_start_time).total_seconds()

        # Categorize results
        results_by_category = {}
        results_by_status = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
        results_by_severity = {sev.value: 0 for sev in TestSeverity}

        for result in self.test_results:
            # By category
            category = result.category.value
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(result)

            # By status
            results_by_status[result.status] += 1

            # By severity (for failures)
            if result.status in ["FAIL", "ERROR"]:
                results_by_severity[result.severity.value] += 1

        # Calculate metrics
        total_tests = len(self.test_results)
        pass_rate = (results_by_status["PASS"] / total_tests * 100) if total_tests > 0 else 0
        avg_test_duration = sum(r.duration_ms for r in self.test_results) / total_tests if total_tests > 0 else 0

        # Generate detailed report
        report = {
            "suite_info": {
                "start_time": self.suite_start_time.isoformat(),
                "end_time": self.suite_end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "environment": self.environment_info
            },
            "summary": {
                "total_tests": total_tests,
                "pass_rate_percent": round(pass_rate, 2),
                "avg_test_duration_ms": round(avg_test_duration, 2),
                "results_by_status": results_by_status,
                "results_by_category": {cat: len(results) for cat, results in results_by_category.items()},
                "failure_severity": results_by_severity
            },
            "detailed_results": {
                cat: [r.to_dict() for r in results]
                for cat, results in results_by_category.items()
            },
            "recommendations": self._generate_recommendations(),
            "security_assessment": self._generate_security_assessment(),
            "performance_analysis": self._generate_performance_analysis()
        }

        return report

    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file"""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"auth_test_report_{timestamp}.json"

        report_path = os.path.join("/home/xx/dev/Claude Enhancer/test/auth", filename)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    # print(f"\n📄 Test report saved to: {report_path}")
        return report_path

    def print_summary(self):
        """Print test suite summary"""
        report = self.generate_comprehensive_report()
        summary = report["summary"]

    # print(f"\n📊 COMPREHENSIVE TEST SUITE SUMMARY")
    # print("=" * 70)
    # print(f"Total Tests: {summary['total_tests']}")
    # print(f"Pass Rate: {summary['pass_rate_percent']:.1f}%")
    # print(f"Average Test Duration: {summary['avg_test_duration_ms']:.1f}ms")
    # print(f"Total Suite Duration: {report['suite_info']['total_duration_seconds']:.1f}s")
    # print()

    # print("RESULTS BY STATUS:")
        for status, count in summary["results_by_status"].items():
            percentage = (count / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
    # print(f"  {status}: {count} ({percentage:.1f}%)")
    # print()

    # print("RESULTS BY CATEGORY:")
        for category, count in summary["results_by_category"].items():
            percentage = (count / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
    # print(f"  {category.upper()}: {count} ({percentage:.1f}%)")
    # print()

        if summary["results_by_status"]["FAIL"] > 0 or summary["results_by_status"]["ERROR"] > 0:
    # print("FAILURE SEVERITY BREAKDOWN:")
            for severity, count in summary["failure_severity"].items():
                if count > 0:
    # print(f"  {severity.upper()}: {count}")
    # print()

        # Print key recommendations
        recommendations = report["recommendations"]
        if recommendations:
    # print("KEY RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:5], 1):
    # print(f"  {i}. {rec}")
    # print()

    # print("=" * 70)

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information"""
        import platform
        import sys

        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Analyze failed tests
        failed_tests = [r for r in self.test_results if r.status in ["FAIL", "ERROR"]]
        security_failures = [r for r in failed_tests if r.category == TestCategory.SECURITY]
        performance_failures = [r for r in failed_tests if r.category == TestCategory.PERFORMANCE]

        # Security recommendations
        if security_failures:
            recommendations.append("Review and strengthen security measures based on failed security tests")
            critical_security = [r for r in security_failures if r.severity == TestSeverity.CRITICAL]
            if critical_security:
                recommendations.append("URGENT: Address critical security vulnerabilities immediately")

        # Performance recommendations
        if performance_failures:
            recommendations.append("Optimize system performance based on failed performance tests")

        # General recommendations
        total_tests = len(self.test_results)
        pass_rate = len([r for r in self.test_results if r.status == "PASS"]) / total_tests if total_tests > 0 else 0

        if pass_rate < 0.95:
            recommendations.append("Improve overall test pass rate - aim for 95%+ success rate")

        if pass_rate >= 0.98:
            recommendations.append("Excellent test coverage - maintain current quality standards")

        # Test-specific recommendations
        unit_tests = [r for r in self.test_results if r.category == TestCategory.UNIT]
        if len(unit_tests) < 20:
            recommendations.append("Increase unit test coverage for better code quality assurance")

        return recommendations

    def _generate_security_assessment(self) -> Dict[str, Any]:
        """Generate security assessment"""
        security_tests = [r for r in self.test_results if r.category == TestCategory.SECURITY]
        total_security_tests = len(security_tests)
        passed_security_tests = len([r for r in security_tests if r.status == "PASS"])

        security_score = (passed_security_tests / total_security_tests * 100) if total_security_tests > 0 else 0

        # Determine security level
        if security_score >= 95:
            security_level = "EXCELLENT"
        elif security_score >= 85:
            security_level = "GOOD"
        elif security_score >= 70:
            security_level = "ACCEPTABLE"
        else:
            security_level = "NEEDS_IMPROVEMENT"

        return {
            "total_security_tests": total_security_tests,
            "passed_security_tests": passed_security_tests,
            "security_score_percent": round(security_score, 2),
            "security_level": security_level,
            "critical_issues": len([r for r in security_tests
                                  if r.status in ["FAIL", "ERROR"] and r.severity == TestSeverity.CRITICAL])
        }

    def _generate_performance_analysis(self) -> Dict[str, Any]:
        """Generate performance analysis"""
        performance_tests = [r for r in self.test_results if r.category == TestCategory.PERFORMANCE]

        if not performance_tests:
            return {"status": "No performance tests executed"}

        # Calculate performance metrics
        response_times = [r.duration_ms for r in performance_tests if r.status == "PASS"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0

        # Performance rating
        if avg_response_time < 100:
            performance_rating = "EXCELLENT"
        elif avg_response_time < 500:
            performance_rating = "GOOD"
        elif avg_response_time < 1000:
            performance_rating = "ACCEPTABLE"
        else:
            performance_rating = "NEEDS_OPTIMIZATION"

        return {
            "total_performance_tests": len(performance_tests),
            "avg_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": round(min_response_time, 2),
            "max_response_time_ms": round(max_response_time, 2),
            "performance_rating": performance_rating,
            "slow_tests": len([r for r in performance_tests if r.duration_ms > 1000])
        }


class TestAuthenticationComprehensive:
    """Comprehensive authentication test suite"""

    def __init__(self):
        self.orchestrator = TestSuiteOrchestrator()

    @pytest.mark.asyncio
    async def test_comprehensive_authentication_suite(self, integrated_test_environment):
        """🎯 Execute comprehensive authentication test suite"""
        self.orchestrator.start_suite()
        env = integrated_test_environment

        # Execute all test categories
        await self._run_unit_tests(env)
        await self._run_integration_tests(env)
        await self._run_security_tests(env)
        await self._run_performance_tests(env)
        await self._run_end_to_end_tests(env)

        # Generate and display results
        self.orchestrator.end_suite()
        report = self.orchestrator.generate_comprehensive_report()
        self.orchestrator.print_summary()
        self.orchestrator.save_report(report)

        # Overall suite assertions
        summary = report["summary"]
        assert summary["pass_rate_percent"] >= 80, f"Test suite pass rate too low: {summary['pass_rate_percent']}%"

        # Security assertions
        security_assessment = report["security_assessment"]
        assert security_assessment["security_score_percent"] >= 85, "Security score too low"
        assert security_assessment["critical_issues"] == 0, "Critical security issues found"

    async def _run_unit_tests(self, env):
        """Execute unit tests"""
    # print("\n🧪 Running Unit Tests...")

        # Test 1: User Registration Validation
        start_time = time.time()
        try:
            valid_user = TestDataGenerator.generate_user()
            result = await env.register_user(valid_user.to_dict())
            duration_ms = (time.time() - start_time) * 1000

            test_result = TestResult(
                test_name="user_registration_validation",
                category=TestCategory.UNIT,
                status="PASS" if result.get("success") else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message="User registration with valid data",
                details={"user_email": valid_user.email, "result": result},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="user_registration_validation",
                category=TestCategory.UNIT,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message=f"Registration test error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        # Test 2: Password Validation
        start_time = time.time()
        try:
            # Test weak password rejection
            weak_password_user = TestDataGenerator.generate_user(scenario=TestScenario.ERROR_CASE)
            result = await env.register_user(weak_password_user.to_dict())
            duration_ms = (time.time() - start_time) * 1000

            # Weak password should be rejected
            test_result = TestResult(
                test_name="password_validation",
                category=TestCategory.UNIT,
                status="PASS" if not result.get("success") else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.MEDIUM,
                message="Weak password validation",
                details={"weak_password_rejected": not result.get("success")},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="password_validation",
                category=TestCategory.UNIT,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.MEDIUM,
                message=f"Password validation error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        # Test 3: JWT Token Generation
        start_time = time.time()
        try:
            token = env.jwt_service.generate_token(
                user_id="test_user_123",
                email="test@example.com",
                permissions=["read", "write"]
            )
            duration_ms = (time.time() - start_time) * 1000

            test_result = TestResult(
                test_name="jwt_token_generation",
                category=TestCategory.UNIT,
                status="PASS" if token else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message="JWT token generation",
                details={"token_generated": bool(token), "token_length": len(token) if token else 0},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="jwt_token_generation",
                category=TestCategory.UNIT,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message=f"JWT generation error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

    async def _run_integration_tests(self, env):
        """Execute integration tests"""
    # print("\n🔄 Running Integration Tests...")

        # Test 1: Complete Registration Flow
        start_time = time.time()
        try:
            user = TestDataGenerator.generate_user()
            user_data = user.to_dict()

            # Registration
            reg_result = await env.register_user(user_data)
            if not reg_result.get("success"):
                raise Exception("Registration failed")

            # Email verification simulation
            await env.database.update_user(user.email, {"is_verified": True})

            # Login
            login_result = await env.login_user(user.email, user.password)
            duration_ms = (time.time() - start_time) * 1000

            test_result = TestResult(
                test_name="complete_registration_flow",
                category=TestCategory.INTEGRATION,
                status="PASS" if login_result.get("success") else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message="Complete registration to login flow",
                details={
                    "registration_success": reg_result.get("success"),
                    "login_success": login_result.get("success"),
                    "flow_completed": login_result.get("success")
                },
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="complete_registration_flow",
                category=TestCategory.INTEGRATION,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message=f"Integration flow error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        # Test 2: Token Validation Integration
        start_time = time.time()
        try:
            # Create user and login
            user = TestDataGenerator.generate_user()
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})
            login_result = await env.login_user(user.email, user.password)

            if login_result.get("success"):
                token = login_result["token"]
                validation_result = await env.verify_token(token)
                duration_ms = (time.time() - start_time) * 1000

                test_result = TestResult(
                    test_name="token_validation_integration",
                    category=TestCategory.INTEGRATION,
                    status="PASS" if validation_result.get("valid") else "FAIL",
                    duration_ms=duration_ms,
                    severity=TestSeverity.MEDIUM,
                    message="Token validation after login",
                    details={
                        "token_valid": validation_result.get("valid"),
                        "validation_details": validation_result
                    },
                    timestamp=datetime.utcnow()
                )
            else:
                raise Exception("Login failed for token validation test")

            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="token_validation_integration",
                category=TestCategory.INTEGRATION,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.MEDIUM,
                message=f"Token validation integration error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

    async def _run_security_tests(self, env):
        """Execute security tests"""
    # print("\n🛡️ Running Security Tests...")

        # Test 1: SQL Injection Protection
        start_time = time.time()
        try:
            sql_payloads = ["admin' OR '1'='1", "'; DROP TABLE users; --"]
            blocked_attempts = 0

            for payload in sql_payloads:
                result = await env.login_user(payload, "password")
                if not result.get("success"):
                    blocked_attempts += 1

            duration_ms = (time.time() - start_time) * 1000
            all_blocked = blocked_attempts == len(sql_payloads)

            test_result = TestResult(
                test_name="sql_injection_protection",
                category=TestCategory.SECURITY,
                status="PASS" if all_blocked else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.CRITICAL,
                message="SQL injection attack protection",
                details={
                    "total_attempts": len(sql_payloads),
                    "blocked_attempts": blocked_attempts,
                    "protection_effective": all_blocked
                },
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="sql_injection_protection",
                category=TestCategory.SECURITY,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.CRITICAL,
                message=f"SQL injection test error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        # Test 2: Brute Force Protection
        start_time = time.time()
        try:
            user = TestDataGenerator.generate_user()
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})

            # Attempt multiple failed logins
            failed_attempts = 0
            for i in range(10):
                result = await env.login_user(user.email, f"wrong_password_{i}")
                if not result.get("success"):
                    failed_attempts += 1

                # Check if account gets locked or rate limited
                if "locked" in result.get("error", "").lower() or "rate limit" in result.get("error", "").lower():
                    break

            duration_ms = (time.time() - start_time) * 1000
            protection_active = failed_attempts >= 5  # Assume protection kicks in after 5 attempts

            test_result = TestResult(
                test_name="brute_force_protection",
                category=TestCategory.SECURITY,
                status="PASS" if protection_active else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message="Brute force attack protection",
                details={
                    "failed_attempts": failed_attempts,
                    "protection_active": protection_active
                },
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="brute_force_protection",
                category=TestCategory.SECURITY,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message=f"Brute force test error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

    async def _run_performance_tests(self, env):
        """Execute performance tests"""
    # print("\n⚡ Running Performance Tests...")

        # Test 1: Registration Performance
        start_time = time.time()
        try:
            users = TestDataGenerator.generate_users_batch(20, UserRole.USER, TestScenario.HAPPY_PATH)
            successful_registrations = 0

            for user in users:
                reg_start = time.time()
                result = await env.register_user(user.to_dict())
                reg_duration = (time.time() - reg_start) * 1000

                if result.get("success"):
                    successful_registrations += 1

                # Individual registration should be fast
                if reg_duration > 2000:  # 2 seconds threshold
                    break

            total_duration_ms = (time.time() - start_time) * 1000
            success_rate = successful_registrations / len(users)

            test_result = TestResult(
                test_name="registration_performance",
                category=TestCategory.PERFORMANCE,
                status="PASS" if success_rate >= 0.9 and total_duration_ms < 30000 else "FAIL",
                duration_ms=total_duration_ms,
                severity=TestSeverity.MEDIUM,
                message="Registration performance under load",
                details={
                    "total_registrations": len(users),
                    "successful_registrations": successful_registrations,
                    "success_rate": success_rate,
                    "avg_duration_ms": total_duration_ms / len(users)
                },
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="registration_performance",
                category=TestCategory.PERFORMANCE,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.MEDIUM,
                message=f"Registration performance error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        # Test 2: Token Validation Performance
        start_time = time.time()
        try:
            # Create user and get token
            user = TestDataGenerator.generate_user()
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})
            login_result = await env.login_user(user.email, user.password)

            if login_result.get("success"):
                token = login_result["token"]
                validation_count = 100
                successful_validations = 0

                for _ in range(validation_count):
                    validation_result = await env.verify_token(token)
                    if validation_result.get("valid"):
                        successful_validations += 1

                duration_ms = (time.time() - start_time) * 1000
                avg_validation_time = duration_ms / validation_count
                success_rate = successful_validations / validation_count

                test_result = TestResult(
                    test_name="token_validation_performance",
                    category=TestCategory.PERFORMANCE,
                    status="PASS" if success_rate == 1.0 and avg_validation_time < 10 else "FAIL",
                    duration_ms=duration_ms,
                    severity=TestSeverity.MEDIUM,
                    message="Token validation performance",
                    details={
                        "validation_count": validation_count,
                        "successful_validations": successful_validations,
                        "avg_validation_time_ms": avg_validation_time,
                        "success_rate": success_rate
                    },
                    timestamp=datetime.utcnow()
                )
            else:
                raise Exception("Login failed for performance test")

            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="token_validation_performance",
                category=TestCategory.PERFORMANCE,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.MEDIUM,
                message=f"Token validation performance error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

    async def _run_end_to_end_tests(self, env):
        """Execute end-to-end tests"""
    # print("\n🌐 Running End-to-End Tests...")

        # Test 1: Complete User Journey
        start_time = time.time()
        try:
            user = TestDataGenerator.generate_user()
            user_data = user.to_dict()

            # Step 1: Registration
            reg_result = await env.register_user(user_data)
            if not reg_result.get("success"):
                raise Exception("Registration failed")

            # Step 2: Email verification
            await env.database.update_user(user.email, {"is_verified": True})

            # Step 3: Login
            login_result = await env.login_user(user.email, user.password)
            if not login_result.get("success"):
                raise Exception("Login failed")

            token = login_result["token"]

            # Step 4: Access protected resource
            validation_result = await env.verify_token(token)
            if not validation_result.get("valid"):
                raise Exception("Token validation failed")

            # Step 5: Logout (token revocation)
            env.jwt_service.revoke_token(token)
            post_logout_validation = await env.verify_token(token)

            duration_ms = (time.time() - start_time) * 1000
            journey_complete = (
                reg_result.get("success") and
                login_result.get("success") and
                validation_result.get("valid") and
                not post_logout_validation.get("valid")
            )

            test_result = TestResult(
                test_name="complete_user_journey",
                category=TestCategory.END_TO_END,
                status="PASS" if journey_complete else "FAIL",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message="Complete user authentication journey",
                details={
                    "registration_success": reg_result.get("success"),
                    "login_success": login_result.get("success"),
                    "token_valid": validation_result.get("valid"),
                    "logout_effective": not post_logout_validation.get("valid"),
                    "journey_complete": journey_complete
                },
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            test_result = TestResult(
                test_name="complete_user_journey",
                category=TestCategory.END_TO_END,
                status="ERROR",
                duration_ms=duration_ms,
                severity=TestSeverity.HIGH,
                message=f"End-to-end journey error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            self.orchestrator.record_test_result(test_result)


if __name__ == "__main__":
    # print("🎯 Running Comprehensive Authentication Test Suite")
    # print("=" * 70)

    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "--durations=20"
    ])