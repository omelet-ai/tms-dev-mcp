# TMS Development Wizard MCP Server

[![English](https://img.shields.io/badge/🇬🇧-English-blue.svg)](README.md)
[![한국어](https://img.shields.io/badge/🇰🇷-한국어-orange.svg)](README.ko.md)

---

## 🎯 Overview

**🚚TMS Development Wizard🧙‍♂️** helps you build a TMS(Transport Management System) by providing you with the tools to explore **[Omelet's Routing Engine](https://www.oaasis.cc/routing)** and **[iNavi's Maps API](https://mapsapi.inavisys.com/)**. No more juggling between multiple API docs - vibe your way to your own customized TMS.

**Perfect for:**
- 🚀 **Rapid API Exploration** - Quickly discover what's possible without reading through walls of documentation
- 🧪 **Prototyping & Testing** - Spin up test implementations in minutes, not hours
- 🏗️ **Production Systems** - Build complex TMS workflows with guided API integration patterns

---

## ✨ Features

- 🚀 **Multi-Provider Support** - Unified access to both Omelet Routing Engine and iNavi Maps API documentation
- 📚 **Endpoint Discovery** - Browse and filter API endpoints by provider with detailed overviews (`list_endpoints`, `get_endpoint_overview`)
- 🧩 **Integration Patterns** - Pre-built workflow patterns with agentic coding guidelines for common TMS use cases (`list_integration_patterns`, `get_integration_pattern`)
- 🔍 **Schema Explorer** - Inspect request/response schemas for any endpoint and HTTP status code (`get_request_body_schema`, `get_response_schema`)
- 💡 **Example Library** - Access real-world API request/response examples extracted from OpenAPI specs (`list_examples`, `get_example`)
- 🛠️ **Troubleshooting Guides** - Access diagnostic guides for common integration and runtime issues (`list_troubleshooting_guides`, `get_troubleshooting_guide`)

> **Note:** API keys from [Omelet](https://routing.oaasis.cc/) and [iNavi](https://mapsapi.inavisys.com/) aren't required to install this MCP server. However, it is recommended you prepare them in advance for a realtime test-enabled vibe coding experience, enabling proper debugging.

---

## 🚀 Quick Start

### MCP Server Installation

**Prerequisites:** Ensure you have **[uv](https://docs.astral.sh/uv/getting-started/installation/)** installed.

<details>
<summary><b>Cursor</b></summary>

Navigate to your MCP settings (Cursor > Settings > Cursor Settings > Tools & MCP) and add:

```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "uvx",
         "args": ["tms-mcp"],
         "env": {
            "INAVI_API_KEY": "your_inavi_api_key",
            "OMELET_API_KEY": "your_omelet_api_key"
         }
      }
   }
}
```
</details>
<details>
<summary><b>Claude Desktop</b></summary>

⚠️ Claude Desktop cannot directly send requests to API servers. Use Claude Desktop only for exploring API endpoints and responses.

1. Check `uvx` installation path via terminal.
   - For MacOS/Linux: `which uvx`
   - For Windows: `where uvx`

2. Open MCP settings JSON file (Claude > Settings > Developer > Edit Config), and add:

```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "[uvx installation path from step 1]",
         "args": ["tms-mcp"],
         "env": {
            "INAVI_API_KEY": "your_inavi_api_key",
            "OMELET_API_KEY": "your_omelet_api_key"
         }
      }
   }
}
```

3. Save the JSON file and restart Claude Desktop.
</details>
<details>
<summary><b>Claude Code</b></summary>

Open a terminal at the project root and run:

```bash
claude mcp add TMS-Development-Wizard uvx tms-mcp --env INAVI_API_KEY=your_inavi_api_key --env OMELET_API_KEY=your_omelet_api_key
```
</details>
<details>
<summary><b>Codex CLI</b></summary>

Open a terminal at the project root and run:

```bash
codex mcp add TMS-Development-Wizard --env INAVI_API_KEY=your_inavi_api_key --env OMELET_API_KEY=your_omelet_api_key uvx tms-mcp
```
</details>
<details>
<summary><b>Gemini CLI</b></summary>

Open a terminal at the project root and run:

```bash
gemini mcp add TMS-Development-Wizard uvx tms-mcp --env INAVI_API_KEY=your_inavi_api_key --env OMELET_API_KEY=your_omelet_api_key
```
</details>

> **Reminder:** Replace the `your_inavi_api_key` and `your_omelet_api_key` placeholders with your actual API credentials before saving or running these commands.

### Usage Examples

<details>
<summary><b>🔍 Exploring Available APIs</b></summary>

```
What routing APIs are available from Omelet?
```

```
Show me all the iNavi endpoints for geocoding
```

```
What's the difference between the VRP and Advanced VRP endpoints?
```

```
List all the integration patterns available
```

</details>

<details>
<summary><b>🏗️ Building a Feature</b></summary>

```
Help me implement route optimization for 50 delivery addresses using Omelet's VRP API
```

```
I need to calculate a distance matrix for 100 locations. Which endpoint should I use and how?
```

```
Build a function to convert addresses to coordinates using iNavi's geocoding API
```

```
Show me how to implement a pickup-delivery problem with time windows
```

</details>

<details>
<summary><b>🧩 Following Integration Patterns</b></summary>

```
I want to build a last-mile delivery system. What integration pattern should I follow?
```

```
Show me the high-precision routing pattern for navigation apps
```

```
How do I combine Omelet's routing with iNavi's maps for a complete TMS?
```

</details>

<details>
<summary><b>🐛 Debugging & Schema Validation</b></summary>

```
I'm getting a 400 error from the VRP endpoint. Show me the request schema
```

```
What's the expected response format for the cost-matrix API?
```

```
Show me valid examples of request bodies for the Advanced VRP endpoint
```

```
What response codes can the route-time endpoint return?
```

</details>

---

## 🛠️ Development

### Setup

If you want to contribute or customize the server:

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/)**

2. **Clone and set up development environment:**
   ```bash
   git clone https://github.com/omelet-ai/tms-dev-mcp.git
   cd tms-dev-mcp
   uv sync --all-groups
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **(Optional) Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

---

### Installing Locally

Configure your MCP client to connect to the local MCP server. Replace `/path/to/tms-dev-mcp` with your actual installation path.

<details>
<summary><b>Cursor / Claude Desktop</b></summary>

Navigate to your MCP settings and add:

```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "/path/to/tms-dev-mcp/.venv/bin/python",
         "args": [
            "/path/to/tms-dev-mcp/tms_mcp/main.py",
            "start-server"
         ],
         "env": {
            "INAVI_API_KEY": "your_inavi_api_key",
            "OMELET_API_KEY": "your_omelet_api_key"
         }
      }
   }
}
```

</details>

<details>
<summary><b>Claude Code</b></summary>

Open a terminal at the project root and run:

```bash
claude mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server --env INAVI_API_KEY=your_inavi_api_key --env OMELET_API_KEY=your_omelet_api_key
```

</details>

<details>
<summary><b>Codex CLI</b></summary>

Open a terminal at the project root and run:

```bash
codex mcp add TMS-Development-Wizard --env INAVI_API_KEY=your_inavi_api_key --env OMELET_API_KEY=your_omelet_api_key /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

</details>

<details>
<summary><b>Gemini CLI</b></summary>

Open a terminal at the project root and run:

```bash
gemini mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server --env INAVI_API_KEY=your_inavi_api_key --env OMELET_API_KEY=your_omelet_api_key
```

</details>

---

### Currently Implemented Tools

Here is an overview of currently implemented tools:

| Tool | Description |
|------|-------------|
| `get_basic_info()` | Get overview information about both Omelet Routing Engine and iNavi Maps APIs |
| `list_endpoints(provider)` | List all available API endpoints, optionally filtered by provider (`omelet`/`inavi`) |
| `list_integration_patterns()` | Browse catalog of integration patterns with descriptions |
| `get_integration_pattern(pattern_id, simple)` | Retrieve a specific integration playbook with agentic coding guidelines |
| `list_troubleshooting_guides()` | Browse catalog of troubleshooting guides for common errors |
| `get_troubleshooting_guide(guide_id)` | Retrieve a specific troubleshooting guide with diagnostic steps |
| `get_endpoint_overview(path, provider)` | Get detailed overview for a specific API endpoint |
| `get_request_body_schema(path, provider)` | Get the request body schema for an endpoint |
| `get_response_schema(path, response_code, provider)` | Get the response schema for an endpoint and status code |
| `list_examples(path, example_type, provider)` | List available request/response examples for an endpoint |
| `get_example(path, example_name, example_type, response_code, provider)` | Get a specific example for an endpoint |


---

### Project Structure

```
tms_mcp/
├── server.py              # FastMCP server instance
├── main.py                # Entry point with CLI
├── config.py              # Configuration management
├── pipeline/
│   ├── pipeline.py        # Document indexing pipeline
│   ├── models.py          # Data models
│   ├── utils.py           # Utility functions
│   ├── generators/        # Documentation generators
│   └── templates/         # Documentation templates
├── tools/
│   └── doc_tools.py       # MCP tools for documentation queries
└── docs/                  # Generated documentation
    ├── basic_info.md      # Shared API overview
    ├── integration_patterns/  # Integration patterns & guidelines
    ├── troubleshooting/   # Troubleshooting guides for common issues
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

(Some folders/files are omitted for brevity)

---

### Document Generation Pipeline

The pipeline automatically processes OpenAPI specifications and generates structured documentation:

1. **Fetch** - Downloads OpenAPI specs from configured URLs
2. **Resolve** - Resolves all `$ref` references using jsonref for complete schemas
3. **Split** - Separates documentation by provider (Omelet/iNavi)
4. **Generate** - Creates integration patterns and guidelines from templates
5. **Structure** - Generates provider-specific documentation:
   - Request/response schemas
   - Endpoint summaries and detailed overviews
   - Request/response examples extracted from OpenAPI specs
6. **Deploy** - Atomically replaces old documentation to ensure consistency

---

### Authoring Integration Pattern Templates

Integration pattern templates live under `tms_mcp/pipeline/templates/integration_patterns/` and are written in Markdown with a required YAML front matter block. The front matter lets the pipeline index patterns accurately without guessing descriptions from body text.

Each template should start with:

```markdown
---
title: Descriptive Pattern Title
description: Short, one-sentence summary used in the generated list.
---
```

Keep summaries concise (a single sentence works best) because the pipeline copies the `description` field directly into `integration_patterns/list.md`. Additional metadata can be added in the front matter if needed; it will be ignored by the current tooling but preserved for future use.

After the front matter, write the guide in Markdown as usual. When you run the docs pipeline, templates are copied verbatim into `tms_mcp/docs/integration_patterns/`, and the list is regenerated from the parsed metadata, so the published content should match what you authored.

---

### Updating Documentation

Use the `update_docs.sh` script to refresh documentation from upstream APIs:

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

---

### Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** (don't forget to run `pre-commit` hooks)
4. **Commit your changes** (`git commit -m 'Add amazing feature'`)
5. **Push to the branch** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

Please ensure your code:
- Passes all pre-commit hooks (ruff, mypy, etc.)
- Includes appropriate tests
- Follows the existing code style
- Includes clear commit messages

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**[⬆ Back to Top](#tms-development-wizard-mcp-server)**

</div
>
