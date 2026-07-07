"""API route and dependency tests."""

import pytest
from starlette.requests import Request

from app.api.dependencies import verify_dashboard_secret
from app.api.routes import health
from app.config.settings import get_settings
from app.main import agent_error_handler
from app.models.errors import AgentError


@pytest.mark.asyncio
async def test_health() -> None:
    """Health endpoint returns the expected dashboard payload."""

    assert await health() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_rejects_invalid_secret(monkeypatch) -> None:
    """The shared dashboard auth dependency rejects health requests."""

    settings = get_settings()
    monkeypatch.setattr(settings, "dashboard_interaction_secret", "expected")
    with pytest.raises(AgentError) as exc:
        await verify_dashboard_secret("wrong")
    assert exc.value.code == "INVALID_DASHBOARD_SECRET"


@pytest.mark.asyncio
async def test_health_auth_error_uses_standard_contract() -> None:
    """Health auth failures are serialized using the standard agent contract."""

    request = Request({"type": "http", "method": "GET", "path": "/health", "headers": []})
    response = await agent_error_handler(
        request,
        AgentError("INVALID_DASHBOARD_SECRET", "Dashboard authentication failed. Please verify the shared key."),
    )
    assert response.status_code == 200
    assert b'"success":false' in response.body
    assert b'"userQuery":""' in response.body
    assert b'"code":"INVALID_DASHBOARD_SECRET"' in response.body
