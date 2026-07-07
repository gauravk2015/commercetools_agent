"""Application-specific exception types."""


class AgentError(Exception):
    """Base exception for clean agent errors."""

    def __init__(self, code: str, message: str, tool_name: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.tool_name = tool_name


class CommerceToolsError(AgentError):
    """Exception raised for commercetools communication or API errors."""
