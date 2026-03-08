from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

# Passlib's bcrypt backend is not compatible with the current bcrypt release line,
# so this skeleton uses a current passlib-native scheme and keeps the hasher isolated.
password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    exp: int
    role: str

    @property
    def user_id(self) -> UUID:
        return UUID(self.sub)


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    return password_context.verify(plain_pin, hashed_pin)


def get_pin_hash(pin: str) -> str:
    return password_context.hash(pin)


def verify_otp_code(plain_code: str, hashed_code: str) -> bool:
    return password_context.verify(plain_code, hashed_code)


def get_otp_code_hash(code: str) -> str:
    return password_context.hash(code)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    settings = get_settings()
    lifetime = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expires_at = datetime.now(timezone.utc) + lifetime
    payload = {"sub": subject, "role": role, "exp": expires_at}

    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload.model_validate(payload)
    except (jwt.InvalidTokenError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        ) from exc
