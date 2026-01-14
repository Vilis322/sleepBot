from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Note: Reads from environment variables set by Docker Compose via env_file directive.
    No need for env_file in SettingsConfigDict - variables come from container environment.
    """

    model_config = SettingsConfigDict(extra="ignore")

    # Bot configuration
    bot_token: str = Field(..., description="Telegram Bot API token")

    # Database configuration
    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(..., description="PostgreSQL database name")
    db_user: str = Field(..., description="PostgreSQL username")
    db_password: str = Field(..., description="PostgreSQL password")

    # Environment
    environment: str = Field(default="development", description="Environment: development or production")

    # Logging
    log_level: str = Field(default="DEBUG", description="Logging level: DEBUG, INFO, WARNING, ERROR")

    # Timezone
    default_timezone: str = Field(default="UTC", description="Default timezone for users")

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


settings = Settings()
