from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.bootstrap.orders import OrdersUseCases
from app.modules.orders.application.dtos.order_dto import CreateOrderDTO, UpdateOrderDTO
from app.modules.orders.infrastructure.http.dependencies import get_orders_use_cases
from app.modules.orders.infrastructure.http.schemas import OrdersReadResponse
from app.shared.infrastructure.logging import logger
from app.modules.users.domain.enums.user_role import UserRole
from app.shared.infrastructure.security.dependencies import get_current_user
from app.shared.infrastructure.security.service import AuthenticatedUser

CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_order_staff(current: CurrentUser) -> AuthenticatedUser:
    if current.user.role not in {
        UserRole.ADMIN, UserRole.MANAGER, UserRole.TECHNICAL, UserRole.FINANCIAL,
    }:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Clientes não podem modificar ordens de serviço")
    return current

router = APIRouter(prefix="/orders", tags=["Orders"])
UseCases = Annotated[OrdersUseCases, Depends(get_orders_use_cases)]
OrderId = Annotated[int, Path(ge=1)]


@router.post("", response_model=OrdersReadResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_order_staff)])
async def create_order(dto: CreateOrderDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para criar pedido.")
    return await use_cases.create_order.execute(dto)


@router.get("", response_model=list[OrdersReadResponse])
async def list_orders(
    use_cases: UseCases,
    current: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    logger.debug("Recebida listagem HTTP de pedidos: offset=%s, limit=%s", offset, limit)
    client_id = current.user.id if current.user.role == UserRole.CLIENT else None
    return await use_cases.list_orders.execute(offset=offset, limit=limit, client_id=client_id)


@router.get("/{order_id}", response_model=OrdersReadResponse)
async def get_order(order_id: OrderId, use_cases: UseCases, current: CurrentUser):
    logger.debug("Recebida consulta HTTP de pedido: order_id=%s", order_id)
    client_id = current.user.id if current.user.role == UserRole.CLIENT else None
    return await use_cases.get_order.execute(order_id, client_id=client_id)


@router.patch("/{order_id}", response_model=OrdersReadResponse,
              dependencies=[Depends(require_order_staff)])
async def update_order(order_id: OrderId, dto: UpdateOrderDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para atualizar pedido: order_id=%s", order_id)
    return await use_cases.update_order.execute(order_id, dto)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_order_staff)])
async def delete_order(order_id: OrderId, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para excluir pedido: order_id=%s", order_id)
    await use_cases.delete_order.execute(order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
