from typing import Protocol

from app.modules.users.domain.value_objects.address import Address


class AddressProvider(Protocol):
    async def get_address(self, cep: str) -> Address:
        ...