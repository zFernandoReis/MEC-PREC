from app.modules.users.application.exceptions import UserNotFoundError
from app.shared.infrastructure.logging import logger


class DeleteUserUseCase:

    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> None:
        logger.debug("Buscando usuário para exclusão: user_id=%s", user_id)
        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            logger.debug("Usuário não encontrado para exclusão: user_id=%s", user_id)
            raise UserNotFoundError()

        await self.user_repository.delete(user)
        logger.debug("Usuário excluído: user_id=%s", user_id)
