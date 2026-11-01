from datetime import datetime, timezone

from app.modules.orders.application.dtos.order_action_dto import OrderActionDTO
from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.domain.entities.order_event import OrderEvent
from app.modules.orders.domain.entities.order_workflow import (
    OrderConflictError, OrderPermissionError, allowed_actions, can_perform, validate_transition,
    validate_relationships,
)
from app.modules.orders.domain.enums.order_action import OrderAction as Action


class OrderWorkflowUseCase:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    @staticmethod
    def check_scope(order, actor_id: int, role: str):
        if order is None or (role == "client" and order.client_id != actor_id):
            raise OrderNotFoundError()

    async def execute(self, order_id: int, action: Action, dto: OrderActionDTO, *, actor_id: int, role: str):
        order = await self.repository.get_for_update(order_id)
        self.check_scope(order, actor_id, role)
        if not can_perform(order, action, actor_id, role):
            raise OrderPermissionError("Usuário sem permissão para esta ação")
        if order.version != dto.expected_version:
            raise OrderConflictError("A OS foi alterada; consulte a versão atual", "stale_order_version")
        target = validate_transition(order, action)
        details = dto.model_dump(exclude={"expected_version"}, exclude_none=True)
        if action == Action.APPROVE and role != "client" and not details.get("evidence"):
            raise OrderConflictError("Informe a evidência da aprovação do cliente", "approval_evidence_required")
        if action in {Action.START_DIAGNOSIS, Action.REQUEST_APPROVAL, Action.APPROVE, Action.START_EXECUTION}:
            context = await self.repository.prepare_budget(order)
            snapshot = validate_relationships(order, context)
            if action in {Action.APPROVE, Action.START_EXECUTION} and snapshot != order.budget_snapshot:
                raise OrderConflictError("O orçamento difere do solicitado para aprovação", "budget_changed")
            if action == Action.REQUEST_APPROVAL:
                order.budget_snapshot = snapshot
                details["budget_snapshot"] = snapshot
        now = datetime.now(timezone.utc)
        if action == Action.APPROVE:
            order.approved_at = now
            order.approved_by = actor_id
            details["client_id"] = order.client_id
            details["approval_source"] = "client" if role == "client" else "staff_recorded"
        elif action == Action.START_EXECUTION:
            order.execution_started_at = now
        elif action == Action.FINISH:
            order.finished_at = now
        elif action == Action.DELIVER:
            order.delivered_at = now
        previous = order.order_status
        order.order_status = target
        order.version += 1
        event = OrderEvent(
            order_id=order_id, action=action.value, previous_status=previous.value,
            next_status=target.value, version=order.version, actor_id=actor_id,
            occurred_at=now, details=details,
        )
        return await self.repository.save_action(order, event, dto.expected_version)

    async def actions(self, order_id: int, *, actor_id: int, role: str):
        order = await self.repository.get_by_id(order_id)
        self.check_scope(order, actor_id, role)
        return {"order_id": order_id, "order_status": order.order_status, "version": order.version,
                "allowed_actions": allowed_actions(order, actor_id, role)}

    async def history(self, order_id: int, *, actor_id: int, role: str, offset: int, limit: int):
        order = await self.repository.get_by_id(order_id)
        self.check_scope(order, actor_id, role)
        events = await self.repository.history(order_id, offset=offset, limit=limit)
        if role == "client":
            # Internal evidence/reports and staff identities are not exposed to clients.
            return [{"event_id": e.event_id, "order_id": e.order_id, "action": e.action,
                     "previous_status": e.previous_status, "next_status": e.next_status,
                     "version": e.version, "occurred_at": e.occurred_at} for e in events]
        return events
