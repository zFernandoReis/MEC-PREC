from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    cep: str
    street: str
    neighborhood: str
    city: str
    state: str
    number: str | None = None
    complement: str | None = None