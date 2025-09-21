#!/usr/bin/env python3
"""
Perfect21 Claude Enhancer - Main Application Entry Point
A production-ready FastAPI application for AI-driven development workflows
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from starlette.middleware.sessions import SessionMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import structlog

# Application imports
from backend.core import (
    agent_scheduler,
    state_manager,
    hook_system,
    controller_manager
)
from backend.api.routes import (
    auth_routes,
    agent_routes,
    workflow_routes,
    health_routes
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""

    # Startup
    logger.info("Starting Perfect21 Claude Enhancer...")

    try:
        # Initialize core systems
        await state_manager.initialize()
        await hook_system.initialize()
        await agent_scheduler.initialize()
        await controller_manager.initialize()

        logger.info("All systems initialized successfully")

        yield

    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        sys.exit(1)

    finally:
        # Shutdown
        logger.info("Shutting down Perfect21 Claude Enhancer...")

        await controller_manager.shutdown()
        await agent_scheduler.shutdown()
        await hook_system.shutdown()
        await state_manager.shutdown()

        logger.info("Shutdown complete")

# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    # Environment configuration
    env = os.getenv("CLAUDE_ENV", "development")
    debug = env == "development"

    # Create app with lifespan management
    app = FastAPI(
        title="Perfect21 Claude Enhancer",
        description="AI-driven development workflow system for non-programmers",
        version="1.0.0",
        debug=debug,
        lifespan=lifespan,
        docs_url=None,  # Custom docs endpoint
        redoc_url=None,
        openapi_url="/api/v1/openapi.json"
    )

    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "your-super-secret-application-key-change-this-in-production")
    )

    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Request middleware for metrics
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        with REQUEST_DURATION.time():
            response = await call_next(request)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            return response

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "HTTP exception occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception occurred",
            error=str(exc),
            path=request.url.path,
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
                "path": request.url.path
            }
        )

    # Include API routes
    app.include_router(health_routes.router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(agent_routes.router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(workflow_routes.router, prefix="/api/v1/workflows", tags=["Workflows"])

    # Custom OpenAPI documentation
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Interactive API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css",
        )

    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "Perfect21 Claude Enhancer API",
            "version": app.version,
            "status": "running",
            "environment": env,
            "docs": "/docs",
            "metrics": "/metrics"
        }

    return app

# Create the application instance
app = create_app()

# Main entry point for direct execution
if __name__ == "__main__":
    # Configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    workers = int(os.getenv("WORKERS", "1"))
    env = os.getenv("CLAUDE_ENV", "development")

    # Logging configuration
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "handlers": ["default"],
        },
    }

    if env == "development":
        # Development mode with hot reload
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_config=log_config,
            access_log=True
        )
    else:
        # Production mode
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers,
            log_config=log_config,
            access_log=True
        )