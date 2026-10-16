from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.database.engine import AsyncSessionLocal
from app.shared.infrastructure.logging import logger


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    logger.debug("Abrindo sessão compartilhada de banco de dados.")
    async with AsyncSessionLocal() as session:
        yield session
    logger.debug("Sessão compartilhada de banco de dados encerrada.")
