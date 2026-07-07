"""Claude provider adapter using direct HTTP calls."""

from typing import Any

import httpx

from app.config.settings import Settings, get_settings
from app.providers.fallback import TemplateProvider
from app.providers.http_helpers import build_messages, build_tool_selection_messages, fallback_if_blank, parse_tool_selection_response
from app.schemas.tools import ToolCall, ToolSpec
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ClaudeProvider(TemplateProvider):
    """Generate responses with Claude when configured, otherwise use fallback text."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate_response(self, prompt: str, tool_name: str, data: Any) -> str:
        """Generate a response from the Claude Messages API."""

        if not self.settings.claude_api_key:
            return await super().generate_response(prompt, tool_name, data)

        fallback = await super().generate_response(prompt, tool_name, data)
        messages = build_messages(prompt, tool_name, data, self.settings.llm_system_prompt)
        system = messages[0]["content"]
        user = messages[1]["content"]
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.settings.claude_api_endpoint,
                    headers={
                        "x-api-key": self.settings.claude_api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": self.settings.claude_model,
                        "max_tokens": 700,
                        "system": system,
                        "messages": [{"role": "user", "content": user}],
                    },
                )
                response.raise_for_status()
                content = response.json()["content"][0]["text"]
                return fallback_if_blank(content, fallback)
        except httpx.HTTPStatusError as exc:
            error_text = exc.response.text
            logger.error(
                "claude_provider_failed status=%s body=%s",
                exc.response.status_code,
                error_text,
            )
            return fallback
        except Exception as exc:
            logger.error("claude_provider_failed error=%s", str(exc))
            return fallback

    async def select_tool(self, prompt: str, tools: list[ToolSpec]) -> ToolCall:
        """Use Claude to select the most appropriate tool for the prompt."""

        if not self.settings.claude_api_key:
            return await super().select_tool(prompt, tools)

        messages = build_tool_selection_messages(prompt, tools, self.settings.llm_system_prompt)
        system = messages[0]["content"]
        user = messages[1]["content"]
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.settings.claude_api_endpoint,
                    headers={
                        "x-api-key": self.settings.claude_api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": self.settings.claude_model,
                        "max_tokens": 200,
                        "system": system,
                        "messages": [{"role": "user", "content": user}],
                    },
                )
                response.raise_for_status()
                content = response.json()["content"][0]["text"]
                return parse_tool_selection_response(content, [tool["name"] for tool in tools])
        except httpx.HTTPStatusError as exc:
            error_text = exc.response.text
            logger.error(
                "claude_tool_selection_failed status=%s body=%s",
                exc.response.status_code,
                error_text,
            )
            return await super().select_tool(prompt, tools)
        except Exception as exc:
            logger.error("claude_tool_selection_failed error=%s", str(exc))
            return await super().select_tool(prompt, tools)
