from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    ROUTING_API_KEY: str = Field(default="test", description="API key for Omelet Routing Engine API")

    # iNAVI Maps API configuration
    IMAPS_API_BASE_URL: str = Field(default="https://dev-imaps.inavi.com", description="Base URL for iNAVI Maps API")
    IMAPS_API_DOCS_URL: str = Field(
        default="https://dev-imaps.inavi.com/api-docs",
        description="URL for IMAPS OpenAPI JSON documentation",
    )

    # Development settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # AWS Bedrock
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS Access Key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS Secret Access Key")
    AWS_DEFAULT_REGION: str = Field(default="", description="AWS Default Region")
    AWS_BEDROCK_MODEL_ID: str = Field(default="", description="AWS Bedrock Model ID")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
