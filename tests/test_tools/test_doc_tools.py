from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp.exceptions import ToolError

from tms_mcp.tools import doc_tools
from tms_mcp.tools.models import (
    EndpointsListResult,
    ExamplesListResult,
    GuidesListResult,
    PatternsListResult,
)


def _call_tool(tool: Any, *args: Any, **kwargs: Any) -> Any:
    """Call a FastMCP tool function, handling the FunctionTool wrapper."""
    if hasattr(tool, "fn"):
        return tool.fn(*args, **kwargs)
    return tool(*args, **kwargs)


class TestGetBasicInfo:
    def test_returns_content_from_file(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_basic_info)
            assert "Basic Info" in result

    def test_masks_api_keys(self, temp_provider_docs: Path) -> None:
        with (
            patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs),
            patch.dict("os.environ", {"INAVI_API_KEY": "secret_key_12345678", "OMELET_API_KEY": "omelet_secret_key"}),
        ):
            result = _call_tool(doc_tools.get_basic_info)
            assert "secret_key_12345678" not in result
            assert "secr...5678" in result
            assert "omel..._key" in result


class TestListIntegrationPatterns:
    def test_returns_patterns_list_result(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.list_integration_patterns)
            assert isinstance(result, PatternsListResult)
            assert result.total_count == 1
            assert result.patterns[0].pattern_id == "test/pattern1"

    def test_raises_tool_error_when_list_not_found(self, tmp_path: Path) -> None:
        empty_docs = tmp_path / "docs"
        empty_docs.mkdir()
        (empty_docs / "integration_patterns").mkdir()
        with patch.object(doc_tools, "_get_docs_dir", return_value=empty_docs):
            with pytest.raises(ToolError, match="not found"):
                _call_tool(doc_tools.list_integration_patterns)


class TestGetIntegrationPattern:
    def test_returns_pattern_content(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_integration_pattern, "test/pattern1", simple=True)
            assert "Test Pattern" in result

    def test_raises_tool_error_for_invalid_pattern_id(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="not found"):
                _call_tool(doc_tools.get_integration_pattern, "nonexistent/pattern")

    def test_rejects_path_traversal(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="Invalid"):
                _call_tool(doc_tools.get_integration_pattern, "../../../etc/passwd")


class TestListTroubleshootingGuides:
    def test_returns_guides_list_result(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.list_troubleshooting_guides)
            assert isinstance(result, GuidesListResult)
            assert result.total_count == 1
            assert result.guides[0].guide_id == "errors/timeout"


class TestGetTroubleshootingGuide:
    def test_returns_guide_content(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_troubleshooting_guide, "errors/timeout")
            assert "Timeout Errors" in result

    def test_raises_tool_error_for_nonexistent_guide(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="not found"):
                _call_tool(doc_tools.get_troubleshooting_guide, "nonexistent/guide")


class TestListEndpoints:
    def test_returns_endpoints_list_result(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.list_endpoints, provider="omelet")
            assert isinstance(result, EndpointsListResult)
            assert result.total_count == 2
            assert result.provider == "omelet"
            assert result.endpoints[0].path == "/api/vrp"

    def test_raises_tool_error_when_no_endpoints(self, tmp_path: Path) -> None:
        empty_docs = tmp_path / "docs"
        empty_docs.mkdir()
        with patch.object(doc_tools, "_get_docs_dir", return_value=empty_docs):
            with pytest.raises(ToolError, match="No endpoints found"):
                _call_tool(doc_tools.list_endpoints)


class TestGetEndpointOverview:
    def test_returns_json_content(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_endpoint_overview, "/api/vrp", provider="omelet")
            assert '"path": "/api/vrp"' in result

    def test_raises_tool_error_for_nonexistent_endpoint(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="not found"):
                _call_tool(doc_tools.get_endpoint_overview, "/api/nonexistent", provider="omelet")


class TestGetRequestBodySchema:
    def test_returns_schema(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_request_body_schema, "/api/vrp", provider="omelet")
            assert '"schema"' in result


class TestGetResponseSchema:
    def test_returns_response_schema(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_response_schema, "/api/vrp", "200", provider="omelet")
            assert '"type": "object"' in result

    def test_raises_tool_error_for_invalid_response_code(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="not found"):
                _call_tool(doc_tools.get_response_schema, "/api/vrp", "404", provider="omelet")


class TestListExamples:
    def test_returns_examples_list_result(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.list_examples, "/api/vrp", provider="omelet")
            assert isinstance(result, ExamplesListResult)
            assert result.endpoint == "/api/vrp"
            assert "default" in result.request_examples
            assert "200" in result.response_examples
            assert "success" in result.response_examples["200"]


class TestProviderValidation:
    def test_rejects_path_traversal_provider(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="Invalid provider"):
                _call_tool(doc_tools.get_endpoint_overview, "/api/vrp", provider="../..")

    def test_rejects_unknown_provider(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="Invalid provider"):
                _call_tool(doc_tools.list_endpoints, provider="unknown_provider")

    def test_accepts_valid_provider_with_whitespace(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.list_endpoints, provider="  omelet  ")
            assert isinstance(result, EndpointsListResult)


class TestListExamplesValidation:
    def test_rejects_invalid_example_type(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="Invalid example_type"):
                _call_tool(doc_tools.list_examples, "/api/vrp", example_type="invalid", provider="omelet")


class TestGetExample:
    def test_returns_request_example(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(doc_tools.get_example, "/api/vrp", "default", "request", provider="omelet")
            assert '"vehicles"' in result

    def test_returns_response_example(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            result = _call_tool(
                doc_tools.get_example, "/api/vrp", "success", "response", response_code="200", provider="omelet"
            )
            assert '"routes"' in result

    def test_raises_tool_error_for_response_without_code(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="response_code is required"):
                _call_tool(doc_tools.get_example, "/api/vrp", "success", "response", provider="omelet")

    def test_raises_tool_error_for_invalid_example_type(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="Invalid example_type"):
                _call_tool(doc_tools.get_example, "/api/vrp", "default", "invalid", provider="omelet")

    def test_raises_tool_error_for_nonexistent_example(self, temp_provider_docs: Path) -> None:
        with patch.object(doc_tools, "_get_docs_dir", return_value=temp_provider_docs):
            with pytest.raises(ToolError, match="not found"):
                _call_tool(doc_tools.get_example, "/api/vrp", "nonexistent", "request", provider="omelet")
