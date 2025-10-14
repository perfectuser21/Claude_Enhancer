"""
Logging Utilities
Centralized logging configuration for Claude Enhancer
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# Default log format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: str = LOG_FORMAT,
) -> logging.Logger:
    """
    Setup a logger with console and optional file output

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional file path for logging
        format_string: Log format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default configuration

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class LogContext:
    """Context manager for temporary log level changes"""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.new_level = level
        self.old_level = logger.level

    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


def log_execution_time(logger: logging.Logger):
    """Decorator to log function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Starting {func.__name__}")
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"{func.__name__} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator
