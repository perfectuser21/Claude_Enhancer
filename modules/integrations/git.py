"""
Git Integration
Wrapper for Git operations with error handling and validation
"""

from pathlib import Path
from typing import Optional, List, Dict, Tuple
import re

from modules.shared.common import Result, success, failure, ErrorCode, CommandRunner


class GitIntegration:
    """
    Git operations wrapper with Claude Enhancer integration
    """

    def __init__(self, repo_path: Path = Path.cwd()):
        """
        Initialize Git integration

        Args:
            repo_path: Repository root path
        """
        self.repo_path = Path(repo_path).resolve()
        self.runner = CommandRunner(cwd=self.repo_path)

    def is_git_repo(self) -> bool:
        """
        Check if current directory is a git repository

        Returns:
            True if git repo, False otherwise
        """
        result = self.runner.run_git('rev-parse', '--git-dir')
        return result.success

    def get_current_branch(self) -> Result:
        """
        Get current branch name

        Returns:
            Result with branch name
        """
        result = self.runner.run_git('rev-parse', '--abbrev-ref', 'HEAD')
        if result.success:
            branch = result.data['stdout'].strip()
            return success(branch)
        return result

    def get_remote_branches(self) -> Result:
        """
        Get list of remote branches

        Returns:
            Result with list of branch names
        """
        result = self.runner.run_git('branch', '-r')
        if result.success:
            branches = [
                b.strip().replace('origin/', '')
                for b in result.data['stdout'].split('\n')
                if b.strip() and not b.strip().endswith('HEAD')
            ]
            return success(branches)
        return result

    def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> Result:
        """
        Create a new branch

        Args:
            branch_name: Name of the new branch
            base_branch: Optional base branch (default: current branch)

        Returns:
            Result indicating success or failure
        """
        # Validate branch name
        if not re.match(r'^[a-zA-Z0-9_/-]+$', branch_name):
            return failure(
                f"Invalid branch name: {branch_name}",
                ErrorCode.VALIDATION_ERROR
            )

        # Check if branch already exists
        check_result = self.runner.run_git('rev-parse', '--verify', branch_name)
        if check_result.success:
            return failure(
                f"Branch already exists: {branch_name}",
                ErrorCode.VALIDATION_ERROR
            )

        # Create branch
        if base_branch:
            result = self.runner.run_git('checkout', '-b', branch_name, base_branch)
        else:
            result = self.runner.run_git('checkout', '-b', branch_name)

        if result.success:
            return success(f"Created branch: {branch_name}")
        return result

    def switch_branch(self, branch_name: str) -> Result:
        """
        Switch to existing branch

        Args:
            branch_name: Branch to switch to

        Returns:
            Result indicating success or failure
        """
        result = self.runner.run_git('checkout', branch_name)
        if result.success:
            return success(f"Switched to branch: {branch_name}")
        return result

    def get_status(self) -> Result:
        """
        Get git status

        Returns:
            Result with status information
        """
        result = self.runner.run_git('status', '--porcelain')
        if result.success:
            status_lines = result.data['stdout'].strip().split('\n')
            status = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': [],
                'clean': len(status_lines) == 1 and not status_lines[0]
            }

            for line in status_lines:
                if not line:
                    continue
                status_code = line[:2]
                file_path = line[3:]

                if 'M' in status_code:
                    status['modified'].append(file_path)
                elif 'A' in status_code:
                    status['added'].append(file_path)
                elif 'D' in status_code:
                    status['deleted'].append(file_path)
                elif '?' in status_code:
                    status['untracked'].append(file_path)

            return success(status)
        return result

    def stage_files(self, files: List[str]) -> Result:
        """
        Stage files for commit

        Args:
            files: List of file paths to stage

        Returns:
            Result indicating success or failure
        """
        if not files:
            return failure("No files specified to stage", ErrorCode.VALIDATION_ERROR)

        result = self.runner.run_git('add', *files)
        if result.success:
            return success(f"Staged {len(files)} file(s)")
        return result

    def commit(self, message: str, files: Optional[List[str]] = None) -> Result:
        """
        Create a commit

        Args:
            message: Commit message
            files: Optional list of files to stage before commit

        Returns:
            Result with commit hash
        """
        if not message:
            return failure("Commit message cannot be empty", ErrorCode.VALIDATION_ERROR)

        # Stage files if provided
        if files:
            stage_result = self.stage_files(files)
            if not stage_result:
                return stage_result

        # Create commit
        result = self.runner.run_git('commit', '-m', message)
        if result.success:
            # Get commit hash
            hash_result = self.runner.run_git('rev-parse', 'HEAD')
            if hash_result.success:
                commit_hash = hash_result.data['stdout'].strip()[:8]
                return success({'hash': commit_hash, 'message': message})
            return success({'message': message})
        return result

    def push(self, branch: Optional[str] = None, set_upstream: bool = False) -> Result:
        """
        Push to remote

        Args:
            branch: Optional branch name (default: current branch)
            set_upstream: Set upstream tracking (default: False)

        Returns:
            Result indicating success or failure
        """
        args = ['push']

        if set_upstream:
            args.extend(['-u', 'origin'])
            if branch:
                args.append(branch)
        elif branch:
            args.extend(['origin', branch])

        result = self.runner.run_git(*args)
        if result.success:
            return success("Pushed to remote")
        return result

    def get_diff(self, cached: bool = False) -> Result:
        """
        Get git diff

        Args:
            cached: Show staged changes (default: False for unstaged)

        Returns:
            Result with diff content
        """
        args = ['diff']
        if cached:
            args.append('--cached')

        result = self.runner.run_git(*args)
        if result.success:
            return success(result.data['stdout'])
        return result

    def get_log(self, count: int = 10, oneline: bool = True) -> Result:
        """
        Get commit history

        Args:
            count: Number of commits to show
            oneline: Format as one line per commit

        Returns:
            Result with commit history
        """
        args = ['log', f'-{count}']
        if oneline:
            args.append('--oneline')

        result = self.runner.run_git(*args)
        if result.success:
            commits = []
            for line in result.data['stdout'].strip().split('\n'):
                if line:
                    commits.append(line)
            return success(commits)
        return result

    def is_clean(self) -> bool:
        """
        Check if working directory is clean (no uncommitted changes)

        Returns:
            True if clean, False otherwise
        """
        status_result = self.get_status()
        if status_result.success:
            return status_result.data['clean']
        return False

    def get_remote_url(self) -> Result:
        """
        Get remote repository URL

        Returns:
            Result with remote URL
        """
        result = self.runner.run_git('remote', 'get-url', 'origin')
        if result.success:
            return success(result.data['stdout'].strip())
        return result
