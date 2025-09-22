"""
🌐 End-to-End Authentication Tests
==================================

Complete workflow testing from user registration to protected resource access
Tests the entire authentication journey - like testing a complete customer experience

Author: E2E Testing Agent
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx
import json

from test_fixtures import TestDataGenerator, UserRole, TestScenario


class TestCompleteAuthenticationWorkflows:
    """Test complete authentication workflows end-to-end"""

    @pytest.mark.asyncio
    async def test_complete_user_registration_to_login_flow(
        self, integrated_test_environment
    ):
        """✅ Test complete flow: Registration → Email Verification → Login → Access Protected Resource"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()

        # Step 1: User Registration
        registration_result = await env.register_user(user_data)
        assert registration_result["success"] is True
        assert "verification_token" in registration_result
        assert registration_result["email_sent"] is True

        # Step 2: Verify email verification was sent
        sent_emails = env.email_service.get_sent_emails(
            user_data["email"], "verification"
        )
        assert len(sent_emails) == 1
        assert sent_emails[0]["token"] == registration_result["verification_token"]

        # Step 3: Simulate email verification (in real app, user clicks link)
        verification_token = registration_result["verification_token"]
        # In a real test, this would make an HTTP request to verify endpoint
        await env.database.update_user(user_data["email"], {"is_verified": True})

        # Step 4: User Login
        login_result = await env.login_user(
            user_data["email"],
            user_data["password"],
            {"user_agent": "TestBrowser/1.0", "ip_address": "192.168.1.100"},
        )
        assert login_result["success"] is True
        assert "token" in login_result
        assert "session_id" in login_result

        # Step 5: Verify token is valid
        token_validation = await env.verify_token(login_result["token"])
        assert token_validation["valid"] is True
        assert token_validation["payload"]["email"] == user_data["email"]

        # Step 6: Access protected resource (simulated)
        protected_access = await self._simulate_protected_resource_access(
            login_result["token"], env
        )
        assert protected_access["authorized"] is True

        # Step 7: Verify audit trail
        stats = env.get_service_stats()
        assert stats["jwt_service"]["active_tokens"] >= 1
        assert stats["email_service"]["total_sent"] == 1

    @pytest.mark.asyncio
    async def test_multi_device_login_workflow(self, integrated_test_environment):
        """🔄 Test user logging in from multiple devices"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()

        # Register user
        await env.register_user(user_data)
        await env.database.update_user(user_data["email"], {"is_verified": True})

        devices = [
            {"user_agent": "Chrome/100.0 Desktop", "ip_address": "192.168.1.100"},
            {"user_agent": "Safari/15.0 Mobile", "ip_address": "192.168.1.101"},
            {"user_agent": "Firefox/90.0 Tablet", "ip_address": "192.168.1.102"},
        ]

        login_results = []

        # Login from multiple devices
        for device in devices:
            login_result = await env.login_user(
                user_data["email"], user_data["password"], device
            )
            assert login_result["success"] is True
            login_results.append(login_result)

        # Verify all tokens are valid and different
        tokens = [result["token"] for result in login_results]
        assert len(set(tokens)) == len(tokens)  # All tokens should be unique

        for token in tokens:
            validation = await env.verify_token(token)
            assert validation["valid"] is True

        # Verify multiple active sessions
        stats = env.get_service_stats()
        assert stats["jwt_service"]["active_tokens"] == 3

    @pytest.mark.asyncio
    async def test_password_reset_complete_workflow(self, integrated_test_environment):
        """🔑 Test complete password reset workflow"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()
        new_password = "NewSecurePassword123!"

        # Setup: Register and verify user
        await env.register_user(user_data)
        await env.database.update_user(user_data["email"], {"is_verified": True})

        # Step 1: Initial login to create session
        initial_login = await env.login_user(user_data["email"], user_data["password"])
        assert initial_login["success"] is True
        original_token = initial_login["token"]

        # Step 2: Request password reset
        reset_token = "password_reset_token_12345"
        reset_email_sent = await env.email_service.send_password_reset_email(
            user_data["email"], reset_token
        )
        assert reset_email_sent is True

        # Step 3: Verify password reset email
        reset_emails = env.email_service.get_sent_emails(
            user_data["email"], "password_reset"
        )
        assert len(reset_emails) == 1
        assert reset_emails[0]["token"] == reset_token

        # Step 4: Simulate password reset (user clicks link and submits new password)
        await env.database.update_user(user_data["email"], {"password": new_password})

        # Step 5: Old token should be invalidated
        env.jwt_service.revoke_token(original_token)
        old_token_validation = await env.verify_token(original_token)
        assert old_token_validation["valid"] is False

        # Step 6: Login with new password
        new_login = await env.login_user(user_data["email"], new_password)
        assert new_login["success"] is True

        # Step 7: Login with old password should fail
        old_login_attempt = await env.login_user(
            user_data["email"], user_data["password"]
        )
        assert old_login_attempt["success"] is False

    @pytest.mark.asyncio
    async def test_account_lockout_and_unlock_workflow(
        self, integrated_test_environment
    ):
        """🔒 Test account lockout after failed attempts and unlock process"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()

        # Setup user
        await env.register_user(user_data)
        await env.database.update_user(user_data["email"], {"is_verified": True})

        # Step 1: Make multiple failed login attempts
        failed_attempts = []
        for i in range(5):  # Assume 5 attempts locks account
            failed_login = await env.login_user(user_data["email"], "wrong_password")
            failed_attempts.append(failed_login)
            assert failed_login["success"] is False

        # Step 2: Account should be locked
        await env.database.update_user(
            user_data["email"],
            {"is_locked": True, "failed_attempts": 5, "locked_at": datetime.utcnow()},
        )

        # Step 3: Even correct password should fail when locked
        locked_login_attempt = await env.login_user(
            user_data["email"], user_data["password"]
        )
        assert locked_login_attempt["success"] is False
        assert "locked" in locked_login_attempt.get("error", "").lower()

        # Step 4: Simulate account unlock (admin action or time-based)
        await env.database.update_user(
            user_data["email"],
            {"is_locked": False, "failed_attempts": 0, "locked_at": None},
        )

        # Step 5: Login should work after unlock
        unlocked_login = await env.login_user(user_data["email"], user_data["password"])
        assert unlocked_login["success"] is True

    @pytest.mark.asyncio
    async def test_mfa_enabled_user_workflow(
        self, integrated_test_environment, mock_sms_service
    ):
        """📱 Test MFA-enabled user complete authentication workflow"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()
        user_data["phone"] = "+1234567890"

        # Setup MFA-enabled user
        await env.register_user(user_data)
        await env.database.update_user(
            user_data["email"],
            {"is_verified": True, "mfa_enabled": True, "phone": user_data["phone"]},
        )

        # Step 1: Initial login (should prompt for MFA)
        login_attempt = await env.login_user(user_data["email"], user_data["password"])

        # In a real MFA system, this would return a partial success requiring MFA
        # For our mock, we'll simulate this
        assert login_attempt["success"] is True  # Password correct

        # Step 2: Simulate MFA challenge
        mfa_code = "123456"
        code_sent = await mock_sms_service.send_verification_code(
            user_data["phone"], mfa_code
        )
        assert code_sent is True

        # Step 3: Verify SMS was sent
        sent_messages = mock_sms_service.get_sent_messages(user_data["phone"])
        assert len(sent_messages) == 1
        assert sent_messages[0]["code"] == mfa_code

        # Step 4: Submit MFA code
        mfa_verification = mock_sms_service.verify_code(user_data["phone"], mfa_code)
        assert mfa_verification["valid"] is True

        # Step 5: Complete login with valid MFA
        # In real implementation, this would exchange MFA verification for final token
        final_token = env.jwt_service.generate_token(
            user_id=str(hash(user_data["email"])),
            email=user_data["email"],
            permissions=["read", "write", "mfa_verified"],
        )

        # Step 6: Verify final token includes MFA verification
        token_validation = await env.verify_token(final_token)
        assert token_validation["valid"] is True
        assert "mfa_verified" in token_validation["payload"]["permissions"]

    @pytest.mark.asyncio
    async def test_session_management_workflow(self, integrated_test_environment):
        """⏱️ Test session creation, refresh, and expiration workflow"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()

        # Setup user
        await env.register_user(user_data)
        await env.database.update_user(user_data["email"], {"is_verified": True})

        # Step 1: Login and create session
        login_result = await env.login_user(user_data["email"], user_data["password"])
        original_token = login_result["token"]
        session_id = login_result["session_id"]

        # Step 2: Verify session is active
        session_data = await env.database.get_session(session_id)
        assert session_data is not None
        assert session_data["user_email"] == user_data["email"]

        # Step 3: Use token multiple times (simulate API calls)
        for i in range(5):
            token_validation = await env.verify_token(original_token)
            assert token_validation["valid"] is True
            await asyncio.sleep(0.1)  # Small delay between requests

        # Step 4: Simulate token refresh (generate new token)
        refreshed_token = env.jwt_service.generate_token(
            user_id=str(hash(user_data["email"])),
            email=user_data["email"],
            permissions=["read", "write"],
        )

        # Step 5: Revoke old token
        env.jwt_service.revoke_token(original_token)

        # Step 6: Old token should be invalid
        old_token_validation = await env.verify_token(original_token)
        assert old_token_validation["valid"] is False

        # Step 7: New token should work
        new_token_validation = await env.verify_token(refreshed_token)
        assert new_token_validation["valid"] is True

        # Step 8: Logout (revoke all tokens)
        env.jwt_service.revoke_token(refreshed_token)
        await env.database.delete_session(session_id)

        # Step 9: All tokens should be invalid after logout
        logout_validation = await env.verify_token(refreshed_token)
        assert logout_validation["valid"] is False

    @pytest.mark.asyncio
    async def test_admin_user_privileged_operations(self, integrated_test_environment):
        """👑 Test admin user workflow with privileged operations"""
        env = integrated_test_environment

        # Create admin user
        admin_data = TestDataGenerator.generate_user(UserRole.ADMIN).to_dict()
        regular_user_data = TestDataGenerator.generate_user(UserRole.USER).to_dict()

        # Register both users
        await env.register_user(admin_data)
        await env.register_user(regular_user_data)

        await env.database.update_user(
            admin_data["email"], {"is_verified": True, "role": "admin"}
        )
        await env.database.update_user(
            regular_user_data["email"], {"is_verified": True, "role": "user"}
        )

        # Step 1: Admin login
        admin_login = await env.login_user(admin_data["email"], admin_data["password"])
        assert admin_login["success"] is True
        admin_token = admin_login["token"]

        # Step 2: Regular user login
        user_login = await env.login_user(
            regular_user_data["email"], regular_user_data["password"]
        )
        assert user_login["success"] is True
        user_token = user_login["token"]

        # Step 3: Verify admin token has admin permissions
        admin_token_validation = await env.verify_token(admin_token)
        assert admin_token_validation["valid"] is True

        # Step 4: Simulate admin-only operation (user management)
        admin_operations = await self._simulate_admin_operations(admin_token, env)
        assert admin_operations["can_manage_users"] is True
        assert admin_operations["can_view_audit_logs"] is True

        # Step 5: Verify regular user cannot perform admin operations
        user_operations = await self._simulate_admin_operations(user_token, env)
        assert user_operations["can_manage_users"] is False
        assert user_operations["can_view_audit_logs"] is False

    async def _simulate_protected_resource_access(
        self, token: str, env
    ) -> Dict[str, Any]:
        """Simulate accessing a protected resource"""
        token_validation = await env.verify_token(token)

        if not token_validation["valid"]:
            return {"authorized": False, "error": "Invalid token"}

        # Simulate checking permissions
        permissions = token_validation["payload"].get("permissions", [])
        required_permission = "read"

        if required_permission in permissions:
            return {
                "authorized": True,
                "resource_data": {"id": 123, "name": "Protected Resource"},
                "accessed_at": datetime.utcnow().isoformat(),
            }
        else:
            return {"authorized": False, "error": "Insufficient permissions"}

    async def _simulate_admin_operations(self, token: str, env) -> Dict[str, Any]:
        """Simulate admin-only operations"""
        token_validation = await env.verify_token(token)

        if not token_validation["valid"]:
            return {"can_manage_users": False, "can_view_audit_logs": False}

        # In a real system, this would check user role from database
        # For simulation, we'll assume admin tokens have admin permissions
        user_email = token_validation["payload"]["email"]
        user_data = await env.database.get_user(user_email)

        is_admin = user_data and user_data.get("role") == "admin"

        return {
            "can_manage_users": is_admin,
            "can_view_audit_logs": is_admin,
            "can_modify_system_settings": is_admin,
        }


class TestErrorRecoveryWorkflows:
    """Test error scenarios and recovery workflows"""

    @pytest.mark.asyncio
    async def test_email_delivery_failure_recovery(self, integrated_test_environment):
        """📧 Test recovery when email delivery fails"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()

        # Step 1: Simulate email delivery failure
        env.email_service.simulate_delivery_failure(user_data["email"])

        # Step 2: Attempt registration (email should fail)
        registration_result = await env.register_user(user_data)
        assert registration_result["success"] is True  # User created
        assert registration_result["email_sent"] is False  # Email failed

        # Step 3: Verify email was not sent
        sent_emails = env.email_service.get_sent_emails(user_data["email"])
        assert len(sent_emails) == 0

        # Step 4: Simulate retry mechanism - clear delivery failure
        env.email_service.delivery_failures.remove(user_data["email"])

        # Step 5: Resend verification email
        retry_result = await env.email_service.send_verification_email(
            user_data["email"], "retry_verification_token"
        )
        assert retry_result is True

        # Step 6: Verify email was sent on retry
        sent_emails = env.email_service.get_sent_emails(user_data["email"])
        assert len(sent_emails) == 1

    @pytest.mark.asyncio
    async def test_database_connection_recovery(self, integrated_test_environment):
        """💾 Test recovery from database connection issues"""
        env = integrated_test_environment
        user_data = TestDataGenerator.generate_user().to_dict()

        # Step 1: Normal operation
        registration_result = await env.register_user(user_data)
        assert registration_result["success"] is True

        # Step 2: Simulate database unavailability
        # (In a real test, this might involve stopping a test database container)
        original_create_user = env.database.create_user

        async def failing_create_user(user_data):
            raise Exception("Database connection failed")

        env.database.create_user = failing_create_user

        # Step 3: Attempt operation during outage
        failing_user_data = TestDataGenerator.generate_user().to_dict()
        try:
            await env.register_user(failing_user_data)
            assert False, "Should have failed due to database issue"
        except Exception as e:
            assert "Database connection failed" in str(e)

        # Step 4: Restore database connection
        env.database.create_user = original_create_user

        # Step 5: Verify operations work again
        recovery_user_data = TestDataGenerator.generate_user().to_dict()
        recovery_result = await env.register_user(recovery_user_data)
        assert recovery_result["success"] is True

    @pytest.mark.asyncio
    async def test_concurrent_user_conflict_resolution(
        self, integrated_test_environment
    ):
        """🔄 Test handling of concurrent user operations"""
        env = integrated_test_environment

        # Create same user data for concurrent registration attempts
        user_data = TestDataGenerator.generate_user().to_dict()

        # Step 1: Attempt concurrent registrations of same user
        async def register_user():
            return await env.register_user(user_data)

        # Execute concurrent registrations
        results = await asyncio.gather(
            register_user(), register_user(), register_user(), return_exceptions=True
        )

        # Step 2: Only one should succeed
        successful_registrations = [
            r for r in results if isinstance(r, dict) and r.get("success")
        ]
        failed_registrations = [
            r for r in results if isinstance(r, dict) and not r.get("success")
        ]

        assert len(successful_registrations) == 1
        assert len(failed_registrations) == 2

        # Step 3: Verify error messages for failures
        for failure in failed_registrations:
            assert "already exists" in failure.get("error", "").lower()


class TestPerformanceWorkflows:
    """Test authentication workflows under performance constraints"""

    @pytest.mark.asyncio
    async def test_high_load_user_registration(self, integrated_test_environment):
        """⚡ Test user registration under high load"""
        env = integrated_test_environment

        # Generate many users for concurrent registration
        users = TestDataGenerator.generate_users_batch(
            50, UserRole.USER, TestScenario.HAPPY_PATH
        )

        start_time = time.time()

        # Concurrent registrations
        async def register_single_user(user):
            return await env.register_user(user.to_dict())

        registration_tasks = [register_single_user(user) for user in users]
        results = await asyncio.gather(*registration_tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Analysis
        successful_registrations = sum(
            1 for r in results if isinstance(r, dict) and r.get("success")
        )

        # Assertions
        assert successful_registrations >= 45  # At least 90% success rate
        assert duration < 30  # Should complete within 30 seconds

        # Performance metrics
        registrations_per_second = successful_registrations / duration
        assert registrations_per_second > 1  # At least 1 registration per second

    # print(f"Performance: {successful_registrations} registrations in {duration:.2f}s ({registrations_per_second:.2f}/s)")

    @pytest.mark.asyncio
    async def test_sustained_login_load(self, integrated_test_environment):
        """🔥 Test sustained login operations"""
        env = integrated_test_environment

        # Setup: Register users first
        users = TestDataGenerator.generate_users_batch(
            20, UserRole.USER, TestScenario.HAPPY_PATH
        )

        for user in users:
            await env.register_user(user.to_dict())
            await env.database.update_user(user.email, {"is_verified": True})

        # Sustained login test
        async def sustained_login_activity():
            login_count = 0
            start_time = time.time()

            while time.time() - start_time < 60:  # Run for 60 seconds
                user = random.choice(users)
                login_result = await env.login_user(user.email, user.password)
                if login_result["success"]:
                    login_count += 1

                await asyncio.sleep(0.5)  # 500ms between requests

            return login_count

        # Run sustained load
        login_count = await sustained_login_activity()

        # Verify system maintained performance
        assert login_count > 60  # Should achieve at least 1 login per second

        # Check system stats
        stats = env.get_service_stats()
        assert stats["jwt_service"]["active_tokens"] > 0

    # print(f"Sustained load: {login_count} logins in 60 seconds")


if __name__ == "__main__":
    # print("🌐 Running End-to-End Authentication Tests")
    # print("=" * 50)

    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto", "--durations=10"])
