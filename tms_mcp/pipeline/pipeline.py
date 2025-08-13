#!/usr/bin/env python3
"""
OpenAPI Indexing Pipeline
Handles the indexing of OpenAPI specifications of Omelet's Routing Engine API
"""

import asyncio
import copy
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from fastmcp.utilities.logging import get_logger

from ..config import settings
from .graph import generate_example_json

logger = get_logger(__name__)


def _split_openapi_by_provider(combined_json: dict) -> dict[str, dict]:
    """
    Split a combined OpenAPI JSON into provider-specific specs.

    Args:
        combined_json: Combined OpenAPI specification with paths from multiple providers

    Returns:
        Dictionary mapping provider names to their respective OpenAPI specs
    """
    omelet_spec = copy.deepcopy(combined_json)
    inavi_spec = copy.deepcopy(combined_json)

    # Split paths by provider
    omelet_paths = {}
    inavi_paths = {}

    for path, path_data in combined_json.get("paths", {}).items():
        if path.startswith("/api/"):
            omelet_paths[path] = path_data
        else:
            inavi_paths[path] = path_data

    # Update specs with provider-specific paths
    omelet_spec["paths"] = omelet_paths
    inavi_spec["paths"] = inavi_paths

    # Update titles to be provider-specific
    if "info" in omelet_spec:
        omelet_spec["info"]["title"] = "Omelet Routing Engine API"
        if "description" in omelet_spec["info"]:
            # Remove the combined description line if present
            desc = omelet_spec["info"]["description"]
            if "This documentation combines:" in desc:
                # Extract original description after the combined line
                lines = desc.split("\n")
                omelet_spec["info"]["description"] = "\n".join(
                    [l for l in lines if not l.startswith("This documentation combines:")]
                )

    if "info" in inavi_spec:
        inavi_spec["info"]["title"] = "iNavi Maps API"
        if "description" in inavi_spec["info"]:
            desc = inavi_spec["info"]["description"]
            if "This documentation combines:" in desc:
                lines = desc.split("\n")
                inavi_spec["info"]["description"] = "\n".join(
                    [l for l in lines if not l.startswith("This documentation combines:")]
                )

    return {"omelet": omelet_spec, "inavi": inavi_spec}


def resolve_refs(schema: dict | list, root_schema: dict) -> Any:
    """
    Recursively resolve all $ref references in the schema.
    If a $ref is found with sibling properties, they will be merged,
    with sibling properties overriding the referenced schema.
    """
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if not ref_path.startswith("#/"):
                raise NotImplementedError("External references not supported")

            # Resolve the reference path
            path_parts = ref_path[2:].split("/")
            ref_value = root_schema
            for part in path_parts:
                ref_value = ref_value[part]

            # Recursively resolve the referenced content
            resolved_ref = resolve_refs(copy.deepcopy(ref_value), root_schema)

            # Get sibling properties and resolve them as well
            sibling_properties = {k: v for k, v in schema.items() if k != "$ref"}

            if not sibling_properties:
                return resolved_ref

            resolved_siblings = resolve_refs(sibling_properties, root_schema)

            if isinstance(resolved_ref, dict):
                # Merge resolved reference with resolved sibling properties
                merged_schema = resolved_ref.copy()
                merged_schema.update(resolved_siblings)
                return merged_schema

            logger.warning(
                f"A $ref to a non-object was found with sibling properties, which will be ignored. Ref: {ref_path}"
            )
            return resolved_ref

        # Recursively process all dictionary values if no $ref is present at this level
        return {k: resolve_refs(v, root_schema) for k, v in schema.items()}

    elif isinstance(schema, list):
        # Recursively process all list items
        return [resolve_refs(item, root_schema) for item in schema]

    else:
        # Return primitive values as-is
        return schema


def _try_extract_and_save_embedded_example(schema_file: Path, examples_path: Path) -> bool:
    """
    Try to extract an embedded example from the requestBody content and save it.

    This prefers inline OpenAPI examples over LLM generation when available. It supports:
    - application/json.example
    - application/json.examples[*].value (first one with an inline value)

    Args:
        schema_file: Path to the saved request body content JSON (contains 'schema', optional 'example(s)')
        examples_path: Directory where the example JSON should be written

    Returns:
        True if an embedded example was found and saved, otherwise False
    """
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        # The saved file mirrors application/json content: may include 'schema', 'example', 'examples'
        if "example" in content:
            example_data = content["example"]
        else:
            example_data = None
            examples_obj = content.get("examples")
            if isinstance(examples_obj, dict):
                # Pick the first example with an inline 'value'
                for _name, ex in examples_obj.items():
                    if isinstance(ex, dict) and "value" in ex:
                        example_data = ex["value"]
                        break

        if example_data is None:
            return False

        # Save example as the same filename under examples path
        examples_path.mkdir(parents=True, exist_ok=True)
        out_file = examples_path / schema_file.name
        with open(out_file, "w", encoding="utf-8") as out:
            json.dump(example_data, out, ensure_ascii=False, indent=2)
            out.write("\n")

        logger.info(f"   📦 Extracted embedded example for {schema_file.name}.")
        return True

    except Exception as e:
        logger.warning(f"   ⚠️  Failed to extract embedded example for {schema_file.name}: {e}")
        return False


async def get_resolved_json() -> dict:
    """
    Download OpenAPI JSON from configured URLs, resolve refs, and merge into a single spec.

    The primary source is ROUTING_API_DOCS_URL. Optionally, IMAPS_API_DOCS_URL
    will be fetched and its paths merged into the combined document.
    """
    async with httpx.AsyncClient() as client:
        combined: dict[str, Any] | None = None

        # Helper to resolve
        async def _fetch_and_resolve(url: str) -> dict | None:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return resolve_refs(data, data)
            except Exception as e:  # Broad catch to continue with other sources
                logger.error(f"Failed to fetch or resolve OpenAPI from {url}: {e}")
                return None

        primary = await _fetch_and_resolve(settings.ROUTING_API_DOCS_URL)
        if primary is None:
            raise RuntimeError("Primary OpenAPI source could not be loaded")

        combined = primary

        # Attempt to fetch and merge IMAPS spec
        if getattr(settings, "IMAPS_API_DOCS_URL", None):
            imaps = await _fetch_and_resolve(settings.IMAPS_API_DOCS_URL)
            if imaps is not None:
                # Merge paths
                combined_paths = combined.setdefault("paths", {})
                for p, v in imaps.get("paths", {}).items():
                    if p in combined_paths:
                        logger.warning(
                            f"Duplicate path found while merging specs: {p}. Overwriting with IMAPS version."
                        )
                    combined_paths[p] = v

                # Optionally merge tags for better summaries
                if "tags" in imaps:
                    existing_tags = {t.get("name"): t for t in combined.get("tags", []) if isinstance(t, dict)}
                    for t in imaps.get("tags", []) or []:
                        if isinstance(t, dict) and t.get("name") not in existing_tags:
                            combined.setdefault("tags", []).append(t)

                # Update info to mention combined sources
                try:
                    title = combined.get("info", {}).get("title", "API")
                    imaps_title = imaps.get("info", {}).get("title", "IMAPS API")
                    combined.setdefault("info", {})
                    combined["info"]["description"] = (
                        f"This documentation combines: {title} and {imaps_title}. "
                        + str(combined["info"].get("description", ""))
                    ).strip()
                except Exception:
                    pass

        return combined


async def generate_basic_info(json_data: dict, target_path: Path) -> None:
    """
    Generate the basic info of the OpenAPI JSON.
    """
    # Compose the content
    content = """## Overview
This MCP server provides intelligent tools to explore two powerful APIs to build effective Transport Management Systems:

### 1. Omelet Routing Engine API
Advanced routing optimization solutions including:
- **Vehicle Routing Problems (VRP)**: Classic and advanced VRP optimization
- **Pickup & Delivery (PDP)**: Optimized pickup and drop-off routing
- **Fleet Size & Mix VRP (FSMVRP)**: Multi-day fleet optimization
- **Cost Matrix**: Distance and duration matrix generation

### 2. iNavi Maps API
Location services including:
- **Geocoding**: Convert addresses to coordinates
- **Batch Geocoding**: Process multiple addresses efficiently

## Important Notes
### Regional Limitation
The OSRM distance_type for auto-calculation of distance matrices is currently only supported in the Republic of Korea. You can still use our optimization engine by providing your own distance matrix.

### API Keys
- **Omelet**: Visit https://routing.oaasis.cc/ to get a free API key after signing up
- **iNavi**: Visit https://mapsapi.inavisys.com/ and setup payment to get an API key
"""

    # Write the content to a file
    basic_info_path = target_path / "basic_info.md"
    with open(basic_info_path, "w", encoding="utf-8") as f:
        f.write(content)


async def generate_endpoints_summary(json_data: dict, target_path: Path, provider: str | None = None) -> None:
    """
    Generate the summary of the endpoints in the OpenAPI JSON.

    Args:
        json_data: OpenAPI specification data
        target_path: Path to write the summary file
        provider: Optional provider name to filter endpoints ("omelet" or "inavi")
    """
    paths = json_data.get("paths", {})

    # Build endpoint rows
    rows = []
    for path, path_data in paths.items():
        for _, method_data in path_data.items():
            if not isinstance(method_data, dict):
                continue

            summary = method_data.get("summary", "")
            description = method_data.get("description", "None")
            rows.append((path, summary, description))

    if not rows:
        logger.warning(f"   ⚠️  No endpoints found for provider: {provider}")
        return

    # Determine base URL and title based on provider
    if provider == "omelet":
        title = "# Omelet Routing Engine"
        base_url = getattr(settings, "ROUTING_API_BASE_URL", "https://routing.oaasis.cc")
    elif provider == "inavi":
        title = "# iNavi Maps"
        imaps_docs_url = getattr(settings, "IMAPS_API_DOCS_URL", "")
        parsed = urlparse(imaps_docs_url) if imaps_docs_url else None
        base_url = (
            f"{parsed.scheme}://{parsed.netloc}"
            if parsed and parsed.scheme and parsed.netloc
            else "https://dev-imaps.inavi.com"
        )
    else:
        # For backward compatibility when provider is None
        title = "# API Endpoints"
        base_url = ""

    # Build markdown content
    markdown_lines = [title]

    if base_url:
        markdown_lines.append(f"**Base URL:** `{base_url}`  ")
        markdown_lines.append("")

    markdown_lines.extend(
        [
            "## Endpoints",
            "| Path | Summary | Description |",
            "|------|---------|-------------|",
        ]
    )

    # Add rows to table
    for path, summary, description in rows:
        # Escape pipe characters and newlines
        path_escaped = path.replace("|", "\\|")
        summary_escaped = summary.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        description_escaped = description.replace("|", "\\|").replace("\n", " ").replace("\r", " ")

        markdown_lines.append(f"| {path_escaped} | {summary_escaped} | {description_escaped} |")

    # Join all lines
    content = "\n".join(markdown_lines)

    # Determine output path based on provider
    if provider:
        endpoints_summary_path = target_path / provider / "endpoints_summary.md"
        endpoints_summary_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        endpoints_summary_path = target_path / "endpoints_summary.md"

    with open(endpoints_summary_path, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")


async def generate_endpoint_overviews(json_data: dict, target_path: Path, provider: str | None = None) -> None:
    """
    Generate the overview of each endpoint in the OpenAPI JSON, which includes method, summary, description, and parameters.

    Args:
        json_data: OpenAPI specification data
        target_path: Path to write overview files
        provider: Optional provider name for organizing files ("omelet" or "inavi")
    """
    # Determine output path based on provider
    if provider:
        overviews_path = target_path / provider / "overviews"
    else:
        overviews_path = target_path / "overviews"

    if overviews_path.exists():
        shutil.rmtree(overviews_path)
    overviews_path.mkdir(parents=True, exist_ok=True)

    paths = json_data.get("paths", {})

    for path, path_data in paths.items():
        for method, method_data in path_data.items():
            if not isinstance(method_data, dict):
                continue

            endpoint_data = {
                "method": method.upper(),
                "summary": method_data.get("summary"),
            }

            if "description" in method_data:
                endpoint_data["description"] = method_data["description"]

            if "parameters" in method_data:
                endpoint_data["parameters"] = method_data["parameters"]

            if path.startswith("/api/"):
                filename_base = path[len("/api/") :]
            else:
                filename_base = path.lstrip("/")

            filename = f"{filename_base.replace('/', '_')}.json"
            file_path = overviews_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(endpoint_data, f, ensure_ascii=False, indent=2)
                f.write("\n")


async def generate_request_body_schemas(json_data: dict, target_path: Path, provider: str | None = None) -> None:
    """
    Generate the details of the request bodies in the OpenAPI JSON.

    Args:
        json_data: OpenAPI specification data
        target_path: Path to write schema files
        provider: Optional provider name for organizing files ("omelet" or "inavi")
    """
    # Determine output path based on provider
    if provider:
        schemas_path = target_path / provider / "schemas"
    else:
        schemas_path = target_path / "schemas"

    schemas_path.mkdir(parents=True, exist_ok=True)

    # Create the request_body subdirectory
    request_body_path = schemas_path / "request_body"
    if request_body_path.exists():
        shutil.rmtree(request_body_path)
    request_body_path.mkdir(parents=True, exist_ok=True)

    paths = json_data.get("paths", {})

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

            # Copy content to avoid mutating original and attach metadata
            schema_to_save = copy.deepcopy(app_json)
            source = "primary" if path.startswith("/api/") else "imaps"
            schema_to_save["_meta"] = {"source": source, "path": path, "method": method.upper()}

            if path.startswith("/api/"):
                filename_base = path[len("/api/") :]
            else:
                filename_base = path.lstrip("/")

            filename = f"{filename_base.replace('/', '_')}.json"
            file_path = request_body_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(schema_to_save, f, ensure_ascii=False, indent=2)
                f.write("\n")


async def generate_response_schemas(json_data: dict, target_path: Path, provider: str | None = None) -> None:
    """
    Generate the response schemas from the OpenAPI JSON.

    Args:
        json_data: OpenAPI specification data
        target_path: Path to write response schema files
        provider: Optional provider name for organizing files ("omelet" or "inavi")
    """
    # Determine output path based on provider
    if provider:
        schemas_path = target_path / provider / "schemas"
    else:
        schemas_path = target_path / "schemas"

    if not schemas_path.exists():
        schemas_path.mkdir(parents=True)

    # Create the response subdirectory
    response_path = schemas_path / "response"
    if response_path.exists():
        shutil.rmtree(response_path)
    response_path.mkdir(parents=True, exist_ok=True)

    paths = json_data.get("paths", {})

    for path, path_data in paths.items():
        for method, method_data in path_data.items():
            if not isinstance(method_data, dict):
                continue

            responses = method_data.get("responses")
            if not responses:
                continue

            # Create path-specific directory
            if path.startswith("/api/"):
                path_id = path[len("/api/") :]
            else:
                path_id = path.lstrip("/")

            path_id = path_id.replace("/", "_")
            path_dir = response_path / path_id
            path_dir.mkdir(exist_ok=True)

            # Process each response code
            for response_code, response_data in responses.items():
                if not isinstance(response_data, dict):
                    continue

                content = response_data.get("content", {})
                app_json = content.get("application/json")
                if not app_json:
                    continue

                schema = app_json.get("schema")
                if not schema:
                    continue

                # Extract properties from schema
                properties = schema.get("properties")
                if not properties:
                    continue

                # Wrap in the specified format
                response_schema_content = {"response_schema": properties}

                # Save the schema
                filename = f"{response_code}.json"
                file_path = path_dir / filename

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(response_schema_content, f, ensure_ascii=False, indent=2)
                    f.write("\n")


async def _generate_request_example_for_schema(schema_file: Path, examples_path: Path) -> None:
    """
    Generate a comprehensive request body example for a single schema using LLM.
    """
    logger.info(f"   🤖 Generating LLM-powered example for {schema_file.name}...")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    # Skip LLM generation for IMAPS sources
    meta = schema_data.get("_meta", {}) if isinstance(schema_data, dict) else {}
    if meta.get("source") == "imaps":
        logger.info(f"   ⏭️  Skipping LLM example generation for IMAPS endpoint: {schema_file.name}")
        return

    schema = schema_data.get("schema", {})

    # Determine the API endpoint from the schema filename
    # Convert filename back to endpoint path (e.g., "cost_matrix.json" -> "/api/cost-matrix")
    endpoint_name = schema_file.stem.replace("_", "-")
    endpoint = f"/api/{endpoint_name}"

    # Use the new LLM-powered generator with API verification enabled
    result = await generate_example_json(schema=schema, endpoint=endpoint, skip_api_verification=False)

    if result.get("success", False):
        # Parse the generated JSON string
        try:
            generated_json = result.get("generated_json")
            if generated_json is None:
                raise ValueError("Generated JSON is None")
            example = json.loads(generated_json)

            # Log success with API verification details
            success_msg = (
                f"   ✅ Successfully generated example for {schema_file.name} "
                f"(attempts: {result.get('attempts_used', 1)})"
            )
            if result.get("api_verification_success"):
                success_msg += (
                    f" [API verified: {result.get('api_response_status')}, {result.get('api_duration_ms', 0):.0f}ms]"
                )
            elif result.get("api_verification_error"):
                success_msg += f" [API verification failed: {result.get('api_verification_error')}]"

            logger.info(success_msg)

        except json.JSONDecodeError as e:
            logger.error(f"   ❌ Failed to parse generated JSON for {schema_file.name}: {e}")
            raise RuntimeError(f"Failed to parse generated JSON for {schema_file.name}: {e}") from e
    else:
        error_msg = f"   ❌ Failed to generate example for {schema_file.name}: {result.get('message', 'Unknown error')}"
        if result.get("api_verification_error"):
            error_msg += f" [API error: {result.get('api_verification_error')}]"
        logger.error(error_msg)
        raise RuntimeError(
            f"Failed to generate example for {schema_file.name}: {result.get('message', 'Unknown error')}"
        )

    # Save example directly as endpoint_name.json (similar to schemas structure)
    example_file = examples_path / schema_file.name
    with open(example_file, "w", encoding="utf-8") as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
        f.write("\n")


async def smart_generate_request_examples(
    current_docs_path: Path, new_docs_path: Path, provider: str | None = None
) -> None:
    """
    Generate request body examples by comparing new schemas with existing ones.
    It only regenerates examples for new or changed schemas.

    Args:
        current_docs_path: Path to current docs directory
        new_docs_path: Path to new docs directory
        provider: Optional provider name for organizing files ("omelet" or "inavi")
    """
    # Determine paths based on provider
    if provider:
        old_schemas_path = current_docs_path / provider / "schemas" / "request_body"
        new_schemas_path = new_docs_path / provider / "schemas" / "request_body"
        old_examples_path = current_docs_path / provider / "examples" / "request_body"
        new_examples_path = new_docs_path / provider / "examples" / "request_body"
    else:
        old_schemas_path = current_docs_path / "schemas" / "request_body"
        new_schemas_path = new_docs_path / "schemas" / "request_body"
        old_examples_path = current_docs_path / "examples" / "request_body"
        new_examples_path = new_docs_path / "examples" / "request_body"

    # Ensure the target examples directory exists
    new_examples_path.mkdir(parents=True, exist_ok=True)

    # Check if old paths exist to avoid errors on first run
    old_schemas_exist = old_schemas_path.exists() and old_schemas_path.is_dir()
    old_examples_exist = old_examples_path.exists() and old_examples_path.is_dir()

    if not new_schemas_path.exists():
        logger.warning("   ⚠️  No request body schemas found in new docs, skipping example generation.")
        return

    new_schema_files = {p for p in new_schemas_path.glob("*.json")}

    for new_schema_file in new_schema_files:
        schema_filename = new_schema_file.name
        old_schema_file = old_schemas_path / schema_filename

        should_regenerate = True
        if old_schemas_exist and old_schema_file.exists():
            try:
                with (
                    open(new_schema_file, "r", encoding="utf-8") as f1,
                    open(old_schema_file, "r", encoding="utf-8") as f2,
                ):
                    if json.load(f1) == json.load(f2):
                        should_regenerate = False
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"   ⚠️  Could not compare schemas for {schema_filename}: {e}. Regenerating example.")

        if should_regenerate:
            logger.info(f"   🔄 Schema for {schema_filename} has changed or is new, updating example.")
            # Prefer embedded example if available in the OpenAPI content
            extracted = _try_extract_and_save_embedded_example(new_schema_file, new_examples_path)
            if not extracted:
                # If this schema is from IMAPS, skip LLM generation entirely
                try:
                    with open(new_schema_file, "r", encoding="utf-8") as f:
                        _content = json.load(f)
                    if isinstance(_content, dict) and _content.get("_meta", {}).get("source") == "imaps":
                        logger.info(
                            f"   ⏭️  No embedded example found for IMAPS {schema_filename}. Skipping example generation."
                        )
                    else:
                        await _generate_request_example_for_schema(new_schema_file, new_examples_path)
                except Exception:
                    # Fallback to LLM generation if metadata can't be read
                    await _generate_request_example_for_schema(new_schema_file, new_examples_path)
        else:
            old_example_file = old_examples_path / schema_filename
            new_example_file = new_examples_path / schema_filename
            if old_examples_exist and old_example_file.exists():
                logger.info(f"   ✅ Schema for {schema_filename} is unchanged, copying existing example.")
                shutil.copy2(old_example_file, new_example_file)
            else:
                logger.warning(
                    f"   ⚠️  Could not find existing example for unchanged schema {schema_filename}. Regenerating."
                )
                # Prefer embedded example if available in the OpenAPI content
                extracted = _try_extract_and_save_embedded_example(new_schema_file, new_examples_path)
                if not extracted:
                    try:
                        with open(new_schema_file, "r", encoding="utf-8") as f:
                            _content = json.load(f)
                        if isinstance(_content, dict) and _content.get("_meta", {}).get("source") == "imaps":
                            logger.info(
                                f"   ⏭️  No embedded example found for IMAPS {schema_filename}. Skipping example generation."
                            )
                        else:
                            await _generate_request_example_for_schema(new_schema_file, new_examples_path)
                    except Exception:
                        await _generate_request_example_for_schema(new_schema_file, new_examples_path)


async def run_openapi_indexing_pipeline() -> None:
    """
    Execute the OpenAPI indexing pipeline.

    This function will:
    1. Download the OpenAPI JSON and resolve the refs
    2. Check if docs/openapi.json exists and compare with downloaded version
    3. Skip pipeline if identical, otherwise continue
    4. Generate and store documents to be used by the MCP server
    5. Generate comprehensive request body examples smartly
    """
    logger.info("🚩 Initializing OpenAPI indexing pipeline... 🚩")

    # Download the OpenAPI JSON and resolve the refs
    try:
        resolved_json = await get_resolved_json()
        logger.info("   ✅ Downloaded and resolved refs of OpenAPI JSON. ✅")
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.error(f"   ❌ Failed to download OpenAPI JSON: {e}. Aborting pipeline.")
        return

    # Split the combined spec by provider
    provider_specs = _split_openapi_by_provider(resolved_json)
    logger.info("   📊 Split OpenAPI spec by provider (omelet, inavi).")

    # Check if existing openapi.json exists and compare
    target_path = Path(__file__).parent.parent / "docs"

    # Use a temporary directory for the new documentation
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_path = Path(temp_dir_str)
        logger.info(f"   📂 Created temporary workspace at {temp_path}.")

        # Generate the shared basic_info.md (at root level)
        await generate_basic_info(resolved_json, temp_path)
        logger.info("   📝 Generated shared basic_info.md")

        # Process each provider separately
        for provider_name, provider_spec in provider_specs.items():
            if not provider_spec.get("paths"):
                logger.info(f"   ⏭️  Skipping {provider_name} - no paths found.")
                continue

            logger.info(f"   🔧 Processing {provider_name} documentation...")

            # Generate provider-specific documents
            await asyncio.gather(
                generate_endpoints_summary(provider_spec, temp_path, provider=provider_name),
                generate_endpoint_overviews(provider_spec, temp_path, provider=provider_name),
                generate_request_body_schemas(provider_spec, temp_path, provider=provider_name),
                generate_response_schemas(provider_spec, temp_path, provider=provider_name),
            )

            # Generate examples for this provider (skip for iNavi)
            if provider_name != "inavi":
                await smart_generate_request_examples(
                    current_docs_path=target_path, new_docs_path=temp_path, provider=provider_name
                )
            else:
                logger.info(f"   ⏭️  Skipping example generation for {provider_name} provider.")

            # Save provider-specific OpenAPI JSON
            provider_openapi_path = temp_path / provider_name / "openapi.json"
            provider_openapi_path.parent.mkdir(parents=True, exist_ok=True)
            with open(provider_openapi_path, "w", encoding="utf-8") as f:
                json.dump(provider_spec, f, ensure_ascii=False, indent=2)
                f.write("\n")

            logger.info(f"   ✅ Completed {provider_name} documentation.")

        logger.info("   🗂️  Generated all provider-specific documents and schemas.")

        # Atomically replace the old docs directory with the new one
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(temp_path, target_path)
        logger.info("   🚀 Replaced old documentation with the newly generated one.")

    logger.info("   🎉 OpenAPI indexing pipeline completed successfully!")
