from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.modules.users.infrastructure.http.schemas import UserReadResponse
from app.shared.infrastructure.security.dependencies import get_auth_service, get_current_user
from app.shared.infrastructure.security.schemas import ChangePasswordRequest, LoginRequest, RefreshRequest, TokenResponse
from app.shared.infrastructure.security.service import AuthenticatedUser, AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
Service = Annotated[AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def prevent_caching(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post("/login", response_model=TokenResponse)
async def login(dto: LoginRequest, service: Service, response: Response):
    prevent_caching(response)
    return await service.login(dto.cpf, dto.password.get_secret_value())


@router.post("/refresh", response_model=TokenResponse)
async def refresh(dto: RefreshRequest, service: Service, response: Response):
    prevent_caching(response)
    return await service.refresh(dto.refresh_token)


@router.get("/me", response_model=UserReadResponse)
async def me(current: CurrentUser, response: Response):
    prevent_caching(response)
    return current.user


@router.post("/logout", status_code=204)
async def logout(current: CurrentUser, service: Service):
    await service.logout(current)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.post("/change-password", status_code=204)
async def change_password(dto: ChangePasswordRequest, current: CurrentUser, service: Service):
    await service.change_password(
        current, dto.current_password.get_secret_value(), dto.new_password.get_secret_value(),
    )
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
