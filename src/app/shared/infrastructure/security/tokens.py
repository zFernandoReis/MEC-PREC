from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException

from app.config import Settings
from app.shared.infrastructure.security.schemas import TokenResponse


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401, detail="Credenciais ou token inválidos",
        headers={"WWW-Authenticate": "Bearer"},
    )


class TokenManager:
    def __init__(self, config: Settings):
        if config.JWT_SECRET_KEY is None:
            raise HTTPException(503, "Configure JWT_SECRET_KEY para habilitar autenticação")
        self.key = config.JWT_SECRET_KEY.get_secret_value()
        self.issuer = config.JWT_ISSUER
        self.audience = config.JWT_AUDIENCE
        self.access_minutes = config.JWT_ACCESS_TOKEN_MINUTES
        self.refresh_days = config.JWT_REFRESH_TOKEN_DAYS

    def issue(self, user_id: int, version: int) -> TokenResponse:
        now = datetime.now(timezone.utc)

        def encode(kind: str, lifetime: timedelta) -> str:
            return jwt.encode({
                "sub": str(user_id), "ver": version, "type": kind,
                "iss": self.issuer, "aud": self.audience,
                "iat": now, "nbf": now, "exp": now + lifetime,
                "jti": str(uuid4()),
            }, self.key, algorithm="HS256")

        return TokenResponse(
            access_token=encode("access", timedelta(minutes=self.access_minutes)),
            refresh_token=encode("refresh", timedelta(days=self.refresh_days)),
            expires_in=self.access_minutes * 60,
        )

    def decode(self, token: str, kind: str) -> tuple[int, int]:
        try:
            claims = jwt.decode(
                token, self.key, algorithms=["HS256"],
                issuer=self.issuer, audience=self.audience,
                options={"require": ["sub", "ver", "type", "iss", "aud", "iat", "nbf", "exp", "jti"]},
            )
            if claims["type"] != kind:
                raise ValueError("Tipo de token inválido")
            user_id = int(claims["sub"])
            version = claims["ver"]
            if user_id < 1 or type(version) is not int or version < 0:
                raise ValueError("Identidade inválida")
            return user_id, version
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            raise unauthorized() from None
