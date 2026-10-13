from app.modules.users.application.dtos.user_dto import CreateUserDTO
from app.modules.users.application.services.address_service import AddressService
from app.modules.users.domain.entities.user import User


class CreateUserUseCase:

    def __init__(
        self,
        user_repository,
        address_service: AddressService,
    ):
        self.user_repository = user_repository
        self.address_service = address_service

    async def execute(self, dto: CreateUserDTO):

        address = await self.address_service.get_address(
            cep=dto.address.cep,
            number=dto.address.number,
            complement=dto.address.complement,
        )

        user = User(
            id=None,
            primary_name=dto.primary_name,
            secondary_name=dto.secondary_name,
            cpf=dto.cpf,
            email=dto.email,
            role=dto.role,
            adress=address,
        )

        await self.user_repository.save(user)

        return user
