from app.modules.users.application.dtos.vehicle_dto import UpdateVehicleDTO
from app.modules.users.application.exceptions import VehicleNotFoundError
from app.shared.infrastructure.logging import logger


class UpdateVehicleUseCase:

    def __init__(
        self,
        vehicle_repository,

    ):
        self.vehicle_repository = vehicle_repository

    async def execute(self, vehicle_id: int, dto: UpdateVehicleDTO):
        logger.debug("Buscando veículo para atualização: vehicle_id=%s", vehicle_id)

        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)

        if vehicle is None:
            logger.debug("Veículo não encontrado para atualização: vehicle_id=%s", vehicle_id)
            raise VehicleNotFoundError()


        for field in ("vehicle_type", "brand", "model", "year_manufacture", "year_model", "license_plate", "color", "mileage", "fuel_type", "chassis", "engine_capacity"):
            value = getattr(dto, field)
            if value is not None:
                setattr(vehicle, field, value)

        logger.debug("Persistindo alterações do veículo: vehicle_id=%s", vehicle_id)
        await self.vehicle_repository.update(vehicle)
        logger.debug("Veículo atualizado: vehicle_id=%s", vehicle_id)

        return vehicle


