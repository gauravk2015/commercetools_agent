"""Shared helpers for direct HTTP-based LLM provider calls."""

import json
import re
from typing import Any

from app.schemas.tools import ToolCall, ToolSpec


def build_messages(prompt: str, tool_name: str, data: Any, system_prompt: str) -> list[dict[str, str]]:
    """Build provider-neutral chat messages from normalized commerce data."""

    user = (
        f"User query: {prompt}\n"
        f"Tool used: {tool_name}\n"
        f"Normalized data for analysis only, not for direct JSON output:\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
        "Write only the natural-language response that should be shown in the chat UI."
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user}]


def build_tool_selection_messages(prompt: str, tools: list[ToolSpec], system_prompt: str) -> list[dict[str, str]]:
    """Build provider-neutral messages for LLM-based tool selection."""

    catalog = json.dumps(tools, ensure_ascii=False, indent=2)
    user = (
        f"User prompt: {prompt}\n\n"
        f"Available tools:\n{catalog}\n\n"
        "Choose exactly one tool and return ONLY valid JSON with this shape:\n"
        '{ "toolName": "tool_name_here", "arguments": { "arg": "value" } }\n'
        "Do not include markdown, code fences, or commentary."
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user}]


def parse_tool_selection_response(text: str, allowed_tools: list[str]) -> ToolCall:
    """Parse and validate an LLM tool-selection response."""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Tool selection response did not contain JSON.")
    payload = json.loads(cleaned[start : end + 1])
    tool_name = payload.get("toolName") or payload.get("tool_name")
    arguments = payload.get("arguments") or {}
    if tool_name not in allowed_tools:
        raise ValueError(f"Unsupported tool selected: {tool_name}")
    if not isinstance(arguments, dict):
        raise ValueError("Tool selection arguments must be an object.")
    return ToolCall(name=tool_name, arguments={str(key): str(value) for key, value in arguments.items()})


def fallback_if_blank(value: str | None, fallback: str) -> str:
    """Return fallback text if a provider response is blank."""

    cleaned = (value or "").strip()
    return cleaned or fallback
