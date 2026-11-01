from dataclasses import dataclass

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.entities.user import User
from app.shared.infrastructure.security.passwords import hash_password, verify_password
from app.shared.infrastructure.security.repository import Credential, CredentialRepository
from app.shared.infrastructure.security.schemas import TokenResponse
from app.shared.infrastructure.security.tokens import TokenManager, unauthorized


@dataclass(frozen=True)
class AuthenticatedUser:
    user: User
    credential: Credential


class AuthService:
    def __init__(self, users: UserRepository, credentials: CredentialRepository, tokens: TokenManager):
        self.users = users
        self.credentials = credentials
        self.tokens = tokens

    async def login(self, cpf: str, password: str) -> TokenResponse:
        user = await self.users.get_by_cpf(cpf)
        credential = await self.credentials.get(user.id) if user is not None else None
        valid = await run_in_threadpool(
            verify_password, password, credential.password_hash if credential else None,
        )
        if not valid or credential is None:
            raise unauthorized()
        return await self._rotate(credential)

    async def authenticate(self, token: str, kind: str = "access") -> AuthenticatedUser:
        user_id, version = self.tokens.decode(token, kind)
        credential = await self.credentials.get(user_id)
        user = await self.users.get_by_id(user_id)
        if user is None or credential is None or credential.password_hash is None or credential.token_version != version:
            raise unauthorized()
        return AuthenticatedUser(user, credential)

    async def _rotate(self, credential: Credential) -> TokenResponse:
        pair = self.tokens.issue(credential.user_id, credential.token_version + 1)
        if not await self.credentials.rotate(credential):
            raise unauthorized()
        return pair

    async def refresh(self, token: str) -> TokenResponse:
        current = await self.authenticate(token, "refresh")
        return await self._rotate(current.credential)

    async def logout(self, current: AuthenticatedUser) -> None:
        if not await self.credentials.rotate(current.credential):
            raise unauthorized()

    async def change_password(self, current: AuthenticatedUser, old: str, new: str) -> None:
        if not await run_in_threadpool(verify_password, old, current.credential.password_hash):
            raise unauthorized()
        if old == new:
            raise HTTPException(422, "A nova senha deve ser diferente da senha atual")
        encoded = await run_in_threadpool(hash_password, new)
        if not await self.credentials.rotate(current.credential, encoded):
            raise unauthorized()
