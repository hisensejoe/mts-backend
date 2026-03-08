from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import create_access_token, normalize_phone, verify_pin
from app.models.user import User, UserStatus
from app.schemas.auth import LoginResponse, UserContext


def authenticate_by_phone_pin(db: Session, phone: str, pin: str) -> LoginResponse:
    settings = get_settings()
    normalized_phone = normalize_phone(phone)
    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.phone == normalized_phone)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or PIN.",
        )

    now = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked. Try again later.",
        )

    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    if not verify_pin(pin, user.pin_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.auth_max_failed_attempts:
            user.status = UserStatus.LOCKED
            user.locked_until = now + timedelta(minutes=settings.auth_lockout_minutes)
        db.add(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or PIN.",
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    user.status = UserStatus.ACTIVE
    user.last_login_at = now
    db.add(user)
    db.commit()
    db.refresh(user)

    expires_in = settings.jwt_access_token_expire_minutes * 60
    token = create_access_token(subject=str(user.id), role=user.role.name)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserContext(
            id=user.id,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role.name,
            customer_id=user.customer_id,
            last_login_at=user.last_login_at,
        ),
    )
