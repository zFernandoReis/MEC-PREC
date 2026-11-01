from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.bootstrap.orders import OrdersUseCases, build_orders_use_cases
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.infrastructure.repositories.sqlalchemy_orders_repository import (
    SQLAlchemyOrderRepository,
)
from app.shared.infrastructure.database.engine import AsyncSessionLocal
from app.shared.infrastructure.logging import logger


async def get_order_repository(request: Request) -> AsyncGenerator[OrderRepository, None]:
    repository = request.app.state.order_repository
    if repository is not None:
        logger.debug("Usando repositório fornecido na configuração da aplicação.")
        yield repository
        return

    

    logger.debug("Abrindo sessão de banco para a requisição.")
    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyOrderRepository(session)
        except Exception:
            logger.debug("Revertendo transação após falha no processamento da requisição.")
            await session.rollback()
            raise


def get_orders_use_cases(
    request: Request,
    repository: Annotated[OrderRepository, Depends(get_order_repository)],
) -> OrdersUseCases:
    return build_orders_use_cases(repository)



