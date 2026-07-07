"""OpenAI provider adapter using direct HTTP calls."""

from typing import Any

import httpx

from app.config.settings import Settings, get_settings
from app.providers.fallback import TemplateProvider
from app.providers.http_helpers import build_messages, build_tool_selection_messages, fallback_if_blank, parse_tool_selection_response
from app.schemas.tools import ToolCall, ToolSpec
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(TemplateProvider):
    """Generate responses with OpenAI when configured, otherwise use fallback text."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate_response(self, prompt: str, tool_name: str, data: Any) -> str:
        """Generate a response from the OpenAI Chat Completions API."""

        if not self.settings.openai_api_key:
            return await super().generate_response(prompt, tool_name, data)

        fallback = await super().generate_response(prompt, tool_name, data)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.settings.openai_api_endpoint,
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json={
                        "model": self.settings.openai_model,
                        "messages": build_messages(prompt, tool_name, data, self.settings.llm_system_prompt),
                        "temperature": 0.2,
                    },
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return fallback_if_blank(content, fallback)
        except Exception as exc:
            logger.error("openai_provider_failed error=%s", str(exc))
            return fallback

    async def select_tool(self, prompt: str, tools: list[ToolSpec]) -> ToolCall:
        """Use OpenAI to select the most appropriate tool for the prompt."""

        if not self.settings.openai_api_key:
            return await super().select_tool(prompt, tools)

        messages = build_tool_selection_messages(prompt, tools, self.settings.llm_system_prompt)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.settings.openai_api_endpoint,
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json={
                        "model": self.settings.openai_model,
                        "messages": messages,
                        "temperature": 0,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return parse_tool_selection_response(content, [tool["name"] for tool in tools])
        except Exception as exc:
            logger.error("openai_tool_selection_failed error=%s", str(exc))
            return await super().select_tool(prompt, tools)
