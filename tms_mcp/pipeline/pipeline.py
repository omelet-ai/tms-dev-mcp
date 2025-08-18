#!/usr/bin/env python3
"""
OpenAPI Indexing Pipeline
Handles the indexing of OpenAPI specifications of Omelet's Routing Engine API
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any

import httpx
import jsonref
from fastmcp.utilities.logging import get_logger

from ..config import settings
from .generators import EndpointGenerator, ExampleGenerator, SchemaGenerator
from .models import OpenAPISpec, Provider, ProviderConfig
from .utils import atomic_directory_replace, write_json_file, write_markdown_file

logger = get_logger(__name__)

# Provider configurations
PROVIDER_CONFIGS = {
    Provider.OMELET: ProviderConfig(
        name=Provider.OMELET,
        base_url=settings.ROUTING_API_DOCS_URL,
        title="Omelet Routing Engine API",
        description="Advanced routing optimization solutions",
        path_prefix="/api/",
        skip_llm_examples=False,
    ),
    Provider.INAVI: ProviderConfig(
        name=Provider.INAVI,
        base_url=settings.IMAPS_API_DOCS_URL,
        title="iNavi Maps API",
        description="Comprehensive location and routing services",
        path_prefix="/maps/v3.0/appkeys/{appkey}/",
        skip_llm_examples=True,
    ),
}


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


async def get_provider_spec(config: ProviderConfig) -> OpenAPISpec | None:
    """
    Fetch OpenAPI specification for a specific provider configuration.

    Args:
        config: ProviderConfig containing provider configuration details

    Returns:
        OpenAPISpec for the provider or None if failed
    """
    # Check if URL is configured (especially for iNavi)
    if not config.base_url:
        logger.warning(f"   ⚠️ No URL configured for {config.name.value} provider")
        return None

    # Fetch and resolve spec
    spec_data = await fetch_and_resolve_spec(config.base_url)
    if not spec_data:
        logger.warning(f"   ⚠️ Failed to fetch {config.name.value} API spec")
        return None

    # Update title and description
    if "info" not in spec_data:
        spec_data["info"] = {}
    spec_data["info"]["title"] = config.title
    spec_data["info"]["description"] = config.description

    logger.info(f"   ✅ Fetched {config.name.value} API spec with {len(spec_data.get('paths', {}))} endpoints")
    return OpenAPISpec(data=spec_data, provider=config.name)


async def get_provider_specs(providers: list[Provider] | None = None) -> dict[Provider, OpenAPISpec]:
    """
    Fetch OpenAPI specifications for specified providers.

    Args:
        providers: List of providers to fetch specs for. If None, fetches all supported providers.

    Returns:
        Dictionary mapping Provider enum to OpenAPISpec
    """
    if providers is None:
        providers = list(PROVIDER_CONFIGS.keys())

    specs = {}

    # Fetch specs for each provider
    for provider in providers:
        config = PROVIDER_CONFIGS[provider]
        spec = await get_provider_spec(config)
        if spec:
            specs[provider] = spec

    return specs


async def generate_basic_info(target_path: Path) -> None:
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


async def process_provider_documentation(
    spec: OpenAPISpec, provider: Provider, temp_path: Path, target_path: Path
) -> None:
    """
    Process documentation for a single provider.

    Args:
        spec: OpenAPI specification for the provider
        provider: Provider enum
        temp_path: Temporary path for generation
        target_path: Target path for current docs
    """
    logger.info(f"   🔧 Processing {provider.value} documentation...")

    # Create generators
    endpoint_gen = EndpointGenerator(temp_path)
    schema_gen = SchemaGenerator(temp_path)
    example_gen = ExampleGenerator(temp_path)

    # Generate documentation in parallel
    await asyncio.gather(endpoint_gen.generate(spec, provider), schema_gen.generate(spec, provider))

    # Generate examples (configurable per provider)
    provider_config = PROVIDER_CONFIGS[provider]
    if not provider_config.skip_llm_examples:
        await example_gen.smart_generate_request_examples(
            current_docs_path=target_path, new_docs_path=temp_path, provider=provider
        )
    else:
        logger.info(f"   ⏭️  Skipping example generation for {provider.value} provider.")

    # Save provider-specific OpenAPI JSON
    provider_openapi_path = temp_path / provider.value / "openapi.json"
    write_json_file(provider_openapi_path, spec.data)

    logger.info(f"   ✅ Completed {provider.value} documentation.")


async def run_openapi_indexing_pipeline(providers: list[Provider] | None = None) -> None:
    """
    Execute the OpenAPI indexing pipeline.

    Args:
        providers: List of providers to process. If None, processes all supported providers.

    This function will:
    1. Download OpenAPI specs for specified providers
    2. Generate documentation for each provider
    3. Generate comprehensive request body examples smartly
    4. Atomically replace old documentation
    """
    if providers:
        provider_names = ", ".join([p.value for p in providers])
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

        # Generate the shared basic_info.md (at root level)
        await generate_basic_info(temp_path)
        logger.info("   📝 Generated shared basic_info.md")

        # Process each provider's spec
        for provider, spec in provider_specs.items():
            if not spec.paths:
                logger.info(f"   ⏭️  Skipping {provider.value} - no paths found.")
                continue

            await process_provider_documentation(spec, provider, temp_path, target_path)

        logger.info("   🗂️  Generated all provider-specific documents and schemas.")

        # Atomically replace the old docs directory with the new one
        if atomic_directory_replace(temp_path, target_path):
            logger.info("   🚀 Replaced old documentation with the newly generated one.")
        else:
            logger.error("   ❌ Failed to replace documentation directory.")

    logger.info("   🎉 OpenAPI indexing pipeline completed successfully!")
