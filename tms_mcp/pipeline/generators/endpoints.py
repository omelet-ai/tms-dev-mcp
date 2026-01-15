#!/usr/bin/env python3
"""
Endpoint documentation generators.
"""

from typing import Any

from ...config import settings
from ..models import EndpointInfo, OpenAPISpec
from ..utils import (
    escape_markdown_table_content,
    get_endpoint_filename,
    get_provider_from_path,
    safe_remove_directory,
    write_json_file,
    write_markdown_file,
)
from .base import BaseGenerator


class EndpointGenerator(BaseGenerator):
    """Generator for endpoint summaries and overviews."""

    async def generate(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate endpoint documentation.

        Args:
            spec: OpenAPI specification
            provider: Optional provider
        """
        await self.generate_endpoints_summary(spec, provider)
        await self.generate_endpoint_overviews(spec, provider)

    async def generate_endpoints_summary(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate the summary of endpoints in markdown format.

        Args:
            spec: OpenAPI specification
            provider: Optional provider name
        """
        rows = self._extract_endpoint_rows(spec)

        if not rows:
            self.log_progress(f"No endpoints found for provider: {provider}", "warning")
            return

        # Determine base URL and title
        title, base_url = self._get_provider_info(provider)

        # Build markdown content
        content = self._build_summary_markdown(title, base_url, rows)

        # Determine output path
        if provider:
            output_path = self.get_output_path(provider) / "endpoints_summary.md"
        else:
            output_path = self.target_path / "endpoints_summary.md"

        write_markdown_file(output_path, content)
        self.log_progress(f"Generated endpoints summary at {output_path}")

    def _get_provider_from_path(self, path: str) -> str:
        return get_provider_from_path(path)

    async def generate_endpoint_overviews(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate detailed overview for each endpoint.

        Args:
            spec: OpenAPI specification
            provider: Optional provider name
        """
        overviews_path = self.get_output_path(provider, "overviews")

        # Clean existing overviews
        safe_remove_directory(overviews_path)
        overviews_path.mkdir(parents=True, exist_ok=True)

        paths = spec.paths

        for path, path_data in paths.items():
            for method, method_data in path_data.items():
                if not isinstance(method_data, dict):
                    continue

                endpoint_info = self._extract_endpoint_info(path, method, method_data)

                current_provider = provider
                if current_provider is None:
                    current_provider = self._get_provider_from_path(path)

                filename = get_endpoint_filename(current_provider, path)
                file_path = overviews_path / filename

                write_json_file(file_path, endpoint_info.__dict__)

        self.log_progress(f"Generated endpoint overviews in {overviews_path}")

    def _extract_endpoint_rows(self, spec: OpenAPISpec) -> list[tuple[str, str, str, str]]:
        """Extract endpoint information for summary table, including HTTP method."""
        rows = []
        paths = spec.paths

        for path, path_data in paths.items():
            for method, method_data in path_data.items():
                if not isinstance(method_data, dict):
                    continue

                summary = method_data.get("summary", "")
                description = method_data.get("description", "None")
                rows.append((path, method.upper(), summary, description))

        return rows

    def _get_provider_info(self, provider: str | None) -> tuple[str, str]:
        """Get provider-specific title and base URL."""
        if provider:
            provider_configs = settings.pipeline_config.provider_configs
            config = provider_configs.get(provider)
            if config:
                title = f"# {config.title}"
                base_url = config.base_url
            else:
                title = "# API Endpoints"
                base_url = ""
        else:
            title = "# API Endpoints"
            base_url = ""

        return title, base_url

    def _build_summary_markdown(self, title: str, base_url: str, rows: list[tuple[str, str, str, str]]) -> str:
        """Build markdown content for endpoints summary."""
        lines = [title]

        if base_url:
            lines.extend([f"**Base URL:** `{base_url}`", ""])

        lines.extend(
            [
                "## Endpoints",
                "| Path | Method | Summary | Description |",
                "|------|--------|---------|-------------|",
            ]
        )

        # Add rows to table
        for path, method, summary, description in rows:
            path_escaped = escape_markdown_table_content(path)
            method_escaped = escape_markdown_table_content(method)
            summary_escaped = escape_markdown_table_content(summary)
            description_escaped = escape_markdown_table_content(description)
            lines.append(f"| {path_escaped} | {method_escaped} | {summary_escaped} | {description_escaped} |")

        return "\n".join(lines)

    def _extract_endpoint_info(self, path: str, method: str, method_data: dict[str, Any]) -> EndpointInfo:
        """Extract endpoint information from method data."""
        return EndpointInfo(
            path=path,
            method=method.upper(),
            summary=method_data.get("summary"),
            description=method_data.get("description"),
            parameters=method_data.get("parameters"),
        )
