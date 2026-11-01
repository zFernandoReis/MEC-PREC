from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.bootstrap.vehicles import VehiclesUseCases
from app.modules.users.application.dtos.vehicle_dto import (
    CreateVehicleDTO,
    UpdateVehicleDTO,
)
from app.modules.users.infrastructure.http.dependencies import get_vehicles_use_cases
from app.modules.users.infrastructure.http.schemas import (
    VehicleReadResponse,
    VehicleResponse,
)
from app.shared.infrastructure.logging import logger

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])
UseCases = Annotated[VehiclesUseCases, Depends(get_vehicles_use_cases)]
VehicleId = Annotated[int, Path(ge=1)]


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(dto: CreateVehicleDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para criar veículo.")
    return await use_cases.create_vehicle.execute(dto)


@router.get("", response_model=list[VehicleReadResponse])
async def list_vehicles(
    use_cases: UseCases,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    logger.debug("Recebida listagem HTTP de veículo: offset=%s, limit=%s", offset, limit)
    return await use_cases.list_vehicles.execute(offset=offset, limit=limit)


@router.get("/{vehicle_id}", response_model=VehicleReadResponse)
async def get_vehicle(vehicle_id: VehicleId, use_cases: UseCases):
    logger.debug("Recebida consulta HTTP de veículo: vehicle_id=%s", vehicle_id)
    return await use_cases.get_vehicle.execute(vehicle_id)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: VehicleId, dto: UpdateVehicleDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para atualizar veículo: vehicle_id=%s", vehicle_id)
    return await use_cases.update_vehicle.execute(vehicle_id, dto)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: VehicleId, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para excluir veículo: vehicle_id=%s", vehicle_id)
    await use_cases.delete_vehicle.execute(vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
