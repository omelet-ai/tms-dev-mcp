#!/usr/bin/env python3
"""
Data models and enums for the OpenAPI indexing pipeline_config.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import settings


class FileConstants:
    """File-related constants from configuration."""

    @property
    def MAX_LINES_PER_READ(self) -> int:
        return settings.pipeline_config.max_lines_per_read

    @property
    def MAX_CHARS_PER_LINE(self) -> int:
        return settings.pipeline_config.max_chars_per_line

    @property
    def JSON_INDENT(self) -> int:
        return settings.pipeline_config.json_indent


# Create singleton instance
file_constants = FileConstants()


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""

    path: str
    method: str
    summary: str | None = None
    description: str | None = None
    parameters: list[dict[str, Any]] | None = None


@dataclass
class SchemaMetadata:
    """Metadata for a schema."""

    source: str
    path: str
    method: str


@dataclass
class GenerationResult:
    """Result from generating documentation or examples."""

    success: bool
    message: str = ""
    generated_json: str | None = None
    attempts_used: int = 1
    api_verification_success: bool | None = None
    api_response_status: int | None = None
    api_duration_ms: float | None = None
    api_verification_error: str | None = None


@dataclass
class PipelineConfig:
    """Configuration for the entire pipeline_config."""

    docs_path: Path
    temp_path: Path | None = None
    force_regenerate: bool = False
    skip_unchanged: bool = True
    parallel_generation: bool = True


@dataclass
class OpenAPISpec:
    """Represents an OpenAPI specification."""

    data: dict[str, Any]
    provider: str | None = None

    @property
    def paths(self) -> dict[str, Any]:
        """Get paths from the spec."""
        return self.data.get("paths", {})

    @property
    def info(self) -> dict[str, Any]:
        """Get info from the spec."""
        return self.data.get("info", {})

    @property
    def tags(self) -> list[dict[str, Any]]:
        """Get tags from the spec."""
        return self.data.get("tags", [])

    def get_title(self) -> str:
        """Get the API title."""
        return self.info.get("title", "API")

    def get_description(self) -> str:
        """Get the API description."""
        return self.info.get("description", "")
