from unittest.mock import AsyncMock, Mock

import pytest

from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.application.use_cases.get_user import GetUserUseCase
from app.modules.users.domain.entities.user import User


@pytest.mark.asyncio
async def test_get_by_cpf_returns_user():
    user = Mock(spec=User, id=1)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_cpf.return_value = user
    use_case = GetUserUseCase(repository)

    result = await use_case.get_by_cpf("52998224725")

    assert result is user
    repository.get_by_cpf.assert_awaited_once_with("52998224725")


@pytest.mark.asyncio
async def test_get_by_cpf_raises_when_user_is_missing():
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_cpf.return_value = None
    use_case = GetUserUseCase(repository)

    with pytest.raises(UserNotFoundError):
        await use_case.get_by_cpf("52998224725")

    repository.get_by_cpf.assert_awaited_once_with("52998224725")
