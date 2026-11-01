from app.modules.users.application.dtos.vehicle_dto import CreateVehicleDTO
from app.modules.users.domain.entities.vehicles import Vehicle
from app.shared.infrastructure.logging import logger


class CreateVehicleUseCase:

    def __init__(
        self,
        vehicle_repository,
    ):
        self.vehicle_repository = vehicle_repository


    async def execute(self, dto: CreateVehicleDTO):
        logger.debug("Iniciando criação de veículo.")

        vehicle = Vehicle(
            owner_id=dto.owner_id,
            vehicle_type=dto.vehicle_type,
            brand=dto.brand,
            model=dto.model,
            year_manufacture=dto.year_manufacture,
            year_model=dto.year_model,
            license_plate=dto.license_plate,
            color=dto.color,
            mileage=dto.mileage,
            fuel_type=dto.fuel_type,
            chassis=dto.chassis,
            engine_capacity=dto.engine_capacity
        )

        logger.debug("Persistindo novo veículo.")
        await self.vehicle_repository.save(vehicle)
        logger.debug("Veículo criado: vehicle_id=%s", vehicle.vehicle_id)

        return vehicle
