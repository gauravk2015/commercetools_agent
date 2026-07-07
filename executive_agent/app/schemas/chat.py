"""Pydantic schemas for the dashboard-agent API contract."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming natural language request from the dashboard."""

    prompt: str = Field(..., min_length=1)


class ErrorInfo(BaseModel):
    """User-friendly error details."""

    code: str
    message: str


class AgentResponse(BaseModel):
    """Standard response contract used by every agent interaction."""

    success: bool
    userQuery: str
    toolUsed: str | None
    response: str
    data: dict[str, Any] | list[dict[str, Any]] | None
    error: ErrorInfo | None
