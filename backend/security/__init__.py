"""
Security Protection Module
=========================

This module provides comprehensive security protection for the authentication system:
- Rate limiting and brute force protection
- IP blacklist management
- Anomaly detection for login patterns
- Security audit logging
- Input validation and XSS/SQL injection prevention
"""

from .rate_limiter import RateLimiter, SecurityRateLimiter
from .ip_blacklist import IPBlacklistManager
from .anomaly_detector import LoginAnomalyDetector
from .audit_logger import SecurityAuditLogger
from .input_validator import InputValidator, SecurityValidator
from .security_middleware import SecurityMiddleware

__all__ = [
    "RateLimiter",
    "SecurityRateLimiter",
    "IPBlacklistManager",
    "LoginAnomalyDetector",
    "SecurityAuditLogger",
    "InputValidator",
    "SecurityValidator",
    "SecurityMiddleware",
]

__version__ = "1.0.0"
