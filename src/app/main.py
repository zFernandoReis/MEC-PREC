from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.infrastructure.http.router_orders import router as orders_router
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
from app.modules.users.application.ports.vehicle_repository import VehicleRepository
from app.modules.users.infrastructure.http.router_users import router as users_router
from app.modules.users.infrastructure.http.router_vehicles import (
    router as vehicles_router,
)
from app.shared.infrastructure.database.integrity_errors import integrity_error_details
from app.shared.infrastructure.logging import configure_logging, logger
from app.shared.infrastructure.security.dependencies import get_current_user, require_admin
from app.shared.infrastructure.security.repository import CredentialRepository
from app.shared.infrastructure.security.router import router as auth_router


def create_app(user_repository: UserRepository | None = None, budget_repository: BudgetRepository | None = None, stock_repository: StockRepository | None = None, vehicle_repository: VehicleRepository | None = None, order_repository: OrderRepository | None = None, credential_repository: CredentialRepository | None = None) -> FastAPI:
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
    application.state.vehicle_repository = vehicle_repository
    application.state.order_repository = order_repository
    application.state.credential_repository = credential_repository
    application.include_router(auth_router)
    application.include_router(users_router, dependencies=[Depends(require_admin)])
    authenticated = [Depends(get_current_user)]
    application.include_router(budgets_router, dependencies=authenticated)
    application.include_router(stocks_router, dependencies=authenticated)
    application.include_router(vehicles_router, dependencies=authenticated)
    application.include_router(orders_router, dependencies=authenticated)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if request.url.path.startswith(("/auth/", "/users")):
            # A resposta padrão inclui input, que pode conter senhas e tokens.
            errors = [
                {key: error[key] for key in ("loc", "msg", "type")}
                for error in exc.errors()
            ]
            return JSONResponse(status_code=422, content={"detail": errors})
        return await request_validation_exception_handler(request, exc)

    @application.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        logger.debug("Tratando conflito de integridade do banco; resposta HTTP 409.")
        return JSONResponse(
            status_code=409,
            content=integrity_error_details(exc),
        )

    @application.exception_handler(UserNotFoundError)
    async def budget_not_found(request: Request, exc: UserNotFoundError):
        logger.debug("Tratando orçamento não encontrado; resposta HTTP 404.")
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(UserNotFoundError)
    async def user_not_found(request: Request, exc: UserNotFoundError):
        logger.debug("Tratando usuário não encontrado; resposta HTTP 404.")
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(OrderNotFoundError)
    async def order_not_found(request: Request, exc: OrderNotFoundError):
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
