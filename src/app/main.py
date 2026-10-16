from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.infrastructure.http.router_budgets import (
    router as budgets_router,
)
from app.modules.quotes.infrastructure.http.router_stock import (
    router as stocks_router,
)
from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.infrastructure.http.router import router as users_router
from app.shared.infrastructure.logging import configure_logging, logger


def create_app(user_repository: UserRepository | None = None, budget_repository: BudgetRepository | None = None, stock_repository: StockRepository | None = None) -> FastAPI:
    configure_logging(settings.LOG_LEVEL)
    logger.debug("Configurando aplicação e registrando rotas HTTP.")

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        logger.debug("Inicializando cliente HTTP compartilhado da aplicação.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            application.state.http_client = client
            yield
        logger.debug("Cliente HTTP encerrado; finalização da aplicação concluída.")

    application = FastAPI(
        title="MEC System",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.state.user_repository = user_repository
    application.state.budget_repository = budget_repository
    application.state.stock_repository = stock_repository
    application.include_router(users_router)
    application.include_router(budgets_router)
    application.include_router(stocks_router)

    @application.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        logger.debug("Tratando conflito de integridade do banco; resposta HTTP 409.")
        return JSONResponse(
            status_code=409,
            content={"detail": "Dados em conflito com as restrições do banco de dados"},
        )

    @application.exception_handler(UserNotFoundError)
    async def budget_not_found(request: Request, exc: UserNotFoundError):
        logger.debug("Tratando orçamento não encontrado; resposta HTTP 404.")
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(UserNotFoundError)
    async def user_not_found(request: Request, exc: UserNotFoundError):
        logger.debug("Tratando usuário não encontrado; resposta HTTP 404.")
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(ValueError)
    async def invalid_value(request: Request, exc: ValueError):
        logger.debug("Tratando valor inválido; resposta HTTP 422.")
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @application.exception_handler(httpx.HTTPError)
    async def provider_error(request: Request, exc: httpx.HTTPError):
        logger.debug("Tratando falha HTTP do provedor de CEP; resposta HTTP 502.")
        return JSONResponse(
            status_code=502, content={"detail": "Falha ao consultar serviço de CEP"}
        )

    return application


app = create_app()
