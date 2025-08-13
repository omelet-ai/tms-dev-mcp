from fastmcp import FastMCP
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import PlainTextResponse

logger = get_logger(__name__)

# Create the main FastMCP server instance
mcp: FastMCP = FastMCP(
    name="API Guide for Building TMS",
    instructions="""
    Use this server's tools to explore Omelet's Routing Engine and iNAVI's Maps APIs to build an effective TMS(Transport Management System).
    """,
)

# JSON-structured logging for log aggregation tools
mcp.add_middleware(StructuredLoggingMiddleware(include_payloads=True, logger=logger))


@mcp.custom_route("/", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Server is running.")


# This will be imported by other modules to register tools
__all__ = ["mcp"]
