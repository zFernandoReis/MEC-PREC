"""Carga inicial transacional, pelas rotas internas, antes de publicar a API."""

import asyncio
import os
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.ingest_json import IngestionError, RESOURCES, load_records
from app.config import settings
from app.main import create_app
from app.modules.quotes.infrastructure.repositories.sqlalchemy_budget_repository import SQLAlchemyBudgetRepository
from app.modules.quotes.infrastructure.repositories.sqlalchemy_stock_repository import SQLAlchemyStockRepository
from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.modules.users.infrastructure.repositories.sqlalchemy_vehicle_repository import SQLAlchemyVehicleRepository
from app.shared.infrastructure.database.engine import engine
from app.shared.infrastructure.logging import configure_logging, logger
from app.shared.infrastructure.security.dependencies import get_current_user, require_admin


SEED_NAME = "initial_dados_v1"


async def import_records(client: httpx.AsyncClient, records: dict[str, list[dict]]) -> int:
    user_ids = {}
    vehicle_ids = {}
    stock_ids = {}
    count = 0
    for resource in RESOURCES:
        for index, record in enumerate(records.get(resource, []), start=1):
            payload = dict(record)
            for field in {
                "vehicles": ("owner_id",), "budgets": ("technical_id", "client_id"),
            }.get(resource, ()):
                payload[field] = user_ids[payload[field]]
            if resource == "budgets":
                payload["vehicle_id"] = vehicle_ids[payload["vehicle_id"]]
                if payload.get("tools") is not None:
                    payload["tools"] = [
                        {**tool, "tool_id": stock_ids[tool["tool_id"]]}
                        if tool.get("tool_id", "").startswith("__seed_stock_position__:") else dict(tool)
                        for tool in payload["tools"]
                    ]
            response = await client.post(f"/{resource}", json=payload)
            if response.status_code != 201:
                raise IngestionError(
                    f"{resource}.json, registro {index}: HTTP {response.status_code}; "
                    "a carga inicial será revertida."
                )
            if resource == "users":
                user_ids[index] = response.json()["id"]
            elif resource == "vehicles":
                vehicle_ids[index] = response.json()["vehicle_id"]
            elif resource == "stock":
                stock_ids[f"__seed_stock_position__:{index}"] = response.json()["tool_id"]
            count += 1
        logger.info("Carga inicial: resource=%s, records=%s", resource, len(records.get(resource, [])))
    return count


async def seed(data_dir: Path) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(
            "CREATE TABLE IF NOT EXISTS bootstrap_ingestions ("
            "name VARCHAR(100) PRIMARY KEY, completed_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        ))
    async with engine.begin() as connection:
        # Coordena inicializações simultâneas; o marcador e os dados são
        # confirmados juntos, somente após todas as rotas terem sucesso.
        await connection.execute(text("SELECT pg_advisory_xact_lock(734216890)"))
        completed = await connection.scalar(text(
            "SELECT name FROM bootstrap_ingestions WHERE name = :name"
        ), {"name": SEED_NAME})
        if completed:
            logger.info("Carga inicial já concluída; nenhum registro será importado.")
            return
        records = load_records(
            data_dir, list(RESOURCES), user_password=os.environ.get("MEC_INITIAL_PASSWORD") or None,
            resolve_stock_names=True,
        )
        async with AsyncSession(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        ) as session:
            application = create_app(
                user_repository=SQLAlchemyUserRepository(session),
                vehicle_repository=SQLAlchemyVehicleRepository(session),
                stock_repository=SQLAlchemyStockRepository(session),
                budget_repository=SQLAlchemyBudgetRepository(session),
            )
            # Esta instância não abre socket e é descartada após a carga.
            # A API publicada pelo Uvicorn mantém suas dependências normais.
            application.dependency_overrides[get_current_user] = lambda: None
            application.dependency_overrides[require_admin] = lambda: None
            async with application.router.lifespan_context(application):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=application), base_url="http://bootstrap",
                ) as client:
                    created = await import_records(client, records)
        await connection.execute(text(
            "INSERT INTO bootstrap_ingestions (name) VALUES (:name)"
        ), {"name": SEED_NAME})
    logger.info("Carga inicial concluída: records_created=%s", created)


async def main() -> None:
    configure_logging(settings.LOG_LEVEL)
    try:
        await seed(Path(os.environ.get("MEC_DATA_DIR", "/app/dados")))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
