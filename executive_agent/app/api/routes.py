"""HTTP routes exposed to the dashboard application."""

from fastapi import APIRouter, Depends

from app.agents.executive_agent import ExecutiveCommerceAgent
from app.api.dependencies import verify_dashboard_secret
from app.models.errors import AgentError
from app.schemas.chat import AgentResponse, ChatRequest, ErrorInfo
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health(_: None = Depends(verify_dashboard_secret)) -> dict[str, str]:
    """Return service health for the dashboard."""

    return {"status": "healthy"}


@router.post("/chat", response_model=AgentResponse)
async def chat(request: ChatRequest, _: None = Depends(verify_dashboard_secret)) -> AgentResponse:
    """Execute the agent workflow for a dashboard prompt."""

    agent = ExecutiveCommerceAgent()
    try:
        response = await agent.run(request.prompt)
        logger.info("agent_response success=%s tool=%s", response.success, response.toolUsed)
        return response
    except AgentError as exc:
        logger.error("agent_error code=%s message=%s", exc.code, exc.message)
        return AgentResponse(
            success=False,
            userQuery=request.prompt,
            toolUsed=exc.tool_name,
            response=exc.message,
            data=None,
            error=ErrorInfo(code=exc.code, message=exc.message),
        )
    except Exception as exc:
        logger.exception("unexpected_agent_error")
        return AgentResponse(
            success=False,
            userQuery=request.prompt,
            toolUsed=None,
            response="The agent could not complete the request.",
            data=None,
            error=ErrorInfo(code="AGENT_ERROR", message=str(exc)),
        )
