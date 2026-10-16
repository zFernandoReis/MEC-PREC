from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.entities.user import User
from app.shared.infrastructure.logging import logger


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        logger.debug("Listando usuários: offset=%s, limit=%s", offset, limit)
        users = await self.user_repository.list(offset=offset, limit=limit)
        logger.debug("Listagem de usuários concluída: quantidade=%s", len(users))
        return users
