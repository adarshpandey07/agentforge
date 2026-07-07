"""Application exception hierarchy and FastAPI handlers."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AgentForgeError(Exception):
    """Base application error mapped to an HTTP response."""

    status_code: int = 500
    default_detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class BadRequestError(AgentForgeError):
    status_code = 400
    default_detail = "Bad request"


class UnauthorizedError(AgentForgeError):
    status_code = 401
    default_detail = "Not authenticated"


class ForbiddenError(AgentForgeError):
    status_code = 403
    default_detail = "Insufficient permissions"


class NotFoundError(AgentForgeError):
    status_code = 404
    default_detail = "Resource not found"


class ConflictError(AgentForgeError):
    status_code = 409
    default_detail = "Resource conflict"


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON handlers for AgentForgeError subclasses."""

    @app.exception_handler(AgentForgeError)
    async def _handle_app_error(request: Request, exc: AgentForgeError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)
