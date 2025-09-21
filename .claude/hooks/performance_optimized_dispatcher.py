#!/usr/bin/env python3
"""
High-Performance Claude Enhancer Dispatcher
Optimized for minimal latency and maximum throughput
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import pickle
from pathlib import Path

# Configure high-performance logging
class FastLogger:
    """Ultra-fast logger with memory buffering"""
    def __init__(self, buffer_size=1000):
        self.buffer = []
        self.buffer_size = buffer_size
        self.lock = threading.Lock()

    def log(self, level: str, message: str):
        with self.lock:
            self.buffer.append(f"{time.time():.3f}|{level}|{message}")
            if len(self.buffer) >= self.buffer_size:
                self._flush()

    def _flush(self):
        """Flush buffer to file asynchronously"""
        if self.buffer:
            log_data = '\n'.join(self.buffer) + '\n'
            self.buffer.clear()
            # Non-blocking write
            threading.Thread(
                target=self._write_to_file,
                args=(log_data,),
                daemon=True
            ).start()

    def _write_to_file(self, data: str):
        try:
            with open('/tmp/claude_enhancer_perf.log', 'a') as f:
                f.write(data)
        except:
            pass  # Silent fail for performance

# Global fast logger instance
fast_logger = FastLogger()

@dataclass
class CachedValidation:
    """Cached validation result"""
    result: bool
    agents: List[str]
    timestamp: float
    task_type: str

class PerformanceOptimizedDispatcher:
    """High-performance dispatcher with aggressive caching and optimization"""

    def __init__(self):
        # Performance-critical settings
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.max_cache_size = 1000

        # Pre-compiled patterns for speed
        self._compile_patterns()

        # Pre-loaded agent mappings
        self.agent_mappings = self._load_agent_mappings()

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="claude_perf")

        # Statistics for optimization
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'validations': 0,
            'avg_latency': 0.0
        }

    def _compile_patterns(self):
        """Pre-compile regex patterns for maximum speed"""
        import re

        self.patterns = {
            'agent_extract': re.compile(r'"subagent_type"\s*:\s*"([^"]+)"'),
            'prompt_extract': re.compile(r'"prompt"\s*:\s*"([^"]*?)"'),
            'task_patterns': {
                'auth': re.compile(r'\b(?:登录|认证|auth|jwt|oauth|用户|权限|session|password)\b', re.I),
                'api': re.compile(r'\b(?:api|接口|rest|graphql|endpoint|route|swagger)\b', re.I),
                'db': re.compile(r'\b(?:数据库|database|schema|sql|mongodb|redis|表结构|migration)\b', re.I),
                'frontend': re.compile(r'\b(?:前端|frontend|react|vue|ui|组件|页面|component|界面)\b', re.I),
                'perf': re.compile(r'\b(?:性能|优化|performance|速度|缓存|optimize|cache)\b', re.I),
                'test': re.compile(r'\b(?:测试|test|spec|jest|mocha|pytest|unit|e2e|integration)\b', re.I)
            }
        }

    def _load_agent_mappings(self) -> Dict[str, List[str]]:
        """Pre-load agent mappings for instant lookup"""
        return {
            'auth': ['backend-architect', 'security-auditor', 'test-engineer', 'api-designer', 'database-specialist'],
            'api': ['api-designer', 'backend-architect', 'test-engineer', 'technical-writer'],
            'db': ['database-specialist', 'backend-architect', 'performance-engineer'],
            'frontend': ['frontend-specialist', 'ux-designer', 'test-engineer'],
            'perf': ['performance-engineer', 'backend-architect', 'monitoring-specialist'],
            'test': ['test-engineer', 'e2e-test-specialist', 'performance-tester'],
            'general': ['backend-architect', 'test-engineer', 'technical-writer']
        }

    def _get_cache_key(self, input_data: str) -> str:
        """Generate cache key from input"""
        return hashlib.md5(input_data.encode()).hexdigest()[:16]

    def _is_cache_valid(self, cached: CachedValidation) -> bool:
        """Check if cache entry is still valid"""
        return (time.time() - cached.timestamp) < self.cache_ttl

    def fast_validate(self, input_data: str) -> Tuple[bool, Dict[str, Any]]:
        """Ultra-fast validation with aggressive caching"""
        start_time = time.time()

        # Check cache first
        cache_key = self._get_cache_key(input_data)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if self._is_cache_valid(cached):
                self.stats['cache_hits'] += 1
                fast_logger.log('DEBUG', f'Cache hit: {cache_key}')
                return cached.result, {
                    'agents': cached.agents,
                    'task_type': cached.task_type,
                    'cached': True,
                    'latency': time.time() - start_time
                }

        self.stats['cache_misses'] += 1

        # Fast extraction using pre-compiled patterns
        agents = self.patterns['agent_extract'].findall(input_data)
        prompt_match = self.patterns['prompt_extract'].search(input_data)
        prompt = prompt_match.group(1) if prompt_match else ""

        # Fast task type detection
        task_type = self._fast_task_detection(prompt)

        # Quick validation
        agent_count = len(agents)
        is_valid = agent_count >= 3

        # Cache the result
        result_obj = CachedValidation(
            result=is_valid,
            agents=agents,
            timestamp=time.time(),
            task_type=task_type
        )

        # Manage cache size
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest 20% of entries
            sorted_cache = sorted(
                self.cache.items(),
                key=lambda x: x[1].timestamp
            )
            for key, _ in sorted_cache[:int(self.max_cache_size * 0.2)]:
                del self.cache[key]

        self.cache[cache_key] = result_obj

        latency = time.time() - start_time
        self.stats['validations'] += 1
        self.stats['avg_latency'] = (
            (self.stats['avg_latency'] * (self.stats['validations'] - 1) + latency)
            / self.stats['validations']
        )

        fast_logger.log('INFO', f'Validation: {agent_count} agents, {task_type}, {latency:.3f}s')

        return is_valid, {
            'agents': agents,
            'task_type': task_type,
            'agent_count': agent_count,
            'cached': False,
            'latency': latency
        }

    def _fast_task_detection(self, prompt: str) -> str:
        """Ultra-fast task type detection using pre-compiled patterns"""
        prompt_lower = prompt.lower()

        # Check patterns in priority order
        for task_type, pattern in self.patterns['task_patterns'].items():
            if pattern.search(prompt_lower):
                return task_type

        return 'general'

    def get_suggested_agents(self, task_type: str, current_agents: List[str]) -> List[str]:
        """Get suggested agents for task type"""
        required = self.agent_mappings.get(task_type, self.agent_mappings['general'])
        missing = [agent for agent in required if agent not in current_agents]
        return missing

    def generate_fast_response(self, validation_result: Dict[str, Any]) -> str:
        """Generate optimized response based on validation"""
        if validation_result['cached']:
            return ""  # No output for cached valid results

        agents = validation_result['agents']
        task_type = validation_result['task_type']
        agent_count = validation_result.get('agent_count', len(agents))

        if agent_count < 3:
            missing_agents = self.get_suggested_agents(task_type, agents)
            return f"""❌ Need {3 - agent_count} more agents. Suggested: {', '.join(missing_agents[:3-agent_count])}"""

        return ""  # Valid, no output needed

    def cleanup_cache(self):
        """Cleanup expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, cached in self.cache.items()
            if (current_time - cached.timestamp) > self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_hit_rate = (
            self.stats['cache_hits'] / max(1, self.stats['cache_hits'] + self.stats['cache_misses'])
        ) * 100

        return {
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'avg_latency': f"{self.stats['avg_latency']:.3f}s",
            'cache_size': len(self.cache),
            'total_validations': self.stats['validations']
        }

# Global dispatcher instance for reuse
_dispatcher_instance = None

def get_dispatcher():
    """Get singleton dispatcher instance"""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = PerformanceOptimizedDispatcher()
    return _dispatcher_instance

def fast_hook_main():
    """Ultra-fast main function for hook execution"""
    # Read input efficiently
    input_data = sys.stdin.read()

    # Skip processing for non-Task operations
    if '"subagent_type"' not in input_data:
        print(input_data)
        return

    # Get dispatcher and validate
    dispatcher = get_dispatcher()
    is_valid, result = dispatcher.fast_validate(input_data)

    if not is_valid:
        response = dispatcher.generate_fast_response(result)
        if response:
            print(response, file=sys.stderr)
            sys.exit(1)

    # Output original input for valid cases
    print(input_data)

def periodic_cleanup():
    """Periodic cleanup function"""
    dispatcher = get_dispatcher()
    dispatcher.cleanup_cache()

    # Log performance stats periodically
    if dispatcher.stats['validations'] % 100 == 0:
        stats = dispatcher.get_performance_stats()
        fast_logger.log('INFO', f"Performance stats: {stats}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        # Output performance statistics
        dispatcher = get_dispatcher()
        stats = dispatcher.get_performance_stats()
        print(json.dumps(stats, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        # Manual cleanup
        dispatcher = get_dispatcher()
        dispatcher.cleanup_cache()
        print("Cache cleaned")
    else:
        # Normal hook execution
        try:
            fast_hook_main()
        finally:
            # Periodic cleanup
            periodic_cleanup()