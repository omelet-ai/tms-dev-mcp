#!/bin/bash

# Get the absolute path to the project root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Export the Python path to include the project root
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo "🚀 Starting document indexing pipeline..."
uv run python -m tms_mcp.main update-docs
