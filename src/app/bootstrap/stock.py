from dataclasses import dataclass

from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.application.use_cases.create_stock import CreateStockUseCase
from app.modules.quotes.application.use_cases.delete_stock import DeleteStockUseCase
from app.modules.quotes.application.use_cases.get_stock import GetStockUseCase
from app.modules.quotes.application.use_cases.list_stock import ListStocksUseCase
from app.modules.quotes.application.use_cases.update_stock import UpdateStockUseCase


@dataclass(frozen=True)
class StockUseCases:
    create_stock: CreateStockUseCase
    get_stock: GetStockUseCase
    list_stocks: ListStocksUseCase
    update_stock: UpdateStockUseCase
    delete_stock: DeleteStockUseCase


def build_stock_use_cases(
    stock_repository: StockRepository
) -> StockUseCases:
    return StockUseCases(
        create_stock=CreateStockUseCase(stock_repository),
        get_stock=GetStockUseCase(stock_repository),
        list_stocks=ListStocksUseCase(stock_repository),
        update_stock=UpdateStockUseCase(stock_repository),
        delete_stock=DeleteStockUseCase(stock_repository),
    )
