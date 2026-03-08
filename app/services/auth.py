import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    get_otp_code_hash,
    verify_pin,
    verify_otp_code,
)
from app.models.auth_otp import AuthOtpChallenge
from app.models.user import User, UserStatus
from app.schemas.auth import (
    LoginResponse,
    OtpChallengeResponse,
    PinVerificationResponse,
    UserContext,
)
from app.services.sms import send_sms_message


def request_login_otp(db: Session, phone: str) -> OtpChallengeResponse:
    settings = get_settings()
    user = _get_active_user_by_phone(db, phone)
    now = datetime.now(timezone.utc)

    if user.locked_until is not None and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked. Try again later.",
        )

    otp_code = _generate_otp_code(settings.auth_otp_length)
    expires_at = now + timedelta(minutes=settings.auth_otp_expire_minutes)

    db.execute(
        update(AuthOtpChallenge)
        .where(
            AuthOtpChallenge.user_id == user.id,
            AuthOtpChallenge.used_at.is_(None),
        )
        .values(used_at=now)
    )

    challenge = AuthOtpChallenge(
        user_id=user.id,
        phone=phone,
        code_hash=get_otp_code_hash(otp_code),
        expires_at=expires_at,
    )
    db.add(challenge)
    db.flush()

    send_sms_message(
        phone,
        f"Your login OTP is {otp_code}. It expires in {settings.auth_otp_expire_minutes} minutes.",
    )

    db.commit()
    return OtpChallengeResponse(
        message="OTP sent successfully.",
        expires_in=settings.auth_otp_expire_minutes * 60,
    )


def verify_login_otp(db: Session, phone: str, otp: str) -> LoginResponse:
    settings = get_settings()
    user = _get_active_user_by_phone(db, phone)
    now = datetime.now(timezone.utc)

    if user.locked_until is not None and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked. Try again later.",
        )

    challenge = db.scalar(
        select(AuthOtpChallenge)
        .where(
            AuthOtpChallenge.user_id == user.id,
            AuthOtpChallenge.phone == phone,
            AuthOtpChallenge.used_at.is_(None),
        )
        .order_by(AuthOtpChallenge.created_at.desc())
    )

    if challenge is None or challenge.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP is invalid or has expired.",
        )

    if not verify_otp_code(otp, challenge.code_hash):
        challenge.attempt_count += 1
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.auth_max_failed_attempts:
            user.status = UserStatus.LOCKED
            user.locked_until = now + timedelta(minutes=settings.auth_lockout_minutes)
        db.add(challenge)
        db.add(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP is invalid or has expired.",
        )

    challenge.used_at = now
    user.failed_login_attempts = 0
    user.locked_until = None
    user.status = UserStatus.ACTIVE
    user.last_login_at = now
    db.add(challenge)
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


def verify_user_pin(
    user: User,
    device_id: str,
    pin: str,
) -> PinVerificationResponse:
    # `device_id` is part of the request contract for the follow-up device trust flow.
    # For now we validate the PIN only and leave device binding for the next slice.
    _ = device_id

    if not verify_pin(pin, user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN mismatch.",
        )

    return PinVerificationResponse(
        matched=True,
        message="PIN matches.",
    )


def _get_active_user_by_phone(db: Session, phone: str) -> User:
    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.phone == phone)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account exists for this phone number.",
        )

    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


def _generate_otp_code(length: int) -> str:
    upper_bound = 10**length
    return str(secrets.randbelow(upper_bound)).zfill(length)
