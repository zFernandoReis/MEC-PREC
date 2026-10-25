"""Define ou redefine a senha de um usuário existente usando acesso administrativo ao banco."""

import argparse
import asyncio
from getpass import getpass

from pydantic import SecretStr, TypeAdapter, ValidationError

from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.shared.infrastructure.database.engine import AsyncSessionLocal, engine
from app.shared.infrastructure.security.passwords import hash_password
from app.shared.infrastructure.security.repository import SQLAlchemyCredentialRepository
from app.shared.infrastructure.security.schemas import NewPassword


async def set_password(cpf: str, password: str) -> None:
    try:
        async with AsyncSessionLocal() as session:
            user = await SQLAlchemyUserRepository(session).get_by_cpf(cpf)
            if user is None:
                raise ValueError("Usuário não encontrado")
            repository = SQLAlchemyCredentialRepository(session)
            credential = await repository.get(user.id)
            encoded = hash_password(password)
            if credential is None or not await repository.rotate(credential, encoded):
                raise ValueError("Credenciais alteradas durante a operação; execute novamente")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpf", required=True, help="CPF do usuário existente, com 11 dígitos")
    args = parser.parse_args()
    if len(args.cpf) != 11 or not args.cpf.isascii() or not args.cpf.isdecimal():
        parser.error("CPF deve conter 11 dígitos")
    password = getpass("Nova senha (12 a 128 caracteres): ")
    try:
        TypeAdapter(NewPassword).validate_python(SecretStr(password))
    except ValidationError:
        parser.error("A senha deve conter de 12 a 128 caracteres")
    if getpass("Confirme a nova senha: ") != password:
        parser.error("As senhas não conferem")
    try:
        asyncio.run(set_password(args.cpf, password))
    except ValueError as exc:
        parser.error(str(exc))
    print("Senha definida. As sessões anteriores foram revogadas.")


if __name__ == "__main__":
    main()
