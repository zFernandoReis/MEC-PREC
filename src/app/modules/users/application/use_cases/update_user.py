from dataclasses import replace

from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.dtos.user_dto import UpdateUserDTO
from app.modules.users.application.services.address_service import AddressService


class UpdateUserUseCase:

    def __init__(
        self,
        user_repository,
        address_service: AddressService,
    ):
        self.user_repository = user_repository
        self.address_service = address_service

    async def execute(self, user_id: int, dto: UpdateUserDTO):

        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError()

        if dto.address is not None:
            changes = dto.address.model_dump(exclude_unset=True)
            cep = changes.pop("cep", None)
            address = user.adress
            if cep is not None and cep != address.cep:
                address = await self.address_service.get_address(
                    cep=cep,
                    number=changes.get("number", address.number),
                )
            address = replace(address, **changes)
            user.change_address(address)

        if dto.email is not None:
            user.change_email(dto.email)

        for field in ("primary_name", "secondary_name", "role"):
            value = getattr(dto, field)
            if value is not None:
                setattr(user, field, value)

        await self.user_repository.update(user)

        return user
