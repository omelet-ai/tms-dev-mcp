#!/usr/bin/env python3
"""Utility functions for the OpenAPI indexing pipeline_config."""

import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml
from fastmcp.utilities.logging import get_logger

from .models import file_constants

logger = get_logger(__name__)

_FRONT_MATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


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


def load_markdown_with_front_matter(file_path: Path) -> tuple[dict[str, Any], str]:
    """
    Load a markdown file and split optional YAML front matter from the body.

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple of (metadata dict, markdown body without front matter)
    """
    text = file_path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    body = text

    match = _FRONT_MATTER_PATTERN.match(text)
    if match:
        front_matter_text = match.group(1)
        body = text[match.end() :]

        try:
            loaded = yaml.safe_load(front_matter_text) or {}
            if isinstance(loaded, dict):
                metadata = loaded
            else:
                logger.warning(f"Front matter in {file_path} is not a mapping; ignoring metadata.")
        except yaml.YAMLError as exc:  # pragma: no cover - defensive guard
            logger.warning(f"Failed to parse front matter in {file_path}: {exc}")

        body = body.lstrip("\n")

    return metadata, body


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
    return text.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def get_provider_from_path(path: str) -> str:
    from ..config import settings

    for provider_name, provider_config in settings.pipeline_config.provider_configs.items():
        if path.startswith(provider_config.path_prefix):
            return provider_name
    return "omelet"


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


def validate_docs_exist(docs_dir: Path | None = None) -> bool:
    """
    Check if documentation exists and has the required structure.

    Args:
        docs_dir: Optional docs directory path. If None, uses default location.

    Returns:
        True if docs exist and are valid, False otherwise.
    """
    from ..config import settings

    if docs_dir is None:
        docs_dir = Path(__file__).parent.parent / "docs"

    if not docs_dir.exists():
        logger.debug(f"Docs directory does not exist: {docs_dir}")
        return False

    # Check for required shared files
    required_shared_files = [
        docs_dir / "basic_info.md",
        docs_dir / "integration_patterns" / "list.md",
        docs_dir / "troubleshooting" / "list.md",
    ]

    for file_path in required_shared_files:
        if not file_path.exists():
            logger.debug(f"Required shared file missing: {file_path}")
            return False

    # Check for at least one provider with endpoints
    provider_configs = settings.pipeline_config.provider_configs
    has_valid_provider = False

    for provider_name in provider_configs.keys():
        provider_dir = docs_dir / provider_name
        endpoints_summary = provider_dir / "endpoints_summary.md"

        if endpoints_summary.exists():
            has_valid_provider = True
            break

    if not has_valid_provider:
        logger.debug("No provider with endpoints_summary.md found")
        return False

    return True


def atomic_directory_replace(source: Path, target: Path) -> bool:
    backup = target.with_suffix(".backup")
    replacement_succeeded = False

    try:
        if backup.exists():
            shutil.rmtree(backup)

        if target.exists():
            target.rename(backup)

        source.rename(target)
        replacement_succeeded = True

    except OSError as e:
        logger.error(f"Failed to replace {target} with {source}: {e}")
        if backup.exists() and not target.exists():
            try:
                backup.rename(target)
                logger.info(f"Rolled back to previous version at {target}")
            except OSError as rollback_error:
                logger.error(f"Failed to rollback {backup} to {target}: {rollback_error}")
        return False

    if backup.exists():
        try:
            shutil.rmtree(backup)
        except OSError as cleanup_error:
            logger.warning(f"Failed to cleanup backup at {backup}: {cleanup_error}")

    return replacement_succeeded
