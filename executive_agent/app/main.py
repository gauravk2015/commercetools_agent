"""FastAPI application entrypoint for the executive agent service."""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config.settings import get_settings
from app.models.errors import AgentError

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError) -> JSONResponse:
    """Return standardized JSON for agent errors raised outside route bodies."""

    user_query = ""
    if request.url.path == "/chat":
        try:
            body = await request.json()
            user_query = body.get("prompt", "")
        except Exception:
            user_query = ""

    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "userQuery": user_query,
            "toolUsed": exc.tool_name,
            "response": exc.message,
            "data": None,
            "error": {"code": exc.code, "message": exc.message},
        },
    )
