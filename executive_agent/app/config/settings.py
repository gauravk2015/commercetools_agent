"""Environment-based application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

DEFAULT_LLM_SYSTEM_PROMPT = (
    "You are an executive commerce insights agent. "
    "Answer concisely in human-readable business language using only the normalized data. "
    "Do not return JSON, code blocks, raw objects, or key-value dumps in the response text. "
    "Use short prose or Markdown bullets when multiple facts are useful. "
    "Do not expose implementation details or raw API mechanics. "
    "The application already returns structured JSON separately in the data field."
)


class Settings(BaseSettings):
    """Typed settings loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Executive Commerce Insights Agent"
    app_env: str = "local"
    enable_logs: bool = True

    dashboard_interaction_secret: str = Field(default="", min_length=0)

    llm_system_prompt: str = DEFAULT_LLM_SYSTEM_PROMPT

    active_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_api_endpoint: str = "https://api.openai.com/v1/chat/completions"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_endpoint: str = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_api_endpoint: str = "https://api.anthropic.com/v1/messages"

    ctp_project_key: str = ""
    ctp_client_id: str = ""
    ctp_client_secret: str = ""
    ctp_auth_url: str = ""
    ctp_api_url: str = ""
    ctp_scopes: str = ""
    ctp_timeout_seconds: float = 20.0
    ctp_token_refresh_skew_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
