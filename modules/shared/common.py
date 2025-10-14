"""
Common Shared Components
Result types, error codes, and command execution utilities
"""

import subprocess
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, List, Dict, Tuple
from pathlib import Path


class ErrorCode(Enum):
    """Standard error codes for Claude Enhancer operations"""
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_NOT_FOUND = 2
    PERMISSION_ERROR = 3
    EXECUTION_ERROR = 4
    CONFIGURATION_ERROR = 5
    HOOK_FAILURE = 6
    PHASE_TRANSITION_ERROR = 7
    AGENT_ERROR = 8
    GIT_ERROR = 9
    UNKNOWN_ERROR = 99


@dataclass
class Result:
    """
    Generic result type for operations

    Attributes:
        success: Whether operation succeeded
        data: Optional result data
        error: Optional error message
        error_code: Error code (ErrorCode enum)
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: ErrorCode = ErrorCode.SUCCESS

    def __bool__(self) -> bool:
        return self.success


def success(data: Any = None) -> Result:
    """
    Create a successful result

    Args:
        data: Optional result data

    Returns:
        Success Result object
    """
    return Result(success=True, data=data, error_code=ErrorCode.SUCCESS)


def failure(error: str, error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR, data: Any = None) -> Result:
    """
    Create a failure result

    Args:
        error: Error message
        error_code: Error code (default: UNKNOWN_ERROR)
        data: Optional partial result data

    Returns:
        Failure Result object
    """
    return Result(success=False, error=error, error_code=error_code, data=data)


class CommandRunner:
    """
    Safe command execution wrapper with error handling
    """

    def __init__(self, cwd: Optional[Path] = None, timeout: int = 300):
        """
        Initialize command runner

        Args:
            cwd: Working directory for commands
            timeout: Command timeout in seconds (default: 300)
        """
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.timeout = timeout

    def run(
        self,
        command: List[str],
        check: bool = True,
        capture_output: bool = True,
        env: Optional[Dict[str, str]] = None
    ) -> Result:
        """
        Run a command and return Result

        Args:
            command: Command and arguments as list
            check: Raise on non-zero exit (default: True)
            capture_output: Capture stdout/stderr (default: True)
            env: Optional environment variables

        Returns:
            Result with command output or error
        """
        try:
            process = subprocess.run(
                command,
                cwd=self.cwd,
                capture_output=capture_output,
                text=True,
                timeout=self.timeout,
                check=check,
                env=env
            )

            return success(data={
                'stdout': process.stdout,
                'stderr': process.stderr,
                'returncode': process.returncode
            })

        except subprocess.TimeoutExpired as e:
            return failure(
                f"Command timed out after {self.timeout}s: {' '.join(command)}",
                ErrorCode.EXECUTION_ERROR,
                data={'timeout': self.timeout, 'command': command}
            )

        except subprocess.CalledProcessError as e:
            return failure(
                f"Command failed with exit code {e.returncode}: {e.stderr}",
                ErrorCode.EXECUTION_ERROR,
                data={
                    'stdout': e.stdout,
                    'stderr': e.stderr,
                    'returncode': e.returncode,
                    'command': command
                }
            )

        except FileNotFoundError:
            return failure(
                f"Command not found: {command[0]}",
                ErrorCode.FILE_NOT_FOUND,
                data={'command': command}
            )

        except Exception as e:
            return failure(
                f"Unexpected error running command: {e}",
                ErrorCode.EXECUTION_ERROR,
                data={'command': command, 'exception': str(e)}
            )

    def run_git(self, *args: str) -> Result:
        """
        Run git command

        Args:
            *args: Git command arguments

        Returns:
            Result with git output or error
        """
        return self.run(['git'] + list(args))

    def run_shell(self, script: str) -> Result:
        """
        Run shell script

        Args:
            script: Shell script content

        Returns:
            Result with script output or error
        """
        return self.run(['bash', '-c', script])


def validate_path(path: Path, must_exist: bool = True, must_be_file: bool = False) -> Result:
    """
    Validate a file system path

    Args:
        path: Path to validate
        must_exist: Whether path must exist (default: True)
        must_be_file: Whether path must be a file (default: False, can be dir)

    Returns:
        Result indicating validation success or failure
    """
    path = Path(path)

    if must_exist and not path.exists():
        return failure(
            f"Path does not exist: {path}",
            ErrorCode.FILE_NOT_FOUND
        )

    if must_be_file and path.exists() and not path.is_file():
        return failure(
            f"Path is not a file: {path}",
            ErrorCode.VALIDATION_ERROR
        )

    return success(data={'path': path, 'exists': path.exists()})


def format_table(headers: List[str], rows: List[List[str]], indent: str = "") -> str:
    """
    Format data as ASCII table

    Args:
        headers: Column headers
        rows: Data rows
        indent: Optional indentation prefix

    Returns:
        Formatted table string
    """
    if not rows:
        return indent + "No data"

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Format header
    header_line = indent + " | ".join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers)
    )
    separator = indent + "-+-".join("-" * w for w in col_widths)

    # Format rows
    row_lines = [
        indent + " | ".join(
            str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
        )
        for row in rows
    ]

    return "\n".join([header_line, separator] + row_lines)
