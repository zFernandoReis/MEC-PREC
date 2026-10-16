from app.modules.users.application.exceptions import UserNotFoundError


class DeleteStockUseCase:

    def __init__(self, stock_repository):
        self.stock_repository = stock_repository

    async def execute(self, stock_id: int) -> None:
        stock = await self.stock_repository.get_by_id(stock_id)

        if stock is None:
            raise UserNotFoundError()

        await self.stock_repository.delete(stock)
