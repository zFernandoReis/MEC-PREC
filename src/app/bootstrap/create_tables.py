import asyncio

from app.modules.users.infrastructure.models.client_model import ClientModel
from app.shared.infrastructure.database.engine import engine


async def create_tables() -> None:
    """Cria a tabela cliente e seu enum quando ainda não existem."""
    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                lambda sync_connection: ClientModel.__table__.create(
                    sync_connection, checkfirst=True
                )
            )
        print("Tabela cliente verificada/criada com sucesso.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
