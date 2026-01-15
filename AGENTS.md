# AGENTS.md - AI Agent Guidelines for tms-dev-mcp

## Project Overview

Python MCP (Model Context Protocol) server providing tools to explore Omelet's Routing Engine and iNavi's Maps API for building Transport Management Systems. Built with FastMCP framework.

## Build/Lint/Test Commands

### Environment Setup
```bash
uv sync --all-groups          # Install all dependencies (dev + test groups)
source .venv/bin/activate     # Activate venv (Unix)
pre-commit install            # Install git hooks
```

### Testing
```bash
uv run pytest -c setup.cfg                              # Run all tests
uv run pytest tests/test_tools/test_doc_tools.py       # Run single file
uv run pytest tests/test_tools/test_doc_tools.py::TestGetBasicInfo  # Run single class
uv run pytest tests/test_tools/test_doc_tools.py::TestGetBasicInfo::test_masks_api_keys  # Single test
uv run pytest -k "test_rejects"                        # Run tests matching pattern
uv run pytest -v                                       # Verbose output
uv run pytest --tb=short                               # Short traceback
```

### Linting & Type Checking
```bash
uv run ruff check .              # Lint (will auto-fix with --fix)
uv run ruff format .             # Format code
uv run mypy tms_mcp              # Type check
uv run pre-commit run --all-files  # Run all hooks
```

### Running the Server
```bash
uv run python -m tms_mcp.main                     # Start server (stdio)
uv run python -m tms_mcp.main update-docs         # Update all provider docs
uv run python -m tms_mcp.main update-docs omelet  # Update specific provider
```

## Code Style Guidelines

### Python Version & Type Hints
- **Python 3.11+** required
- Use **native collection types** for type hints:
  ```python
  # CORRECT
  def process(items: list[str], config: dict[str, Any]) -> tuple[int, str]: ...
  def fetch(url: str | None = None) -> dict[str, Any] | None: ...

  # WRONG - Do NOT use typing module equivalents
  from typing import List, Dict, Optional  # NO!
  ```
- Use `Annotated[type, "description"]` for MCP tool parameters

### Formatting (ruff enforced)
- **Line length**: 120 characters
- **Imports**: Auto-sorted (isort via ruff)
- **Indentation**: 4 spaces
- **Trailing newline**: Required

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Functions/variables | `snake_case` | `get_provider_from_path` |
| Classes | `PascalCase` | `EndpointGenerator` |
| Constants | `UPPER_SNAKE_CASE` | `HTTP_TIMEOUT`, `MAX_RETRIES` |
| Private members | `_leading_underscore` | `_validate_provider` |
| Module loggers | `logger = get_logger(__name__)` | |

### Error Handling for MCP Tools
Use `ToolError` from FastMCP for user-facing errors:
```python
from fastmcp.exceptions import ToolError

def _validate_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in provider_configs:
        raise ToolError(f"Invalid provider '{provider}'. Must be one of: {', '.join(provider_configs.keys())}")
    return normalized

@mcp.tool
def get_data(path: str, provider: str | None = None) -> str:
    if provider is not None:
        provider = _validate_provider(provider)  # Raises ToolError if invalid
    # ... rest of implementation
```

### Structured Tool Outputs
Return Pydantic models for structured data (defined in `tms_mcp/tools/models.py`):
```python
from pydantic import BaseModel, Field

class EndpointSummary(BaseModel):
    path: str = Field(description="API endpoint path")
    method: str = Field(description="HTTP method")

@mcp.tool
def list_endpoints(provider: str | None = None) -> EndpointsListResult:
    return EndpointsListResult(endpoints=[...], total_count=len(endpoints))
```

### File Operations
Use utilities from `tms_mcp/pipeline/utils.py`:
```python
from tms_mcp.pipeline.utils import write_json_file, write_markdown_file, read_json_file

write_json_file(path, data)      # Auto-creates parent dirs, adds trailing newline
write_markdown_file(path, content)
```

## Security Considerations

### Input Validation
Always validate user-provided identifiers against allowlists:
```python
# Provider validation - prevents path traversal
if provider not in provider_configs:
    raise ToolError(f"Invalid provider")

# Document ID sanitization
parts = [p for p in doc_id.split("/") if p and p not in {".", ".."}]
```

### API Key Masking
Mask sensitive data in outputs:
```python
def _mask_api_key(key: str) -> str:
    return "****" if len(key) <= 8 else f"{key[:4]}...{key[-4:]}"
```

## File Organization
```
tms_mcp/
├── server.py           # FastMCP instance + prompts
├── main.py             # CLI entry point
├── config.py           # Pydantic settings
├── tools/
│   ├── doc_tools.py    # MCP tools (@mcp.tool decorated)
│   └── models.py       # Pydantic models for structured outputs
├── pipeline/
│   ├── pipeline.py     # Doc generation orchestration
│   ├── utils.py        # File I/O, path utilities
│   └── generators/     # Schema, endpoint, example generators
└── docs/               # Generated docs (DO NOT edit manually)
```

## Things to Avoid

- **Do NOT** use `typing.List`, `typing.Dict`, `typing.Tuple` - use native types
- **Do NOT** edit files in `tms_mcp/docs/` - they are auto-generated
- **Do NOT** return error strings from tools - raise `ToolError` instead
- **Do NOT** use `# type: ignore` without error code - use `# type: ignore[specific-error]`
- **Do NOT** catch bare `Exception` - use specific exception types
- **Do NOT** retry HTTP 4xx errors (except 408, 429) - they're permanent failures

## Pre-commit Hooks (run automatically)
1. `trailing-whitespace`, `end-of-file-fixer` - Whitespace
2. `check-yaml`, `check-toml` - Config validation
3. `ruff`, `ruff-format` - Lint and format
4. `codespell` - Spell check
5. `pytest` - Tests
6. `mypy` - Type checking
