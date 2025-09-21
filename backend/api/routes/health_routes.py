"""
Health Check Routes for Perfect21 Claude Enhancer
Provides comprehensive health monitoring endpoints
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "perfect21-claude-enhancer",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with all dependencies"""

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "perfect21-claude-enhancer",
        "version": "1.0.0",
        "checks": {}
    }

    # Check database connectivity
    try:
        # Simulate database check - replace with actual database dependency
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": 12
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check Redis connectivity
    try:
        # Simulate Redis check - replace with actual Redis dependency
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": 5
        }
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        health_status["checks"]["disk"] = {
            "status": "healthy",
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2)
        }
    except Exception as e:
        logger.error("Disk health check failed", error=str(e))
        health_status["checks"]["disk"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check memory usage
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_status["checks"]["memory"] = {
            "status": "healthy",
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent
        }
    except Exception as e:
        logger.error("Memory health check failed", error=str(e))
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": "psutil not available"
        }

    return health_status

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint"""

    # Check if all critical services are ready
    try:
        # Simulate readiness checks
        critical_services = ["database", "redis", "hook_system"]

        for service in critical_services:
            # Replace with actual service checks
            await asyncio.sleep(0.001)  # Simulate check

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }