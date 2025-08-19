#!/usr/bin/env python3
"""
Base generator class for OpenAPI documentation generation.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from fastmcp.utilities.logging import get_logger

from ..models import OpenAPISpec
from ..utils import ensure_directory, get_provider_path

logger = get_logger(__name__)


class BaseGenerator(ABC):
    """Abstract base class for all documentation generators."""

    def __init__(self, target_path: Path):
        """
        Initialize the generator.

        Args:
            target_path: Base path for generated files
        """
        self.target_path = target_path

    def get_output_path(self, provider: str | None = None, subdirectory: str | None = None) -> Path:
        """
        Get the output path for generated files.

        Args:
            provider: Optional provider for provider-specific paths
            subdirectory: Optional subdirectory under the provider path

        Returns:
            Path object for the output directory
        """
        path = get_provider_path(self.target_path, provider)
        if subdirectory:
            path = path / subdirectory
        return ensure_directory(path)

    @abstractmethod
    async def generate(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate documentation from the OpenAPI specification.

        Args:
            spec: OpenAPI specification
            provider: Optional provider for provider-specific generation
        """
        pass

    def log_progress(self, message: str, level: str = "info") -> None:
        """
        Log progress messages.

        Args:
            message: Message to log
            level: Log level (info, warning, error)
        """
        log_func = getattr(logger, level, logger.info)
        log_func(f"   {message}")

    def should_skip_endpoint(self, path: str, provider: str | None = None) -> bool:
        """
        Check if an endpoint should be skipped.

        Args:
            path: Endpoint path
            provider: Optional provider

        Returns:
            True if endpoint should be skipped
        """
        # Override in subclasses for specific skip logic
        return False
