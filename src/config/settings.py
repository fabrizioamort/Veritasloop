"""Centralized configuration management for VeritasLoop backend.

This module uses pydantic-settings to manage all environment variables
and configuration in a type-safe, validated manner.
"""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Phoenix Observability Configuration
    phoenix_enabled: bool = True
    phoenix_host: str = "localhost"
    phoenix_port: int = 6006

    # CORS Configuration
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Environment
    environment: str = "development"  # development, staging, production

    # HTTP Request Timeouts (in seconds)
    request_timeout: int = 10

    # API Keys (required)
    openai_api_key: str
    brave_search_api_key: str

    # API Keys (optional)
    news_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    gemini_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def phoenix_url(self) -> str:
        """Get Phoenix server URL."""
        return f"http://{self.phoenix_host}:{self.phoenix_port}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
