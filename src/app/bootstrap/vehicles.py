from dataclasses import dataclass

from app.modules.users.application.ports.vehicle_repository import VehicleRepository
from app.modules.users.application.use_cases.create_vehicle import CreateVehicleUseCase
from app.modules.users.application.use_cases.delete_vehicle import DeleteVehicleUseCase
from app.modules.users.application.use_cases.get_vehicle import GetVehicleUseCase
from app.modules.users.application.use_cases.list_vehicles import ListVehiclesUseCase
from app.modules.users.application.use_cases.update_vehicle import UpdateVehicleUseCase
from app.shared.infrastructure.logging import logger


@dataclass(frozen=True)
class VehiclesUseCases:
    create_vehicle: CreateVehicleUseCase
    get_vehicle: GetVehicleUseCase
    list_vehicles: ListVehiclesUseCase
    update_vehicle: UpdateVehicleUseCase
    delete_vehicle: DeleteVehicleUseCase


def build_vehicles_use_cases(vehicle_repository: VehicleRepository
) -> VehiclesUseCases:
    logger.debug("Montando dependências e casos de uso de veículos.")
    return VehiclesUseCases(
        create_vehicle=CreateVehicleUseCase(vehicle_repository),
        get_vehicle=GetVehicleUseCase(vehicle_repository),
        list_vehicles=ListVehiclesUseCase(vehicle_repository),
        update_vehicle=UpdateVehicleUseCase(vehicle_repository),
        delete_vehicle=DeleteVehicleUseCase(vehicle_repository),
    )
