from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.entities.user import User


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return user
