from app.modules.users.domain.entities.vehicles import Vehicle
from app.shared.infrastructure.logging import logger


class ListVehiclesUseCase:
    def __init__(self, vehicle_repository):
        self.vehicle_repository = vehicle_repository

    async def execute(self, *, offset: int = 0, limit: int = 100) -> list[Vehicle]:
        logger.debug("Listando veículos: offset=%s, limit=%s", offset, limit)
        vehicles = await self.vehicle_repository.list(offset=offset, limit=limit)
        logger.debug("Listagem de veículos concluída: quantidade=%s", len(vehicles))
        return vehicles
