import httpx

from app.config import settings
from app.modules.users.domain.value_objects.address import Address
from app.shared.infrastructure.logging import logger


class ViaCepClient:

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_address(self, cep: str) -> Address:
        logger.debug("Validando formato do CEP antes de consultar ViaCEP.")
        if len(cep) != 8 or not cep.isascii() or not cep.isdecimal():
            logger.debug("Consulta ao ViaCEP interrompida: formato de CEP inválido.")
            raise ValueError("CEP deve conter exatamente 8 números")

        logger.debug("Consultando endereço no ViaCEP.")
        response = await self.client.get(
            settings.viacep_url(cep)
        )

        logger.debug("Resposta recebida do ViaCEP: status=%s", response.status_code)
        response.raise_for_status()

        data = response.json()

        if data.get("erro"):
            logger.debug("ViaCEP não encontrou o endereço solicitado.")
            raise ValueError("CEP não encontrado")

        logger.debug("Convertendo resposta do ViaCEP em endereço.")
        return Address(
            cep=data["cep"].replace("-", ""),
            street=data["logradouro"],
            neighborhood=data["bairro"],
            city=data["localidade"],
            state=data["uf"],
            complement=data.get("complemento") or None,
        )
