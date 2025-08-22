#!/usr/bin/env python3
"""
Example generation for request and response bodies from OpenAPI spec.
"""

from ...config import settings
from ..models import OpenAPISpec
from ..utils import ensure_directory, write_json_file
from .base import BaseGenerator


class ExampleGenerator(BaseGenerator):
    """Generator for request and response body examples."""

    async def generate(self, spec: OpenAPISpec, provider: str | None = None) -> None:
        """
        Generate examples from the OpenAPI specification.

        Args:
            spec: OpenAPI specification
            provider: Optional provider
        """
        self.log_progress(f"Generating examples for {provider}...")
        for path, path_item in spec.paths.items():
            for method, operation in path_item.items():
                if "requestBody" in operation:
                    self._extract_examples(
                        operation["requestBody"],
                        "request_body",
                        path,
                        method,
                        provider,
                    )
                if "responses" in operation:
                    for status_code, response in operation["responses"].items():
                        self._extract_examples(
                            response,
                            "response_body",
                            path,
                            method,
                            provider,
                            status_code=status_code,
                        )

    def _extract_examples(
        self,
        content_owner: dict,
        example_type: str,
        path: str,
        method: str,
        provider: str | None,
        status_code: str | None = None,
    ) -> None:
        """
        Extract and save examples from a part of the OpenAPI spec.

        Args:
            content_owner: The object that contains the 'content' field.
            example_type: 'request_body' or 'response_body'.
            path: The endpoint path.
            method: The HTTP method.
            provider: The provider name.
            status_code: The HTTP status code for responses.
        """
        if "content" not in content_owner:
            return

        for content_type, content_details in content_owner["content"].items():
            if "application/json" not in content_type:
                continue

            # Handle single 'example'
            if "example" in content_details:
                self._save_example(
                    content_details["example"],
                    "default",
                    example_type,
                    path,
                    method,
                    provider,
                    status_code=status_code,
                )

            # Handle multiple 'examples'
            if "examples" in content_details:
                for example_name, example_details in content_details["examples"].items():
                    if "value" in example_details:
                        self._save_example(
                            example_details["value"],
                            example_name,
                            example_type,
                            path,
                            method,
                            provider,
                            status_code=status_code,
                        )

    def _save_example(
        self,
        example_data: dict,
        example_name: str,
        example_type: str,
        path: str,
        method: str,
        provider: str | None,
        status_code: str | None = None,
    ) -> None:
        """
        Save an example to a file.

        Args:
            example_data: The example data to save.
            example_name: The name of the example.
            example_type: 'request_body' or 'response_body'.
            path: The endpoint path.
            method: The HTTP method.
            provider: The provider name.
            status_code: The HTTP status code for responses.
        """
        # Get path prefix from settings
        path_prefix = ""
        if provider and provider in settings.pipeline_config.provider_configs:
            path_prefix = settings.pipeline_config.provider_configs[provider].path_prefix

        # Remove path prefix from path
        if path_prefix and path.startswith(path_prefix):
            path = path[len(path_prefix) :]

        # Sanitize path and method for filename
        sane_path = path.replace("/", "_").strip("_")

        # Create a directory for the endpoint
        if example_type == "response_body" and status_code:
            endpoint_dir = self.get_output_path(provider, f"examples/{example_type}/{sane_path}/{status_code}")
        else:
            endpoint_dir = self.get_output_path(provider, f"examples/{example_type}/{sane_path}")
        ensure_directory(endpoint_dir)

        # Create the filename
        example_filename = f"{example_name}.json"
        example_file_path = endpoint_dir / example_filename

        # Save the example
        write_json_file(example_file_path, example_data)
        self.log_progress(f"Saved example '{example_name}' to {example_file_path}")
