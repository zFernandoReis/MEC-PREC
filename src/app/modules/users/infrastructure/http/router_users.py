from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.bootstrap.users import UsersUseCases
from app.modules.users.application.dtos.user_dto import CreateUserDTO, UpdateUserDTO
from app.modules.users.infrastructure.http.dependencies import get_users_use_cases
from app.modules.users.infrastructure.http.schemas import UserReadResponse, UserResponse
from app.shared.infrastructure.logging import logger

router = APIRouter(prefix="/users", tags=["Users"])
UseCases = Annotated[UsersUseCases, Depends(get_users_use_cases)]
UserId = Annotated[int, Path(ge=1)]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(dto: CreateUserDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para criar usuário.")
    return await use_cases.create_user.execute(dto)


@router.get("", response_model=list[UserReadResponse])
async def list_users(
    use_cases: UseCases,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    logger.debug("Recebida listagem HTTP de usuário: offset=%s, limit=%s", offset, limit)
    return await use_cases.list_users.execute(offset=offset, limit=limit)


@router.get("/cpf/{cpf}", response_model=UserReadResponse)
async def get_user_by_cpf(
    cpf: Annotated[str, Path(pattern=r"^[0-9]{11}$")], use_cases: UseCases
):
    logger.debug("Recebida consulta HTTP de usuário por CPF.")
    return await use_cases.get_user.get_by_cpf(cpf)


@router.get("/{user_id}", response_model=UserReadResponse)
async def get_user(user_id: UserId, use_cases: UseCases):
    logger.debug("Recebida consulta HTTP de usuário: user_id=%s", user_id)
    return await use_cases.get_user.execute(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: UserId, dto: UpdateUserDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para atualizar usuário: user_id=%s", user_id)
    return await use_cases.update_user.execute(user_id, dto)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UserId, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para excluir usuário: user_id=%s", user_id)
    await use_cases.delete_user.execute(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
