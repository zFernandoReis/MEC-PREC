from types import SimpleNamespace

import pytest

from app.modules.orders.domain.entities.order_workflow import OrderConflictError, validate_transition
from app.modules.orders.domain.enums.order_action import OrderAction
from app.modules.orders.domain.enums.order_status import OrderStatus


@pytest.mark.parametrize("source", list(OrderStatus))
@pytest.mark.parametrize("action", list(OrderAction))
def test_all_status_action_combinations(source, action):
    expected = {
        OrderAction.START_DIAGNOSIS: (OrderStatus.RECEBIDA, OrderStatus.EM_DIAGNOSTICO),
        OrderAction.REQUEST_APPROVAL: (OrderStatus.EM_DIAGNOSTICO, OrderStatus.AGUARDANDO_APROVACAO),
        OrderAction.APPROVE: (OrderStatus.AGUARDANDO_APROVACAO, OrderStatus.AGUARDANDO_APROVACAO),
        OrderAction.START_EXECUTION: (OrderStatus.AGUARDANDO_APROVACAO, OrderStatus.EM_EXECUCAO),
        OrderAction.FINISH: (OrderStatus.EM_EXECUCAO, OrderStatus.FINALIZADA),
        OrderAction.DELIVER: (OrderStatus.FINALIZADA, OrderStatus.ENTREGUE),
    }
    order = SimpleNamespace(order_status=source, budget_snapshot={"budget_id": 1},
                            approved_at=None if action == OrderAction.APPROVE else "approved")
    origin, target = expected[action]
    if source == origin:
        assert validate_transition(order, action) == target
    else:
        with pytest.raises(OrderConflictError):
            validate_transition(order, action)
    assert order.order_status == source
