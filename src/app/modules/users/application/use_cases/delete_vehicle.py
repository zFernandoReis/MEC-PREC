from app.modules.users.application.exceptions import VehicleNotFoundError
from app.shared.infrastructure.logging import logger


class DeleteVehicleUseCase:

    def __init__(self, vehicle_repository):
        self.vehicle_repository = vehicle_repository

    async def execute(self, vehicle_id: int) -> None:
        logger.debug("Buscando veículo para exclusão: vehicle_id=%s", vehicle_id)
        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)

        if vehicle is None:
            logger.debug("Veículo não encontrado para exclusão: vehicle_id=%s", vehicle_id)
            raise VehicleNotFoundError()

        await self.vehicle_repository.delete(vehicle)
        logger.debug("Veículo excluído: vehicle_id=%s", vehicle_id)
