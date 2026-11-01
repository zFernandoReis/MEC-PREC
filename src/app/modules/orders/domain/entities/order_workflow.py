from app.modules.orders.domain.enums.order_action import OrderAction as Action
from app.modules.orders.domain.enums.order_status import OrderStatus as Status
from dataclasses import dataclass

class OrderConflictError(Exception):
    def __init__(self, message: str, code: str = "invalid_order_transition"):
        super().__init__(message)
        self.code = code


class OrderPermissionError(Exception):
    pass


@dataclass(frozen=True)
class OrderContext:
    budget: dict | None
    vehicle_owner_id: int | None
    responsible_role: str | None


def validate_relationships(order, context: OrderContext) -> dict:
    budget = context.budget
    if (budget is None or budget["client_id"] != order.client_id
            or budget["vehicle_id"] != order.vehicle_id or context.vehicle_owner_id != order.client_id):
        raise OrderConflictError("Cliente, veículo e orçamento da OS são incompatíveis", "invalid_order_relationships")
    if context.responsible_role not in {"technical", "admin", "manager"}:
        raise OrderConflictError("Responsável técnico inválido", "invalid_technician")
    return budget


TRANSITIONS = {
    Action.START_DIAGNOSIS: (Status.RECEBIDA, Status.EM_DIAGNOSTICO),
    Action.REQUEST_APPROVAL: (Status.EM_DIAGNOSTICO, Status.AGUARDANDO_APROVACAO),
    Action.APPROVE: (Status.AGUARDANDO_APROVACAO, Status.AGUARDANDO_APROVACAO),
    Action.START_EXECUTION: (Status.AGUARDANDO_APROVACAO, Status.EM_EXECUCAO),
    Action.FINISH: (Status.EM_EXECUCAO, Status.FINALIZADA),
    Action.DELIVER: (Status.FINALIZADA, Status.ENTREGUE),
}


def can_perform(order, action: Action, actor_id: int, role: str) -> bool:
    if role in {"admin", "manager"}:
        return True
    if role == "client":
        return action == Action.APPROVE and order.client_id == actor_id
    return (
        role == "technical" and order.technical_responser_id == actor_id
        and action not in {Action.APPROVE, Action.DELIVER}
    )


def validate_transition(order, action: Action) -> Status:
    source, target = TRANSITIONS[action]
    if order.order_status != source:
        raise OrderConflictError(f"A ação {action} não é permitida no status {order.order_status}")
    if action == Action.APPROVE and order.approved_at is not None:
        raise OrderConflictError("A aprovação já foi registrada", "already_approved")
    if action in {Action.APPROVE, Action.START_EXECUTION} and not order.budget_snapshot:
        raise OrderConflictError("Solicite aprovação de um orçamento antes desta ação", "missing_budget_snapshot")
    if action == Action.START_EXECUTION and order.approved_at is None:
        raise OrderConflictError("O orçamento ainda não foi aprovado", "approval_required")
    return target


def allowed_actions(order, actor_id: int, role: str) -> list[Action]:
    actions = []
    for action in Action:
        if not can_perform(order, action, actor_id, role):
            continue
        try:
            validate_transition(order, action)
        except OrderConflictError:
            continue
        actions.append(action)
    return actions


def require_editable(order) -> None:
    if order.order_status not in {Status.RECEBIDA, Status.EM_DIAGNOSTICO}:
        raise OrderConflictError("A OS não permite edição após a solicitação de aprovação", "order_locked")
from dataclasses import dataclass

