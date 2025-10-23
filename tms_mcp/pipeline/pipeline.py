#!/usr/bin/env python3
"""
OpenAPI Indexing Pipeline
Handles the indexing of OpenAPI specifications of Omelet's Routing Engine API
"""

import argparse
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any

import httpx
import jsonref
from fastmcp.utilities.logging import get_logger

from ..config import settings
from .generators import EndpointGenerator, ExampleGenerator, SchemaGenerator
from .models import OpenAPISpec
from .utils import (
    atomic_directory_replace,
    escape_markdown_table_content,
    load_markdown_with_front_matter,
    write_json_file,
    write_markdown_file,
)

logger = get_logger(__name__)

# Provider configurations from settings
provider_configs = settings.pipeline_config.provider_configs


async def fetch_and_resolve_spec(url: str) -> dict[str, Any] | None:
    """
    Fetch and resolve an OpenAPI specification from a URL.

    Args:
        url: URL to fetch the OpenAPI spec from

    Returns:
        Resolved OpenAPI specification or None if failed
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            json_text = resp.text
            # Use jsonref.loads to resolve references directly from JSON string
            return jsonref.loads(json_text)
        except Exception as e:
            logger.error(f"Failed to fetch or resolve OpenAPI from {url}: {e}")
            return None


async def get_provider_spec(provider: str) -> OpenAPISpec | None:
    """
    Fetch OpenAPI specification for a specific provider configuration.

    Args:
        provider: Provider name

    Returns:
        OpenAPISpec for the provider or None if failed
    """
    # Check if URL is configured
    if not provider_configs[provider].docs_url:
        logger.warning(f"   ⚠️ No URL configured for {provider_configs[provider].name} provider")
        return None

    # Fetch and resolve spec
    spec_data = await fetch_and_resolve_spec(provider_configs[provider].docs_url)
    if not spec_data:
        logger.warning(f"   ⚠️ Failed to fetch {provider_configs[provider].name} API spec")
        return None

    # Update title and description
    if "info" not in spec_data:
        spec_data["info"] = {}
    spec_data["info"]["title"] = provider_configs[provider].title
    spec_data["info"]["description"] = provider_configs[provider].description

    logger.info(
        f"   ✅ Fetched {provider_configs[provider].name} API spec with {len(spec_data.get('paths', {}))} endpoints"
    )
    return OpenAPISpec(data=spec_data, provider=provider_configs[provider].name)


async def get_provider_specs(providers: list[str] | None = None) -> dict[str, OpenAPISpec]:
    """
    Fetch OpenAPI specifications for specified providers.

    Args:
        providers: List of providers to fetch specs for. If None, fetches all supported providers.

    Returns:
        Dictionary mapping Provider enum to OpenAPISpec
    """
    if providers is None:
        providers = list(provider_configs.keys())

    specs = {}

    # Fetch specs for each provider
    for provider in providers:
        spec = await get_provider_spec(provider)
        if spec:
            specs[provider] = spec

    return specs


async def generate_basic_info(target_path: Path) -> None:
    """
    Generate the basic info of the OpenAPI JSON.
    """
    # Load template
    template_path = Path(__file__).parent / "templates" / "basic_info.md.template"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        # Fallback to default content if template doesn't exist
        content = """## Overview
This MCP server provides intelligent tools to explore two powerful APIs to build effective Transport Management Systems:

### 1. Omelet Routing Engine API
Advanced routing optimization solutions including:
- **Vehicle Routing Problems (VRP)**: Classic and advanced VRP optimization
- **Pickup & Delivery (PDP)**: Optimized pickup and drop-off routing
- **Fleet Size & Mix VRP (FSMVRP)**: Multi-day fleet optimization
- **Cost Matrix**: Distance and duration matrix generation

### 2. iNavi Maps API
Comprehensive location and routing services including:
- **Geocoding**: Convert addresses to coordinates
- **Multi Geocoding**: Process multiple addresses efficiently (batch geocoding)
- **Route Time Prediction**: Get detailed route guidance with estimated travel times
- **Route Distance Matrix**: Calculate distances and times between multiple origin/destination points
- **Multi Optimal Point Search**: Convert coordinates to optimal routing points

## Important Notes
### Regional Limitation
- The OSRM distance_type for auto-calculation of distance matrices for Omelet's API is currently only supported in the Republic of Korea.
- All APIs provided by iNavi Maps exclusively support addresses within the Republic of Korea.

### API Keys
- **Omelet**: Visit https://routing.oaasis.cc/ to get a free API key after signing up
- **iNavi**: Visit https://mapsapi.inavisys.com/ and setup payment to get an API key
"""

    # Write the content to a file
    basic_info_path = target_path / "basic_info.md"
    write_markdown_file(basic_info_path, content)


def _extract_pattern_description(file_path: Path) -> str:
    """Extract the first meaningful line to use as a pattern description."""

    try:
        metadata, body = load_markdown_with_front_matter(file_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(f"   ⚠️ Failed to read description from {file_path}: {exc}")
        return ""

    description = metadata.get("description")
    if isinstance(description, str):
        stripped = description.strip()
        if stripped:
            return stripped

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line == "---":
            continue
        return line

    return ""


def generate_integration_patterns(target_path: Path) -> None:
    """Copy integration pattern templates and generate the list file."""

    templates_dir = Path(__file__).parent / "templates" / "integration_patterns"
    if not templates_dir.exists():
        logger.warning("   ⚠️ Integration pattern templates directory not found; skipping generation.")
        return

    output_dir = target_path / "integration_patterns"

    if output_dir.exists():
        shutil.rmtree(output_dir)

    shutil.copytree(templates_dir, output_dir)

    patterns: list[tuple[str, str]] = []

    for path in sorted(output_dir.rglob("*.md")):
        if path.parent == output_dir:
            # Skip standalone templates (e.g., agentic guidelines) from the listing
            continue

        relative = path.relative_to(output_dir)
        if ".." in relative.parts:
            continue

        pattern_id = "/".join(relative.with_suffix("").parts)
        description = _extract_pattern_description(path) or "(description unavailable)"
        patterns.append((pattern_id, escape_markdown_table_content(description)))

    list_lines = ["| pattern_id | description |", "| --- | --- |"]

    for pattern_id, description in sorted(patterns, key=lambda item: item[0]):
        list_lines.append(f"| {pattern_id} | {description} |")

    write_markdown_file(output_dir / "list.md", "\n".join(list_lines))
    logger.info("   🧩 Generated integration pattern documentation and listing.")


def generate_troubleshooting_guides(target_path: Path) -> None:
    """Copy troubleshooting templates and generate the list file."""

    templates_dir = Path(__file__).parent / "templates" / "troubleshooting"
    if not templates_dir.exists():
        logger.warning("   ⚠️ Troubleshooting templates directory not found; skipping generation.")
        return

    output_dir = target_path / "troubleshooting"

    if output_dir.exists():
        shutil.rmtree(output_dir)

    shutil.copytree(templates_dir, output_dir)

    guides: list[tuple[str, str]] = []

    for path in sorted(output_dir.rglob("*.md")):
        if path.parent == output_dir:
            # Skip standalone templates (e.g., general guidelines) from the listing
            continue

        relative = path.relative_to(output_dir)
        if ".." in relative.parts:
            continue

        guide_id = "/".join(relative.with_suffix("").parts)
        description = _extract_pattern_description(path) or "(description unavailable)"
        guides.append((guide_id, escape_markdown_table_content(description)))

    list_lines = ["| guide_id | description |", "| --- | --- |"]

    for guide_id, description in sorted(guides, key=lambda item: item[0]):
        list_lines.append(f"| {guide_id} | {description} |")

    write_markdown_file(output_dir / "list.md", "\n".join(list_lines))
    logger.info("   🛠️ Generated troubleshooting documentation and listing.")


async def process_provider_documentation(spec: OpenAPISpec, provider: str, temp_path: Path, target_path: Path) -> None:
    """
    Process documentation for a single provider.

    Args:
        spec: OpenAPI specification for the provider
        provider: Provider name
        temp_path: Temporary path for generation
        target_path: Target path for current docs
    """
    logger.info(f"   🔧 Processing {provider} documentation...")

    # Create generators
    endpoint_gen = EndpointGenerator(temp_path)
    schema_gen = SchemaGenerator(temp_path)
    example_gen = ExampleGenerator(temp_path)

    # Generate documentation in parallel
    await asyncio.gather(
        endpoint_gen.generate(spec, provider),
        schema_gen.generate(spec, provider),
        example_gen.generate(spec, provider),
    )

    # Save provider-specific OpenAPI JSON
    provider_openapi_path = temp_path / provider / "openapi.json"
    write_json_file(provider_openapi_path, spec.data)

    logger.info(f"   ✅ Completed {provider} documentation.")


async def run_openapi_indexing_pipeline(providers: list[str] | None = None) -> None:
    """
    Execute the OpenAPI indexing pipeline.

    Args:
        providers: List of providers to process. If None, processes all supported providers.

    This function will:
    1. Download OpenAPI specs for specified providers
    2. Generate documentation for each provider
    3. Extract request and response examples from OpenAPI specs
    4. Atomically replace old documentation
    """
    if providers:
        provider_names = ", ".join(providers)
        logger.info(f"🚩 Initializing OpenAPI indexing pipeline for: {provider_names}... 🚩")
    else:
        logger.info("🚩 Initializing OpenAPI indexing pipeline for all providers... 🚩")

    # Fetch specs for specified providers
    try:
        provider_specs = await get_provider_specs(providers)
        if not provider_specs:
            logger.error("   ❌ No OpenAPI specs could be loaded. Aborting pipeline.")
            return
        logger.info(f"   ✅ Fetched {len(provider_specs)} provider spec(s).")
    except Exception as e:
        logger.error(f"   ❌ Failed to fetch OpenAPI specs: {e}. Aborting pipeline.")
        return

    # Target path for documentation
    target_path = Path(__file__).parent.parent / "docs"

    # Use a temporary directory for the new documentation
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_path = Path(temp_dir_str)
        logger.info(f"   📂 Created temporary workspace at {temp_path}.")

        # If updating specific providers (not all), preserve existing docs for other providers
        if providers and target_path.exists():
            all_providers = list(provider_configs.keys())
            providers_to_preserve = [p for p in all_providers if p not in providers]

            if providers_to_preserve:
                logger.info(f"   📁 Preserving existing docs for: {', '.join(providers_to_preserve)}")
                for preserve_provider in providers_to_preserve:
                    source_dir = target_path / preserve_provider
                    if source_dir.exists():
                        dest_dir = temp_path / preserve_provider
                        shutil.copytree(source_dir, dest_dir)
                        logger.info(f"   ✅ Preserved {preserve_provider} documentation")

        # Generate the shared basic_info.md (at root level)
        await generate_basic_info(temp_path)
        logger.info("   📝 Generated shared basic_info.md")

        # Copy integration patterns and create listing
        generate_integration_patterns(temp_path)

        # Copy troubleshooting guides and create listing
        generate_troubleshooting_guides(temp_path)

        # Process each provider's spec
        for provider, spec in provider_specs.items():
            if not spec.paths:
                logger.info(f"   ⏭️  Skipping {provider} - no paths found.")
                continue

            await process_provider_documentation(spec, provider, temp_path, target_path)

        logger.info("   🗂️  Generated all provider-specific documents and schemas.")

        # Atomically replace the old docs directory with the new one
        if atomic_directory_replace(temp_path, target_path):
            logger.info("   🚀 Replaced old documentation with the newly generated one.")
        else:
            logger.error("   ❌ Failed to replace documentation directory.")

    logger.info("   🎉 OpenAPI indexing pipeline completed successfully!")


def main() -> None:
    """
    Main entry point for the OpenAPI indexing pipeline.
    Accepts optional provider names as command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="OpenAPI Indexing Pipeline - Generate documentation for TMS providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Update all providers
  uv run python -m tms_mcp.pipeline.pipeline

  # Update specific providers
  uv run python -m tms_mcp.pipeline.pipeline omelet
  uv run python -m tms_mcp.pipeline.pipeline omelet inavi

  # List available providers
  uv run python -m tms_mcp.pipeline.pipeline --list-providers
""",
    )

    parser.add_argument(
        "providers",
        nargs="*",
        help="Provider names to update (e.g., omelet, inavi). If not specified, updates all providers.",
        choices=list(provider_configs.keys()) + [[]],  # Allow empty list
    )

    parser.add_argument("--list-providers", action="store_true", help="List all available providers and exit")

    args = parser.parse_args()

    # List providers if requested
    if args.list_providers:
        print("Available providers:")
        for provider_key, provider_config in provider_configs.items():
            print(f"  - {provider_key}: {provider_config.title}")
        return

    # Run the pipeline with specified providers (or all if none specified)
    providers_to_update = args.providers if args.providers else None

    if providers_to_update:
        logger.info(f"Updating specific providers: {', '.join(providers_to_update)}")
    else:
        logger.info("Updating all providers")

    asyncio.run(run_openapi_indexing_pipeline(providers_to_update))


if __name__ == "__main__":
    main()
