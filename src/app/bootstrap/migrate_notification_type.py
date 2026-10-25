"""Adiciona o tipo de notificação a uma tabela PostgreSQL existente."""

import asyncio

from sqlalchemy import text

from app.config import settings
from app.shared.infrastructure.database.engine import engine
from app.shared.infrastructure.logging import configure_logging, logger


async def migrate() -> None:
    try:
        async with engine.begin() as connection:
            await connection.execute(text(
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS "
                "notification_type VARCHAR(30) NOT NULL DEFAULT 'upcoming'"
            ))
        logger.info("Tipo de notificação verificado/criado com sucesso.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    configure_logging(settings.LOG_LEVEL)
    asyncio.run(migrate())
