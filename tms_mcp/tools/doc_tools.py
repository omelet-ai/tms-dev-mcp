"""
Documentation tools for the Omelet Routing Engine MCP server.
"""

import json
from pathlib import Path

from tms_mcp.server import mcp


def _get_docs_dir() -> Path:
    """Get the docs directory path."""
    return Path(__file__).parent.parent / "docs"


def _get_provider_from_path(path: str) -> str:
    """
    Determine the provider based on the API path.

    Args:
        path: API endpoint path

    Returns:
        Provider name ("omelet" or "inavi")
    """
    if path.startswith("/api/"):
        return "omelet"
    return "inavi"


def _read_text_file(file_path: Path) -> str:
    """
    Helper function to read a text file with error handling.

    Args:
        file_path: Path to the file to read

    Returns:
        Content of the file or error message if file cannot be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: {file_path.name} file not found."
    except Exception as e:
        return f"Error reading {file_path.name}: {str(e)}"


def _read_json_file(file_path: Path, file_type: str, path: str, path_id: str) -> str:
    """
    Helper function to read a JSON file and return formatted content.

    Args:
        file_path: Path to the JSON file
        file_type: Type of file for error messages (e.g., "overview", "schema")
        path: Original API path for error messages
        path_id: Converted path ID for error messages

    Returns:
        Formatted JSON content or error message if file cannot be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
            return json.dumps(json_data, indent=2, ensure_ascii=False)
    except FileNotFoundError:
        return f"Error: {file_type.capitalize()} file for '{path}' (path_id: {path_id}) not found."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in {file_type} file for '{path}': {str(e)}"
    except Exception as e:
        return f"Error reading {file_type} for '{path}': {str(e)}"


def _path_to_path_id(path: str) -> str:
    """
    Convert API path to path_id format.

    Args:
        path: API path (e.g., "/api/foo/bar")

    Returns:
        Path ID (e.g., "foo_bar")
    """
    # Remove leading slash and "api" prefix, then replace remaining slashes with underscores
    path_parts = path.strip("/").split("/")
    if path_parts[0] == "api":
        path_parts = path_parts[1:]  # Remove "api" prefix
    return "_".join(path_parts)


@mcp.tool
def get_basic_info() -> str:
    """
    Get basic information about the Omelet Routing Engine API.
    """
    file_path = _get_docs_dir() / "basic_info.md"
    return _read_text_file(file_path)


@mcp.tool
def list_endpoints(provider: str | None = None) -> str:
    """
    Get a list of available API endpoints with their summaries and descriptions.

    Args:
        provider: Optional provider filter ("omelet" or "inavi"). If None, returns combined list.

    Returns:
        Markdown table of endpoints
    """
    docs_dir = _get_docs_dir()

    if provider:
        # Return provider-specific endpoints
        file_path = docs_dir / provider / "endpoints_summary.md"
        if not file_path.exists():
            return f"Error: No endpoints found for provider '{provider}'."
        return _read_text_file(file_path)

    # Return combined endpoints from both providers
    content_parts = []

    # Try to read Omelet endpoints
    omelet_path = docs_dir / "omelet" / "endpoints_summary.md"
    if omelet_path.exists():
        omelet_content = _read_text_file(omelet_path)
        if not omelet_content.startswith("Error:"):
            content_parts.append("# Omelet Routing Engine\n" + omelet_content)

    # Try to read iNavi endpoints
    inavi_path = docs_dir / "inavi" / "endpoints_summary.md"
    if inavi_path.exists():
        inavi_content = _read_text_file(inavi_path)
        if not inavi_content.startswith("Error:"):
            if content_parts:
                content_parts.append("\n---\n")
            content_parts.append("# iNavi Maps\n" + inavi_content)

    if not content_parts:
        return "Error: No endpoints found. Please run 'update-docs' first."

    return "\n".join(content_parts)


@mcp.tool
def get_endpoint_overview(path: str, provider: str | None = None) -> str:
    """
    Get detailed overview information for a specific API endpoint.

    Args:
        path: API endpoint path (e.g., "/api/fsmvrp", "/api/cost-matrix")
        provider: Optional provider name. If None, auto-detects from path.

    Returns:
        JSON content of the endpoint overview
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = _get_provider_from_path(path)

    path_id = _path_to_path_id(path)
    file_path = _get_docs_dir() / provider / "overviews" / f"{path_id}.json"
    return _read_json_file(file_path, "overview", path, path_id)


@mcp.tool
def get_request_body_schema(path: str, provider: str | None = None) -> str:
    """
    Get the request body schema for a specific API endpoint.

    Args:
        path: API endpoint path (e.g., "/api/fsmvrp", "/api/cost-matrix")
        provider: Optional provider name. If None, auto-detects from path.

    Returns:
        JSON schema content for the request body
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = _get_provider_from_path(path)

    path_id = _path_to_path_id(path)
    file_path = _get_docs_dir() / provider / "schemas" / "request_body" / f"{path_id}.json"
    return _read_json_file(file_path, "schema", path, path_id)


@mcp.tool
def get_request_body_example(path: str, provider: str | None = None) -> str:
    """
    Get the request body example for a specific API endpoint.

    Args:
        path: API endpoint path (e.g., "/api/fsmvrp", "/api/cost-matrix")
        provider: Optional provider name. If None, auto-detects from path.

    Returns:
        JSON example content for the request body
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = _get_provider_from_path(path)

    path_id = _path_to_path_id(path)
    file_path = _get_docs_dir() / provider / "examples" / "request_body" / f"{path_id}.json"
    return _read_json_file(file_path, "example", path, path_id)


@mcp.tool
def get_response_schema(path: str, response_code: str, provider: str | None = None) -> str:
    """
    Get the response schema for a specific API endpoint and response code.

    Most successful response codes are 200, however endpoints with "-long" in their name
    return a 201 code when successful. This tool should be used when trying to design
    post-processes for handling the API response.

    Args:
        path: API endpoint path (e.g., "/api/fsmvrp", "/api/cost-matrix")
        response_code: HTTP response code (e.g., "200", "201", "400", "404")
        provider: Optional provider name. If None, auto-detects from path.

    Returns:
        JSON schema content for the response
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = _get_provider_from_path(path)

    path_id = _path_to_path_id(path)
    file_path = _get_docs_dir() / provider / "schemas" / "response" / path_id / f"{response_code}.json"
    return _read_json_file(file_path, f"response schema (code: {response_code})", path, path_id)
