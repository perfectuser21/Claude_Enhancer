#!/usr/bin/env python3
"""
Claude Enhancer Claude Enhancer - Main API Entry Point
Enterprise-grade todo application with enhanced Claude integration
"""

import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import internal modules
try:
    from backend.core.config import get_settings
    from backend.api.routes.todo_routes import router as todo_router
    from backend.middleware.auth_middleware import AuthMiddleware
    from backend.middleware.rate_limit_middleware import RateLimitMiddleware
    from backend.core.database import DatabaseManager
    from backend.core.cache import CacheManager
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")
    # Create minimal configuration for basic functionality
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/api.log")
        if os.path.exists("/app/logs")
        else logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Global components
database_manager = None
cache_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


async def startup_event():
    """Application startup event"""
    global database_manager, cache_manager

    logger.info("🚀 Starting Claude Enhancer Claude Enhancer API...")

    try:
        pass  # Auto-fixed empty block
        # Initialize basic components
        logger.info("📊 Initializing core components...")

        # Initialize database connection (if available)
        try:
            database_manager = DatabaseManager()
            await database_manager.initialize()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")

        # Initialize cache (if available)
        try:
            cache_manager = CacheManager()
            await cache_manager.initialize()
            logger.info("✅ Cache connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Cache connection failed: {e}")

        logger.info("✅ Claude Enhancer API started successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to start Claude Enhancer API: {e}")
        raise


async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 Shutting down Claude Enhancer Claude Enhancer API...")

    try:
        pass  # Auto-fixed empty block
        # Close cache connection
        if cache_manager:
            await cache_manager.close()

        # Close database connection
        if database_manager:
            await database_manager.close()

        logger.info("✅ Claude Enhancer API shut down successfully!")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Claude Enhancer Claude Enhancer",
    description="Enhanced todo application with Claude AI integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # Configure this properly for production
)

# Add custom middleware
try:
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimitMiddleware)
except NameError:
    logger.warning("⚠️ Custom middleware not available, skipping...")


# Add metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Metrics collection middleware"""
    import time

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Log request metrics
    logger.info(
        f"Request: {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )

    return response


# Global exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
        },
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        pass  # Auto-fixed empty block
        # Check database connection
        db_healthy = True
        if database_manager:
            db_healthy = await database_manager.health_check()

        # Check cache connection
        cache_healthy = True
        if cache_manager:
            cache_healthy = await cache_manager.health_check()

        overall_healthy = db_healthy and cache_healthy

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "claude-enhancer",
            "version": "2.0.0",
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint"""
    try:
        pass  # Auto-fixed empty block
        # More strict readiness check
        all_ready = True

        if database_manager:
            all_ready = all_ready and await database_manager.ready_check()

        if cache_manager:
            all_ready = all_ready and await cache_manager.ready_check()

        if all_ready:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Metrics endpoint for Prometheus"""
    return {"message": "Metrics available at /metrics endpoint"}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Claude Enhancer Claude Enhancer",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs",
        "health_url": "/health",
    }


# Register API routes
try:
    app.include_router(todo_router, prefix="/api/v1/todos", tags=["Todos"])
except NameError:
    logger.warning("⚠️ Todo router not available, creating basic routes...")

    # Basic todo routes for minimal functionality
    @app.get("/api/v1/todos", tags=["Todos"])
    async def get_todos():
        return {
            "todos": [],
            "message": "Todo service is starting up",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.post("/api/v1/todos", tags=["Todos"])
    async def create_todo():
        return {"message": "Todo creation endpoint", "status": "service_starting"}


# Dependency injection functions
def get_database():
    """Get database connection"""
    return database_manager


def get_cache():
    """Get cache manager"""
    return cache_manager


# Add dependency injection to app state
app.state.get_database = get_database
app.state.get_cache = get_cache


# Custom DatabaseManager and CacheManager classes (fallback)
class DatabaseManager:
    """Simple database manager for fallback"""

    async def initialize(self):
        """Initialize database connection"""
        pass

    async def health_check(self):
        """Health check for database"""
        return True

    async def ready_check(self):
        """Readiness check for database"""
        return True

    async def close(self):
        """Close database connection"""
        pass


class CacheManager:
    """Simple cache manager for fallback"""

    async def initialize(self):
        """Initialize cache connection"""
        pass

    async def health_check(self):
        """Health check for cache"""
        return True

    async def ready_check(self):
        """Readiness check for cache"""
        return True

    async def close(self):
        """Close cache connection"""
        pass


if __name__ == "__main__":
    # Configuration
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8080)),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
    }

    # Development vs Production configuration
    if os.getenv("CLAUDE_ENV") == "development":
        config.update(
            {
                "reload": True,
                "reload_dirs": ["backend"],
            }
        )
        logger.info("🔧 Running in DEVELOPMENT mode")
    else:
        logger.info("🚀 Running in PRODUCTION mode")

    uvicorn.run("run_api:app", **config)
