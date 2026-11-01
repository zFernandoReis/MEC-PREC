from enum import StrEnum


class OrderAction(StrEnum):
    START_DIAGNOSIS = "start_diagnosis"
    REQUEST_APPROVAL = "request_approval"
    APPROVE = "approve"
    START_EXECUTION = "start_execution"
    FINISH = "finish"
    DELIVER = "deliver"
