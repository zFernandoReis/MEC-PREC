import inspect
import logging
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.modules.quotes.application.use_cases.get_budget import GetBudgetUseCase
from app.modules.quotes.application.use_cases.get_stock import GetStockUseCase
from app.modules.quotes.application.use_cases.list_budget import ListBudgetsUseCase
from app.modules.quotes.application.use_cases.list_stock import ListStocksUseCase
from app.modules.quotes.exceptions import StockNotFoundError
from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.use_cases.get_user import GetUserUseCase
from app.modules.users.application.use_cases.list_users import ListUsersUseCase
from app.shared.infrastructure.logging import LOG_FORMAT, logger


@pytest.fixture
def debug_records(caplog):
    previous_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)
        logger.setLevel(previous_level)


@pytest.mark.parametrize("use_case, identifier, error", [
    (GetUserUseCase, 1, UserNotFoundError),
    (GetBudgetUseCase, 1, UserNotFoundError),
    (GetStockUseCase, "ABC-1234", StockNotFoundError),
])
@pytest.mark.parametrize("found", [True, False])
async def test_lookup_logs_real_source_and_result(
    debug_records, use_case, identifier, error, found
):
    entity = object() if found else None
    repository = AsyncMock()
    repository.get_by_id.return_value = entity
    if found:
        assert await use_case(repository).execute(identifier) is entity
    else:
        with pytest.raises(error):
            await use_case(repository).execute(identifier)

    source = Path(inspect.getfile(use_case))
    records = [record for record in debug_records.records if record.pathname == str(source)]
    assert len(records) == 2
    lines = source.read_text(encoding="utf-8").splitlines()
    for record in records:
        assert record.levelno == logging.DEBUG
        assert record.funcName == "execute"
        assert "logger.debug(" in lines[record.lineno - 1]
        formatted = logging.Formatter(LOG_FORMAT).format(record)
        assert f"arquivo={source.name}" in formatted
        assert f"linha={record.lineno}" in formatted
        assert "metodo=execute" in formatted
        assert str(identifier) in record.getMessage()
    assert ("não encontrado" in records[-1].getMessage()) is (not found)


@pytest.mark.parametrize("use_case", [ListUsersUseCase, ListBudgetsUseCase, ListStocksUseCase])
async def test_list_logs_pagination_and_count_without_entity_data(debug_records, use_case):
    repository = AsyncMock()
    repository.list.return_value = ["conteúdo privado"]
    assert await use_case(repository).execute(offset=2, limit=5) == ["conteúdo privado"]
    repository.list.assert_awaited_once_with(offset=2, limit=5)
    messages = "\n".join(record.getMessage() for record in debug_records.records)
    assert "offset=2, limit=5" in messages
    assert "quantidade=1" in messages
    assert "conteúdo privado" not in messages
