from dataclasses import replace

from app.modules.users.application.ports.address_provider import (
    AddressProvider,
)
from app.modules.users.domain.value_objects.address import Address
from app.shared.infrastructure.logging import logger


class AddressService:

    def __init__(self, provider: AddressProvider):
        self.provider = provider

    async def get_address(
        self,
        cep: str,
        number: str | None = None,
        complement: str | None = None,
    ) -> Address:

        logger.debug("Resolvendo endereço pelo provedor de CEP.")
        address = await self.provider.get_address(cep)
        logger.debug("Endereço resolvido; aplicando número e complemento informados.")

        return replace(
            address,
            number=number,
            complement=(
                complement
                if complement is not None
                else address.complement
            ),
        )
