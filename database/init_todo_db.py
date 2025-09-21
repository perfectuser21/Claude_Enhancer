#!/usr/bin/env python3
"""
Database initialization script for Todo system.
Production-ready initialization with error handling, logging, and validation.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.models.base import Base
from backend.models.todo_models import *


# =============================================================================
# CONFIGURATION
# =============================================================================

class DatabaseConfig:
    """Database configuration class."""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", 5432))
        self.database = os.getenv("DB_NAME", "perfect21")
        self.username = os.getenv("DB_USERNAME", "postgres")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.ssl_mode = os.getenv("DB_SSL_MODE", "prefer")

        # Async connection string
        self.async_url = (
            f"postgresql+asyncpg://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

        # Sync connection string
        self.sync_url = (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def __repr__(self):
        return f"DatabaseConfig(host={self.host}, port={self.port}, database={self.database})"


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("todo_db_init.log")
    ]
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATABASE INITIALIZATION FUNCTIONS
# =============================================================================

async def check_database_connection(config: DatabaseConfig) -> bool:
    """Check if database connection is working."""
    try:
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password
        )
        await conn.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def create_database_if_not_exists(config: DatabaseConfig) -> bool:
    """Create database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database="postgres",
            user=config.username,
            password=config.password
        )

        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            config.database
        )

        if not db_exists:
            logger.info(f"Creating database: {config.database}")
            await conn.execute(f'CREATE DATABASE "{config.database}"')
            logger.info("✅ Database created successfully")
        else:
            logger.info(f"Database {config.database} already exists")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False


async def create_extensions(config: DatabaseConfig) -> bool:
    """Create required PostgreSQL extensions."""
    try:
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password
        )

        extensions = [
            "uuid-ossp",
            "btree_gin",
            "pg_trgm"  # For better text search
        ]

        for ext in extensions:
            try:
                await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                logger.info(f"✅ Extension {ext} enabled")
            except Exception as e:
                logger.warning(f"⚠️ Could not enable extension {ext}: {e}")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create extensions: {e}")
        return False


def create_schema_and_tables(config: DatabaseConfig) -> bool:
    """Create database schema and tables using SQLAlchemy."""
    try:
        # Create sync engine for schema creation
        engine = create_engine(config.sync_url, echo=True)

        # Create all tables
        logger.info("Creating database schema and tables...")
        Base.metadata.create_all(engine)

        logger.info("✅ Schema and tables created successfully")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'todo'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")

        engine.dispose()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create schema and tables: {e}")
        return False


async def run_sql_script(config: DatabaseConfig, script_path: str) -> bool:
    """Run SQL script file."""
    try:
        if not Path(script_path).exists():
            logger.warning(f"SQL script not found: {script_path}")
            return False

        with open(script_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password
        )

        # Execute SQL script
        await conn.execute(sql_content)
        logger.info(f"✅ SQL script executed: {script_path}")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to run SQL script {script_path}: {e}")
        return False


async def verify_installation(config: DatabaseConfig) -> bool:
    """Verify the database installation is complete and working."""
    try:
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password
        )

        # Check schema exists
        schema_exists = await conn.fetchval(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'todo'"
        )

        if not schema_exists:
            logger.error("❌ Todo schema not found")
            return False

        # Check required tables exist
        required_tables = [
            "users", "categories", "items", "attachments",
            "comments", "shared_todos", "activity_log"
        ]

        for table in required_tables:
            table_exists = await conn.fetchval(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'todo' AND table_name = $1
                """,
                table
            )

            if not table_exists:
                logger.error(f"❌ Required table not found: todo.{table}")
                return False
            else:
                logger.info(f"✅ Table verified: todo.{table}")

        # Check functions exist
        functions = [
            "update_updated_at_column",
            "get_user_stats",
            "search_todos"
        ]

        for func in functions:
            func_exists = await conn.fetchval(
                """
                SELECT 1 FROM information_schema.routines
                WHERE routine_schema = 'todo' AND routine_name = $1
                """,
                func
            )

            if func_exists:
                logger.info(f"✅ Function verified: todo.{func}")
            else:
                logger.warning(f"⚠️ Function not found: todo.{func}")

        # Test a simple query
        user_count = await conn.fetchval("SELECT COUNT(*) FROM todo.users")
        logger.info(f"✅ Database query test successful (users: {user_count})")

        await conn.close()
        logger.info("✅ Database installation verification completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False


async def create_sample_data(config: DatabaseConfig) -> bool:
    """Create sample data for development/testing."""
    try:
        # Create async engine and session
        engine = create_async_engine(config.async_url)
        SessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with SessionLocal() as session:
            # Create sample user
            sample_user = User(
                email="demo@example.com",
                username="demo_user",
                password_hash="$2b$12$dummy_hash_for_demo",  # In real app, hash properly
                first_name="Demo",
                last_name="User",
                is_verified=True
            )
            session.add(sample_user)
            await session.flush()  # Get the user ID

            # Create sample categories
            categories = [
                Category(
                    user_id=sample_user.id,
                    name="Work",
                    description="Work-related tasks",
                    color="#dc3545",
                    icon="briefcase"
                ),
                Category(
                    user_id=sample_user.id,
                    name="Personal",
                    description="Personal tasks and goals",
                    color="#28a745",
                    icon="user"
                ),
                Category(
                    user_id=sample_user.id,
                    name="Learning",
                    description="Educational and skill development",
                    color="#ffc107",
                    icon="book"
                )
            ]

            for category in categories:
                session.add(category)

            await session.flush()  # Get category IDs

            # Create sample todos
            sample_todos = [
                TodoItem(
                    user_id=sample_user.id,
                    category_id=categories[0].id,
                    title="Complete quarterly report",
                    description="Finish Q3 financial analysis and projections",
                    priority=PriorityLevel.HIGH,
                    status=StatusType.IN_PROGRESS,
                    progress_percentage=60,
                    tags=["work", "report", "finance"]
                ),
                TodoItem(
                    user_id=sample_user.id,
                    category_id=categories[1].id,
                    title="Plan weekend trip",
                    description="Research destinations and book accommodation",
                    priority=PriorityLevel.MEDIUM,
                    status=StatusType.PENDING,
                    tags=["travel", "personal", "weekend"]
                ),
                TodoItem(
                    user_id=sample_user.id,
                    category_id=categories[2].id,
                    title="Learn Python FastAPI",
                    description="Complete FastAPI tutorial and build sample project",
                    priority=PriorityLevel.MEDIUM,
                    status=StatusType.PENDING,
                    estimated_hours=20.0,
                    tags=["learning", "python", "api"]
                ),
                TodoItem(
                    user_id=sample_user.id,
                    title="Buy groceries",
                    description="Milk, bread, eggs, vegetables",
                    priority=PriorityLevel.LOW,
                    status=StatusType.COMPLETED,
                    progress_percentage=100,
                    tags=["shopping", "daily"]
                )
            ]

            for todo in sample_todos:
                session.add(todo)

            await session.commit()
            logger.info("✅ Sample data created successfully")

        await engine.dispose()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")
        return False


# =============================================================================
# MAIN INITIALIZATION FUNCTION
# =============================================================================

async def initialize_database(
    config: Optional[DatabaseConfig] = None,
    create_sample: bool = False,
    run_sql: bool = True
) -> bool:
    """
    Initialize the todo database with complete setup.

    Args:
        config: Database configuration (uses env vars if None)
        create_sample: Whether to create sample data
        run_sql: Whether to run the SQL schema script

    Returns:
        True if initialization successful, False otherwise
    """
    if config is None:
        config = DatabaseConfig()

    logger.info("🚀 Starting Todo database initialization")
    logger.info(f"Configuration: {config}")

    # Step 1: Create database if needed
    if not await create_database_if_not_exists(config):
        return False

    # Step 2: Check connection
    if not await check_database_connection(config):
        return False

    # Step 3: Create extensions
    if not await create_extensions(config):
        return False

    # Step 4: Run SQL schema script if requested
    if run_sql:
        script_path = Path(__file__).parent / "todo_schema.sql"
        if not await run_sql_script(config, str(script_path)):
            logger.warning("SQL script execution failed, trying SQLAlchemy...")

    # Step 5: Create schema and tables with SQLAlchemy
    if not create_schema_and_tables(config):
        return False

    # Step 6: Verify installation
    if not await verify_installation(config):
        return False

    # Step 7: Create sample data if requested
    if create_sample:
        if not await create_sample_data(config):
            logger.warning("Sample data creation failed, but continuing...")

    logger.info("🎉 Todo database initialization completed successfully!")
    return True


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize Todo Database")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Create sample data for development"
    )
    parser.add_argument(
        "--no-sql",
        action="store_true",
        help="Skip running SQL schema script"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Database host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="Database port"
    )
    parser.add_argument(
        "--database",
        default="perfect21",
        help="Database name"
    )
    parser.add_argument(
        "--username",
        default="postgres",
        help="Database username"
    )
    parser.add_argument(
        "--password",
        help="Database password (or use DB_PASSWORD env var)"
    )

    args = parser.parse_args()

    # Create config from CLI args
    config = DatabaseConfig()
    config.host = args.host
    config.port = args.port
    config.database = args.database
    config.username = args.username

    if args.password:
        config.password = args.password

    # Update connection strings
    config.async_url = (
        f"postgresql+asyncpg://{config.username}:{config.password}@"
        f"{config.host}:{config.port}/{config.database}"
    )
    config.sync_url = (
        f"postgresql://{config.username}:{config.password}@"
        f"{config.host}:{config.port}/{config.database}"
    )

    # Run initialization
    success = await initialize_database(
        config=config,
        create_sample=args.sample,
        run_sql=not args.no_sql
    )

    if success:
        logger.info("✅ Database initialization completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Database initialization failed!")
        sys.exit(1)


# =============================================================================
# UTILITY FUNCTIONS FOR EXTERNAL USE
# =============================================================================

async def get_database_stats(config: Optional[DatabaseConfig] = None) -> dict:
    """Get database statistics."""
    if config is None:
        config = DatabaseConfig()

    try:
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password
        )

        stats = {}

        # Table row counts
        tables = ["users", "categories", "items", "attachments", "comments", "shared_todos", "activity_log"]
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM todo.{table}")
            stats[f"{table}_count"] = count

        # Database size
        db_size = await conn.fetchval(
            "SELECT pg_size_pretty(pg_database_size($1))",
            config.database
        )
        stats["database_size"] = db_size

        await conn.close()
        return stats

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


if __name__ == "__main__":
    asyncio.run(main())