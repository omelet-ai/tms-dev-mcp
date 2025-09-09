from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderSettings(BaseModel):
    """Configuration for a specific API provider."""

    name: str
    base_url: str
    docs_url: str
    title: str
    description: str = ""
    path_prefix: str = "/"


class PipelineSettings(BaseModel):
    """Configuration for the OpenAPI pipeline.

    [ NOTE ] The current pipeline & tools rely on the assumption that the `path prefixes` are unique for each provider. Further refactoring is needed to support multiple providers with overlapping path prefixes.
    """

    # File processing constants
    max_lines_per_read: int = 2000
    max_chars_per_line: int = 2000
    json_indent: int = 2

    # Provider configurations
    provider_configs: dict[str, ProviderSettings] = {
        "omelet": ProviderSettings(
            name="Omelet",
            base_url="",  # Will be populated from ROUTING_API_BASE_URL
            docs_url="",  # Will be populated from ROUTING_API_DOCS_URL
            title="Omelet Routing Engine API",
            description="Advanced routing optimization solutions",
            path_prefix="/api/",
        ),
        "inavi": ProviderSettings(
            name="iNavi",
            base_url="",  # Will be populated from IMAPS_API_BASE_URL
            docs_url="",  # Will be populated from IMAPS_API_DOCS_URL
            title="iNavi Maps API",
            description="Comprehensive location and routing services",
            path_prefix="/maps/v3.0/appkeys/{appkey}/",
        ),
    }


class Settings(BaseSettings):
    """Application settings for the Omelet Routing Engine MCP server."""

    # Server configuration (for streamable-http transport)
    HOST: str = Field(default="0.0.0.0", description="Host for remote server")
    PORT: int = Field(default=8000, description="Port for remote server")

    # Transport configuration
    MCP_TRANSPORT: Literal["stdio", "streamable-http"] = Field(
        default="stdio", description="MCP transport to use: 'stdio' for local or 'streamable-http' for remote"
    )

    # Omelet Routing Engine API configuration
    ROUTING_API_BASE_URL: str = Field(
        default="https://routing.oaasis.cc", description="Base URL for Omelet Routing Engine API"
    )
    ROUTING_API_DOCS_URL: str = Field(
        default="https://routing.oaasis.cc/docs/json", description="URL for OpenAPI JSON documentation"
    )

    # iNAVI Maps API configuration
    IMAPS_API_BASE_URL: str = Field(default="https://dev-maps.inavi.com", description="Base URL for iNAVI Maps API")
    IMAPS_API_DOCS_URL: str = Field(
        default="https://dev-imaps.inavi.com/api-docs",
        description="URL for IMAPS OpenAPI JSON documentation",
    )

    # Development settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Example generation
    EXAMPLE_LENGTH_LIMIT: int = Field(
        default=3,
        description="Max elements to keep when a top-level value is a list in saved examples",
    )

    # Pipeline configuration
    pipeline_config: PipelineSettings = Field(default_factory=PipelineSettings, description="Pipeline configuration")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Populate provider base URLs and docs URLs from settings
        self.pipeline_config.provider_configs["omelet"].base_url = self.ROUTING_API_BASE_URL
        self.pipeline_config.provider_configs["omelet"].docs_url = self.ROUTING_API_DOCS_URL
        self.pipeline_config.provider_configs["inavi"].base_url = self.IMAPS_API_BASE_URL
        self.pipeline_config.provider_configs["inavi"].docs_url = self.IMAPS_API_DOCS_URL


settings = Settings()
