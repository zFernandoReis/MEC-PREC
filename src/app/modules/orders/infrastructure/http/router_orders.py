from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.bootstrap.orders import OrdersUseCases
from app.modules.orders.application.dtos.order_action_dto import (
    ApproveOrderDTO,
    DeliverOrderDTO,
    FinishOrderDTO,
    OrderActionDTO,
    RequestApprovalDTO,
)
from app.modules.orders.application.dtos.order_dto import CreateOrderDTO, UpdateOrderDTO
from app.modules.orders.domain.enums.order_action import OrderAction
from app.modules.orders.infrastructure.http.dependencies import get_orders_use_cases
from app.modules.orders.infrastructure.http.schemas import (
    OrderActionsResponse,
    OrderHistoryResponse,
    OrdersReadResponse,
)
from app.modules.users.domain.enums.user_role import UserRole
from app.shared.infrastructure.logging import logger
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


@router.post("/{order_id}/start-diagnosis", response_model=OrdersReadResponse)
async def start_diagnosis(order_id: OrderId, dto: OrderActionDTO, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.execute(order_id, OrderAction.START_DIAGNOSIS, dto,
                                           actor_id=current.user.id, role=current.user.role)


@router.post("/{order_id}/request-approval", response_model=OrdersReadResponse)
async def request_approval(order_id: OrderId, dto: RequestApprovalDTO, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.execute(order_id, OrderAction.REQUEST_APPROVAL, dto,
                                           actor_id=current.user.id, role=current.user.role)


@router.post("/{order_id}/approve", response_model=OrdersReadResponse)
async def approve_order(order_id: OrderId, dto: ApproveOrderDTO, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.execute(order_id, OrderAction.APPROVE, dto,
                                           actor_id=current.user.id, role=current.user.role)


@router.post("/{order_id}/start-execution", response_model=OrdersReadResponse)
async def start_execution(order_id: OrderId, dto: OrderActionDTO, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.execute(order_id, OrderAction.START_EXECUTION, dto,
                                           actor_id=current.user.id, role=current.user.role)


@router.post("/{order_id}/finish", response_model=OrdersReadResponse)
async def finish_order(order_id: OrderId, dto: FinishOrderDTO, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.execute(order_id, OrderAction.FINISH, dto,
                                           actor_id=current.user.id, role=current.user.role)


@router.post("/{order_id}/deliver", response_model=OrdersReadResponse)
async def deliver_order(order_id: OrderId, dto: DeliverOrderDTO, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.execute(order_id, OrderAction.DELIVER, dto,
                                           actor_id=current.user.id, role=current.user.role)


@router.get("/{order_id}/allowed-actions", response_model=OrderActionsResponse)
async def get_allowed_actions(order_id: OrderId, use_cases: UseCases, current: CurrentUser):
    return await use_cases.workflow.actions(order_id, actor_id=current.user.id, role=current.user.role)


@router.get("/{order_id}/history", response_model=list[OrderHistoryResponse], response_model_exclude_none=True)
async def get_order_history(
    order_id: OrderId, use_cases: UseCases, current: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return await use_cases.workflow.history(order_id, actor_id=current.user.id, role=current.user.role,
                                           offset=offset, limit=limit)
