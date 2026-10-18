from app.modules.users.application.exceptions import (
    VehicleNotFoundError,
)
from app.modules.users.domain.entities.vehicles import Vehicle
from app.shared.infrastructure.logging import logger


class GetVehicleUseCase:
    def __init__(self, vehicle_repository):
        self.vehicle_repository = vehicle_repository

    async def execute(self, vehicle_id: int) -> Vehicle:
        logger.debug("Consultando veículo: vehicle_id=%s", vehicle_id)
        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)
        if vehicle is None:
            logger.debug("Veículo não encontrado: vehicle_id=%s", vehicle_id)
            raise VehicleNotFoundError()
        logger.debug("Veículo encontrado: vehicle_id=%s", vehicle_id)
        return vehicle
