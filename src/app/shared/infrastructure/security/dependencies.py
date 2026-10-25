from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.infrastructure.http.dependencies import get_user_repository
from app.shared.infrastructure.database.engine import AsyncSessionLocal
from app.shared.infrastructure.security.repository import CredentialRepository, SQLAlchemyCredentialRepository
from app.shared.infrastructure.security.service import AuthenticatedUser, AuthService
from app.shared.infrastructure.security.tokens import TokenManager, unauthorized

bearer = HTTPBearer(auto_error=False)


async def get_credential_repository(request: Request) -> AsyncGenerator[CredentialRepository, None]:
    repository = request.app.state.credential_repository
    if repository is not None:
        yield repository
        return
    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyCredentialRepository(session)
        except Exception:
            await session.rollback()
            raise


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    credentials: Annotated[CredentialRepository, Depends(get_credential_repository)],
) -> AuthService:
    return AuthService(users, credentials, TokenManager(settings))


def get_bearer_token(
    header: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if header is None:
        raise unauthorized()
    return header.credentials


async def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedUser:
    return await service.authenticate(token)


def require_admin(
    current: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    if current.user.role != UserRole.ADMIN:
        raise HTTPException(403, "Acesso restrito a administradores")
    return current
