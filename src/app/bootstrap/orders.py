from dataclasses import dataclass

from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.application.use_cases.create_order import CreateOrderUseCase
from app.modules.orders.application.use_cases.delete_order import DeleteOrderUseCase
from app.modules.orders.application.use_cases.get_order import GetOrderUseCase
from app.modules.orders.application.use_cases.list_order import ListOrdersUseCase
from app.modules.orders.application.use_cases.update_order import UpdateOrderUseCase
from app.shared.infrastructure.logging import logger


@dataclass(frozen=True)
class OrdersUseCases:
    create_order: CreateOrderUseCase
    get_order: GetOrderUseCase
    list_orders: ListOrdersUseCase
    update_order: UpdateOrderUseCase
    delete_order: DeleteOrderUseCase


def build_orders_use_cases(
   order_repository: OrderRepository
) -> OrdersUseCases:
    logger.debug("Montando dependências e casos de uso de ordens.")

    return OrdersUseCases(
        create_order=CreateOrderUseCase(order_repository),
        get_order=GetOrderUseCase(order_repository),
        list_orders=ListOrdersUseCase(order_repository),
        update_order=UpdateOrderUseCase(order_repository),
        delete_order=DeleteOrderUseCase(order_repository),
    )
