#!/usr/bin/env python3
"""
Claude Enhancer Smart Dispatcher
Intelligent routing for hooks based on context and content
"""

import sys
import os
import json
import re
import subprocess
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=os.getenv('CLAUDE_ENHANCER_LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_enhancer.dispatcher')

@dataclass
class HookContext:
    """Context for hook execution"""
    event: str
    tool: str
    input_data: str
    file_paths: List[str]
    environment: Dict[str, str]
    metadata: Dict[str, Any]

class SmartDispatcher:
    """Intelligent hook dispatcher with routing logic"""

    def __init__(self):
        self.routes = self._initialize_routes()
        self.cache = {}
        self.stats = {'total': 0, 'routed': 0, 'skipped': 0}

    def _initialize_routes(self) -> Dict[str, List[Callable]]:
        """Initialize routing rules"""
        return {
            'PreToolUse': [
                self._route_security_check,
                self._route_agent_validation,
                self._route_quality_check,
            ],
            'PostToolUse': [
                self._route_formatting,
                self._route_test_analysis,
                self._route_commit_preparation,
            ],
            'UserPromptSubmit': [
                self._route_task_analysis,
                self._route_context_injection,
            ],
            'Stop': [
                self._route_completion_check,
                self._route_summary_generation,
            ],
            'SessionStart': [
                self._route_initialization,
            ],
            'SessionEnd': [
                self._route_cleanup,
                self._route_reporting,
            ],
        }

    def dispatch(self, context: HookContext) -> Dict[str, Any]:
        """Dispatch hook based on context"""
        self.stats['total'] += 1
        results = {'executed': [], 'skipped': [], 'errors': []}

        # Get routes for this event
        routes = self.routes.get(context.event, [])

        for route_func in routes:
            try:
                should_execute, command = route_func(context)
                if should_execute:
                    result = self._execute_hook(command, context)
                    results['executed'].append({
                        'route': route_func.__name__,
                        'command': command,
                        'result': result
                    })
                    self.stats['routed'] += 1
                else:
                    results['skipped'].append(route_func.__name__)
                    self.stats['skipped'] += 1
            except Exception as e:
                logger.error(f"Route error in {route_func.__name__}: {e}")
                results['errors'].append(str(e))

        return results

    def _execute_hook(self, command: str, context: HookContext) -> Any:
        """Execute a hook command"""
        env = os.environ.copy()
        env.update(context.environment)

        # Add context to environment
        if context.file_paths:
            env['CLAUDE_FILE_PATHS'] = ' '.join(context.file_paths)
        env['CLAUDE_EVENT'] = context.event
        env['CLAUDE_TOOL'] = context.tool

        try:
            result = subprocess.run(
                command,
                shell=True,
                input=context.input_data,
                text=True,
                capture_output=True,
                env=env,
                timeout=30
            )

            # Parse JSON output if applicable
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return result.stdout

        except subprocess.TimeoutExpired:
            logger.warning(f"Hook timeout: {command}")
            return {'error': 'timeout'}
        except Exception as e:
            logger.error(f"Hook execution error: {e}")
            return {'error': str(e)}

    # Routing functions
    def _route_security_check(self, context: HookContext) -> Tuple[bool, str]:
        """Route to security validation for dangerous operations"""
        if context.tool in ['Bash', 'Shell']:
            # Check for dangerous patterns
            dangerous_patterns = ['rm ', 'sudo', 'chmod', 'curl', 'wget']
            if any(p in context.input_data.lower() for p in dangerous_patterns):
                return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/security_validator.py"
        return False, ""

    def _route_agent_validation(self, context: HookContext) -> Tuple[bool, str]:
        """Route to agent validation for Task operations"""
        if context.tool == 'Task' and 'subagent_type' in context.input_data:
            return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py validate-agents"
        return False, ""

    def _route_quality_check(self, context: HookContext) -> Tuple[bool, str]:
        """Route to quality checks for code operations"""
        if context.tool in ['Edit', 'Write', 'MultiEdit']:
            return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py pre-edit"
        return False, ""

    def _route_formatting(self, context: HookContext) -> Tuple[bool, str]:
        """Route to code formatting after edits"""
        if context.tool in ['Edit', 'Write', 'MultiEdit'] and context.file_paths:
            # Check if files are formattable
            formattable_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.json', '.md']
            if any(Path(f).suffix in formattable_extensions for f in context.file_paths):
                return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py format-code"
        return False, ""

    def _route_test_analysis(self, context: HookContext) -> Tuple[bool, str]:
        """Route to test analysis after test execution"""
        if context.tool == 'Bash':
            test_indicators = ['test', 'pytest', 'jest', 'mocha', 'npm test']
            if any(ind in context.input_data.lower() for ind in test_indicators):
                return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py analyze-test-results"
        return False, ""

    def _route_commit_preparation(self, context: HookContext) -> Tuple[bool, str]:
        """Route to commit preparation for git operations"""
        if context.tool == 'Bash' and 'git commit' in context.input_data:
            return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/git_helper.py prepare-commit"
        return False, ""

    def _route_task_analysis(self, context: HookContext) -> Tuple[bool, str]:
        """Route to task analysis on prompt submission"""
        # Analyze all prompts for task type
        return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py analyze-task"

    def _route_context_injection(self, context: HookContext) -> Tuple[bool, str]:
        """Route to context injection for enrichment"""
        # Check if prompt needs context
        if any(kw in context.input_data.lower() for kw in ['implement', 'create', 'build', 'develop']):
            return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/context_injector.py"
        return False, ""

    def _route_completion_check(self, context: HookContext) -> Tuple[bool, str]:
        """Route to completion check on stop"""
        return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py check-completion"

    def _route_summary_generation(self, context: HookContext) -> Tuple[bool, str]:
        """Route to summary generation"""
        # Generate summary for long sessions
        if self.stats['total'] > 10:
            return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py generate-report"
        return False, ""

    def _route_initialization(self, context: HookContext) -> Tuple[bool, str]:
        """Route to session initialization"""
        return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py load-context"

    def _route_cleanup(self, context: HookContext) -> Tuple[bool, str]:
        """Route to cleanup operations"""
        return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/cleanup.py"

    def _route_reporting(self, context: HookContext) -> Tuple[bool, str]:
        """Route to final reporting"""
        return True, "python3 /home/xx/dev/Claude Enhancer/.claude/hooks/claude_enhancer_core.py generate-report"

    def get_stats(self) -> Dict[str, int]:
        """Get dispatcher statistics"""
        return self.stats.copy()

def main():
    """Main entry point for dispatcher"""
    # Read input
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
    else:
        input_data = ""

    # Parse context from environment and input
    context = HookContext(
        event=os.getenv('CLAUDE_EVENT', 'Unknown'),
        tool=os.getenv('CLAUDE_TOOL', 'Unknown'),
        input_data=input_data,
        file_paths=os.getenv('CLAUDE_FILE_PATHS', '').split(),
        environment=dict(os.environ),
        metadata={}
    )

    # Try to parse input as JSON for additional metadata
    try:
        context.metadata = json.loads(input_data)
    except json.JSONDecodeError:
        pass

    # Dispatch
    dispatcher = SmartDispatcher()
    results = dispatcher.dispatch(context)

    # Output results
    if results['executed']:
        logger.info(f"Executed {len(results['executed'])} hooks")
        for item in results['executed']:
    # print(item.get('result', ''))

    if results['errors']:
        for error in results['errors']:
            logger.error(f"Error: {error}")

    # Log statistics
    stats = dispatcher.get_stats()
    logger.info(f"Dispatcher stats: {stats}")

if __name__ == "__main__":
    main()