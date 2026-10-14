from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.domain.entities.user import User
from app.modules.users.infrastructure.models.users_model import UserModel


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> None:
        model = UserModel.from_entity(user)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        user.id = model.id
        user.create_at = model.create_at
        user.update_at = model.update_at

    async def get_by_id(self, user_id: int) -> User | None:
        model = await self.session.get(UserModel, user_id)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int) -> list[User]:
        result = await self.session.scalars(
            select(UserModel).order_by(UserModel.id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, user: User) -> None:
        model = await self.session.get(UserModel, user.id)
        if model is None:
            raise UserNotFoundError()
        model.primary_name = user.primary_name
        model.secondary_name = user.secondary_name
        model.cpf = user.cpf
        model.email = user.email
        model.role = user.role
        model.address = user.adress
        await self.session.commit()
        await self.session.refresh(model)
        user.create_at = model.create_at
        user.update_at = model.update_at

    async def delete(self, user: User) -> None:
        model = await self.session.get(UserModel, user.id)
        if model is None:
            raise UserNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
