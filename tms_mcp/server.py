from typing import Annotated

from fastmcp import FastMCP
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import PlainTextResponse

logger = get_logger(__name__)

mcp: FastMCP = FastMCP(
    name="API Guide for Building TMS",
    instructions="""
    Use this server's tools to explore Omelet's Routing Engine and iNAVI's Maps APIs to build an effective TMS(Transport Management System).
    """,
)

mcp.add_middleware(StructuredLoggingMiddleware(include_payloads=True, logger=logger))


@mcp.custom_route("/", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Server is running.")


@mcp.prompt()
def debug_api_error(
    endpoint: Annotated[str, "The API endpoint that returned an error"],
    error_code: Annotated[str, "The HTTP error code received (e.g., 400, 404, 500)"],
    request_body: Annotated[str, "The request body that was sent (JSON string)"] = "",
) -> str:
    """Help diagnose and resolve API integration issues."""
    return f"""To debug this API error, I need to:
1. Check the request schema for {endpoint} using get_request_body_schema
2. Identify common causes for error {error_code} using get_troubleshooting_guide or list_troubleshooting_guides
3. Review the endpoint documentation using get_endpoint_overview

Error details:
- Endpoint: {endpoint}
- Error code: {error_code}
- Request body: {request_body if request_body else "(not provided)"}

Please help me diagnose why this request failed and suggest corrections."""


__all__ = ["mcp"]
