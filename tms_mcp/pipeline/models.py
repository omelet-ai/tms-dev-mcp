#!/usr/bin/env python3
"""
Data models and enums for the OpenAPI indexing pipeline.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class Provider(Enum):
    """Supported API providers."""

    OMELET = "omelet"
    INAVI = "inavi"


class PathPrefix(Enum):
    """API path prefixes for different providers."""

    OMELET = "/api/"
    INAVI = "/"


class FileConstants:
    """File-related constants."""

    MAX_LINES_PER_READ = 2000
    MAX_CHARS_PER_LINE = 2000
    JSON_INDENT = 2


class HttpStatus:
    """HTTP status codes."""

    OK = 200
    NOT_FOUND = 404
    SERVER_ERROR = 500


@dataclass
class ProviderConfig:
    """Configuration for a specific provider."""

    name: Provider
    base_url: str
    title: str
    description: str = ""
    path_prefix: str = "/"
    skip_llm_examples: bool = False


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
    """Configuration for the entire pipeline."""

    docs_path: Path
    temp_path: Path | None = None
    force_regenerate: bool = False
    skip_unchanged: bool = True
    parallel_generation: bool = True


@dataclass
class OpenAPISpec:
    """Represents an OpenAPI specification."""

    data: dict[str, Any]
    provider: Provider | None = None

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
