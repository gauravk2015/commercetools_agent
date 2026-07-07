"""FastAPI dependencies for route security."""

from fastapi import Header

from app.config.settings import get_settings
from app.models.errors import AgentError


async def verify_dashboard_secret(x_dashboard_secret: str | None = Header(default=None)) -> None:
    """Validate the shared dashboard-agent secret header."""

    settings = get_settings()
    if not settings.dashboard_interaction_secret:
        raise AgentError("AGENT_AUTH_NOT_CONFIGURED", "Agent dashboard authentication secret is not configured.")
    if x_dashboard_secret != settings.dashboard_interaction_secret:
        raise AgentError("INVALID_DASHBOARD_SECRET", "Dashboard authentication failed. Please verify the shared key.")
