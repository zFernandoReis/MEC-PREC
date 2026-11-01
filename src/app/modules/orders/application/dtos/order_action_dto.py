from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class OrderActionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1, strict=True)


class RequestApprovalDTO(OrderActionDTO):
    diagnosis: RequiredText


class ApproveOrderDTO(OrderActionDTO):
    # Required for staff recording consent obtained outside the application.
    evidence: RequiredText | None = None


class FinishOrderDTO(OrderActionDTO):
    service_report: RequiredText


class DeliverOrderDTO(OrderActionDTO):
    received_by: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
