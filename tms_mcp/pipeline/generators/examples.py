#!/usr/bin/env python3
"""
Example generation for request bodies using LLM and embedded examples.
"""

import json
from pathlib import Path

from ..graph import RequestBodyGeneratorState, generate_example_json
from ..models import OpenAPISpec, Provider
from ..utils import (
    compare_json_files,
    copy_file_if_exists,
    ensure_directory,
    read_json_file,
    write_json_file,
)
from .base import BaseGenerator


class ExampleGenerator(BaseGenerator):
    """Generator for request body examples."""

    async def generate(self, spec: OpenAPISpec, provider: Provider | None = None) -> None:
        """
        Generate examples (currently not used directly, see smart_generate_request_examples).

        Args:
            spec: OpenAPI specification
            provider: Optional provider
        """
        # This is handled by smart_generate_request_examples in the main pipeline
        pass

    async def smart_generate_request_examples(
        self, current_docs_path: Path, new_docs_path: Path, provider: Provider | None = None
    ) -> None:
        """
        Generate request body examples by comparing new schemas with existing ones.
        Only regenerates examples for new or changed schemas.

        Args:
            current_docs_path: Path to current docs directory
            new_docs_path: Path to new docs directory
            provider: Optional provider name
        """
        # Determine paths based on provider
        if provider:
            provider_str = provider.value
            old_schemas_path = current_docs_path / provider_str / "schemas" / "request_body"
            new_schemas_path = new_docs_path / provider_str / "schemas" / "request_body"
            old_examples_path = current_docs_path / provider_str / "examples" / "request_body"
            new_examples_path = new_docs_path / provider_str / "examples" / "request_body"
        else:
            old_schemas_path = current_docs_path / "schemas" / "request_body"
            new_schemas_path = new_docs_path / "schemas" / "request_body"
            old_examples_path = current_docs_path / "examples" / "request_body"
            new_examples_path = new_docs_path / "examples" / "request_body"

        # Ensure the target examples directory exists
        ensure_directory(new_examples_path)

        # Check if old paths exist to avoid errors on first run
        old_schemas_exist = old_schemas_path.exists() and old_schemas_path.is_dir()
        old_examples_exist = old_examples_path.exists() and old_examples_path.is_dir()

        if not new_schemas_path.exists():
            self.log_progress("No request body schemas found in new docs, skipping example generation.", "warning")
            return

        new_schema_files = {p for p in new_schemas_path.glob("*.json")}

        for new_schema_file in new_schema_files:
            schema_filename = new_schema_file.name
            old_schema_file = old_schemas_path / schema_filename

            should_regenerate = self._should_regenerate_example(new_schema_file, old_schema_file, old_schemas_exist)

            if should_regenerate:
                await self._regenerate_example(new_schema_file, new_examples_path)
            else:
                self._copy_existing_example(
                    schema_filename, old_examples_path, new_examples_path, old_examples_exist, new_schema_file
                )

    def _should_regenerate_example(self, new_schema_file: Path, old_schema_file: Path, old_schemas_exist: bool) -> bool:
        """
        Check if an example should be regenerated.

        Args:
            new_schema_file: Path to new schema file
            old_schema_file: Path to old schema file
            old_schemas_exist: Whether old schemas directory exists

        Returns:
            True if example should be regenerated
        """
        if not old_schemas_exist or not old_schema_file.exists():
            return True

        # Compare schemas
        return not compare_json_files(new_schema_file, old_schema_file)

    async def _regenerate_example(self, schema_file: Path, examples_path: Path) -> None:
        """
        Regenerate an example for a schema.

        Args:
            schema_file: Path to schema file
            examples_path: Path to examples directory
        """
        self.log_progress(f"Schema for {schema_file.name} has changed or is new, updating example.")

        # Try to extract embedded example first
        extracted = self._try_extract_embedded_example(schema_file, examples_path)
        if not extracted:
            # Check if this is an IMAPS schema that should skip LLM generation
            try:
                schema_data = read_json_file(schema_file)
                if isinstance(schema_data, dict) and schema_data.get("_meta", {}).get("source") == "imaps":
                    self.log_progress(
                        f"No embedded example found for IMAPS {schema_file.name}. Skipping example generation."
                    )
                else:
                    await self._generate_llm_example(schema_file, examples_path)
            except Exception:
                # Fallback to LLM generation if metadata can't be read
                await self._generate_llm_example(schema_file, examples_path)

    def _copy_existing_example(
        self,
        schema_filename: str,
        old_examples_path: Path,
        new_examples_path: Path,
        old_examples_exist: bool,
        new_schema_file: Path,
    ) -> None:
        """
        Copy an existing example or regenerate if not found.

        Args:
            schema_filename: Name of the schema file
            old_examples_path: Path to old examples
            new_examples_path: Path to new examples
            old_examples_exist: Whether old examples exist
            new_schema_file: Path to new schema file
        """
        old_example_file = old_examples_path / schema_filename
        new_example_file = new_examples_path / schema_filename

        if old_examples_exist and old_example_file.exists():
            self.log_progress(f"Schema for {schema_filename} is unchanged, copying existing example.")
            copy_file_if_exists(old_example_file, new_example_file)
        else:
            self.log_progress(
                f"Could not find existing example for unchanged schema {schema_filename}. Regenerating.", "warning"
            )
            # Try to extract or generate
            extracted = self._try_extract_embedded_example(new_schema_file, new_examples_path)
            if not extracted:
                try:
                    schema_data = read_json_file(new_schema_file)
                    if isinstance(schema_data, dict) and schema_data.get("_meta", {}).get("source") == "imaps":
                        self.log_progress(
                            f"No embedded example found for IMAPS {schema_filename}. Skipping example generation."
                        )
                except Exception:
                    pass  # Silent fail, already logged warning

    def _try_extract_embedded_example(self, schema_file: Path, examples_path: Path) -> bool:
        """
        Try to extract an embedded example from the requestBody content.

        Args:
            schema_file: Path to the schema file
            examples_path: Directory where the example should be written

        Returns:
            True if an embedded example was found and saved
        """
        try:
            content = read_json_file(schema_file)

            # Look for embedded example
            example_data = None
            if "example" in content:
                example_data = content["example"]
            else:
                examples_obj = content.get("examples")
                if isinstance(examples_obj, dict):
                    # Pick the first example with an inline 'value'
                    for _, ex in examples_obj.items():
                        if isinstance(ex, dict) and "value" in ex:
                            example_data = ex["value"]
                            break

            if example_data is None:
                return False

            # Save example
            example_file = examples_path / schema_file.name
            write_json_file(example_file, example_data)
            self.log_progress(f"Extracted embedded example for {schema_file.name}.")
            return True

        except Exception as e:
            self.log_progress(f"Failed to extract embedded example for {schema_file.name}: {e}", "warning")
            return False

    async def _generate_llm_example(self, schema_file: Path, examples_path: Path) -> None:
        """
        Generate an example using LLM.

        Args:
            schema_file: Path to schema file
            examples_path: Path to examples directory
        """
        self.log_progress(f"Generating LLM-powered example for {schema_file.name}...")

        schema_data = read_json_file(schema_file)

        # Skip LLM generation for IMAPS sources
        meta = schema_data.get("_meta", {}) if isinstance(schema_data, dict) else {}
        if meta.get("source") == "imaps":
            self.log_progress(f"Skipping LLM example generation for IMAPS endpoint: {schema_file.name}")
            return

        schema = schema_data.get("schema", {})

        # Determine the API endpoint from the schema filename
        endpoint_name = schema_file.stem.replace("_", "-")
        endpoint = f"/api/{endpoint_name}"

        # Use the LLM-powered generator
        result = await generate_example_json(schema=schema, endpoint=endpoint, skip_api_verification=False)

        if result.get("success", False):
            # Parse and save the generated JSON
            try:
                generated_json = result.get("generated_json")
                if generated_json is None:
                    raise ValueError("Generated JSON is None")
                example = json.loads(generated_json)

                # Log success with details
                self._log_generation_success(result, schema_file.name)

                # Save example
                example_file = examples_path / schema_file.name
                write_json_file(example_file, example)

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse generated JSON for {schema_file.name}: {e}"
                self.log_progress(error_msg, "error")
                raise RuntimeError(error_msg) from e
        else:
            self._handle_generation_failure(result, schema_file.name)

    def _log_generation_success(self, result: RequestBodyGeneratorState, filename: str) -> None:
        """Log successful generation with details."""
        success_msg = f"Successfully generated example for {filename} (attempts: {result.get('attempts_used', 1)})"
        if result.get("api_verification_success"):
            success_msg += (
                f" [API verified: {result.get('api_response_status')}, {result.get('api_duration_ms', 0):.0f}ms]"
            )
        elif result.get("api_verification_error"):
            success_msg += f" [API verification failed: {result.get('api_verification_error')}]"

        self.log_progress(success_msg)

    def _handle_generation_failure(self, result: RequestBodyGeneratorState, filename: str) -> None:
        """Handle and log generation failure."""
        error_msg = f"Failed to generate example for {filename}: {result.get('message', 'Unknown error')}"
        if result.get("api_verification_error"):
            error_msg += f" [API error: {result.get('api_verification_error')}]"
        self.log_progress(error_msg, "error")
        raise RuntimeError(f"Failed to generate example for {filename}: {result.get('message', 'Unknown error')}")
