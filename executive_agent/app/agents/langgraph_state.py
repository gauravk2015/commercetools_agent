"""Typed state passed through the LangGraph executive agent workflow."""

from typing import Any, TypedDict

from app.schemas.tools import ToolCall


class ExecutiveAgentState(TypedDict, total=False):
    """Workflow state for tool selection, execution, and response generation."""

    prompt: str
    tool_call: ToolCall
    tool_name: str
    data: dict[str, Any] | list[dict[str, Any]]
    response: str
    error_code: str
    error_message: str
