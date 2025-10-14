"""
NPM Integration
Wrapper for NPM/Node.js package management operations
"""

from pathlib import Path
from typing import Optional, Dict, List
import json

from modules.shared.common import Result, success, failure, ErrorCode, CommandRunner
from modules.utils.file_handler import read_json_file, write_json_file


class NPMIntegration:
    """
    NPM/Node.js integration wrapper
    """

    def __init__(self, project_path: Path = Path.cwd()):
        """
        Initialize NPM integration

        Args:
            project_path: Project root path (where package.json lives)
        """
        self.project_path = Path(project_path).resolve()
        self.package_json_path = self.project_path / 'package.json'
        self.runner = CommandRunner(cwd=self.project_path)

    def has_package_json(self) -> bool:
        """
        Check if project has package.json

        Returns:
            True if package.json exists, False otherwise
        """
        return self.package_json_path.exists()

    def read_package_json(self) -> Result:
        """
        Read package.json content

        Returns:
            Result with parsed package.json data
        """
        if not self.has_package_json():
            return failure(
                f"package.json not found in {self.project_path}",
                ErrorCode.FILE_NOT_FOUND
            )

        data = read_json_file(self.package_json_path)
        if data is None:
            return failure(
                "Failed to parse package.json",
                ErrorCode.VALIDATION_ERROR
            )

        return success(data)

    def write_package_json(self, data: Dict) -> Result:
        """
        Write package.json content

        Args:
            data: Package.json data to write

        Returns:
            Result indicating success or failure
        """
        if write_json_file(self.package_json_path, data, indent=2):
            return success("package.json updated")
        return failure(
            "Failed to write package.json",
            ErrorCode.EXECUTION_ERROR
        )

    def install(self, packages: Optional[List[str]] = None, dev: bool = False) -> Result:
        """
        Install npm packages

        Args:
            packages: Optional list of packages to install (None = install all)
            dev: Install as dev dependencies

        Returns:
            Result indicating success or failure
        """
        args = ['install']

        if packages:
            args.extend(packages)
            if dev:
                args.append('--save-dev')

        result = self.runner.run(['npm'] + args)
        if result.success:
            if packages:
                return success(f"Installed {len(packages)} package(s)")
            return success("Dependencies installed")
        return result

    def uninstall(self, packages: List[str]) -> Result:
        """
        Uninstall npm packages

        Args:
            packages: List of packages to uninstall

        Returns:
            Result indicating success or failure
        """
        if not packages:
            return failure("No packages specified", ErrorCode.VALIDATION_ERROR)

        result = self.runner.run(['npm', 'uninstall'] + packages)
        if result.success:
            return success(f"Uninstalled {len(packages)} package(s)")
        return result

    def run_script(self, script_name: str, args: Optional[List[str]] = None) -> Result:
        """
        Run npm script from package.json

        Args:
            script_name: Script name (e.g., 'test', 'build')
            args: Optional arguments to pass to script

        Returns:
            Result with script output
        """
        # Check if script exists
        pkg_result = self.read_package_json()
        if not pkg_result:
            return pkg_result

        scripts = pkg_result.data.get('scripts', {})
        if script_name not in scripts:
            return failure(
                f"Script '{script_name}' not found in package.json",
                ErrorCode.VALIDATION_ERROR
            )

        # Run script
        cmd = ['npm', 'run', script_name]
        if args:
            cmd.append('--')
            cmd.extend(args)

        result = self.runner.run(cmd)
        if result.success:
            return success(result.data['stdout'])
        return result

    def list_scripts(self) -> Result:
        """
        List available npm scripts

        Returns:
            Result with dict of script names and commands
        """
        pkg_result = self.read_package_json()
        if not pkg_result:
            return pkg_result

        scripts = pkg_result.data.get('scripts', {})
        return success(scripts)

    def get_version(self) -> Result:
        """
        Get project version from package.json

        Returns:
            Result with version string
        """
        pkg_result = self.read_package_json()
        if not pkg_result:
            return pkg_result

        version = pkg_result.data.get('version')
        if not version:
            return failure(
                "Version not found in package.json",
                ErrorCode.VALIDATION_ERROR
            )

        return success(version)

    def set_version(self, version: str) -> Result:
        """
        Set project version in package.json

        Args:
            version: New version string (e.g., '1.2.3')

        Returns:
            Result indicating success or failure
        """
        # Validate version format
        import re
        if not re.match(r'^\d+\.\d+\.\d+(-[\w.]+)?$', version):
            return failure(
                f"Invalid version format: {version}",
                ErrorCode.VALIDATION_ERROR
            )

        # Read, update, write
        pkg_result = self.read_package_json()
        if not pkg_result:
            return pkg_result

        data = pkg_result.data
        old_version = data.get('version', 'unknown')
        data['version'] = version

        write_result = self.write_package_json(data)
        if write_result:
            return success(f"Version updated: {old_version} -> {version}")
        return write_result

    def outdated(self) -> Result:
        """
        Check for outdated packages

        Returns:
            Result with outdated packages information
        """
        result = self.runner.run(['npm', 'outdated', '--json'], check=False)

        # npm outdated returns non-zero if packages are outdated
        if result.success or result.data.get('returncode') == 1:
            try:
                outdated = json.loads(result.data['stdout'] or '{}')
                return success(outdated)
            except json.JSONDecodeError:
                return success({})

        return result

    def audit(self, fix: bool = False) -> Result:
        """
        Run npm security audit

        Args:
            fix: Automatically fix vulnerabilities

        Returns:
            Result with audit information
        """
        args = ['audit', '--json']
        if fix:
            args.insert(1, 'fix')

        result = self.runner.run(['npm'] + args, check=False)

        # npm audit returns non-zero if vulnerabilities found
        if result.success or result.data.get('returncode') == 1:
            try:
                audit_data = json.loads(result.data['stdout'] or '{}')
                return success(audit_data)
            except json.JSONDecodeError:
                return failure(
                    "Failed to parse audit results",
                    ErrorCode.EXECUTION_ERROR
                )

        return result

    def get_dependencies(self, include_dev: bool = True) -> Result:
        """
        Get project dependencies

        Args:
            include_dev: Include devDependencies

        Returns:
            Result with dependencies dict
        """
        pkg_result = self.read_package_json()
        if not pkg_result:
            return pkg_result

        deps = {}
        data = pkg_result.data

        deps['dependencies'] = data.get('dependencies', {})
        if include_dev:
            deps['devDependencies'] = data.get('devDependencies', {})

        return success(deps)

    def check_node_version(self) -> Result:
        """
        Check Node.js version

        Returns:
            Result with Node.js version string
        """
        result = self.runner.run(['node', '--version'])
        if result.success:
            version = result.data['stdout'].strip()
            return success(version)
        return result

    def check_npm_version(self) -> Result:
        """
        Check npm version

        Returns:
            Result with npm version string
        """
        result = self.runner.run(['npm', '--version'])
        if result.success:
            version = result.data['stdout'].strip()
            return success(version)
        return result
