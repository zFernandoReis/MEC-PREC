from app.modules.users.application.exceptions import UserNotFoundError


class DeleteUserUseCase:

    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> None:
        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError()

        await self.user_repository.delete(user)
