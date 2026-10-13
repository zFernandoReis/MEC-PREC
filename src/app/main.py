from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.infrastructure.http.router import router as users_router


def create_app(user_repository: UserRepository | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with httpx.AsyncClient(timeout=10.0) as client:
            application.state.http_client = client
            yield

    application = FastAPI(
        title="MEC System",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.state.user_repository = user_repository
    application.include_router(users_router)

    @application.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={"detail": "Dados em conflito com as restrições do banco de dados"},
        )

    @application.exception_handler(UserNotFoundError)
    async def user_not_found(request: Request, exc: UserNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(ValueError)
    async def invalid_value(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @application.exception_handler(httpx.HTTPError)
    async def provider_error(request: Request, exc: httpx.HTTPError):
        return JSONResponse(
            status_code=502, content={"detail": "Falha ao consultar serviço de CEP"}
        )

    return application


app = create_app()
