#!/usr/bin/env python3
"""
Utility functions for the OpenAPI indexing pipeline_config.
"""

import json
import shutil
from pathlib import Path
from typing import Any

from fastmcp.utilities.logging import get_logger

from .models import file_constants

logger = get_logger(__name__)


def write_json_file(file_path: Path, data: Any, ensure_ascii: bool = False) -> None:
    """
    Write JSON data to a file with consistent formatting.

    Args:
        file_path: Path to write the file
        data: Data to serialize as JSON
        ensure_ascii: Whether to ensure ASCII encoding
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=file_constants.JSON_INDENT)
        f.write("\n")


def read_json_file(file_path: Path) -> dict[str, Any]:
    """
    Read JSON data from a file.

    Args:
        file_path: Path to read the file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_markdown_file(file_path: Path, content: str) -> None:
    """
    Write markdown content to a file.

    Args:
        file_path: Path to write the file
        content: Markdown content
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")


def safe_remove_directory(path: Path) -> bool:
    """
    Safely remove a directory and all its contents.

    Args:
        path: Directory path to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to remove directory {path}: {e}")
        return False


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        The path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def compare_json_files(file1: Path, file2: Path) -> bool:
    """
    Compare two JSON files for equality.

    Args:
        file1: First file path
        file2: Second file path

    Returns:
        True if files contain identical JSON, False otherwise
    """
    try:
        if not (file1.exists() and file2.exists()):
            return False

        with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
            return json.load(f1) == json.load(f2)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not compare {file1} and {file2}: {e}")
        return False


def copy_file_if_exists(source: Path, destination: Path) -> bool:
    """
    Copy a file if it exists.

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        True if file was copied, False otherwise
    """
    try:
        if source.exists() and source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to copy {source} to {destination}: {e}")
        return False


def get_provider_path(base_path: Path, provider: str | None) -> Path:
    """
    Get the path for a specific provider.

    Args:
        base_path: Base directory path
        provider: Provider name or None

    Returns:
        Path with provider subdirectory if provider is specified
    """
    if provider:
        return base_path / provider
    return base_path


def sanitize_path_for_filename(provider: str, path: str) -> str:
    """
    Convert an API path to a safe filename.

    Args:
        path: API path (e.g., "/api/cost-matrix")

    Returns:
        Safe filename (e.g., "cost_matrix")
    """
    from ..config import settings

    # Remove common prefixes
    prefix = settings.pipeline_config.provider_configs[provider].path_prefix
    if path.startswith(prefix):
        path = path[len(prefix) :]
    else:
        path = path.lstrip("/")

    # Replace slashes with underscores
    return path.replace("/", "_")


def escape_markdown_table_content(text: str) -> str:
    """
    Escape text for use in markdown tables.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for markdown tables
    """
    return text.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def get_endpoint_filename(provider: str, path: str) -> str:
    """
    Generate a filename for an endpoint.

    Args:
        provider: Provider name
        path: API endpoint path

    Returns:
        Filename with .json extension
    """
    base = sanitize_path_for_filename(provider, path)
    return f"{base}.json"


def atomic_directory_replace(source: Path, target: Path) -> bool:
    """
    Atomically replace a target directory with source directory.

    Args:
        source: Source directory
        target: Target directory to replace

    Returns:
        True if successful, False otherwise
    """
    try:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return True
    except Exception as e:
        logger.error(f"Failed to replace {target} with {source}: {e}")
        return False
