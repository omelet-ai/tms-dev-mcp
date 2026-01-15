import json
from pathlib import Path

import pytest


@pytest.fixture
def temp_docs_dir(tmp_path: Path) -> Path:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "basic_info.md").write_text("# Basic Info\nTest content")

    integration_patterns = docs_dir / "integration_patterns"
    integration_patterns.mkdir()
    (integration_patterns / "list.md").write_text(
        "| pattern_id | description |\n| --- | --- |\n| test/pattern1 | Test pattern 1 |\n"
    )
    test_category = integration_patterns / "test"
    test_category.mkdir()
    (test_category / "pattern1.md").write_text("---\ntitle: Test Pattern\n---\n# Test Pattern\nContent")

    troubleshooting = docs_dir / "troubleshooting"
    troubleshooting.mkdir()
    (troubleshooting / "list.md").write_text(
        "| guide_id | description |\n| --- | --- |\n| errors/timeout | Timeout errors guide |\n"
    )
    errors_dir = troubleshooting / "errors"
    errors_dir.mkdir()
    (errors_dir / "timeout.md").write_text("# Timeout Errors\nGuide content")

    return docs_dir


@pytest.fixture
def temp_provider_docs(temp_docs_dir: Path) -> Path:
    omelet_dir = temp_docs_dir / "omelet"
    omelet_dir.mkdir()

    (omelet_dir / "endpoints_summary.md").write_text(
        "# Omelet Routing Engine API\n"
        "## Endpoints\n"
        "| Path | Method | Summary | Description |\n"
        "|------|--------|---------|-------------|\n"
        "| /api/vrp | POST | VRP endpoint | Solve VRP problems |\n"
        "| /api/cost-matrix | POST | Cost matrix | Generate cost matrix |\n"
    )

    overviews = omelet_dir / "overviews"
    overviews.mkdir()
    (overviews / "vrp.json").write_text(
        json.dumps(
            {
                "path": "/api/vrp",
                "method": "POST",
                "summary": "VRP endpoint",
                "description": "Solve VRP problems",
            }
        )
    )

    schemas = omelet_dir / "schemas"
    schemas.mkdir()
    request_body = schemas / "request_body"
    request_body.mkdir()
    (request_body / "vrp.json").write_text(json.dumps({"schema": {"type": "object"}}))

    response = schemas / "response"
    response.mkdir()
    vrp_response = response / "vrp"
    vrp_response.mkdir()
    (vrp_response / "200.json").write_text(json.dumps({"type": "object", "properties": {}}))

    examples = omelet_dir / "examples"
    examples.mkdir()
    req_body_examples = examples / "request_body" / "vrp"
    req_body_examples.mkdir(parents=True)
    (req_body_examples / "default.json").write_text(json.dumps({"vehicles": [], "jobs": []}))

    resp_body_examples = examples / "response_body" / "vrp" / "200"
    resp_body_examples.mkdir(parents=True)
    (resp_body_examples / "success.json").write_text(json.dumps({"routes": []}))

    return temp_docs_dir


@pytest.fixture
def sample_openapi_spec() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/test": {
                "post": {
                    "summary": "Test endpoint",
                    "description": "A test endpoint",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                                "example": {"name": "test"},
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            }
        },
    }
