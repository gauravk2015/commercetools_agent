"""Gemini provider adapter using direct HTTP calls."""

from typing import Any

import httpx

from app.config.settings import Settings, get_settings
from app.providers.fallback import TemplateProvider
from app.providers.http_helpers import build_messages, build_tool_selection_messages, fallback_if_blank, parse_tool_selection_response
from app.schemas.tools import ToolCall, ToolSpec
from app.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(TemplateProvider):
    """Generate responses with Gemini when configured, otherwise use fallback text."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate_response(self, prompt: str, tool_name: str, data: Any) -> str:
        """Generate a response from the Gemini generateContent API."""

        if not self.settings.gemini_api_key:
            return await super().generate_response(prompt, tool_name, data)

        fallback = await super().generate_response(prompt, tool_name, data)
        messages = build_messages(prompt, tool_name, data, self.settings.llm_system_prompt)
        gemini_prompt = "\n\n".join(message["content"] for message in messages)
        url = self.settings.gemini_api_endpoint.format(model=self.settings.gemini_model)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    params={"key": self.settings.gemini_api_key},
                    json={"contents": [{"parts": [{"text": gemini_prompt}]}]},
                )
                response.raise_for_status()
                content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return fallback_if_blank(content, fallback)
        except Exception as exc:
            logger.error("gemini_provider_failed error=%s", str(exc))
            return fallback

    async def select_tool(self, prompt: str, tools: list[ToolSpec]) -> ToolCall:
        """Use Gemini to select the most appropriate tool for the prompt."""

        if not self.settings.gemini_api_key:
            return await super().select_tool(prompt, tools)

        messages = build_tool_selection_messages(prompt, tools, self.settings.llm_system_prompt)
        gemini_prompt = "\n\n".join(message["content"] for message in messages)
        url = self.settings.gemini_api_endpoint.format(model=self.settings.gemini_model)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    params={"key": self.settings.gemini_api_key},
                    json={
                        "contents": [{"parts": [{"text": gemini_prompt}]}],
                        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
                    },
                )
                response.raise_for_status()
                content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return parse_tool_selection_response(content, [tool["name"] for tool in tools])
        except Exception as exc:
            logger.error("gemini_tool_selection_failed error=%s", str(exc))
            return await super().select_tool(prompt, tools)
