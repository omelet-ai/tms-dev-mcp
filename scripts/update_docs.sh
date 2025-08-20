#!/bin/bash

# Script to update OpenAPI documentation for TMS providers

# Function to display usage information
show_usage() {
    cat << EOF
Usage: $0 [PROVIDER...]

Update OpenAPI documentation for TMS providers.

Arguments:
  PROVIDER    Optional provider name(s) to update (omelet, inavi)
              If not specified, updates all providers

Examples:
  $0                  # Update all providers
  $0 omelet           # Update only Omelet provider
  $0 inavi            # Update only iNavi provider
  $0 omelet inavi     # Update multiple providers

Available providers:
  - omelet: Omelet Routing Engine API
  - inavi: iNavi Maps API

EOF
}

# Check for help flag
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "help" ]]; then
    show_usage
    exit 0
fi

# Get the absolute path to the project root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Export the Python path to include the project root
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Build the command with provider arguments
if [ $# -eq 0 ]; then
    echo "🚀 Starting document indexing pipeline for all providers..."
    uv run python -m tms_mcp.main update-docs
else
    echo "🚀 Starting document indexing pipeline for: $*"
    uv run python -m tms_mcp.main update-docs "$@"
fi
