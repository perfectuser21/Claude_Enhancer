#!/usr/bin/env python3
"""
Optimized Logging System for Claude Enhancer
Minimal overhead with intelligent buffering and compression
"""

import os
import sys
import time
import threading
import gzip
import json
from collections import deque
from typing import Dict, Any, Optional
from pathlib import Path
import atexit

class OptimizedLogger:
    """High-performance logger with intelligent buffering"""

    def __init__(self,
                 log_dir: str = "/tmp/claude_enhancer_logs",
                 buffer_size: int = 500,
                 compress_after: int = 1000,
                 auto_cleanup_days: int = 7):

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.buffer_size = buffer_size
        self.compress_after = compress_after
        self.auto_cleanup_days = auto_cleanup_days

        # In-memory buffer with thread safety
        self.buffer = deque(maxlen=buffer_size)
        self.buffer_lock = threading.Lock()

        # Performance counters
        self.counters = {
            'logs_written': 0,
            'logs_compressed': 0,
            'logs_dropped': 0,
            'buffer_flushes': 0
        }

        # Current log file
        self.current_log = self.log_dir / f"claude_enhancer_{int(time.time())}.log"

        # Background thread for async operations
        self.bg_thread = None
        self.bg_queue = deque()
        self.bg_lock = threading.Lock()
        self.shutdown = False

        self._start_background_thread()

        # Register cleanup on exit
        atexit.register(self.shutdown_logger)

    def _start_background_thread(self):
        """Start background thread for async operations"""
        self.bg_thread = threading.Thread(
            target=self._background_worker,
            daemon=True,
            name="ClaudeEnhancerLogger"
        )
        self.bg_thread.start()

    def _background_worker(self):
        """Background worker for async file operations"""
        while not self.shutdown:
            try:
                # Process background tasks
                with self.bg_lock:
                    if self.bg_queue:
                        task = self.bg_queue.popleft()
                        self._execute_background_task(task)

                # Periodic cleanup
                if int(time.time()) % 3600 == 0:  # Every hour
                    self._cleanup_old_logs()

                time.sleep(0.1)  # Small delay to prevent CPU spinning

            except Exception:
                pass  # Silent fail to maintain performance

    def _execute_background_task(self, task: Dict[str, Any]):
        """Execute background task"""
        task_type = task.get('type')

        if task_type == 'flush_buffer':
            self._flush_buffer_to_file(task['data'])
        elif task_type == 'compress_file':
            self._compress_log_file(task['file_path'])
        elif task_type == 'cleanup':
            self._cleanup_old_logs()

    def log(self, level: str, message: str, extra: Optional[Dict] = None):
        """Log message with minimal overhead"""
        timestamp = time.time()

        # Create log entry
        entry = {
            'ts': timestamp,
            'level': level,
            'msg': message[:1000],  # Truncate long messages
        }

        if extra:
            entry['extra'] = {k: str(v)[:100] for k, v in extra.items()}  # Limit extra data

        # Add to buffer with thread safety
        with self.buffer_lock:
            if len(self.buffer) >= self.buffer_size:
                # Buffer full, schedule async flush
                self._schedule_buffer_flush()

            self.buffer.append(entry)

        # Auto-flush for critical errors
        if level == 'ERROR':
            self._schedule_buffer_flush()

    def _schedule_buffer_flush(self):
        """Schedule buffer flush in background"""
        with self.buffer_lock:
            if self.buffer:
                buffer_data = list(self.buffer)
                self.buffer.clear()

                with self.bg_lock:
                    self.bg_queue.append({
                        'type': 'flush_buffer',
                        'data': buffer_data
                    })

                self.counters['buffer_flushes'] += 1

    def _flush_buffer_to_file(self, buffer_data: list):
        """Flush buffer data to file"""
        try:
            with open(self.current_log, 'a') as f:
                for entry in buffer_data:
                    # Fast JSON serialization
                    json_line = json.dumps(entry, separators=(',', ':'))
                    f.write(json_line + '\n')

            self.counters['logs_written'] += len(buffer_data)

            # Check if file needs compression
            if self.current_log.stat().st_size > self.compress_after:
                self._schedule_compression(self.current_log)
                # Start new log file
                self.current_log = self.log_dir / f"claude_enhancer_{int(time.time())}.log"

        except Exception:
            self.counters['logs_dropped'] += len(buffer_data)

    def _schedule_compression(self, file_path: Path):
        """Schedule file compression"""
        with self.bg_lock:
            self.bg_queue.append({
                'type': 'compress_file',
                'file_path': str(file_path)
            })

    def _compress_log_file(self, file_path: str):
        """Compress log file to save space"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return

            compressed_path = source_path.with_suffix('.log.gz')

            with open(source_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Remove original file
            source_path.unlink()
            self.counters['logs_compressed'] += 1

        except Exception:
            pass  # Silent fail

    def _cleanup_old_logs(self):
        """Cleanup old log files"""
        try:
            cutoff_time = time.time() - (self.auto_cleanup_days * 24 * 3600)

            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()

        except Exception:
            pass  # Silent fail

    def force_flush(self):
        """Force immediate flush of buffer"""
        with self.buffer_lock:
            if self.buffer:
                buffer_data = list(self.buffer)
                self.buffer.clear()
                self._flush_buffer_to_file(buffer_data)

    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics"""
        return {
            'counters': self.counters.copy(),
            'buffer_size': len(self.buffer),
            'log_dir_size': sum(f.stat().st_size for f in self.log_dir.glob("*") if f.is_file()),
            'current_log': str(self.current_log),
            'background_queue_size': len(self.bg_queue)
        }

    def shutdown_logger(self):
        """Shutdown logger gracefully"""
        self.shutdown = True

        # Flush remaining buffer
        self.force_flush()

        # Wait for background thread
        if self.bg_thread and self.bg_thread.is_alive():
            self.bg_thread.join(timeout=2.0)

# Global logger instances
_performance_logger = None
_error_logger = None

def get_performance_logger():
    """Get performance logger instance"""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = OptimizedLogger(
            log_dir="/tmp/claude_enhancer_perf",
            buffer_size=1000,
            compress_after=5000
        )
    return _performance_logger

def get_error_logger():
    """Get error logger instance"""
    global _error_logger
    if _error_logger is None:
        _error_logger = OptimizedLogger(
            log_dir="/tmp/claude_enhancer_errors",
            buffer_size=100,
            compress_after=1000
        )
    return _error_logger

# Convenience functions
def log_performance(message: str, **extra):
    """Log performance information"""
    get_performance_logger().log('PERF', message, extra)

def log_error(message: str, **extra):
    """Log error information"""
    get_error_logger().log('ERROR', message, extra)

def log_info(message: str, **extra):
    """Log general information"""
    get_performance_logger().log('INFO', message, extra)

def log_debug(message: str, **extra):
    """Log debug information"""
    if os.getenv('CLAUDE_ENHANCER_DEBUG'):
        get_performance_logger().log('DEBUG', message, extra)

def cleanup_logs():
    """Manual log cleanup"""
    if _performance_logger:
        _performance_logger._cleanup_old_logs()
    if _error_logger:
        _error_logger._cleanup_old_logs()

def get_logger_stats():
    """Get all logger statistics"""
    stats = {}
    if _performance_logger:
        stats['performance'] = _performance_logger.get_stats()
    if _error_logger:
        stats['error'] = _error_logger.get_stats()
    return stats

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stats":
            stats = get_logger_stats()
            print(json.dumps(stats, indent=2))
        elif command == "cleanup":
            cleanup_logs()
            print("Logs cleaned up")
        elif command == "test":
            # Test the logger
            perf_logger = get_performance_logger()
            error_logger = get_error_logger()

            start_time = time.time()
            for i in range(1000):
                perf_logger.log('TEST', f'Test message {i}', {'iteration': i})

            end_time = time.time()
            print(f"1000 log entries in {end_time - start_time:.3f} seconds")

            # Force flush and show stats
            perf_logger.force_flush()
            stats = perf_logger.get_stats()
            print(f"Stats: {json.dumps(stats, indent=2)}")