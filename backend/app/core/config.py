"""Application settings loaded from environment via pydantic-settings."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration for AgentForge (see CONTRACT.md env vars)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Infrastructure
    DATABASE_URL: str = "postgresql+asyncpg://agentforge:agentforge@localhost:5432/agentforge"
    REDIS_URL: str = "redis://localhost:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672//"

    # Auth
    JWT_SECRET: str = "dev-insecure-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LANGSMITH_API_KEY: str = ""

    # Object storage
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "agentforge"

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        """Accept managed-Postgres URLs (Render/Heroku give `postgres://` or
        `postgresql://`) and coerce them to the async asyncpg driver. Also drops
        an `sslmode` query param that asyncpg does not accept as a libpq option."""
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        if "sslmode=" in v:
            base, _, query = v.partition("?")
            kept = "&".join(p for p in query.split("&") if not p.startswith("sslmode="))
            v = f"{base}?{kept}" if kept else base
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
