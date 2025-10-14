"""
File Handling Utilities
Safe file operations for JSON, YAML, and general file I/O
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
import tempfile


def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists, create if necessary

    Args:
        path: Directory path

    Returns:
        The directory path
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json_file(file_path: Path, default: Any = None) -> Any:
    """
    Read JSON file with error handling

    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return default

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return default


def write_json_file(file_path: Path, data: Any, indent: int = 2) -> bool:
    """
    Write JSON file with atomic operation

    Args:
        file_path: Path to JSON file
        data: Data to write
        indent: JSON indentation level

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)

    try:
        # Atomic write: write to temp file, then move
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=file_path.parent,
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            json.dump(data, tmp_file, indent=indent, ensure_ascii=False)
            tmp_path = Path(tmp_file.name)

        # Move temp file to target (atomic on POSIX)
        shutil.move(str(tmp_path), str(file_path))
        return True
    except (IOError, OSError) as e:
        print(f"Error: Failed to write {file_path}: {e}")
        return False


def read_yaml_file(file_path: Path, default: Any = None) -> Any:
    """
    Read YAML file with error handling

    Args:
        file_path: Path to YAML file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Parsed YAML data or default value
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return default

    try:
        import yaml
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return default


def write_yaml_file(file_path: Path, data: Any) -> bool:
    """
    Write YAML file with atomic operation

    Args:
        file_path: Path to YAML file
        data: Data to write

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)

    try:
        import yaml
        # Atomic write: write to temp file, then move
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=file_path.parent,
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            yaml.safe_dump(data, tmp_file, default_flow_style=False)
            tmp_path = Path(tmp_file.name)

        # Move temp file to target (atomic on POSIX)
        shutil.move(str(tmp_path), str(file_path))
        return True
    except (yaml.YAMLError, IOError, OSError) as e:
        print(f"Error: Failed to write {file_path}: {e}")
        return False


def safe_file_write(file_path: Path, content: str, backup: bool = True) -> bool:
    """
    Write file with optional backup

    Args:
        file_path: Target file path
        content: Content to write
        backup: Create backup before overwriting

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)

    try:
        # Create backup if file exists
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)

        # Atomic write
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=file_path.parent,
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        shutil.move(str(tmp_path), str(file_path))
        return True
    except (IOError, OSError) as e:
        print(f"Error: Failed to write {file_path}: {e}")
        return False


def copy_with_backup(src: Path, dst: Path) -> bool:
    """
    Copy file with backup of destination

    Args:
        src: Source file path
        dst: Destination file path

    Returns:
        True if successful, False otherwise
    """
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        print(f"Error: Source file {src} does not exist")
        return False

    ensure_dir(dst.parent)

    try:
        # Backup destination if exists
        if dst.exists():
            backup_path = dst.with_suffix(dst.suffix + '.bak')
            shutil.copy2(dst, backup_path)

        # Copy source to destination
        shutil.copy2(src, dst)
        return True
    except (IOError, OSError) as e:
        print(f"Error: Failed to copy {src} to {dst}: {e}")
        return False
