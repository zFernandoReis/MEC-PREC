from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.infrastructure.models.users_model import UserModel


@dataclass(frozen=True)
class Credential:
    user_id: int
    password_hash: str | None = field(repr=False)
    token_version: int = 0


class CredentialRepository(Protocol):
    async def get(self, user_id: int) -> Credential | None: ...
    async def rotate(self, credential: Credential, password_hash: str | None = None) -> bool: ...


class SQLAlchemyCredentialRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int) -> Credential | None:
        model = await self.session.get(UserModel, user_id, populate_existing=True)
        if model is None:
            return None
        return Credential(model.id, model.password_hash, model.token_version)

    async def rotate(self, credential: Credential, password_hash: str | None = None) -> bool:
        # Compare-and-swap: apenas uma renovação concorrente pode consumir a versão.
        values: dict[str, int | str] = {"token_version": credential.token_version + 1}
        if password_hash is not None:
            values["password_hash"] = password_hash
        result = await self.session.execute(
            update(UserModel)
            .where(
                UserModel.id == credential.user_id,
                UserModel.token_version == credential.token_version,
            )
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        await self.session.commit()
        return result.rowcount == 1
