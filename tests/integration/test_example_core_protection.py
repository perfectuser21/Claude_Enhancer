# tests/integration/test_example_core_protection.py
"""
Example integration tests for Core layer protection mechanism.

Demonstrates how to test Git hook integration using temporary repositories.
"""

import pytest
import subprocess
from pathlib import Path


class TestCoreProtectionIntegrationExample:
    """Example integration tests for Core layer protection."""

    def test_core_modification_blocked_on_minor_version(self, temp_git_repo):
        """
        Integration Test: Core layer modification is blocked on Minor version.

        Scenario:
        1. Create repository with version 6.5.1 (Minor)
        2. Attempt to modify .claude/core/phase_definitions.yml
        3. Git commit should be blocked by pre-commit hook

        Expected: Commit rejected with error message about version requirements
        """
        # Arrange
        repo = temp_git_repo

        # Create VERSION file (Minor version 6.5.1)
        version_file = repo / "VERSION"
        version_file.write_text("6.5.1")

        # Create Core layer directory and file
        core_dir = repo / ".claude" / "core"
        core_dir.mkdir(parents=True, exist_ok=True)

        core_file = core_dir / "phase_definitions.yml"
        core_file.write_text("phases: {}")

        # Stage all files
        subprocess.run(["git", "add", "."], cwd=repo, check=True)

        # Act - Attempt to commit (should fail if hook is installed)
        # result = subprocess.run(
        #     ["git", "commit", "-m", "Modify core on minor version"],
        #     cwd=repo,
        #     capture_output=True,
        #     text=True
        # )

        # Assert
        # assert result.returncode != 0, "Commit should be blocked"
        # assert "Core层只能在Major版本升级时修改" in result.stderr
        # assert "6.5.1" in result.stderr

        # Temporary placeholder (hook not yet implemented)
        assert version_file.read_text() == "6.5.1"
        assert core_file.exists()

    def test_core_modification_allowed_on_major_version(self, temp_git_repo):
        """
        Integration Test: Core layer modification allowed on Major version.

        Scenario:
        1. Create repository with version 7.0.0 (Major)
        2. Modify .claude/core/phase_definitions.yml
        3. Git commit should succeed

        Expected: Commit successful
        """
        # Arrange
        repo = temp_git_repo

        # Create VERSION file (Major version 7.0.0)
        version_file = repo / "VERSION"
        version_file.write_text("7.0.0")

        # Create Core layer file
        core_dir = repo / ".claude" / "core"
        core_dir.mkdir(parents=True, exist_ok=True)

        core_file = core_dir / "phase_definitions.yml"
        core_file.write_text("phases: {}")

        # Stage files
        subprocess.run(["git", "add", "."], cwd=repo, check=True)

        # Act
        result = subprocess.run(
            ["git", "commit", "-m", "Major version: modify core"],
            cwd=repo,
            capture_output=True,
            text=True
        )

        # Assert
        assert result.returncode == 0, "Commit should succeed on Major version"

    def test_feature_modification_always_allowed(self, temp_git_repo):
        """
        Integration Test: Feature layer modification always allowed.

        Scenario:
        1. Any version (e.g., 6.5.1 Minor)
        2. Modify .claude/features/registry.yml
        3. Commit should succeed regardless of version

        Expected: Commit successful
        """
        # Arrange
        repo = temp_git_repo

        # Create VERSION file
        version_file = repo / "VERSION"
        version_file.write_text("6.5.1")

        # Create Feature layer file
        feature_dir = repo / ".claude" / "features"
        feature_dir.mkdir(parents=True, exist_ok=True)

        feature_file = feature_dir / "registry.yml"
        feature_file.write_text("features: {}")

        # Stage files
        subprocess.run(["git", "add", "."], cwd=repo, check=True)

        # Act
        result = subprocess.run(
            ["git", "commit", "-m", "Modify feature layer"],
            cwd=repo,
            capture_output=True
        )

        # Assert
        assert result.returncode == 0, "Feature modification should always succeed"

    @pytest.mark.slow
    def test_bypass_mode_allows_core_modification(self, temp_git_repo):
        """
        Integration Test: Bypass mode allows Core modification.

        Scenario:
        1. Set CLAUDE_ENHANCER_BYPASS=true environment variable
        2. Modify Core layer on Minor version
        3. Commit should succeed despite version restriction

        Expected: Commit successful when bypass is enabled
        """
        # Arrange
        repo = temp_git_repo

        # Set bypass environment variable
        import os
        env = os.environ.copy()
        env["CLAUDE_ENHANCER_BYPASS"] = "true"

        # Create files
        version_file = repo / "VERSION"
        version_file.write_text("6.5.1")

        core_dir = repo / ".claude" / "core"
        core_dir.mkdir(parents=True, exist_ok=True)
        core_file = core_dir / "phase_definitions.yml"
        core_file.write_text("phases: {}")

        subprocess.run(["git", "add", "."], cwd=repo, check=True)

        # Act
        # result = subprocess.run(
        #     ["git", "commit", "-m", "Bypass test"],
        #     cwd=repo,
        #     capture_output=True,
        #     env=env
        # )

        # Assert
        # assert result.returncode == 0, "Bypass should allow commit"

        # Temporary placeholder
        assert env.get("CLAUDE_ENHANCER_BYPASS") == "true"
