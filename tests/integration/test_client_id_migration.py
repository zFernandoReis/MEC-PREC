from uuid import uuid4

import pytest
from sqlalchemy import text

from app.bootstrap.migrate_client_ids import MIGRATION_SQL
from app.shared.infrastructure.database.engine import engine


@pytest.mark.asyncio
async def test_migration_preserves_uuids_and_generates_sequential_ids():
    # Schema exclusivo dentro de uma transação sempre desfeita.
    schema = "test_client_migration_" + uuid4().hex
    original_ids = [uuid4(), uuid4()]
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            await connection.execute(text("CREATE TABLE cliente (id uuid PRIMARY KEY)"))
            for original_id in original_ids:
                await connection.execute(
                    text("INSERT INTO cliente (id) VALUES (:id)"), {"id": original_id}
                )
            await connection.execute(text(MIGRATION_SQL))
            await connection.execute(text(MIGRATION_SQL))
            rows = (await connection.execute(text(
                "SELECT id, system_id, create_at, update_at FROM cliente ORDER BY id"
            ))).all()
            assert [row.id for row in rows] == [1, 2]
            assert {row.system_id for row in rows} == set(original_ids)
            assert all(row.create_at is not None and row.update_at is not None for row in rows)
            next_id = await connection.scalar(text(
                "INSERT INTO cliente (system_id) VALUES (:uuid) RETURNING id"
            ), {"uuid": uuid4()})
            assert next_id == 3
        finally:
            await transaction.rollback()
