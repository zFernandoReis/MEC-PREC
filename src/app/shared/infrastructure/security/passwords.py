from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hasher = PasswordHash.recommended()
_dummy_hash = password_hasher.hash("dummy-password-for-missing-credentials")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        valid = password_hasher.verify(password, password_hash or _dummy_hash)
    except (UnknownHashError, ValueError):
        return False
    return valid and password_hash is not None
