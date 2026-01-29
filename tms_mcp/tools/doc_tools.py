"""Documentation tools for the Omelet Routing Engine MCP server."""

import json
import os
import re
from pathlib import Path
from typing import Annotated

from fastmcp.exceptions import ToolError

from tms_mcp.config import settings
from tms_mcp.pipeline.utils import get_provider_from_path, load_markdown_with_front_matter
from tms_mcp.server import mcp
from tms_mcp.tools.models import (
    EndpointsListResult,
    EndpointSummary,
    ExamplesListResult,
    GuidesListResult,
    GuideSummary,
    PatternsListResult,
    PatternSummary,
)

provider_configs = settings.pipeline_config.provider_configs


def _get_docs_dir() -> Path:
    """Get the docs directory path."""
    return Path(__file__).parent.parent / "docs"


def _get_integration_patterns_dir() -> Path:
    """Get the integration patterns directory path."""
    return _get_docs_dir() / "integration_patterns"


def _get_troubleshooting_dir() -> Path:
    """Get the troubleshooting guides directory path."""
    return _get_docs_dir() / "troubleshooting"


_get_provider_from_path = get_provider_from_path


def _path_to_path_id(path: str, provider: str | None = None) -> str:
    """
    Convert API path to path_id format based on provider configuration.

    Args:
        path: API path (e.g., "/api/foo/bar" or "/maps/v3.0/appkeys/{appkey}/coordinates")
        provider: Optional provider name to determine conversion logic

    Returns:
        Path ID (e.g., "foo_bar" for Omelet, "coordinates" for iNavi)
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = _get_provider_from_path(path)

    # Get provider configuration
    provider_config = provider_configs.get(provider)
    if not provider_config:
        # Fallback to default behavior
        return "_".join(path.strip("/").split("/"))

    # Remove the provider's path prefix
    prefix = provider_config.path_prefix
    if path.startswith(prefix):
        endpoint_name = path[len(prefix) :].strip("/")
    else:
        endpoint_name = path.strip("/")

    return endpoint_name.replace("/", "_")


def _read_text_file(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise ToolError(f"File not found: {file_path.name}")
    except PermissionError:
        raise ToolError(f"Permission denied: {file_path.name}")
    except OSError as e:
        raise ToolError(f"Error reading {file_path.name}: {e}")


def _read_json_file(file_path: Path, file_type: str, path: str, path_id: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
            return json.dumps(json_data, indent=2, ensure_ascii=False)
    except FileNotFoundError:
        raise ToolError(f"{file_type.capitalize()} for '{path}' (path_id: {path_id}) not found")
    except json.JSONDecodeError as e:
        raise ToolError(f"Invalid JSON in {file_type} for '{path}': {e}")
    except OSError as e:
        raise ToolError(f"Error reading {file_type} for '{path}': {e}")


def _validate_provider(provider: str) -> str:
    """
    Validate and normalize provider name.

    Args:
        provider: Provider name to validate

    Returns:
        Normalized provider name

    Raises:
        ToolError: If provider is not in the allowed list
    """
    normalized = provider.strip().lower()
    if normalized not in provider_configs:
        valid_providers = ", ".join(sorted(provider_configs.keys()))
        raise ToolError(f"Invalid provider '{provider}'. Must be one of: {valid_providers}")
    return normalized


def _resolve_provider_and_path_id(path: str, provider: str | None) -> tuple[str, str]:
    """
    Resolve provider and convert path to path_id.

    Args:
        path: API endpoint path
        provider: Optional provider name

    Returns:
        Tuple of (resolved_provider, path_id)

    Raises:
        ToolError: If provider is invalid
    """
    resolved_provider = _validate_provider(provider) if provider is not None else _get_provider_from_path(path)
    path_id = _path_to_path_id(path, resolved_provider)
    return resolved_provider, path_id


def _get_json_file_content(path: str, provider: str | None, file_subpath: str, file_type: str) -> str:
    """
    Generic function to get JSON file content for an endpoint.

    Args:
        path: API endpoint path
        provider: Optional provider name
        file_subpath: Subpath within the provider directory (e.g., "overviews", "schemas/request_body")
        file_type: Type of file for error messages

    Returns:
        JSON content or error message
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    file_path = _get_docs_dir() / resolved_provider / file_subpath / f"{path_id}.json"
    return _read_json_file(file_path, file_type, path, path_id)


def _sanitize_document_id(document_id: str) -> list[str] | None:
    """Validate and normalize a nested document identifier."""

    if not document_id:
        return None

    parts = [part for part in document_id.strip().split("/") if part]
    if not parts:
        return None

    for part in parts:
        if part in {".", ".."}:
            return None

    return parts


def _read_integration_pattern(pattern_id: str) -> tuple[str, Path]:
    docs_dir = _get_integration_patterns_dir()
    parts = _sanitize_document_id(pattern_id)
    if not parts:
        raise ToolError("Invalid pattern_id provided")

    pattern_path = docs_dir.joinpath(*parts).with_suffix(".md")

    try:
        docs_root = docs_dir.resolve(strict=False)
        resolved_path = pattern_path.resolve(strict=False)
        if not resolved_path.is_relative_to(docs_root):
            raise ToolError("Invalid pattern_id provided")
    except (OSError, ValueError):
        pass

    if not pattern_path.exists():
        raise ToolError(
            f"Integration pattern '{pattern_id}' not found. Try restarting the server or run 'update-docs'."
        )

    try:
        _, body = load_markdown_with_front_matter(pattern_path)
    except (OSError, ValueError):
        return (_read_text_file(pattern_path), pattern_path)

    if body:
        return (body, pattern_path)

    return (_read_text_file(pattern_path), pattern_path)


def _read_troubleshooting_guide(guide_id: str) -> tuple[str, Path]:
    docs_dir = _get_troubleshooting_dir()
    parts = _sanitize_document_id(guide_id)
    if not parts:
        raise ToolError("Invalid guide_id provided")

    guide_path = docs_dir.joinpath(*parts).with_suffix(".md")

    try:
        docs_root = docs_dir.resolve(strict=False)
        resolved_path = guide_path.resolve(strict=False)
        if not resolved_path.is_relative_to(docs_root):
            raise ToolError("Invalid guide_id provided")
    except (OSError, ValueError):
        pass

    if not guide_path.exists():
        raise ToolError(
            f"Troubleshooting guide '{guide_id}' not found. Try restarting the server or run 'update-docs'."
        )

    try:
        _, body = load_markdown_with_front_matter(guide_path)
    except (OSError, ValueError):
        return (_read_text_file(guide_path), guide_path)

    if body:
        return (body, guide_path)

    return (_read_text_file(guide_path), guide_path)


def _mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


@mcp.tool
def get_basic_info() -> str:
    """
    Get basic information about Omelet Routing Engine API and iNavi Maps API.
    Includes masked user-provided API keys.
    """
    file_path = _get_docs_dir() / "basic_info.md"
    content = _read_text_file(file_path)
    inavi_key = os.getenv("INAVI_API_KEY")
    omelet_key = os.getenv("OMELET_API_KEY")
    if inavi_key:
        content += f"\n\nINAVI_API_KEY: {_mask_api_key(inavi_key)}"
    if omelet_key:
        content += f"\n\nOMELET_API_KEY: {_mask_api_key(omelet_key)}"
    return content


_MARKDOWN_TABLE_ROW_PATTERN = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")


def _parse_markdown_table(content: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    lines = content.strip().split("\n")
    for line in lines:
        if line.startswith("|") and "---" not in line:
            match = _MARKDOWN_TABLE_ROW_PATTERN.match(line.strip())
            if match:
                col1, col2 = match.group(1).strip(), match.group(2).strip()
                if col1 and col2 and col1 != "pattern_id" and col1 != "guide_id":
                    rows.append((col1, col2))
    return rows


@mcp.tool
def list_integration_patterns() -> PatternsListResult:
    """
    Return a table of all available integration patterns, which are guidelines for integrating different API endpoints for specific use cases.
    """
    list_path = _get_integration_patterns_dir() / "list.md"
    if not list_path.exists():
        raise ToolError("Integration pattern list not found. Try restarting the server or run 'update-docs'.")

    content = _read_text_file(list_path)
    rows = _parse_markdown_table(content)

    patterns = [PatternSummary(pattern_id=pid, description=desc) for pid, desc in rows]
    return PatternsListResult(patterns=patterns, total_count=len(patterns))


@mcp.tool
def get_integration_pattern(
    pattern_id: Annotated[str, "Integration pattern identifier in the format 'category/pattern'"],
    simple: Annotated[
        bool,
        "If True, return only the standalone document. If False, provide additional guidelines for agentic coding tips, to enhance tool usage and autonomous agentic development. Refer to these tips for creating or revising TO DO lists.",
    ] = False,
) -> str:
    """
    Retrieve the specified integration pattern document.
    These integration patterns serve as starting points for further API exploration and development.

    It is **STRONGLY** advised that the user provide or setup API keys in advance for autonomous agentic development.
    """
    content, _ = _read_integration_pattern(pattern_id)

    if simple:
        return content

    guidelines_path = _get_integration_patterns_dir() / "agentic_coding_guidelines.md"
    try:
        guidelines_content = _read_text_file(guidelines_path)
        return f"{content.rstrip()}\n\n---\n\n{guidelines_content.strip()}\n"
    except ToolError:
        return content


@mcp.tool
def list_troubleshooting_guides() -> GuidesListResult:
    """
    Return a table of all available troubleshooting guides, covering common errors and recommended fixes.
    """
    list_path = _get_troubleshooting_dir() / "list.md"
    if not list_path.exists():
        raise ToolError("Troubleshooting guide list not found. Try restarting the server or run 'update-docs'.")

    content = _read_text_file(list_path)
    rows = _parse_markdown_table(content)

    guides = [GuideSummary(guide_id=gid, description=desc) for gid, desc in rows]
    return GuidesListResult(guides=guides, total_count=len(guides))


@mcp.tool
def get_troubleshooting_guide(
    guide_id: Annotated[str, "Troubleshooting guide identifier in the format 'category/guide'"],
) -> str:
    """
    Retrieve the specified troubleshooting guide.
    These guides outline steps to diagnose and resolve recurring integration or runtime issues.
    """
    content, _ = _read_troubleshooting_guide(guide_id)
    return content


_ENDPOINTS_TABLE_PATTERN = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")


def _parse_endpoints_markdown(content: str) -> list[EndpointSummary]:
    endpoints: list[EndpointSummary] = []
    for line in content.strip().split("\n"):
        if line.startswith("|") and "---" not in line:
            match = _ENDPOINTS_TABLE_PATTERN.match(line.strip())
            if match:
                path, method, summary, description = (
                    match.group(1).strip(),
                    match.group(2).strip(),
                    match.group(3).strip(),
                    match.group(4).strip(),
                )
                if path and path != "Path":
                    endpoints.append(
                        EndpointSummary(path=path, method=method, summary=summary, description=description)
                    )
    return endpoints


@mcp.tool
def list_endpoints(
    provider: Annotated[
        str | None, "Optional provider filter ('omelet' or 'inavi'). If None, returns combined list."
    ] = None,
) -> EndpointsListResult:
    """Get a list of available API endpoints with their summaries and descriptions."""
    docs_dir = _get_docs_dir()
    all_endpoints: list[EndpointSummary] = []

    if provider is not None:
        validated_provider = _validate_provider(provider)
        providers_to_check = [validated_provider]
    else:
        providers_to_check = list(provider_configs.keys())

    for provider_name in providers_to_check:
        file_path = docs_dir / provider_name / "endpoints_summary.md"
        if file_path.exists():
            try:
                content = _read_text_file(file_path)
                all_endpoints.extend(_parse_endpoints_markdown(content))
            except ToolError:
                continue

    if not all_endpoints:
        raise ToolError("No endpoints found. Try restarting the server or run 'update-docs'.")

    return EndpointsListResult(endpoints=all_endpoints, total_count=len(all_endpoints), provider=provider)


@mcp.tool
def get_endpoint_overview(
    path: Annotated[str, "API endpoint path (e.g., '/api/fsmvrp', '/api/cost-matrix')"],
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get detailed overview information for a specific API endpoint.

    Returns:
        JSON content of the endpoint overview
    """
    return _get_json_file_content(path, provider, "overviews", "overview")


@mcp.tool
def get_request_body_schema(
    path: Annotated[str, "API endpoint path (e.g., '/api/fsmvrp', '/api/cost-matrix')"],
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get the request body schema for a specific API endpoint (only works for endpoints that require a request body, typically POST/PUT methods).

    Returns:
        JSON schema content for the request body
    """
    return _get_json_file_content(path, provider, "schemas/request_body", "schema")


@mcp.tool
def get_response_schema(
    path: Annotated[str, "API endpoint path (e.g., '/api/fsmvrp', '/api/cost-matrix')"],
    response_code: Annotated[str, "HTTP response code (e.g., '200', '201', '400', '404')"],
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get the response schema for a specific API endpoint and response code.
    Most successful response codes are 200, however endpoints with "-long" in their name
    return a 201 code when successful. This tool should be used when trying to design
    post-processes for handling the API response.

    Returns:
        JSON schema content for the response
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    file_path = _get_docs_dir() / resolved_provider / "schemas" / "response" / path_id / f"{response_code}.json"
    return _read_json_file(file_path, f"response schema (code: {response_code})", path, path_id)


_VALID_EXAMPLE_TYPES = {"request", "response", "both"}


@mcp.tool
def list_examples(
    path: Annotated[str, "API endpoint path (e.g., '/api/vrp', '/api/cost-matrix')"],
    example_type: Annotated[
        str | None, "Type of examples to list: 'request', 'response', or 'both' (default: 'both')"
    ] = "both",
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> ExamplesListResult:
    """
    List available request and response examples for a specific API endpoint.
    Currently, only usable for "omelet" provider endpoints.
    """
    if example_type not in _VALID_EXAMPLE_TYPES:
        raise ToolError(
            f"Invalid example_type '{example_type}'. Must be one of: {', '.join(sorted(_VALID_EXAMPLE_TYPES))}"
        )

    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    docs_dir = _get_docs_dir() / resolved_provider / "examples"

    request_examples: list[str] = []
    response_examples: dict[str, list[str]] = {}

    if example_type in ["request", "both"]:
        request_dir = docs_dir / "request_body" / path_id
        if request_dir.exists() and request_dir.is_dir():
            request_examples = sorted([f.stem for f in request_dir.glob("*.json")])

    if example_type in ["response", "both"]:
        response_dir = docs_dir / "response_body" / path_id
        if response_dir.exists() and response_dir.is_dir():
            for code_dir in response_dir.iterdir():
                if code_dir.is_dir() and code_dir.name.isdigit():
                    code_examples = sorted([f.stem for f in code_dir.glob("*.json")])
                    if code_examples:
                        response_examples[code_dir.name] = code_examples

    return ExamplesListResult(
        endpoint=path,
        path_id=path_id,
        request_examples=request_examples,
        response_examples=response_examples,
    )


@mcp.tool
def get_example(
    path: Annotated[str, "API endpoint path (e.g., '/api/vrp', '/api/cost-matrix')"],
    example_name: Annotated[str, "Name of the example"],
    example_type: Annotated[str, "Type of example: 'request' or 'response'"],
    response_code: Annotated[
        str | None, "HTTP response code (required if example_type is 'response', e.g., '200', '201')"
    ] = None,
    provider: Annotated[str | None, "Optional provider name. If None, auto-detects from path."] = None,
) -> str:
    """
    Get a specific example for an API endpoint.
    Check the list of examples using the list_examples tool first for the `example_name`.
    Currently, only usable for "omelet" provider endpoints.

    Note: Saved examples may be truncated, so the returned example may not be complete.
    """
    resolved_provider, path_id = _resolve_provider_and_path_id(path, provider)
    docs_dir = _get_docs_dir() / resolved_provider / "examples"

    if example_type == "request":
        file_path = docs_dir / "request_body" / path_id / f"{example_name}.json"
    elif example_type == "response":
        if response_code is None:
            raise ToolError("response_code is required when example_type is 'response'")
        file_path = docs_dir / "response_body" / path_id / response_code / f"{example_name}.json"
    else:
        raise ToolError(f"Invalid example_type '{example_type}'. Must be 'request' or 'response'")

    if not file_path.exists():
        raise ToolError(f"Example '{example_name}' not found for {example_type} at path '{path}' (path_id: {path_id})")

    return _read_json_file(file_path, f"{example_type} example", path, path_id)
