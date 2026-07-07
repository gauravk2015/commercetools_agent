"""LLM provider factory selected by environment configuration."""

from app.config.settings import Settings, get_settings
from app.providers.base import LLMProvider
from app.providers.claude_provider import ClaudeProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider


class LLMFactory:
    """Create the configured LLM provider without frontend involvement."""

    @staticmethod
    def create(settings: Settings | None = None) -> LLMProvider:
        """Return a provider based on ACTIVE_PROVIDER."""

        resolved_settings = settings or get_settings()
        active = resolved_settings.active_provider.lower().strip()
        if active == "gemini":
            return GeminiProvider(resolved_settings)
        if active == "claude":
            return ClaudeProvider(resolved_settings)
        return OpenAIProvider(resolved_settings)
