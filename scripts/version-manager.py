#!/usr/bin/env python3
"""
Version Manager - Single Source of Truth for Version Numbers

Manages version numbers across multiple files in Claude Enhancer project.
Uses VERSION file as the single source of truth.

Features:
- Scan all version references across the project
- Check consistency with VERSION file
- Auto-sync all locations to target version
- Intelligent pattern matching (handles X.Y and X.Y.Z formats)
- Dry-run mode for safe previews
- Color-coded output for clarity
- Backup before changes

Usage:
    ./scripts/version-manager.py --get              # Get current version
    ./scripts/version-manager.py --set 6.2.0        # Set version (sync all)
    ./scripts/version-manager.py --check            # Check consistency
    ./scripts/version-manager.py --fix              # Auto-fix mismatches
    ./scripts/version-manager.py --check --verbose  # Detailed check
    ./scripts/version-manager.py list               # List all references
    ./scripts/version-manager.py scan               # Scan for all versions
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class VersionLocation:
    """Represents a location where version number is stored."""
    file_path: Path
    description: str
    line_pattern: Optional[str] = None  # Regex pattern to find version
    update_callback: Optional[callable] = None  # Custom update function


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


class VersionManager:
    """Manages version numbers across the project."""

    # Semantic version regex pattern
    SEMVER_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')
    SEMVER_OR_MINOR = re.compile(r'^\d+\.\d+(\.\d+)?$')

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_file = project_root / 'VERSION'
        self.backup_dir = project_root / '.temp' / 'version-backups'

        # Define all locations where version numbers appear
        self.locations: List[VersionLocation] = self._init_locations()

    def _init_locations(self) -> List[VersionLocation]:
        """Initialize all version locations in the project."""
        locations = []

        # VERSION file (source of truth)
        locations.append(VersionLocation(
            file_path=self.version_file,
            description="VERSION file (source of truth)",
            line_pattern=r'^(\d+\.\d+\.\d+)\s*$',
            update_callback=self._update_version_file
        ))

        # CLAUDE.md (multiple locations)
        claude_md = self.project_root / 'CLAUDE.md'
        if claude_md.exists():
            locations.append(VersionLocation(
                file_path=claude_md,
                description="CLAUDE.md (title line)",
                line_pattern=r'^# Claude Enhancer (\d+\.\d+(?:\.\d+)?)',
                update_callback=lambda path, ver: self._update_claude_md(path, ver)
            ))

        # /root/.claude/CLAUDE.md (global config)
        global_claude = Path('/root/.claude/CLAUDE.md')
        if global_claude.exists():
            locations.append(VersionLocation(
                file_path=global_claude,
                description="/root/.claude/CLAUDE.md (global config)",
                line_pattern=r'# 🌟 Claude Enhancer.*?Configuration',
                update_callback=lambda path, ver: self._update_global_claude(path, ver)
            ))

        # package.json
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            locations.append(VersionLocation(
                file_path=package_json,
                description="package.json",
                update_callback=self._update_package_json
            ))

        # README.md (badges)
        readme = self.project_root / 'README.md'
        if readme.exists():
            locations.append(VersionLocation(
                file_path=readme,
                description="README.md (badges)",
                line_pattern=r'badge/version-(\d+\.\d+\.\d+)',
                update_callback=self._update_readme
            ))

        # CHANGELOG.md
        changelog = self.project_root / 'CHANGELOG.md'
        if changelog.exists():
            locations.append(VersionLocation(
                file_path=changelog,
                description="CHANGELOG.md",
                line_pattern=r'^## \[(\d+\.\d+\.\d+)\]',
                update_callback=None  # Read-only, manually managed
            ))

        return locations

    def get_version(self) -> str:
        """Get current version from VERSION file."""
        if not self.version_file.exists():
            self._error(f"VERSION file not found: {self.version_file}")
            sys.exit(1)

        version = self.version_file.read_text().strip()
        if not self.SEMVER_PATTERN.match(version):
            self._error(f"Invalid version format in VERSION file: {version}")
            sys.exit(1)

        return version

    def set_version(self, new_version: str, dry_run: bool = False) -> bool:
        """Set version across all locations."""
        # Validate version format
        if not self.SEMVER_PATTERN.match(new_version):
            self._error(f"Invalid version format: {new_version}")
            self._info("Expected format: X.Y.Z (e.g., 6.2.0)")
            return False

        current_version = self.get_version()

        print(f"\n{Colors.BOLD}Setting version: {current_version} → {new_version}{Colors.END}\n")

        # Create backup before making changes
        if not dry_run:
            self._create_backup()

        # Update all locations
        success = True
        for location in self.locations:
            if not location.file_path.exists():
                self._warning(f"Skipping (file not found): {location.file_path}")
                continue

            # Skip read-only locations
            if location.update_callback is None:
                self._info(f"Skipping (read-only): {location.description}")
                continue

            try:
                if dry_run:
                    print(f"[DRY RUN] Would update: {location.description}")
                else:
                    location.update_callback(location.file_path, new_version)
                    self._success(f"Updated: {location.description}")
            except Exception as e:
                self._error(f"Failed to update {location.description}: {e}")
                success = False

        if success and not dry_run:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Version set to {new_version} successfully!{Colors.END}")
            print(f"\nBackup created at: {self.backup_dir}")

        return success

    def check_consistency(self, verbose: bool = False) -> Tuple[bool, Dict[str, str]]:
        """Check version consistency across all locations."""
        source_version = self.get_version()
        results = {}
        all_consistent = True

        print(f"\n{Colors.BOLD}Version Consistency Check{Colors.END}")
        print(f"Source of Truth: {Colors.BLUE}{source_version}{Colors.END} (VERSION file)\n")

        for location in self.locations:
            if not location.file_path.exists():
                if verbose:
                    self._warning(f"File not found: {location.file_path}")
                continue

            try:
                found_versions = self._extract_versions(location)

                if not found_versions:
                    self._warning(f"No version found: {location.description}")
                    results[location.description] = "NOT_FOUND"
                    all_consistent = False
                    continue

                # Check each found version
                for line_num, version in found_versions:
                    key = f"{location.description} (line {line_num})" if len(found_versions) > 1 else location.description

                    # Normalize version for comparison (6.0 == 6.0.0)
                    normalized_version = self._normalize_version(version)
                    normalized_source = self._normalize_version(source_version)

                    if normalized_version == normalized_source:
                        self._success(f"✓ {key}: {version}")
                        results[key] = version
                    else:
                        self._error(f"✗ {key}: {version} (expected {source_version})")
                        results[key] = version
                        all_consistent = False

            except Exception as e:
                self._error(f"Error checking {location.description}: {e}")
                results[location.description] = "ERROR"
                all_consistent = False

        # Summary
        total = len(results)
        consistent = sum(1 for key, v in results.items()
                        if v not in ["NOT_FOUND", "ERROR"] and
                        self._normalize_version(v) == self._normalize_version(source_version))
        inconsistent = total - consistent

        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"Total locations: {total}")
        print(f"Consistent: {Colors.GREEN}{consistent}{Colors.END}")
        print(f"Inconsistent: {Colors.RED}{inconsistent}{Colors.END}")

        if all_consistent:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All versions are consistent!{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Version mismatches detected!{Colors.END}")
            print(f"Run '{sys.argv[0]} --fix' to auto-correct")

        return all_consistent, results

    def fix_inconsistencies(self, dry_run: bool = False) -> bool:
        """Fix all version inconsistencies."""
        is_consistent, results = self.check_consistency(verbose=False)

        if is_consistent:
            print(f"\n{Colors.GREEN}No fixes needed - all versions are consistent!{Colors.END}")
            return True

        print(f"\n{Colors.BOLD}Fixing version inconsistencies...{Colors.END}\n")

        source_version = self.get_version()
        return self.set_version(source_version, dry_run=dry_run)

    def list_all_references(self) -> None:
        """List all version references with detailed information."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}📋 All Version References{Colors.END}\n")

        for location in self.locations:
            if not location.file_path.exists():
                continue

            try:
                found_versions = self._extract_versions(location)
                relative_path = self._relative_path(location.file_path)

                print(f"{Colors.BOLD}📄 {relative_path}{Colors.END}")
                print(f"   Description: {location.description}")
                print(f"   Pattern: {location.pattern_description()}")

                if found_versions:
                    for line_num, version in found_versions:
                        print(f"   Line {line_num:4d}: {Colors.BLUE}{version}{Colors.END}")
                else:
                    print(f"   {Colors.YELLOW}No versions found{Colors.END}")

                print()

            except Exception as e:
                print(f"   {Colors.RED}Error: {e}{Colors.END}\n")

    def scan_all_files(self) -> Dict[Path, List[Tuple[int, str]]]:
        """Deep scan all files for version patterns."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Deep Version Scan{Colors.END}\n")

        # Version patterns to search for
        patterns = [
            r'\d+\.\d+\.\d+',  # X.Y.Z
            r'v\d+\.\d+\.\d+',  # vX.Y.Z
            r'\d+\.\d+',  # X.Y
            r'v\d+\.\d+',  # vX.Y
        ]

        # Files to scan
        scan_files = [
            'CLAUDE.md',
            'README.md',
            'package.json',
            'CHANGELOG.md',
            'VERSION',
            '.github/workflows/*.yml',
            'scripts/*.py',
            'scripts/*.sh',
        ]

        results = {}

        # Scan each file
        for pattern in scan_files:
            if '*' in pattern:
                # Glob pattern
                for file_path in self.project_root.glob(pattern):
                    if file_path.is_file():
                        versions = self._scan_file_for_versions(file_path)
                        if versions:
                            results[file_path] = versions
            else:
                # Direct file
                file_path = self.project_root / pattern
                if file_path.exists():
                    versions = self._scan_file_for_versions(file_path)
                    if versions:
                        results[file_path] = versions

        # Display results
        for file_path, versions in sorted(results.items()):
            relative_path = self._relative_path(file_path)
            print(f"{Colors.BOLD}📄 {relative_path}{Colors.END}")

            # Group by version
            version_groups = {}
            for line_num, version in versions:
                if version not in version_groups:
                    version_groups[version] = []
                version_groups[version].append(line_num)

            for version, line_nums in sorted(version_groups.items()):
                lines_str = ', '.join(str(ln) for ln in line_nums)
                print(f"   {Colors.BLUE}{version:10s}{Colors.END} → Lines: {lines_str}")

            print()

        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"Scanned files: {len(results)}")
        print(f"Total version references: {sum(len(v) for v in results.values())}")

        return results

    def _scan_file_for_versions(self, file_path: Path) -> List[Tuple[int, str]]:
        """Scan a single file for all version patterns."""
        try:
            content = file_path.read_text(encoding='utf-8')
            versions = []

            for line_num, line in enumerate(content.splitlines(), 1):
                # Find all version-like patterns
                matches = re.finditer(r'v?(\d+\.\d+(?:\.\d+)?)', line)
                for match in matches:
                    version = match.group(1)
                    # Filter out unlikely versions (e.g., file extensions, IPs)
                    if self._is_likely_version(version, line):
                        versions.append((line_num, version))

            return versions

        except Exception:
            return []

    def _is_likely_version(self, version: str, context: str) -> bool:
        """Heuristic to determine if a pattern is likely a version number."""
        # Skip if it looks like an IP address
        if re.search(r'\d+\.\d+\.\d+\.\d+', context):
            return False

        # Skip if it's in a URL path (common false positive)
        if '/1.0/' in context or '/2.0/' in context:
            return False

        # Must have reasonable version numbers (not 192.168.x.x)
        parts = version.split('.')
        try:
            major = int(parts[0])
            if major > 100:  # Unlikely to be a version number
                return False
        except ValueError:
            return False

        return True

    def _normalize_version(self, version: str) -> str:
        """Normalize version for comparison (e.g., 6.0 -> 6.0.0)."""
        parts = version.split('.')
        while len(parts) < 3:
            parts.append('0')
        return '.'.join(parts[:3])

    def _extract_versions(self, location: VersionLocation) -> List[Tuple[int, str]]:
        """Extract version numbers from a file."""
        content = location.file_path.read_text()
        versions = []

        if location.file_path.name == 'package.json':
            # Handle JSON files specially
            try:
                data = json.loads(content)
                if 'version' in data:
                    versions.append((0, data['version']))
            except json.JSONDecodeError:
                pass
        elif location.line_pattern:
            # Use regex pattern to find versions
            for line_num, line in enumerate(content.splitlines(), 1):
                if isinstance(location.line_pattern, str):
                    match = re.search(location.line_pattern, line)
                    if match:
                        # Try to extract version from captured group
                        try:
                            version_str = match.group(1)
                            # Validate it looks like a version
                            if re.match(r'\d+\.\d+(?:\.\d+)?', version_str):
                                versions.append((line_num, version_str))
                        except IndexError:
                            # No captured group, skip this line
                            pass
        else:
            # Fallback: search for any semver pattern
            for line_num, line in enumerate(content.splitlines(), 1):
                matches = re.findall(r'\d+\.\d+\.\d+', line)
                for match in matches:
                    versions.append((line_num, match))

        return versions

    def _create_backup(self):
        """Create backup of all version-related files."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for location in self.locations:
            if not location.file_path.exists():
                continue

            backup_name = f"{location.file_path.name}.{timestamp}.bak"
            backup_path = self.backup_dir / backup_name

            backup_path.write_text(location.file_path.read_text())

        print(f"{Colors.BLUE}Backup created: {self.backup_dir}{Colors.END}")

    def _relative_path(self, path: Path) -> str:
        """Get relative path from project root."""
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    # Update methods for different file types

    def _update_version_file(self, file_path: Path, version: str):
        """Update VERSION file."""
        file_path.write_text(f"{version}\n")

    def _update_claude_md(self, file_path: Path, version: str):
        """Update CLAUDE.md file."""
        content = file_path.read_text()

        # Update title line (e.g., "# Claude Enhancer 6.0" -> "# Claude Enhancer 6.2")
        major_minor = '.'.join(version.split('.')[:2])  # Get X.Y from X.Y.Z
        content = re.sub(
            r'^# Claude Enhancer \d+\.\d+(?:\.\d+)?',
            f'# Claude Enhancer {major_minor}',
            content,
            flags=re.MULTILINE
        )

        # Update certification badges (preserve full version)
        content = re.sub(
            r'Claude Enhancer \d+\.\d+(?:\.\d+)? Certified',
            f'Claude Enhancer {version} Certified',
            content
        )

        # Update version evolution mentions (e.g., "v6.1核心成就")
        # Keep history intact, but update current version references
        content = re.sub(
            r'## 🏆 v\d+\.\d+核心成就',
            f'## 🏆 v{major_minor}核心成就',
            content
        )

        file_path.write_text(content)

    def _update_global_claude(self, file_path: Path, version: str):
        """Update /root/.claude/CLAUDE.md (global config)."""
        # This file typically doesn't contain version numbers
        # It's a configuration file, not a versioned document
        # We'll skip updating it for now
        pass

    def _update_package_json(self, file_path: Path, version: str):
        """Update package.json file."""
        content = file_path.read_text()
        data = json.loads(content)
        data['version'] = version

        # Pretty print with 2-space indentation (matching original)
        file_path.write_text(json.dumps(data, indent=2) + '\n')

    def _update_readme(self, file_path: Path, version: str):
        """Update README.md file."""
        content = file_path.read_text()

        # Update title line (e.g., "# Claude Enhancer 6.2.0")
        content = re.sub(
            r'^# Claude Enhancer \d+\.\d+\.\d+',
            f'# Claude Enhancer {version}',
            content,
            flags=re.MULTILINE
        )

        # Update version badges
        content = re.sub(
            r'badge/version-\d+\.\d+\.\d+-blue',
            f'badge/version-{version}-blue',
            content
        )

        # Update certification badges
        content = re.sub(
            r'Claude Enhancer \d+\.\d+\.\d+ Certified',
            f'Claude Enhancer {version} Certified',
            content
        )

        # Update system component version mentions
        content = re.sub(
            r'Claude Enhancer v\d+\.\d+\.\d+',
            f'Claude Enhancer v{version}',
            content
        )

        file_path.write_text(content)

    # Utility methods

    def _success(self, message: str):
        """Print success message."""
        print(f"{Colors.GREEN}✓{Colors.END} {message}")

    def _error(self, message: str):
        """Print error message."""
        print(f"{Colors.RED}✗{Colors.END} {message}", file=sys.stderr)

    def _warning(self, message: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

    def _info(self, message: str):
        """Print info message."""
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


# Add method to VersionLocation for better display
def pattern_description(self):
    """Get human-readable pattern description."""
    if self.line_pattern:
        return self.line_pattern
    return "Auto-detect"

VersionLocation.pattern_description = pattern_description


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Version Manager - Single Source of Truth for Version Numbers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --get                 Get current version
  %(prog)s --set 6.2.0          Set version to 6.2.0
  %(prog)s --check              Check version consistency
  %(prog)s --check --verbose    Detailed consistency check
  %(prog)s --fix                Auto-fix version mismatches
  %(prog)s --fix --dry-run      Preview fix changes
  %(prog)s list                 List all managed version locations
  %(prog)s scan                 Deep scan all files for versions
        """
    )

    # Positional commands
    parser.add_argument('command', nargs='?', choices=['list', 'scan'],
                       help='Command to execute (optional)')

    # Optional flags
    parser.add_argument('--get', action='store_true',
                       help='Get current version from VERSION file')
    parser.add_argument('--set', metavar='VERSION',
                       help='Set version across all files (format: X.Y.Z)')
    parser.add_argument('--check', action='store_true',
                       help='Check version consistency across files')
    parser.add_argument('--fix', action='store_true',
                       help='Auto-fix version inconsistencies')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    parser.add_argument('--project-root', type=Path,
                       help='Project root directory (default: current directory)')

    args = parser.parse_args()

    # Determine project root
    project_root = args.project_root or Path.cwd()
    if not project_root.exists():
        print(f"Error: Project root not found: {project_root}", file=sys.stderr)
        sys.exit(1)

    # Initialize version manager
    manager = VersionManager(project_root)

    # Handle commands
    if args.command == 'list':
        manager.list_all_references()
        return 0

    elif args.command == 'scan':
        manager.scan_all_files()
        return 0

    elif args.get:
        version = manager.get_version()
        print(version)
        return 0

    elif args.set:
        success = manager.set_version(args.set, dry_run=args.dry_run)
        return 0 if success else 1

    elif args.check:
        is_consistent, _ = manager.check_consistency(verbose=args.verbose)
        return 0 if is_consistent else 1

    elif args.fix:
        success = manager.fix_inconsistencies(dry_run=args.dry_run)
        return 0 if success else 1

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
