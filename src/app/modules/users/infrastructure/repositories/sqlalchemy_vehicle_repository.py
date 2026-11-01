from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.application.exceptions import (
    VehicleNotFoundError,
)
from app.modules.users.domain.entities.vehicles import Vehicle
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
from app.shared.infrastructure.logging import logger


class SQLAlchemyVehicleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, vehicle: Vehicle) -> None:
        logger.debug("Inserindo veículo no banco de dados.")
        model = VehicleModel.from_entity(vehicle)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        logger.debug("Inserção de veículo concluída: vehicle_id=%s", model.vehicle_id)
        vehicle.vehicle_id = model.vehicle_id
        vehicle.create_at = model.create_at
        vehicle.update_at = model.update_at
        vehicle.system_id = model.system_id


    async def get_by_id(self, vehicle_id: int) -> Vehicle | None:
        logger.debug("Consultando veículo no banco: vehicle_id=%s", vehicle_id)
        model = await self.session.get(VehicleModel, vehicle_id)
        logger.debug("Consulta de veículo concluída: encontrado=%s", model is not None)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int) -> list[Vehicle]:
        logger.debug("Consultando página de veículo no banco: offset=%s, limit=%s", offset, limit)
        result = await self.session.scalars(
            select(VehicleModel).order_by(VehicleModel.vehicle_id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, vehicle: Vehicle) -> None:
        logger.debug("Atualizando veículo no banco: vehicle_id=%s", vehicle.vehicle_id)
        model = await self.session.get(VehicleModel, vehicle.vehicle_id)
        if model is None:
            logger.debug("Vehicle não encontrado no banco: vehicle_id=%s", vehicle.vehicle_id)
            raise VehicleNotFoundError()
        model.vehicle_type = vehicle.vehicle_type
        model.brand = vehicle.brand
        model.model = vehicle.model
        model.year_manufacture = vehicle.year_manufacture
        model.year_model = vehicle.year_model
        model.license_plate = vehicle.license_plate
        model.color = vehicle.color
        model.mileage = vehicle.mileage
        model.fuel_type = vehicle.fuel_type
        model.chassis = vehicle.chassis
        model.engine_capacity = vehicle.engine_capacity
        await self.session.commit()
        await self.session.refresh(model)
        vehicle.create_at = model.create_at
        vehicle.update_at = model.update_at
        logger.debug("Atualização de veículo confirmada no banco: vehicle_id=%s", vehicle.vehicle_id)

    async def delete(self, vehicle: Vehicle) -> None:
        logger.debug("Excluindo veículo no banco: vehicle_id=%s", vehicle.vehicle_id)
        model = await self.session.get(VehicleModel, vehicle.vehicle_id)
        if model is None:
            logger.debug("Vehicle não encontrado no banco: vehicle_id=%s", vehicle.vehicle_id)
            raise VehicleNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
        logger.debug("Exclusão de veículo confirmada no banco: vehicle_id=%s", vehicle.vehicle_id)
