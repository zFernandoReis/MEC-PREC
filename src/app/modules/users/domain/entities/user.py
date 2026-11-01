from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.domain.value_objects.address import Address


@dataclass
class User:
    id: int | None
    primary_name: str
    secondary_name: str
    cpf: str
    email: str
    role: UserRole
    adress: Address
    system_id: UUID = field(default_factory=uuid4)
    create_at: datetime | None = None
    update_at: datetime | None = None
    password_hash: str | None = field(default=None, repr=False)
    token_version: int = field(default=0, repr=False)

    def __post_init__(self):
        self.validate_email(self.email)
        self.validate_cpf(self.cpf)

    @staticmethod
    def validate_email(email: str):
        if "@" not in email:
            raise ValueError("Email inválido")

    @staticmethod
    def validate_cpf(cpf: str):
        if not isinstance(cpf, str):
            raise ValueError("CPF deve ser uma string")

        if len(cpf) != 11 or not cpf.isascii() or not cpf.isdecimal():
            raise ValueError("CPF deve conter exatamente 11 números")

        if len(set(cpf)) == 1:
            raise ValueError("CPF inválido")

        for position in (9, 10):
            total = sum(
                int(cpf[i]) * (position + 1 - i)
                for i in range(position)
            )

            remainder = (total * 10) % 11
            digit = 0 if remainder == 10 else remainder

            if digit != int(cpf[position]):
                raise ValueError("CPF inválido")

    def change_email(self, email: str):
        self.validate_email(email)
        self.email = email

    def change_address(self, address: Address):
        self.adress = address

    def change_cpf(self, cpf: str):
        self.validate_cpf(cpf)
        self.cpf = cpf
