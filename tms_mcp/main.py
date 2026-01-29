#!/usr/bin/env python3
"""
Main entry point for the TMS MCP server with CLI options
"""

import argparse
import asyncio
import logging
import sys
from typing import Literal

from fastmcp.utilities.logging import get_logger

from tms_mcp.config import settings
from tms_mcp.custom_logging.logging_format import formatter
from tms_mcp.pipeline import run_openapi_indexing_pipeline
from tms_mcp.pipeline.utils import validate_docs_exist
from tms_mcp.server import mcp
from tms_mcp.tools import *  # noqa: F403

logger = get_logger(__name__)


def setup_logging() -> None:
    fastmcp_logger = logging.getLogger("FastMCP")
    for h in fastmcp_logger.handlers[:]:
        fastmcp_logger.removeHandler(h)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    fastmcp_logger.addHandler(console_handler)


async def update_documents(providers: list[str] | None = None) -> None:
    """Execute only the document indexing pipeline.

    Args:
        providers: List of providers to update. If None, updates all providers.
    """
    try:
        if providers:
            logger.info(f"🚀 Starting document indexing pipeline for: {', '.join(providers)}...")
        else:
            logger.info("🚀 Starting document indexing pipeline for all providers...")
        await run_openapi_indexing_pipeline(providers)
        logger.info("✅ Document indexing completed successfully")
    except Exception as e:
        logger.error(f"❌ Document indexing failed: {e}")
        raise


async def _try_update_docs_with_fallback() -> bool:
    """
    Try to update docs, fall back to existing if update fails.

    Returns:
        True if docs are available (updated or existing), False if no docs available.
    """
    try:
        logger.info("📦 Updating documentation...")
        await run_openapi_indexing_pipeline()
        logger.info("✅ Documentation updated successfully")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Documentation update failed: {e}")

        if validate_docs_exist():
            logger.info("📂 Using existing documentation as fallback")
            return True
        else:
            logger.error("❌ No existing documentation available as fallback")
            return False


def start_server(transport: Literal["stdio", "streamable-http"] | None = None) -> None:
    """
    Start only the MCP server without document indexing.
    Args:
        transport: The transport to use for the MCP server. (streamable-http or stdio)
    """
    try:
        setup_logging()

        if settings.AUTO_UPDATE_DOCS:
            docs_available = asyncio.run(_try_update_docs_with_fallback())
            if not docs_available:
                raise RuntimeError(
                    "Documentation is required but unavailable. "
                    "Check network connectivity or run 'update-docs' manually."
                )
        elif not validate_docs_exist():
            logger.warning("⚠️ Documentation not found. Tools may fail. Run 'update-docs' or set AUTO_UPDATE_DOCS=true")

        logger.info("🚀 Starting MCP server...")
        selected_transport = transport or settings.MCP_TRANSPORT
        logger.info(f"🔌 Transport selected: {selected_transport}")
        if selected_transport == "streamable-http":
            mcp.run(
                transport=selected_transport,
                host=settings.HOST,
                port=settings.PORT,
                uvicorn_config={
                    "log_config": {
                        "version": 1,
                        "disable_existing_loggers": False,
                        "formatters": {
                            "default": {
                                "format": "[%(asctime)s] %(levelname)-8s %(message)s",
                                "datefmt": "%d/%m/%y %H:%M:%S",
                            }
                        },
                    }
                },
            )
        else:
            mcp.run(transport=selected_transport)

    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        raise


def update_and_start(
    transport: Literal["stdio", "streamable-http"] | None = None, providers: list[str] | None = None
) -> None:
    """
    Update documents and then start the server.
    Args:
        transport: The transport to use for the MCP server. (streamable-http or stdio)
        providers: List of providers to update. If None, updates all providers.
    """
    try:
        # First update documents (run in async context)
        logger.info("🚀 Starting combined operation: document indexing + server startup")
        asyncio.run(update_documents(providers))

        # Then start server (run in sync context)
        logger.info("📄 Document indexing completed, now starting server...")
        start_server(transport)
    except Exception as e:
        logger.error(f"❌ Combined operation failed: {e}")
        raise


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Omelet Routing Engine MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Start server only (default)
  %(prog)s update-docs          # Update all provider documents
  %(prog)s update-docs omelet   # Update only Omelet provider documents
  %(prog)s update-docs omelet inavi  # Update specific providers
  %(prog)s start-server         # Only start server (same as default)
  %(prog)s update-and-start     # Update all docs and start server
  %(prog)s update-and-start omelet  # Update Omelet docs and start server
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="start-server",
        choices=["update-docs", "start-server", "update-and-start"],
        help="Command to execute (default: start-server)",
    )

    parser.add_argument(
        "providers",
        nargs="*",
        choices=["omelet", "inavi"],
        help="Provider(s) to update (for update-docs and update-and-start commands). If not specified, updates all providers.",
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help=(
            "Transport to use: 'stdio' for local MCP (default for local use) or 'streamable-http' for remote server. "
            "If omitted, uses environment setting MCP_TRANSPORT (default: stdio)."
        ),
    )

    args = parser.parse_args()

    try:
        if args.command == "update-docs":
            providers = args.providers if args.providers else None
            asyncio.run(update_documents(providers))
        elif args.command == "start-server":
            start_server(args.transport)
        elif args.command == "update-and-start":
            providers = args.providers if args.providers else None
            update_and_start(args.transport, providers)
    except KeyboardInterrupt:
        logger.info("🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
