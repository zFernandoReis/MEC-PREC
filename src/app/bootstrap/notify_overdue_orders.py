"""Job independente para avisar sobre ordens atrasadas ainda em execução."""

import argparse
import asyncio

from app.config import settings
from app.modules.orders.infrastructure.jobs.notify_overdue_orders import NotifyOverdueOrdersJob
from app.shared.infrastructure.database.engine import AsyncSessionLocal, engine
from app.shared.infrastructure.logging import configure_logging, logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=100, help="Ordens por transação (padrão: 100).")
    parser.add_argument(
        "--interval-seconds", type=int, default=None,
        help="Repete a varredura neste intervalo; omitido executa uma vez.",
    )
    return parser


async def run(*, batch_size: int, interval_seconds: int | None) -> None:
    try:
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    await NotifyOverdueOrdersJob(session).execute(batch_size=batch_size)
            except Exception:
                logger.exception("Falha na varredura de ordens atrasadas.")
                if interval_seconds is None:
                    raise
            if interval_seconds is None:
                return
            await asyncio.sleep(interval_seconds)
    finally:
        await engine.dispose()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size deve ser >= 1")
    if args.interval_seconds is not None and args.interval_seconds < 1:
        parser.error("--interval-seconds deve ser >= 1")
    configure_logging(settings.LOG_LEVEL)
    try:
        asyncio.run(run(**vars(args)))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
