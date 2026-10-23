import asyncio

from app.config import settings
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.quotes.infrastructure.models.stock_model import StockModel
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
from app.shared.infrastructure.database.base import Base
from app.shared.infrastructure.database.engine import engine
from app.shared.infrastructure.logging import configure_logging, logger


async def create_tables() -> None:
    """Cria as tabelas e enums ausentes respeitando as chaves estrangeiras."""
    logger.debug("Iniciando verificação e criação das tabelas da aplicação.")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                lambda sync_connection: Base.metadata.create_all(
                    sync_connection,
                    tables=[
                        UserModel.__table__,
                        VehicleModel.__table__,
                        BudgetModel.__table__,
                        StockModel.__table__,
                        OrderModel.__table__,
                    ],
                    checkfirst=True,
                )
            )

        logger.debug("Tabelas de usuários, veículos, orçamentos e estoque verificadas/criadas com sucesso.")
    finally:
        logger.debug("Liberando conexões após verificação das tabelas.")
        await engine.dispose()


if __name__ == "__main__":
    configure_logging(settings.LOG_LEVEL)
    asyncio.run(create_tables())
