"""Provider interface for LLM-backed response generation."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.tools import ToolCall, ToolSpec


class LLMProvider(ABC):
    """Common contract implemented by all supported LLM providers."""

    @abstractmethod
    async def generate_response(self, prompt: str, tool_name: str, data: Any) -> str:
        """Generate a natural language answer from normalized tool data."""

    @abstractmethod
    async def select_tool(self, prompt: str, tools: list[ToolSpec]) -> ToolCall:
        """Select the best tool for a prompt using the provider's model."""
