from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.bootstrap.orders import OrdersUseCases
from app.modules.orders.application.dtos.order_dto import CreateOrderDTO, UpdateOrderDTO
from app.modules.orders.infrastructure.http.dependencies import get_orders_use_cases
from app.modules.orders.infrastructure.http.schemas import OrdersReadResponse
from app.shared.infrastructure.logging import logger

router = APIRouter(prefix="/orders", tags=["Orders"])
UseCases = Annotated[OrdersUseCases, Depends(get_orders_use_cases)]
OrderId = Annotated[int, Path(ge=1)]


@router.post("", response_model=OrdersReadResponse, status_code=status.HTTP_201_CREATED)
async def create_order(dto: CreateOrderDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para criar pedido.")
    return await use_cases.create_order.execute(dto)


@router.get("", response_model=list[OrdersReadResponse])
async def list_orders(
    use_cases: UseCases,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    logger.debug("Recebida listagem HTTP de pedidos: offset=%s, limit=%s", offset, limit)
    return await use_cases.list_orders.execute(offset=offset, limit=limit)


@router.get("/{order_id}", response_model=OrdersReadResponse)
async def get_order(order_id: OrderId, use_cases: UseCases):
    logger.debug("Recebida consulta HTTP de pedido: order_id=%s", order_id)
    return await use_cases.get_order.execute(order_id)


@router.patch("/{order_id}", response_model=OrdersReadResponse)
async def update_order(order_id: OrderId, dto: UpdateOrderDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para atualizar pedido: order_id=%s", order_id)
    return await use_cases.update_order.execute(order_id, dto)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: OrderId, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para excluir pedido: order_id=%s", order_id)
    await use_cases.delete_order.execute(order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
