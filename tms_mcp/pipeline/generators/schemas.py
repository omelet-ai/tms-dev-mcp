#!/usr/bin/env python3
"""
Schema generators for request and response bodies.
"""

import copy
from typing import Any

from ...config import settings
from ..models import OpenAPISpec
from ..utils import get_endpoint_filename, get_provider_from_path, safe_remove_directory, write_json_file
from .base import BaseGenerator


class SchemaGenerator(BaseGenerator):
    """Generator for request and response schemas."""

    async def generate(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate schema documentation.

        Args:
            spec: OpenAPI specification
            provider: Optional provider
        """
        await self.generate_request_body_schemas(spec, provider)
        await self.generate_response_schemas(spec, provider)

    async def generate_request_body_schemas(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate request body schemas from the OpenAPI specification.

        Args:
            spec: OpenAPI specification
            provider: Optional provider name
        """
        schemas_path = self.get_output_path(provider, "schemas")
        request_body_path = schemas_path / "request_body"

        # Clean and recreate directory
        safe_remove_directory(request_body_path)
        request_body_path.mkdir(parents=True, exist_ok=True)

        paths = spec.paths

        for path, path_data in paths.items():
            for method, method_data in path_data.items():
                if method.lower() != "post" or not isinstance(method_data, dict):
                    continue

                request_body = method_data.get("requestBody")
                if not request_body:
                    continue

                content = request_body.get("content", {})
                app_json = content.get("application/json")
                if not app_json:
                    continue
                # Ensure a schema exists; skip if absent
                if not isinstance(app_json, dict) or not app_json.get("schema"):
                    continue

                # Save schema with metadata
                current_provider = provider or self._get_provider_from_path(path)
                schema_to_save = self._prepare_request_schema(app_json, path, method, current_provider)
                filename = get_endpoint_filename(current_provider, path)
                file_path = request_body_path / filename

                write_json_file(file_path, schema_to_save)

        self.log_progress(f"Generated request body schemas in {request_body_path}")

    async def generate_response_schemas(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate response schemas from the OpenAPI specification.

        Args:
            spec: OpenAPI specification
            provider: Optional provider name
        """
        schemas_path = self.get_output_path(provider, "schemas")
        response_path = schemas_path / "response"

        # Clean and recreate directory
        safe_remove_directory(response_path)
        response_path.mkdir(parents=True, exist_ok=True)

        paths = spec.paths

        for path, path_data in paths.items():
            for method, method_data in path_data.items():
                if not isinstance(method_data, dict):
                    continue

                responses = method_data.get("responses")
                if not responses:
                    continue

                # Create path-specific directory
                current_provider = provider or self._get_provider_from_path(path)
                path_id = self._get_path_id(current_provider, path)
                path_dir = response_path / path_id
                path_dir.mkdir(exist_ok=True)

                # Process each response code
                for response_code, response_data in responses.items():
                    if not isinstance(response_data, dict):
                        continue

                    response_schema = self._extract_response_schema(response_data)
                    if response_schema:
                        filename = f"{response_code}.json"
                        file_path = path_dir / filename
                        write_json_file(file_path, response_schema)

        self.log_progress(f"Generated response schemas in {response_path}")

    def _get_provider_from_path(self, path: str) -> str:
        return get_provider_from_path(path)

    def _prepare_request_schema(
        self, app_json: dict[str, Any], path: str, method: str, provider: str
    ) -> dict[str, Any]:
        """
        Prepare request schema with metadata.

        Args:
            app_json: Application/json content from OpenAPI
            path: API endpoint path
            method: HTTP method
            provider: Provider name

        Returns:
            Schema with metadata attached
        """
        # Only persist the JSON Schema, excluding any examples or other fields
        schema_only: dict[str, Any] = {"schema": copy.deepcopy(app_json.get("schema"))}

        # Intentionally do not include examples or metadata to keep only the schema
        return schema_only

    def _get_path_id(self, provider: str, path: str) -> str:
        """
        Convert API path to directory-safe ID.

        Args:
            path: API endpoint path

        Returns:
            Safe directory name
        """
        if path.startswith(settings.pipeline_config.provider_configs[provider].path_prefix):
            path_id = path[len(settings.pipeline_config.provider_configs[provider].path_prefix) :]
        else:
            path_id = path.lstrip("/")

        return path_id.replace("/", "_")

    def _extract_response_schema(self, response_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Extract schema from response data.

        Args:
            response_data: Response data from OpenAPI

        Returns:
            Extracted full schema or None
        """
        content = response_data.get("content", {})
        app_json = content.get("application/json")
        if not app_json:
            return None

        schema = app_json.get("schema")
        if not schema:
            return None

        return schema
