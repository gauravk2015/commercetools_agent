"""Internal schemas for selected tool execution."""

from typing import TypedDict

from pydantic import BaseModel


class ToolCall(BaseModel):
    """Tool name and arguments selected by the agent."""

    name: str
    arguments: dict[str, str]


class ToolSpec(TypedDict):
    """Tool metadata used by the LLM to decide which action to take."""

    name: str
    description: str
    arguments: list[str]
