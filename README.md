# TMS Development MCP Server

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![한국어](https://img.shields.io/badge/언어-한국어-orange.svg)](README.ko.md)

A FastMCP-based MCP server providing intelligent tools to navigate through **Omelet's Routing Engine API** and **iNavi's Maps API** to build effective Transport Management Systems (TMS).

## Features

- 🚀 **Multi-Provider Support**: Seamlessly access both Omelet and iNavi API documents through unified tools
- 📚 **Smart Documentation**: Provider-aware tools with automatic API detection
- 🔄 **Auto-Generated Examples**: Request and response body examples from OpenAPI specifications
- 🎯 **Provider Filtering**: Query specific provider documentation or get combined results

For the API keys, please visit [Omelet's Routing Engine Homepage](https://routing.oaasis.cc/) and [iNavi's iMPS Homepage](https://mapsapi.inavisys.com/).
(Note that the API keys are not required to run this MCP server)


## Quick Start

### Prerequisites

Before getting started, make sure you have [uv](https://docs.astral.sh/uv/getting-started/installation/) installed on your system:

### Installation

1. Clone the repository:
```bash
git clone https://github.com/omelet-ai/tms-dev-mcp.git
cd tms-dev-mcp
```

2. Create and activate virtual environment:
```bash
uv sync --all-groups
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

4. (Optional, for server development) Install pre-commit
```bash
pre-commit install
```

### Running the Server (Locally)

#### Cursor / Claude Desktop
```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "/path/to/tms-dev-mcp/.venv/bin/python",
         "args": [
            "/path/to/tms-dev-mcp/tms_mcp/main.py",
            "start-server"
         ]
      }
   }
}
```

## Project Structure

```
tms_mcp/
├── server.py              # FastMCP server instance
├── main.py                # Entry point with CLI
├── config.py              # Configuration management
├── pipeline/
│   └── pipeline.py        # Document indexing pipeline
├── tools/
│   └── doc_tools.py       # Documentation query tools
└── docs/                  # Generated documentation
    ├── basic_info.md      # Shared API overview
    ├── omelet/            # Omelet-specific docs
    │   ├── openapi.json
    │   ├── endpoints_summary.md
    │   ├── overviews/
    │   ├── schemas/
    │   └── examples/
    └── inavi/             # iNavi-specific docs
        ├── openapi.json
        ├── endpoints_summary.md
        ├── overviews/
        └── schemas/
```

(Note that some folders/files are omitted in the structure)

## Available Tools

- `get_basic_info()`: Get basic information about both Omelet Routing Engine and iNavi Maps APIs.
- `list_endpoints(provider)`: Get a list of available API endpoints with filtering by provider (omelet/inavi).
- `get_endpoint_overview(path, provider)`: Get detailed overview information for a specific API endpoint.
- `get_request_body_schema(path, provider)`: Get the request body schema for a specific API endpoint.
- `get_response_schema(path, response_code, provider)`: Get the response schema for a specific API endpoint and response code.
- `list_examples(path, example_type, provider)`: List available request and response examples for a specific API endpoint.
- `get_example(path, example_name, example_type, response_code, provider)`: Get a specific example for an API endpoint.


## Document Generation Pipeline

The pipeline automatically:
1. Fetches OpenAPI specifications from configured URLs
2. Resolves all `$ref` references using jsonref
3. Splits documentation by provider (Omelet/iNavi)
4. Generates provider-specific documentation structure:
   - Endpoint summaries and overviews
   - Request/response schemas
   - Request/response examples extracted from OpenAPI specs
5. Atomically replaces old documentation to ensure consistency

### Document Update

Use the `update_docs.sh` script to update OpenAPI documentation:

```bash
cd scripts

# Update all providers
./update_docs.sh

# Update only Omelet provider
./update_docs.sh omelet

# Update only iNavi provider
./update_docs.sh inavi

# Update multiple providers
./update_docs.sh omelet inavi

# Show usage information
./update_docs.sh --help
```
