"""Pydantic models for structured MCP tool outputs."""

from pydantic import BaseModel, Field


class EndpointSummary(BaseModel):
    path: str = Field(description="API endpoint path")
    method: str = Field(description="HTTP method (GET, POST, etc.)")
    summary: str = Field(description="Brief description of the endpoint")
    description: str = Field(description="Detailed description of the endpoint")


class EndpointsListResult(BaseModel):
    endpoints: list[EndpointSummary] = Field(description="List of endpoint summaries")
    total_count: int = Field(description="Total number of endpoints")
    provider: str | None = Field(default=None, description="Provider filter applied")


class ExamplesListResult(BaseModel):
    endpoint: str = Field(description="API endpoint path")
    path_id: str = Field(description="Sanitized path identifier")
    request_examples: list[str] = Field(default_factory=list, description="Available request example names")
    response_examples: dict[str, list[str]] = Field(
        default_factory=dict, description="Response examples by HTTP status code"
    )


class PatternSummary(BaseModel):
    pattern_id: str = Field(description="Integration pattern identifier")
    description: str = Field(description="Brief description of the pattern")


class PatternsListResult(BaseModel):
    patterns: list[PatternSummary] = Field(description="List of integration patterns")
    total_count: int = Field(description="Total number of patterns")


class GuideSummary(BaseModel):
    guide_id: str = Field(description="Troubleshooting guide identifier")
    description: str = Field(description="Brief description of the guide")


class GuidesListResult(BaseModel):
    guides: list[GuideSummary] = Field(description="List of troubleshooting guides")
    total_count: int = Field(description="Total number of guides")
