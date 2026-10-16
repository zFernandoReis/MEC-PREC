from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.domain.entities.user import User
from app.modules.users.infrastructure.models.users_model import UserModel
from app.shared.infrastructure.logging import logger


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> None:
        logger.debug("Inserindo usuário no banco de dados.")
        model = UserModel.from_entity(user)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        logger.debug("Inserção de usuário concluída: user_id=%s", model.id)
        user.id = model.id
        user.create_at = model.create_at
        user.update_at = model.update_at

    async def get_by_id(self, user_id: int) -> User | None:
        logger.debug("Consultando usuário no banco: user_id=%s", user_id)
        model = await self.session.get(UserModel, user_id)
        logger.debug("Consulta de usuário concluída: encontrado=%s", model is not None)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int) -> list[User]:
        logger.debug("Consultando página de usuário no banco: offset=%s, limit=%s", offset, limit)
        result = await self.session.scalars(
            select(UserModel).order_by(UserModel.id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, user: User) -> None:
        logger.debug("Atualizando usuário no banco: user_id=%s", user.id)
        model = await self.session.get(UserModel, user.id)
        if model is None:
            logger.debug("User não encontrado no banco: user_id=%s", user.id)
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
        logger.debug("Atualização de usuário confirmada no banco: user_id=%s", user.id)

    async def delete(self, user: User) -> None:
        logger.debug("Excluindo usuário no banco: user_id=%s", user.id)
        model = await self.session.get(UserModel, user.id)
        if model is None:
            logger.debug("User não encontrado no banco: user_id=%s", user.id)
            raise UserNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
        logger.debug("Exclusão de usuário confirmada no banco: user_id=%s", user.id)
