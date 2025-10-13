"""
Rate Limiting and Brute Force Protection
========================================

Implements multiple layers of rate limiting:
- Per-IP rate limiting
- Per-user rate limiting  
- Adaptive rate limiting based on threat level
- Distributed rate limiting support
"""

import time
import redis
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_allowance: int = 10
    window_size: int = 60
    penalty_duration: int = 300  # 5 minutes


@dataclass
class RateLimitResult:
    """Rate limiting check result"""

    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    threat_level: ThreatLevel = ThreatLevel.LOW


class RateLimiter:
    """Basic rate limiter using Redis backend"""

    def __init__(self, redis_client: redis.Redis, config: RateLimitConfig):
        self.redis = redis_client
        self.config = config

    def _get_key(self, identifier: str, window_type: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"ratelimit:{window_type}:{identifier}"

    def _get_current_window(self, window_size: int) -> int:
        """Get current time window"""
        return int(time.time() // window_size)

    def check_rate_limit(self, identifier: str) -> RateLimitResult:
        """Check if request is within rate limits"""
        try:
            current_time = int(time.time())
            minute_window = self._get_current_window(60)
            hour_window = self._get_current_window(3600)

            # Check minute rate limit
            minute_key = self._get_key(identifier, f"minute:{minute_window}")
            minute_count = self.redis.incr(minute_key)
            if minute_count == 1:
                self.redis.expire(minute_key, 60)

            # Check hour rate limit
            hour_key = self._get_key(identifier, f"hour:{hour_window}")
            hour_count = self.redis.incr(hour_key)
            if hour_count == 1:
                self.redis.expire(hour_key, 3600)

            # Check if limits exceeded
            minute_exceeded = minute_count > self.config.requests_per_minute
            hour_exceeded = hour_count > self.config.requests_per_hour

            if minute_exceeded or hour_exceeded:
                pass  # Auto-fixed empty block
                # Calculate retry after
                if minute_exceeded:
                    retry_after = 60 - (current_time % 60)
                else:
                    retry_after = 3600 - (current_time % 3600)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=current_time + retry_after,
                    retry_after=retry_after,
                    threat_level=ThreatLevel.MEDIUM
                    if minute_exceeded
                    else ThreatLevel.LOW,
                )

            remaining = min(
                self.config.requests_per_minute - minute_count,
                self.config.requests_per_hour - hour_count,
            )

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=current_time + 60,
                threat_level=ThreatLevel.LOW,
            )

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if Redis is down
            return RateLimitResult(
                allowed=True, remaining=999, reset_time=int(time.time()) + 60
            )


class SecurityRateLimiter(RateLimiter):
    """Advanced rate limiter with security features"""

    def __init__(self, redis_client: redis.Redis, config: RateLimitConfig):
        super().__init__(redis_client, config)
        self.suspicious_patterns = {
            "rapid_fire": {"threshold": 10, "window": 10},
            "burst_attack": {"threshold": 50, "window": 60},
            "sustained_attack": {"threshold": 200, "window": 3600},
        }

    def check_security_rate_limit(
        self, identifier: str, user_id: Optional[str] = None, endpoint: str = "default"
    ) -> RateLimitResult:
        """Enhanced rate limiting with security pattern detection"""

        # Basic rate limit check
        basic_result = self.check_rate_limit(f"{endpoint}:{identifier}")

        if not basic_result.allowed:
            return basic_result

        # Check for suspicious patterns
        threat_level = self._analyze_threat_patterns(identifier, endpoint)

        # Apply adaptive limits based on threat level
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            stricter_config = RateLimitConfig(
                requests_per_minute=10, requests_per_hour=100
            )
            strict_limiter = RateLimiter(self.redis, stricter_config)
            strict_result = strict_limiter.check_rate_limit(f"strict:{identifier}")
            strict_result.threat_level = threat_level
            return strict_result

        basic_result.threat_level = threat_level
        return basic_result

    def _analyze_threat_patterns(self, identifier: str, endpoint: str) -> ThreatLevel:
        """Analyze request patterns for threat assessment"""
        try:
            current_time = int(time.time())

            # Check rapid fire pattern (10 requests in 10 seconds)
            rapid_key = f"pattern:rapid:{identifier}:{current_time // 10}"
            rapid_count = self.redis.incr(rapid_key)
            self.redis.expire(rapid_key, 10)

            if rapid_count > self.suspicious_patterns["rapid_fire"]["threshold"]:
                self._log_suspicious_activity(identifier, "rapid_fire", rapid_count)
                return ThreatLevel.CRITICAL

            # Check burst pattern (50 requests in 1 minute)
            burst_key = f"pattern:burst:{identifier}:{current_time // 60}"
            burst_count = self.redis.incr(burst_key)
            self.redis.expire(burst_key, 60)

            if burst_count > self.suspicious_patterns["burst_attack"]["threshold"]:
                self._log_suspicious_activity(identifier, "burst_attack", burst_count)
                return ThreatLevel.HIGH

            # Check sustained pattern (200 requests in 1 hour)
            sustained_key = f"pattern:sustained:{identifier}:{current_time // 3600}"
            sustained_count = self.redis.incr(sustained_key)
            self.redis.expire(sustained_key, 3600)

            if (
                sustained_count
                > self.suspicious_patterns["sustained_attack"]["threshold"]
            ):
                self._log_suspicious_activity(
                    identifier, "sustained_attack", sustained_count
                )
                return ThreatLevel.MEDIUM

            return ThreatLevel.LOW

        except Exception as e:
            logger.error(f"Threat analysis error: {e}")
            return ThreatLevel.LOW

    def _log_suspicious_activity(self, identifier: str, pattern_type: str, count: int):
        """Log suspicious activity for further investigation"""
        log_data = {
            "timestamp": time.time(),
            "identifier": identifier,
            "pattern_type": pattern_type,
            "request_count": count,
            "severity": "security_alert",
        }

        # Store in Redis for real-time monitoring
        alert_key = f"security:alert:{identifier}:{int(time.time())}"
        self.redis.setex(alert_key, 86400, json.dumps(log_data))  # Keep for 24 hours

        logger.warning(f"Suspicious activity detected: {log_data}")

    def add_penalty(self, identifier: str, duration: int = None):
        """Add penalty time for an identifier"""
        duration = duration or self.config.penalty_duration
        penalty_key = f"penalty:{identifier}"
        self.redis.setex(penalty_key, duration, int(time.time() + duration))
        logger.info(f"Added penalty for {identifier}: {duration}s")

    def is_penalized(self, identifier: str) -> bool:
        """Check if identifier is currently penalized"""
        penalty_key = f"penalty:{identifier}"
        return self.redis.exists(penalty_key)

    def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        """Get comprehensive rate limit status"""
        try:
            current_time = int(time.time())
            minute_window = self._get_current_window(60)
            hour_window = self._get_current_window(3600)

            minute_key = self._get_key(identifier, f"minute:{minute_window}")
            hour_key = self._get_key(identifier, f"hour:{hour_window}")

            minute_count = int(self.redis.get(minute_key) or 0)
            hour_count = int(self.redis.get(hour_key) or 0)

            penalty_key = f"penalty:{identifier}"
            penalty_expires = self.redis.get(penalty_key)

            return {
                "identifier": identifier,
                "current_time": current_time,
                "minute_requests": minute_count,
                "hour_requests": hour_count,
                "minute_limit": self.config.requests_per_minute,
                "hour_limit": self.config.requests_per_hour,
                "is_penalized": bool(penalty_expires),
                "penalty_expires": int(penalty_expires) if penalty_expires else None,
                "threat_level": self._analyze_threat_patterns(
                    identifier, "status_check"
                ).value,
            }

        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {"error": str(e)}
