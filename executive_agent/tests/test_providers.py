"""Tests for LLM provider endpoint configuration."""

from typing import Any

import pytest

from app.config.settings import DEFAULT_LLM_SYSTEM_PROMPT, Settings
from app.providers.http_helpers import build_messages
from app.providers.claude_provider import ClaudeProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider


class FakeResponse:
    """Minimal HTTP response double for provider tests."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        """Simulate a successful HTTP status."""

    def json(self) -> dict[str, Any]:
        """Return the fake provider payload."""

        return self.payload


class FakeAsyncClient:
    """Async httpx client double that records outgoing POST requests."""

    calls: list[dict[str, Any]] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        return None

    async def post(self, url: str, **kwargs: Any) -> FakeResponse:
        """Record the outbound call and return a provider-shaped response."""

        self.calls.append({"url": url, "kwargs": kwargs})
        if "openai" in url:
            return FakeResponse({"choices": [{"message": {"content": "openai response"}}]})
        if "gemini" in url:
            return FakeResponse({"candidates": [{"content": {"parts": [{"text": "gemini response"}]}}]})
        return FakeResponse({"content": [{"text": "claude response"}]})


@pytest.fixture(autouse=True)
def reset_fake_client() -> None:
    """Reset recorded calls before each provider test."""

    FakeAsyncClient.calls = []


def test_provider_prompt_requires_human_readable_response() -> None:
    """Provider prompt forbids JSON in the generated response text."""

    messages = build_messages(
        "Show order 100001",
        "get_order_by_order_number",
        {"orderNumber": "100001"},
        DEFAULT_LLM_SYSTEM_PROMPT,
    )
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    assert "Do not return JSON" in system_prompt
    assert "structured JSON separately in the data field" in system_prompt
    assert "Write only the natural-language response" in user_prompt


def test_provider_prompt_uses_configured_system_prompt() -> None:
    """Provider message builder uses the centrally configured system prompt."""

    messages = build_messages("Show order 100001", "get_order_by_order_number", {}, "Custom executive prompt")
    assert messages[0]["content"] == "Custom executive prompt"


@pytest.mark.asyncio
async def test_openai_provider_uses_configured_endpoint(monkeypatch) -> None:
    """OpenAI calls the endpoint from OPENAI_API_ENDPOINT."""

    monkeypatch.setattr("app.providers.openai_provider.httpx.AsyncClient", FakeAsyncClient)
    settings = Settings(openai_api_key="key", openai_api_endpoint="https://openai.example/chat")
    response = await OpenAIProvider(settings).generate_response("prompt", "tool", {"value": 1})
    assert response == "openai response"
    assert FakeAsyncClient.calls[0]["url"] == "https://openai.example/chat"


@pytest.mark.asyncio
async def test_gemini_provider_uses_configured_endpoint(monkeypatch) -> None:
    """Gemini calls GEMINI_API_ENDPOINT after formatting the model placeholder."""

    monkeypatch.setattr("app.providers.gemini_provider.httpx.AsyncClient", FakeAsyncClient)
    settings = Settings(
        gemini_api_key="key",
        gemini_model="gemini-test",
        gemini_api_endpoint="https://gemini.example/models/{model}:generateContent",
    )
    response = await GeminiProvider(settings).generate_response("prompt", "tool", {"value": 1})
    assert response == "gemini response"
    assert FakeAsyncClient.calls[0]["url"] == "https://gemini.example/models/gemini-test:generateContent"


@pytest.mark.asyncio
async def test_claude_provider_uses_configured_endpoint(monkeypatch) -> None:
    """Claude calls the endpoint from CLAUDE_API_ENDPOINT."""

    monkeypatch.setattr("app.providers.claude_provider.httpx.AsyncClient", FakeAsyncClient)
    settings = Settings(claude_api_key="key", claude_api_endpoint="https://claude.example/messages")
    response = await ClaudeProvider(settings).generate_response("prompt", "tool", {"value": 1})
    assert response == "claude response"
    assert FakeAsyncClient.calls[0]["url"] == "https://claude.example/messages"
    assert "temperature" not in FakeAsyncClient.calls[0]["kwargs"]["json"]


@pytest.mark.asyncio
async def test_claude_tool_selection_omits_temperature(monkeypatch) -> None:
    """Claude tool-selection payload should not send deprecated temperature."""

    monkeypatch.setattr("app.providers.claude_provider.httpx.AsyncClient", FakeAsyncClient)
    settings = Settings(claude_api_key="key", claude_api_endpoint="https://claude.example/messages")
    await ClaudeProvider(settings).select_tool(
        "Show order history for seb@example.de",
        [
            {"name": "get_customer_order_history_by_email", "description": "x", "arguments": ["email"]},
        ],
    )
    assert "temperature" not in FakeAsyncClient.calls[0]["kwargs"]["json"]
