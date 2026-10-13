import httpx

from app.config import settings
from app.modules.users.domain.value_objects.address import Address


class ViaCepClient:

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_address(self, cep: str) -> Address:
        if len(cep) != 8 or not cep.isascii() or not cep.isdecimal():
            raise ValueError("CEP deve conter exatamente 8 números")

        response = await self.client.get(
            settings.viacep_url(cep)
        )

        response.raise_for_status()

        data = response.json()

        if data.get("erro"):
            raise ValueError("CEP não encontrado")

        return Address(
            cep=data["cep"].replace("-", ""),
            street=data["logradouro"],
            neighborhood=data["bairro"],
            city=data["localidade"],
            state=data["uf"],
            complement=data.get("complemento") or None,
        )