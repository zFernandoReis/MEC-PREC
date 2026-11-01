import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.database.engine import (
    AsyncSessionLocal,
    engine,
)


@pytest.mark.asyncio
async def test_engine_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))

        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_session_creation():
    async with AsyncSessionLocal() as session:

        assert isinstance(session, AsyncSession)

        result = await session.execute(text("SELECT 1"))

        assert result.scalar_one() == 1

@pytest.mark.asyncio
async def test_session_lifecycle():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))

        assert result.scalar_one() == 1

    # Verifica que a sessão encerrou a transação
    assert not session.in_transaction()