from dataclasses import replace

from app.modules.users.application.ports.address_provider import (
    AddressProvider,
)
from app.modules.users.domain.value_objects.address import Address


class AddressService:

    def __init__(self, provider: AddressProvider):
        self.provider = provider

    async def get_address(
        self,
        cep: str,
        number: str | None = None,
        complement: str | None = None,
    ) -> Address:

        address = await self.provider.get_address(cep)

        return replace(
            address,
            number=number,
            complement=(
                complement
                if complement is not None
                else address.complement
            ),
        )