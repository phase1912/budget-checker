import logging
import os
from typing import Awaitable, Callable

import anyio
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from .database import Base, engine
from .routers import health

logger = logging.getLogger("budget_checker")

REQUEST_TIMEOUT_SECONDS = float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "10"))
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5174").split(",")

# ERR-1/ERR-2/ERR-3: callers see this and nothing more specific — the specific
# cause (bad input, DB down, timeout) is only in the server-side log (ERR-4/5/6).
GENERIC_ERROR_MESSAGE = "The request could not be completed. Please try again."


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_seconds: float) -> None:
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            with anyio.fail_after(self.timeout_seconds):
                return await call_next(request)
        except TimeoutError:
            logger.error(
                "request timed out on %s %s after %.1fs",
                request.method,
                request.url.path,
                self.timeout_seconds,
            )
            return JSONResponse(status_code=504, content={"error": GENERIC_ERROR_MESSAGE})


def register_error_handling(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "invalid input on %s %s: %s", request.method, request.url.path, exc.errors()
        )
        return JSONResponse(status_code=422, content={"error": GENERIC_ERROR_MESSAGE})

    @app.exception_handler(SQLAlchemyError)
    async def handle_db_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error(
            "database unavailable on %s %s: %s", request.method, request.url.path, exc
        )
        return JSONResponse(status_code=503, content={"error": GENERIC_ERROR_MESSAGE})


def create_app() -> FastAPI:
    app = FastAPI(title="Budget Checker API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TimeoutMiddleware, timeout_seconds=REQUEST_TIMEOUT_SECONDS)

    from .routers import auth, health

    register_error_handling(app)

    app.include_router(health.router)
    app.include_router(auth.router)

    Base.metadata.create_all(bind=engine)

    return app


app = create_app()
