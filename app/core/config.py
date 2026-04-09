from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Handles database credentials, LLM configurations, and security keys.
    """

    # Database connection parameters
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Groq API Configuration
    GROQ_API_KEY: str

    # Agent behaviors & MDL defaults
    BLOCKED_TABLES: str = "users,sessions,audit_logs,passwords,tokens,mdl_schemas"
    MDL_DEFAULT_NAME: str = "database_mdl"
    MAX_SQL_RETRIES: int = 3
    MAX_EXPLORATIONS: int = 3
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE_SQL: float = 0.0
    LLM_TEMPERATURE_ANSWER: float = 0.3

    # Security: JWT and Credential Encryption
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key"
    ENCRYPTION_KEY: str = "gR1WjM-z_n8q2a7r1O0Q-v1M7wH0MhA9fK4V6xV9KzY="

    @property
    def async_database_url(self) -> str:
        """Constructs the asynchronous PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Constructs the synchronous PostgreSQL connection string for introspection."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def blocked_tables_list(self) -> list[str]:
        """Parses the blocked tables string into a clean list of lowercase names."""
        return [t.strip().lower() for t in self.BLOCKED_TABLES.split(",") if t.strip()]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Provides a cached instance of the application settings."""
    return Settings()
