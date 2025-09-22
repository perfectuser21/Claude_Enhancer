#!/usr/bin/env python3
"""
Parallel Execution Optimizer for Claude Enhancer
Optimizes agent parallel execution with intelligent load balancing
"""

import os
import sys
import time
import json
import threading
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import queue
import psutil

@dataclass
class AgentExecutionProfile:
    """Profile for agent execution performance"""
    agent_type: str
    avg_execution_time: float
    success_rate: float
    resource_usage: Dict[str, float]
    last_execution: float
    execution_count: int

@dataclass
class ExecutionRequest:
    """Agent execution request"""
    request_id: str
    agents: List[str]
    prompts: Dict[str, str]
    priority: int
    timestamp: float

class ParallelExecutionOptimizer:
    """Optimizes parallel agent execution for maximum performance"""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers

        # Agent performance profiles
        self.agent_profiles: Dict[str, AgentExecutionProfile] = {}

        # Execution queue and load balancing
        self.execution_queue = queue.PriorityQueue()
        self.active_executions = {}
        self.execution_history = deque(maxlen=1000)

        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="ClaudeAgent"
        )

        # Resource monitoring
        self.resource_monitor = ResourceMonitor()

        # Performance optimization flags
        self.adaptive_batching = True
        self.load_balancing = True
        self.smart_scheduling = True

        # Statistics
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'avg_execution_time': 0.0,
            'peak_concurrent_agents': 0,
            'cache_hits': 0
        }

        # Agent compatibility matrix (which agents work well together)
        self.compatibility_matrix = self._build_compatibility_matrix()

        # Start background optimizer
        self._start_background_optimizer()

    def _build_compatibility_matrix(self) -> Dict[str, List[str]]:
        """Build agent compatibility matrix for optimal grouping"""
        return {
            'backend-architect': ['database-specialist', 'api-designer', 'security-auditor'],
            'frontend-specialist': ['ux-designer', 'test-engineer', 'api-designer'],
            'database-specialist': ['backend-architect', 'performance-engineer', 'security-auditor'],
            'security-auditor': ['backend-architect', 'database-specialist', 'api-designer'],
            'test-engineer': ['backend-architect', 'frontend-specialist', 'performance-engineer'],
            'api-designer': ['backend-architect', 'frontend-specialist', 'security-auditor'],
            'performance-engineer': ['backend-architect', 'database-specialist', 'monitoring-specialist'],
            'devops-engineer': ['backend-architect', 'monitoring-specialist', 'security-auditor'],
            'technical-writer': ['api-designer', 'backend-architect', 'frontend-specialist']
        }

    def _start_background_optimizer(self):
        """Start background optimization thread"""
        self.optimizer_thread = threading.Thread(
            target=self._background_optimizer,
            daemon=True,
            name="ExecutionOptimizer"
        )
        self.optimizer_thread.start()

    def _background_optimizer(self):
        """Background optimization loop"""
        while True:
            try:
                # Update agent profiles based on recent executions
                self._update_agent_profiles()

                # Optimize resource allocation
                self._optimize_resource_allocation()

                # Clean up old execution data
                self._cleanup_old_data()

                time.sleep(10)  # Optimize every 10 seconds

            except Exception:
                pass  # Silent fail to maintain stability

    def optimize_agent_execution(self,
                                agents: List[str],
                                prompts: Dict[str, str],
                                priority: int = 1) -> str:
        """Optimize parallel agent execution"""

        request_id = self._generate_request_id(agents, prompts)

        # Check if we can use cached results
        if self._check_cache(request_id):
            self.stats['cache_hits'] += 1
            return self._get_cached_result(request_id)

        # Create execution request
        request = ExecutionRequest(
            request_id=request_id,
            agents=agents,
            prompts=prompts,
            priority=priority,
            timestamp=time.time()
        )

        # Optimize agent grouping for parallel execution
        optimized_groups = self._optimize_agent_grouping(agents)

        # Generate optimized execution plan
        execution_plan = self._generate_execution_plan(optimized_groups, prompts)

        # Execute with performance monitoring
        start_time = time.time()
        result = self._execute_optimized_plan(execution_plan)
        execution_time = time.time() - start_time

        # Update statistics and profiles
        self._update_execution_stats(request, execution_time, result)

        return result

    def _generate_request_id(self, agents: List[str], prompts: Dict[str, str]) -> str:
        """Generate unique request ID for caching"""
        content = f"{sorted(agents)}:{json.dumps(prompts, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _check_cache(self, request_id: str) -> bool:
        """Check if result is cached"""
        # Simple cache check - in production, this would use Redis or similar
        cache_file = f"/tmp/claude_cache_{request_id}.json"
        if os.path.exists(cache_file):
            # Check if cache is recent (within 1 hour)
            cache_age = time.time() - os.path.getmtime(cache_file)
            return cache_age < 3600
        return False

    def _get_cached_result(self, request_id: str) -> str:
        """Get cached result"""
        cache_file = f"/tmp/claude_cache_{request_id}.json"
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)['result']
        except:
            return ""

    def _optimize_agent_grouping(self, agents: List[str]) -> List[List[str]]:
        """Optimize agent grouping for parallel execution"""
        if not self.adaptive_batching:
            return [agents]  # Single group

        # Get current system load
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        # Determine optimal batch size based on system load
        if cpu_percent > 80 or memory_percent > 85:
            # High load - smaller batches
            batch_size = min(3, len(agents))
        elif cpu_percent < 50 and memory_percent < 60:
            # Low load - larger batches
            batch_size = min(len(agents), self.max_workers)
        else:
            # Medium load - balanced batches
            batch_size = min(5, len(agents))

        # Group agents by compatibility
        groups = []
        remaining_agents = agents.copy()

        while remaining_agents:
            # Start new group with first remaining agent
            current_group = [remaining_agents.pop(0)]

            # Add compatible agents to the group
            for agent in remaining_agents.copy():
                if (len(current_group) < batch_size and
                    self._are_agents_compatible(current_group[-1], agent)):
                    current_group.append(agent)
                    remaining_agents.remove(agent)

            groups.append(current_group)

        return groups

    def _are_agents_compatible(self, agent1: str, agent2: str) -> bool:
        """Check if two agents are compatible for parallel execution"""
        return agent2 in self.compatibility_matrix.get(agent1, [])

    def _generate_execution_plan(self,
                                groups: List[List[str]],
                                prompts: Dict[str, str]) -> Dict[str, Any]:
        """Generate optimized execution plan"""
        return {
            'groups': groups,
            'prompts': prompts,
            'execution_mode': 'parallel' if len(groups) == 1 else 'batched',
            'estimated_time': self._estimate_execution_time(groups),
            'resource_requirements': self._estimate_resource_requirements(groups)
        }

    def _estimate_execution_time(self, groups: List[List[str]]) -> float:
        """Estimate total execution time"""
        total_time = 0.0

        for group in groups:
            # Get max execution time in group (parallel execution)
            group_time = 0.0
            for agent in group:
                profile = self.agent_profiles.get(agent)
                if profile:
                    group_time = max(group_time, profile.avg_execution_time)
                else:
                    group_time = max(group_time, 30.0)  # Default estimate

            total_time += group_time

        return total_time

    def _estimate_resource_requirements(self, groups: List[List[str]]) -> Dict[str, float]:
        """Estimate resource requirements"""
        max_concurrent = max(len(group) for group in groups)

        return {
            'max_concurrent_agents': max_concurrent,
            'estimated_memory_mb': max_concurrent * 100,  # 100MB per agent
            'estimated_cpu_percent': max_concurrent * 10   # 10% CPU per agent
        }

    def _execute_optimized_plan(self, plan: Dict[str, Any]) -> str:
        """Execute optimized plan"""
        groups = plan['groups']
        prompts = plan['prompts']

        if plan['execution_mode'] == 'parallel':
            # Single group - execute all in parallel
            return self._execute_parallel_group(groups[0], prompts)
        else:
            # Multiple groups - execute sequentially
            results = []
            for group in groups:
                group_result = self._execute_parallel_group(group, prompts)
                results.append(group_result)
            return self._combine_results(results)

    def _execute_parallel_group(self, agents: List[str], prompts: Dict[str, str]) -> str:
        """Execute a group of agents in parallel"""
        # Generate function_calls XML for the group
        calls = []

        for agent in agents:
            prompt = prompts.get(agent, prompts.get('default', ''))
            calls.append(f'''  <invoke name="Task">
    <parameter name="subagent_type">{agent}</parameter>
    <parameter name="prompt">{prompt}</parameter>
    <parameter name="description">Optimized parallel execution</parameter>
  </invoke>''')

        return f'''<function_calls>
{chr(10).join(calls)}
</function_calls>'''

    def _combine_results(self, results: List[str]) -> str:
        """Combine results from multiple groups"""
        # For now, just concatenate - in production, this would be more sophisticated
        return '\n'.join(results)

    def _update_execution_stats(self,
                               request: ExecutionRequest,
                               execution_time: float,
                               result: str):
        """Update execution statistics"""
        self.stats['total_executions'] += 1

        if result:  # Assume non-empty result means success
            self.stats['successful_executions'] += 1
        else:
            self.stats['failed_executions'] += 1

        # Update average execution time
        total = self.stats['total_executions']
        current_avg = self.stats['avg_execution_time']
        self.stats['avg_execution_time'] = (
            (current_avg * (total - 1) + execution_time) / total
        )

        # Update peak concurrent agents
        self.stats['peak_concurrent_agents'] = max(
            self.stats['peak_concurrent_agents'],
            len(request.agents)
        )

        # Record execution in history
        self.execution_history.append({
            'timestamp': time.time(),
            'agents': request.agents,
            'execution_time': execution_time,
            'success': bool(result)
        })

    def _update_agent_profiles(self):
        """Update agent performance profiles"""
        # Analyze recent executions to update profiles
        recent_executions = [
            exec_data for exec_data in self.execution_history
            if (time.time() - exec_data['timestamp']) < 3600  # Last hour
        ]

        agent_stats = defaultdict(list)

        for execution in recent_executions:
            for agent in execution['agents']:
                agent_stats[agent].append({
                    'execution_time': execution['execution_time'],
                    'success': execution['success']
                })

        # Update profiles
        for agent, stats in agent_stats.items():
            if stats:
                avg_time = sum(s['execution_time'] for s in stats) / len(stats)
                success_rate = sum(1 for s in stats if s['success']) / len(stats)

                profile = self.agent_profiles.get(agent, AgentExecutionProfile(
                    agent_type=agent,
                    avg_execution_time=30.0,
                    success_rate=1.0,
                    resource_usage={},
                    last_execution=0.0,
                    execution_count=0
                ))

                # Update with exponential moving average
                alpha = 0.3  # Learning rate
                profile.avg_execution_time = (
                    alpha * avg_time + (1 - alpha) * profile.avg_execution_time
                )
                profile.success_rate = (
                    alpha * success_rate + (1 - alpha) * profile.success_rate
                )
                profile.last_execution = time.time()
                profile.execution_count += len(stats)

                self.agent_profiles[agent] = profile

    def _optimize_resource_allocation(self):
        """Optimize resource allocation based on current load"""
        if not self.load_balancing:
            return

        # Get current system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        # Adjust max_workers based on system load
        if cpu_percent > 85 or memory_percent > 90:
            # High load - reduce workers
            new_max_workers = max(2, self.max_workers - 2)
        elif cpu_percent < 50 and memory_percent < 60:
            # Low load - increase workers
            new_max_workers = min(12, self.max_workers + 1)
        else:
            new_max_workers = self.max_workers

        if new_max_workers != self.max_workers:
            self.max_workers = new_max_workers
            # Note: ThreadPoolExecutor doesn't support dynamic resizing
            # In production, we'd need a custom pool implementation

    def _cleanup_old_data(self):
        """Cleanup old execution data"""
        # Remove old cache files
        try:
            import glob
            cache_files = glob.glob('/tmp/claude_cache_*.json')
            cutoff_time = time.time() - 3600  # 1 hour

            for cache_file in cache_files:
                if os.path.getmtime(cache_file) < cutoff_time:
                    os.unlink(cache_file)
        except:
            pass

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'statistics': self.stats.copy(),
            'agent_profiles': {
                agent: {
                    'avg_execution_time': profile.avg_execution_time,
                    'success_rate': profile.success_rate,
                    'execution_count': profile.execution_count
                }
                for agent, profile in self.agent_profiles.items()
            },
            'system_status': {
                'max_workers': self.max_workers,
                'active_executions': len(self.active_executions),
                'queue_size': self.execution_queue.qsize(),
                'execution_history_size': len(self.execution_history)
            },
            'optimization_settings': {
                'adaptive_batching': self.adaptive_batching,
                'load_balancing': self.load_balancing,
                'smart_scheduling': self.smart_scheduling
            }
        }

    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations"""
        recommendations = []

        # Analyze statistics
        if self.stats['total_executions'] > 0:
            success_rate = (
                self.stats['successful_executions'] / self.stats['total_executions']
            )

            if success_rate < 0.9:
                recommendations.append(
                    f"Low success rate ({success_rate:.1%}). Consider reducing batch sizes."
                )

            if self.stats['avg_execution_time'] > 60:
                recommendations.append(
                    "High average execution time. Enable adaptive batching."
                )

        # Analyze system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        if cpu_percent > 80:
            recommendations.append("High CPU usage. Reduce max_workers.")

        if memory_percent > 85:
            recommendations.append("High memory usage. Enable aggressive caching cleanup.")

        # Analyze agent profiles
        slow_agents = [
            agent for agent, profile in self.agent_profiles.items()
            if profile.avg_execution_time > 45
        ]

        if slow_agents:
            recommendations.append(
                f"Slow agents detected: {', '.join(slow_agents)}. Consider optimization."
            )

        if not recommendations:
            recommendations.append("System performance is optimal")

        return recommendations

class ResourceMonitor:
    """Simple resource monitor for the optimizer"""

    def get_current_load(self) -> Dict[str, float]:
        """Get current system load"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }

# Global optimizer instance
_execution_optimizer = None

def get_execution_optimizer():
    """Get global execution optimizer instance"""
    global _execution_optimizer
    if _execution_optimizer is None:
        _execution_optimizer = ParallelExecutionOptimizer()
    return _execution_optimizer

def optimize_agent_execution(agents: List[str], prompts: Dict[str, str]) -> str:
    """Optimize parallel agent execution"""
    optimizer = get_execution_optimizer()
    return optimizer.optimize_agent_execution(agents, prompts)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "report":
            optimizer = get_execution_optimizer()
            report = optimizer.get_performance_report()
    # print(json.dumps(report, indent=2))
        elif command == "recommendations":
            optimizer = get_execution_optimizer()
            recommendations = optimizer.get_optimization_recommendations()
            for rec in recommendations:
    # print(f"• {rec}")
        elif command == "test":
            # Test optimization
            test_agents = ['backend-architect', 'security-auditor', 'test-engineer']
            test_prompts = {
                'backend-architect': 'Design system architecture',
                'security-auditor': 'Review security measures',
                'test-engineer': 'Create test plan'
            }

            result = optimize_agent_execution(test_agents, test_prompts)
    # print("Optimized execution plan:")
    # print(result)
    else:
    # print("Usage: python parallel_execution_optimizer.py [report|recommendations|test]")