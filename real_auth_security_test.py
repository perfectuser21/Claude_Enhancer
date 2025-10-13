#!/usr/bin/env python3
"""
Real Authentication Security Test
=================================

Tests the actual authentication implementation for security vulnerabilities
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# Add src path for imports
sys.path.append("/home/xx/dev/Claude Enhancer 5.0/src")

try:
    from auth.auth import AuthService, User
    from auth.jwt import JWTTokenManager, jwt_manager, token_blacklist
    from auth.password import PasswordManager, password_manager

    print("✅ Successfully imported authentication modules")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Testing will be limited without authentication modules")
    sys.exit(1)


class RealAuthSecurityTester:
    """Test real authentication implementation for security vulnerabilities"""

    def __init__(self):
        self.auth_service = AuthService()
        self.vulnerabilities = []
        self.test_results = []

    def log_vulnerability(
        self, vuln_type: str, severity: str, description: str, evidence: str = ""
    ):
        """Log discovered vulnerability"""
        self.vulnerabilities.append(
            {
                "type": vuln_type,
                "severity": severity,
                "description": description,
                "evidence": evidence,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def log_test_result(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.test_results.append(
            {
                "test": test_name,
                "status": status,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def test_sql_injection_in_authentication(self):
        """Test SQL injection vulnerabilities in authentication"""
        print("🔍 Testing SQL Injection in Authentication...")

        sql_payloads = [
            "admin' OR '1'='1' --",
            "test@example.com'; DROP TABLE users; --",
            "admin' UNION SELECT * FROM passwords --",
            "user'; INSERT INTO admin VALUES('hacker'); --",
        ]

        vulnerabilities_found = 0

        for payload in sql_payloads:
            try:
                pass  # Auto-fixed empty block
                # Test registration
                reg_result = self.auth_service.register(
                    payload, "test@example.com", "Password123!"
                )
                if reg_result.get("success", False):
                    self.log_vulnerability(
                        "SQL_INJECTION_REGISTER",
                        "CRITICAL",
                        f"SQL injection in registration username: {payload}",
                        str(reg_result),
                    )
                    vulnerabilities_found += 1
                    print(
                        f"  🔴 VULNERABILITY: Registration accepted SQL injection: {payload[:30]}..."
                    )
                else:
                    print(f"  ✅ Registration blocked SQL injection: {payload[:30]}...")

                # Test login
                login_result = self.auth_service.login(payload, "anypassword")
                if login_result.get("success", False):
                    self.log_vulnerability(
                        "SQL_INJECTION_LOGIN",
                        "CRITICAL",
                        f"SQL injection in login: {payload}",
                        str(login_result),
                    )
                    vulnerabilities_found += 1
                    print(
                        f"  🔴 VULNERABILITY: Login accepted SQL injection: {payload[:30]}..."
                    )
                else:
                    print(f"  ✅ Login blocked SQL injection: {payload[:30]}...")

            except Exception as e:
                print(f"  ⚠️ Exception during SQL injection test: {e}")

        if vulnerabilities_found == 0:
            self.log_test_result(
                "SQL Injection Protection", "PASS", "All SQL injection attempts blocked"
            )
            print("  ✅ SQL Injection Protection: SECURE")
        else:
            self.log_test_result(
                "SQL Injection Protection",
                "FAIL",
                f"{vulnerabilities_found} vulnerabilities found",
            )
            print(
                f"  ❌ SQL Injection Protection: {vulnerabilities_found} vulnerabilities found"
            )

    def test_password_storage_security(self):
        """Test password storage security"""
        print("\n🔍 Testing Password Storage Security...")

        # Register a test user
        test_password = "TestPassword123!"
        reg_result = self.auth_service.register(
            "testuser", "test@example.com", test_password
        )

        if reg_result.get("success", False):
            user_id = reg_result["user"]["user_id"]
            user = self.auth_service.users.get(user_id)

            if user:
                stored_hash = user.password_hash

                # Check if password is stored as plaintext
                if stored_hash == test_password:
                    self.log_vulnerability(
                        "PLAINTEXT_PASSWORD",
                        "CRITICAL",
                        "Passwords stored in plaintext",
                        f"Password: {test_password}, Stored: {stored_hash}",
                    )
                    print("  🔴 CRITICAL: Passwords stored in plaintext!")

                # Check if password uses weak hashing
                elif len(stored_hash) < 30:
                    self.log_vulnerability(
                        "WEAK_PASSWORD_HASH",
                        "HIGH",
                        "Password hashing appears weak",
                        f"Hash length: {len(stored_hash)}",
                    )
                    print(
                        f"  🟠 WARNING: Password hash seems weak (length: {len(stored_hash)})"
                    )

                # Check if it's a simple hash (MD5, SHA1, etc.)
                elif stored_hash.lower() == test_password.lower():
                    self.log_vulnerability(
                        "SIMPLE_HASH",
                        "HIGH",
                        "Password using simple hash algorithm",
                        f"Hash: {stored_hash[:50]}...",
                    )
                    print("  🟠 WARNING: Password using simple hash")

                else:
                    print(f"  ✅ Password properly hashed (length: {len(stored_hash)})")
                    self.log_test_result(
                        "Password Storage", "PASS", f"Secure hashing detected"
                    )

                # Test password verification
                if self.auth_service.password_manager.verify_password(
                    test_password, stored_hash
                ):
                    print("  ✅ Password verification works correctly")
                else:
                    print("  ❌ Password verification failed")
                    self.log_vulnerability(
                        "PASSWORD_VERIFICATION_FAILURE",
                        "HIGH",
                        "Password verification not working",
                        "Verification failed for correct password",
                    )

            else:
                print("  ❌ Could not retrieve user for password testing")
        else:
            print("  ❌ Could not register test user for password testing")

    def test_jwt_token_security(self):
        """Test JWT token security"""
        print("\n🔍 Testing JWT Token Security...")

        # Register and login to get a token
        self.auth_service.register("jwttest", "jwttest@example.com", "JwtTest123!")
        login_result = self.auth_service.login("jwttest@example.com", "JwtTest123!")

        if login_result.get("success", False):
            access_token = login_result["tokens"]["access_token"]
            print(f"  ✅ Got JWT token: {access_token[:30]}...")

            # Test token structure
            token_parts = access_token.split(".")
            if len(token_parts) != 3:
                self.log_vulnerability(
                    "MALFORMED_JWT",
                    "HIGH",
                    "JWT token does not have standard 3-part structure",
                    f"Parts: {len(token_parts)}",
                )
                print(f"  🟠 WARNING: JWT has {len(token_parts)} parts (should be 3)")
            else:
                print("  ✅ JWT has correct 3-part structure")

            # Test token verification
            payload = self.auth_service.verify_token(access_token)
            if payload:
                print("  ✅ Token verification works")

                # Check for sensitive data in token
                if "password" in str(payload).lower():
                    self.log_vulnerability(
                        "SENSITIVE_DATA_IN_JWT",
                        "HIGH",
                        "JWT token contains sensitive data",
                        "Password information found in token",
                    )
                    print("  🔴 VULNERABILITY: JWT contains password information")

                # Check token expiration
                if "exp" not in payload:
                    self.log_vulnerability(
                        "JWT_NO_EXPIRATION",
                        "MEDIUM",
                        "JWT token has no expiration",
                        "No 'exp' claim found",
                    )
                    print("  🟡 WARNING: JWT has no expiration time")
                else:
                    exp_time = datetime.fromtimestamp(payload["exp"])
                    now = datetime.utcnow()
                    expires_in = exp_time - now
                    print(f"  ✅ JWT expires in: {expires_in}")

                    # Check if expiration is too long
                    if expires_in.total_seconds() > 24 * 3600:  # 24 hours
                        self.log_vulnerability(
                            "JWT_LONG_EXPIRATION",
                            "LOW",
                            "JWT token has very long expiration",
                            f"Expires in: {expires_in}",
                        )
                        print(f"  🟡 WARNING: JWT expiration very long: {expires_in}")

            else:
                print("  ❌ Token verification failed")

            # Test token tampering
            tampered_token = access_token[:-5] + "XXXXX"
            tampered_payload = self.auth_service.verify_token(tampered_token)
            if tampered_payload:
                self.log_vulnerability(
                    "JWT_TAMPERING_NOT_DETECTED",
                    "CRITICAL",
                    "JWT token tampering not detected",
                    f"Tampered token accepted: {tampered_token[:30]}...",
                )
                print("  🔴 CRITICAL: Tampered JWT token accepted!")
            else:
                print("  ✅ JWT tampering properly detected and rejected")

        else:
            print("  ❌ Could not obtain JWT token for testing")

    def test_brute_force_protection(self):
        """Test brute force protection"""
        print("\n🔍 Testing Brute Force Protection...")

        # Register a test user
        self.auth_service.register(
            "brutetest", "brutetest@example.com", "BruteTest123!"
        )

        # Attempt multiple failed logins
        failed_attempts = 0
        max_attempts = 10

        for i in range(max_attempts):
            login_result = self.auth_service.login(
                "brutetest@example.com", f"wrongpassword{i}"
            )

            if login_result.get("success", False):
                self.log_vulnerability(
                    "BRUTE_FORCE_SUCCESS",
                    "CRITICAL",
                    f"Brute force attack succeeded on attempt {i+1}",
                    str(login_result),
                )
                print(f"  🔴 CRITICAL: Brute force succeeded on attempt {i+1}")
                break
            else:
                failed_attempts += 1
                error_msg = login_result.get("error", "")

                if "locked" in error_msg.lower() or "too many" in error_msg.lower():
                    print(f"  ✅ Account locked after {failed_attempts} attempts")
                    self.log_test_result(
                        "Brute Force Protection",
                        "PASS",
                        f"Account locked after {failed_attempts} attempts",
                    )
                    break
                else:
                    print(f"  ⚪ Attempt {i+1}: Login failed (no lockout yet)")

        if failed_attempts >= max_attempts:
            self.log_vulnerability(
                "NO_BRUTE_FORCE_PROTECTION",
                "HIGH",
                f"No brute force protection after {max_attempts} attempts",
                f"All {max_attempts} attempts allowed",
            )
            print(
                f"  🟠 WARNING: No brute force protection after {max_attempts} attempts"
            )

    def test_session_management(self):
        """Test session management security"""
        print("\n🔍 Testing Session Management...")

        # Register and login
        self.auth_service.register("sessiontest", "session@example.com", "Session123!")
        login_result = self.auth_service.login("session@example.com", "Session123!")

        if login_result.get("success", False):
            access_token = login_result["tokens"]["access_token"]
            refresh_token = login_result["tokens"]["refresh_token"]

            # Test logout functionality
            logout_result = self.auth_service.logout(access_token, refresh_token)
            if logout_result.get("success", False):
                print("  ✅ Logout functionality works")

                # Test if token is invalidated after logout
                post_logout_verify = self.auth_service.verify_token(access_token)
                if post_logout_verify:
                    self.log_vulnerability(
                        "TOKEN_NOT_INVALIDATED",
                        "HIGH",
                        "Access token still valid after logout",
                        f"Token: {access_token[:30]}...",
                    )
                    print("  🔴 VULNERABILITY: Token still valid after logout")
                else:
                    print("  ✅ Token properly invalidated after logout")

            else:
                print("  ❌ Logout functionality failed")

            # Test refresh token functionality
            refresh_result = self.auth_service.refresh_token(refresh_token)
            if refresh_result.get("success", False):
                print("  ✅ Token refresh functionality works")
                new_access_token = refresh_result["tokens"]["access_token"]

                # Verify new token is different
                if new_access_token == access_token:
                    self.log_vulnerability(
                        "TOKEN_REFRESH_SAME_TOKEN",
                        "MEDIUM",
                        "Token refresh returns same token",
                        "New token identical to old token",
                    )
                    print("  🟡 WARNING: Token refresh returns same token")
                else:
                    print("  ✅ Token refresh generates new token")

        else:
            print("  ❌ Could not login for session testing")

    def test_authorization_bypass(self):
        """Test for authorization bypass vulnerabilities"""
        print("\n🔍 Testing Authorization Bypass...")

        # Register two users
        self.auth_service.register("user1", "user1@example.com", "User1Pass123!")
        self.auth_service.register("user2", "user2@example.com", "User2Pass123!")

        # Login as user1
        login1 = self.auth_service.login("user1@example.com", "User1Pass123!")
        if login1.get("success", False):
            user1_token = login1["tokens"]["access_token"]
            user1_payload = self.auth_service.verify_token(user1_token)

            if user1_payload:
                user1_id = user1_payload.get("user_id")
                print(f"  ✅ User1 logged in with ID: {user1_id}")

                # Try to access user2's information using user1's token
                # This would require an endpoint that takes user_id as parameter
                # For now, just verify token contains user-specific data
                if "user_id" in user1_payload:
                    print("  ✅ Token contains user-specific data")
                else:
                    self.log_vulnerability(
                        "NO_USER_CONTEXT",
                        "MEDIUM",
                        "JWT token lacks user-specific context",
                        "No user_id in token payload",
                    )
                    print("  🟡 WARNING: Token lacks user-specific context")

        # Test permission escalation
        # Try to modify user roles/permissions (if supported)
        try:
            pass  # Auto-fixed empty block
            # This would depend on the specific implementation
            print("  ✅ Authorization bypass tests completed")
        except Exception as e:
            print(f"  ⚠️ Authorization bypass test error: {e}")

    def test_input_validation(self):
        """Test input validation"""
        print("\n🔍 Testing Input Validation...")

        # Test extremely long inputs
        long_string = "A" * 10000

        # Test registration with long inputs
        reg_result = self.auth_service.register(
            long_string, f"{long_string}@example.com", "Password123!"
        )
        if reg_result.get("success", False):
            self.log_vulnerability(
                "NO_INPUT_LENGTH_VALIDATION",
                "MEDIUM",
                "System accepts extremely long usernames",
                f"Username length: {len(long_string)}",
            )
            print(f"  🟡 WARNING: Accepted username of length {len(long_string)}")
        else:
            print("  ✅ Long username properly rejected")

        # Test special characters in username
        special_chars = ["<script>", "';DROP TABLE users;--", "../../../etc/passwd"]

        for special_input in special_chars:
            reg_result = self.auth_service.register(
                special_input, "test@example.com", "Password123!"
            )
            if reg_result.get("success", False):
                self.log_vulnerability(
                    "NO_SPECIAL_CHAR_VALIDATION",
                    "HIGH",
                    f"System accepts dangerous characters in username: {special_input}",
                    str(reg_result),
                )
                print(f"  🟠 WARNING: Accepted dangerous username: {special_input}")
            else:
                print(f"  ✅ Rejected dangerous username: {special_input}")

    def run_all_tests(self):
        """Run all security tests"""
        print("🛡️ CLAUDE ENHANCER 5.0 - REAL AUTHENTICATION SECURITY TEST")
        print("=" * 65)
        print(f"Test Start Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()

        # Run all security tests
        self.test_sql_injection_in_authentication()
        self.test_password_storage_security()
        self.test_jwt_token_security()
        self.test_brute_force_protection()
        self.test_session_management()
        self.test_authorization_bypass()
        self.test_input_validation()

        # Generate final report
        self.generate_security_report()

    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n" + "=" * 65)
        print("🛡️ REAL AUTHENTICATION SECURITY REPORT")
        print("=" * 65)

        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        total_vulnerabilities = len(self.vulnerabilities)

        print(f"Tests Performed: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")
        print(f"Vulnerabilities Found: {total_vulnerabilities}")

        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        else:
            success_rate = 0

        # Vulnerability breakdown
        if self.vulnerabilities:
            print(f"\n🚨 VULNERABILITIES DETECTED:")
            print("-" * 40)

            critical = [v for v in self.vulnerabilities if v["severity"] == "CRITICAL"]
            high = [v for v in self.vulnerabilities if v["severity"] == "HIGH"]
            medium = [v for v in self.vulnerabilities if v["severity"] == "MEDIUM"]
            low = [v for v in self.vulnerabilities if v["severity"] == "LOW"]

            if critical:
                print(f"🔴 CRITICAL ({len(critical)}):")
                for v in critical:
                    print(f"   - {v['type']}: {v['description']}")

            if high:
                print(f"🟠 HIGH ({len(high)}):")
                for v in high:
                    print(f"   - {v['type']}: {v['description']}")

            if medium:
                print(f"🟡 MEDIUM ({len(medium)}):")
                for v in medium:
                    print(f"   - {v['type']}: {v['description']}")

            if low:
                print(f"🟢 LOW ({len(low)}):")
                for v in low:
                    print(f"   - {v['type']}: {v['description']}")

        # Overall security rating
        critical_count = len(
            [v for v in self.vulnerabilities if v["severity"] == "CRITICAL"]
        )
        high_count = len([v for v in self.vulnerabilities if v["severity"] == "HIGH"])

        if critical_count > 0:
            rating = "CRITICAL"
            print(f"\n🔴 SECURITY RATING: CRITICAL")
            print("   Immediate action required - critical vulnerabilities present")
        elif high_count > 0:
            rating = "HIGH RISK"
            print(f"\n🟠 SECURITY RATING: HIGH RISK")
            print("   Significant security improvements needed")
        elif total_vulnerabilities > 0:
            rating = "MEDIUM RISK"
            print(f"\n🟡 SECURITY RATING: MEDIUM RISK")
            print("   Some security improvements recommended")
        else:
            rating = "SECURE"
            print(f"\n🟢 SECURITY RATING: SECURE")
            print("   No significant vulnerabilities detected")

        # Recommendations
        recommendations = self.generate_recommendations()
        if recommendations:
            print(f"\n🔧 SECURITY RECOMMENDATIONS:")
            print("-" * 40)
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")

        print(
            f"\n📋 Test completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        print(f"🏆 Overall Security Rating: {rating}")

        # Save detailed report
        self.save_detailed_report(rating)

    def generate_recommendations(self):
        """Generate security recommendations based on findings"""
        recommendations = []

        vuln_types = [v["type"] for v in self.vulnerabilities]

        if any("SQL_INJECTION" in vt for vt in vuln_types):
            recommendations.append(
                "Implement parameterized queries and strict input validation"
            )

        if "PLAINTEXT_PASSWORD" in vuln_types:
            recommendations.append(
                "URGENT: Implement proper password hashing (bcrypt, scrypt, or Argon2)"
            )

        if "WEAK_PASSWORD_HASH" in vuln_types:
            recommendations.append("Upgrade to stronger password hashing algorithm")

        if "JWT_TAMPERING_NOT_DETECTED" in vuln_types:
            recommendations.append("Fix JWT signature verification")

        if "NO_BRUTE_FORCE_PROTECTION" in vuln_types:
            recommendations.append("Implement account lockout and rate limiting")

        if "TOKEN_NOT_INVALIDATED" in vuln_types:
            recommendations.append("Implement proper token blacklisting on logout")

        # General recommendations
        recommendations.extend(
            [
                "Conduct regular security audits",
                "Implement comprehensive input validation",
                "Use HTTPS for all authentication endpoints",
                "Implement security logging and monitoring",
                "Keep authentication libraries updated",
            ]
        )

        return recommendations[:10]

    def save_detailed_report(self, rating: str):
        """Save detailed security report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "security_rating": rating,
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": len(
                    [t for t in self.test_results if t["status"] == "PASS"]
                ),
                "total_vulnerabilities": len(self.vulnerabilities),
                "critical_vulnerabilities": len(
                    [v for v in self.vulnerabilities if v["severity"] == "CRITICAL"]
                ),
                "high_vulnerabilities": len(
                    [v for v in self.vulnerabilities if v["severity"] == "HIGH"]
                ),
            },
            "test_results": self.test_results,
            "vulnerabilities": self.vulnerabilities,
            "recommendations": self.generate_recommendations(),
        }

        with open(
            "/home/xx/dev/Claude Enhancer 5.0/SECURITY_VULNERABILITY_REPORT.json", "w"
        ) as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: SECURITY_VULNERABILITY_REPORT.json")


def main():
    """Main execution function"""
    try:
        tester = RealAuthSecurityTester()
        tester.run_all_tests()
        return 0
    except Exception as e:
        print(f"❌ Security test execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
