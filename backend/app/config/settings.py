"""
Application settings loaded from environment variables.
Uses pydantic-settings for type-safe config management.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyHttpUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "TripMate AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")          # development | production
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="change-me-in-production-please")
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://tripmate:tripmate@localhost:5432/tripmate"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # ── Auth / JWT ───────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(default="jwt-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── LiteLLM / LLM ────────────────────────────────────────────────────────
    LITELLM_BASE_URL: Optional[str] = Field(default=None)   # proxy URL if using LiteLLM proxy
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)

    # Model routing
    SUPERVISOR_MODEL: str = Field(default="gpt-4o")
    FLIGHT_AGENT_MODEL: str = Field(default="gpt-4o-mini")
    HOTEL_AGENT_MODEL: str = Field(default="gpt-4o-mini")
    WEATHER_AGENT_MODEL: str = Field(default="gpt-4o-mini")
    BUDGET_AGENT_MODEL: str = Field(default="gpt-4o-mini")
    ITINERARY_AGENT_MODEL: str = Field(default="gpt-4o")
    FINAL_AGENT_MODEL: str = Field(default="gpt-4o")
    GUARDRAIL_MODEL: str = Field(default="gpt-4o-mini")
    RAG_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")

    # ── External APIs ─────────────────────────────────────────────────────────
    AVIATIONSTACK_API_KEY: Optional[str] = Field(default=None)
    TAVILY_API_KEY: Optional[str] = Field(default=None)
    OPENWEATHER_API_KEY: Optional[str] = Field(default=None)
    EXCHANGERATE_API_KEY: Optional[str] = Field(default=None)

    # ── MCP Server Ports ─────────────────────────────────────────────────────
    MCP_FLIGHT_PORT: int = Field(default=8001)
    MCP_HOTEL_PORT: int = Field(default=8002)
    MCP_WEATHER_PORT: int = Field(default=8003)
    MCP_BUDGET_PORT: int = Field(default=8004)

    # ── RAG / Vector Store ────────────────────────────────────────────────────
    CHROMA_HOST: str = Field(default="localhost")
    CHROMA_PORT: int = Field(default=8005)
    CHROMA_COLLECTION_NAME: str = Field(default="tripmate_knowledge")
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5

    # ── HITL ─────────────────────────────────────────────────────────────────
    HITL_TIMEOUT_SECONDS: int = Field(default=300)       # 5-min user review window
    HITL_AUTO_APPROVE_AFTER_TIMEOUT: bool = Field(default=False)

    # ── Guardrails ────────────────────────────────────────────────────────────
    GUARDRAIL_MAX_RETRIES: int = 2
    BLOCKED_KEYWORDS_FILE: str = "app/config/blocked_keywords.json"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(default=30)

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = "json"   # json | text


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


# Convenience alias
settings = get_settings()
