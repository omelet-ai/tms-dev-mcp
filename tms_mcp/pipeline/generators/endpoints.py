#!/usr/bin/env python3
"""
Endpoint documentation generators.
"""

from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ...config import settings
from ..models import EndpointInfo, OpenAPISpec, Provider
from ..utils import (
    escape_markdown_table_content,
    get_endpoint_filename,
    safe_remove_directory,
    write_json_file,
    write_markdown_file,
)
from .base import BaseGenerator


class EndpointGenerator(BaseGenerator):
    """Generator for endpoint summaries and overviews."""

    async def generate(self, spec: OpenAPISpec, provider: Optional[Provider] = None) -> None:
        """
        Generate endpoint documentation.

        Args:
            spec: OpenAPI specification
            provider: Optional provider
        """
        await self.generate_endpoints_summary(spec, provider)
        await self.generate_endpoint_overviews(spec, provider)

    async def generate_endpoints_summary(self, spec: OpenAPISpec, provider: Optional[Provider] = None) -> None:
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

    async def generate_endpoint_overviews(self, spec: OpenAPISpec, provider: Optional[Provider] = None) -> None:
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
                filename = get_endpoint_filename(path)
                file_path = overviews_path / filename

                write_json_file(file_path, endpoint_info.__dict__)

        self.log_progress(f"Generated endpoint overviews in {overviews_path}")

    def _extract_endpoint_rows(self, spec: OpenAPISpec) -> List[Tuple[str, str, str]]:
        """Extract endpoint information for summary table."""
        rows = []
        paths = spec.paths

        for path, path_data in paths.items():
            for _, method_data in path_data.items():
                if not isinstance(method_data, dict):
                    continue

                summary = method_data.get("summary", "")
                description = method_data.get("description", "None")
                rows.append((path, summary, description))

        return rows

    def _get_provider_info(self, provider: Optional[Provider]) -> Tuple[str, str]:
        """Get provider-specific title and base URL."""
        if provider == Provider.OMELET:
            title = "# Omelet Routing Engine"
            base_url = getattr(settings, "ROUTING_API_BASE_URL", "https://routing.oaasis.cc")
        elif provider == Provider.INAVI:
            title = "# iNavi Maps"
            imaps_docs_url = getattr(settings, "IMAPS_API_DOCS_URL", "")
            parsed = urlparse(imaps_docs_url) if imaps_docs_url else None
            base_url = (
                f"{parsed.scheme}://{parsed.netloc}"
                if parsed and parsed.scheme and parsed.netloc
                else "https://dev-imaps.inavi.com"
            )
        else:
            title = "# API Endpoints"
            base_url = ""

        return title, base_url

    def _build_summary_markdown(self, title: str, base_url: str, rows: List[Tuple[str, str, str]]) -> str:
        """Build markdown content for endpoints summary."""
        lines = [title]

        if base_url:
            lines.extend([f"**Base URL:** `{base_url}`", ""])

        lines.extend(["## Endpoints", "| Path | Summary | Description |", "|------|---------|-------------|"])

        # Add rows to table
        for path, summary, description in rows:
            path_escaped = escape_markdown_table_content(path)
            summary_escaped = escape_markdown_table_content(summary)
            description_escaped = escape_markdown_table_content(description)
            lines.append(f"| {path_escaped} | {summary_escaped} | {description_escaped} |")

        return "\n".join(lines)

    def _extract_endpoint_info(self, path: str, method: str, method_data: Dict[str, Any]) -> EndpointInfo:
        """Extract endpoint information from method data."""
        return EndpointInfo(
            path=path,
            method=method.upper(),
            summary=method_data.get("summary"),
            description=method_data.get("description"),
            parameters=method_data.get("parameters"),
        )
