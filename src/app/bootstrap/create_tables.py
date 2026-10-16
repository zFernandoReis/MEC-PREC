import asyncio

from app.config import settings
from app.shared.infrastructure.logging import configure_logging, logger

from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.quotes.infrastructure.models.stock_model import StockModel
from app.modules.users.infrastructure.models.users_model import UserModel
from app.shared.infrastructure.database.engine import engine


async def create_tables() -> None:
    """Cria a tabela cliente e seu enum quando ainda não existem."""
    logger.debug("Iniciando verificação e criação das tabelas da aplicação.")
    try:
        async with engine.begin() as connection:
            logger.debug("Verificando tabela de usuários.")
            await connection.run_sync(
                lambda sync_connection: UserModel.__table__.create(
                    sync_connection, checkfirst=True
                )
            )
            logger.debug("Verificando tabela de orçamentos.")
            await connection.run_sync(
                lambda sync_connection: BudgetModel.__table__.create(
                    sync_connection, checkfirst=True
                )
            )
            logger.debug("Verificando tabela de estoque.")
            await connection.run_sync(
                lambda sync_connection: StockModel.__table__.create(
                    sync_connection, checkfirst=True
                )
            )


        logger.debug("Tabelas de usuários, orçamentos e estoque verificadas/criadas com sucesso.")
    finally:
        logger.debug("Liberando conexões após verificação das tabelas.")
        await engine.dispose()


if __name__ == "__main__":
    configure_logging(settings.LOG_LEVEL)
    asyncio.run(create_tables())
