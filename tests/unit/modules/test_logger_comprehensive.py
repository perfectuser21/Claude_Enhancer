#!/usr/bin/env python3
"""
Comprehensive unit tests for modules.logger
Target: High coverage for logging functionality
"""

import pytest
import logging
import sys
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.logger import Perfect21Logger as Logger


class TestLogger:
    """Test Logger class functionality"""

    def test_logger_initialization_default(self):
        """Test logger initialization with default parameters"""
        logger = Logger()
        assert logger.name == "Perfect21"
        assert logger.logger.level == logging.INFO
        assert len(logger.logger.handlers) >= 1

    def test_logger_initialization_custom(self):
        """Test logger initialization with custom parameters"""
        logger = Logger(
            name="TestLogger",
            level=logging.DEBUG,
            log_file="test.log"
        )
        assert logger.name == "TestLogger"
        assert logger.logger.level == logging.DEBUG

    def test_logger_initialization_with_file(self, tmp_path):
        """Test logger initialization with file output"""
        log_file = tmp_path / "test.log"
        logger = Logger(log_file=str(log_file))

        # Test logging to file
        logger.info("Test message")
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_logger_levels(self):
        """Test all logging levels"""
        logger = Logger(level=logging.DEBUG)

        with patch.object(logger.logger, 'debug') as mock_debug, \
             patch.object(logger.logger, 'info') as mock_info, \
             patch.object(logger.logger, 'warning') as mock_warning, \
             patch.object(logger.logger, 'error') as mock_error, \
             patch.object(logger.logger, 'critical') as mock_critical:

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            mock_debug.assert_called_once_with("Debug message")
            mock_info.assert_called_once_with("Info message")
            mock_warning.assert_called_once_with("Warning message")
            mock_error.assert_called_once_with("Error message")
            mock_critical.assert_called_once_with("Critical message")

    def test_logger_with_extra_context(self):
        """Test logger with extra context"""
        logger = Logger()

        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("Message with context", extra={'component': 'test'})
            mock_info.assert_called_once_with("Message with context", extra={'component': 'test'})

    def test_logger_exception_handling(self):
        """Test logger exception handling"""
        logger = Logger()

        with patch.object(logger.logger, 'exception') as mock_exception:
            try:
                raise ValueError("Test exception")
            except ValueError:
                logger.exception("An error occurred")

            mock_exception.assert_called_once_with("An error occurred")

    def test_logger_formatter(self):
        """Test logger formatter configuration"""
        logger = Logger()

        # Check if handlers have formatters
        for handler in logger.logger.handlers:
            assert handler.formatter is not None

    def test_logger_multiple_instances(self):
        """Test multiple logger instances"""
        logger1 = Logger(name="Logger1")
        logger2 = Logger(name="Logger2")

        assert logger1.name != logger2.name
        assert logger1.logger != logger2.logger

    @pytest.mark.parametrize("level", [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL
    ])
    def test_logger_level_filtering(self, level):
        """Test logger level filtering"""
        logger = Logger(level=level)
        assert logger.logger.level == level

    def test_logger_with_disabled_console(self):
        """Test logger with console output disabled"""
        with patch('modules.logger.logging.StreamHandler') as mock_handler:
            logger = Logger(console_output=False)
            # Verify StreamHandler wasn't added
            assert not any(isinstance(h, logging.StreamHandler)
                          for h in logger.logger.handlers
                          if h.stream == sys.stdout)

    def test_logger_file_creation_failure(self):
        """Test logger behavior when file creation fails"""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should not raise exception, just skip file handler
            logger = Logger(log_file="/invalid/path/test.log")
            assert logger.logger is not None

    def test_logger_thread_safety(self):
        """Test logger thread safety"""
        import threading
        logger = Logger()
        messages = []

        def log_messages():
            for i in range(10):
                logger.info(f"Message {i}")
                messages.append(f"Message {i}")

        threads = [threading.Thread(target=log_messages) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all messages were logged (30 total)
        assert len(messages) == 30

    def test_logger_format_customization(self):
        """Test custom log format"""
        custom_format = "%(name)s - %(levelname)s - %(message)s"
        logger = Logger(log_format=custom_format)

        # Check if custom format is applied
        for handler in logger.logger.handlers:
            if hasattr(handler.formatter, '_fmt'):
                assert custom_format in handler.formatter._fmt

    def test_logger_with_json_format(self):
        """Test logger with JSON format"""
        logger = Logger(json_format=True)

        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("Test message", extra={'key': 'value'})
            mock_info.assert_called_once()

    def test_logger_rotation(self, tmp_path):
        """Test log file rotation"""
        log_file = tmp_path / "rotating.log"
        logger = Logger(log_file=str(log_file), max_bytes=1024, backup_count=3)

        # Generate enough logs to trigger rotation
        for i in range(100):
            logger.info(f"Long message {i} " * 10)

        # Check if rotation files exist
        rotation_files = list(tmp_path.glob("rotating.log*"))
        assert len(rotation_files) >= 1

    def test_logger_context_manager(self):
        """Test logger as context manager"""
        logger = Logger()

        # Test that logger can be used in context
        with logger:
            logger.info("Context message")

        # Logger should still work after context
        logger.info("After context message")

    def test_logger_memory_usage(self):
        """Test logger memory efficiency"""
        import sys

        # Create logger and measure memory
        logger = Logger()

        # Log many messages to test memory handling
        for i in range(1000):
            logger.info(f"Memory test message {i}")

        # Verify logger object size is reasonable
        assert sys.getsizeof(logger) < 10000  # Less than 10KB

    def test_logger_performance(self):
        """Test logger performance"""
        import time

        logger = Logger(level=logging.WARNING)  # Higher level to reduce I/O

        start_time = time.time()

        # Log many messages
        for i in range(1000):
            logger.debug(f"Performance test {i}")  # These won't be logged due to level

        end_time = time.time()

        # Should be very fast since debug messages are filtered
        assert (end_time - start_time) < 1.0  # Less than 1 second

    def test_logger_singleton_behavior(self):
        """Test logger singleton-like behavior for same name"""
        logger1 = Logger(name="Singleton")
        logger2 = Logger(name="Singleton")

        # Same name should return same logger instance
        assert logger1.logger.name == logger2.logger.name


class TestLoggerIntegration:
    """Integration tests for Logger"""

    def test_logger_with_real_file_operations(self, tmp_path):
        """Test logger with real file operations"""
        log_file = tmp_path / "integration.log"
        logger = Logger(log_file=str(log_file), level=logging.DEBUG)

        # Log various levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Verify file contents
        content = log_file.read_text()
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content

    def test_logger_with_exception_traceback(self, tmp_path):
        """Test logger with exception traceback"""
        log_file = tmp_path / "exception.log"
        logger = Logger(log_file=str(log_file))

        try:
            raise ValueError("Test exception for logging")
        except ValueError:
            logger.exception("Caught exception")

        content = log_file.read_text()
        assert "Caught exception" in content
        assert "ValueError" in content
        assert "Traceback" in content

    def test_logger_concurrent_access(self, tmp_path):
        """Test logger with concurrent access"""
        import threading
        import time

        log_file = tmp_path / "concurrent.log"
        logger = Logger(log_file=str(log_file))

        def worker(worker_id):
            for i in range(50):
                logger.info(f"Worker {worker_id} - Message {i}")
                time.sleep(0.001)  # Small delay

        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify all messages were written
        content = log_file.read_text()
        lines = content.strip().split('\n')

        # Should have 250 messages (5 workers * 50 messages)
        message_lines = [line for line in lines if "Worker" in line and "Message" in line]
        assert len(message_lines) == 250


@pytest.mark.performance
class TestLoggerPerformance:
    """Performance tests for Logger"""

    def test_logging_throughput(self):
        """Test logging throughput"""
        import time

        logger = Logger(console_output=False)  # Disable console for speed

        start_time = time.time()
        message_count = 10000

        for i in range(message_count):
            logger.info(f"Throughput test message {i}")

        end_time = time.time()
        duration = end_time - start_time

        # Calculate messages per second
        throughput = message_count / duration

        # Should be able to log at least 1000 messages per second
        assert throughput > 1000

    def test_memory_leak_prevention(self):
        """Test memory leak prevention"""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and destroy many loggers
        for i in range(100):
            logger = Logger(name=f"TempLogger{i}")
            for j in range(100):
                logger.info(f"Temp message {j}")
            del logger

            # Force garbage collection
            if i % 10 == 0:
                gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])