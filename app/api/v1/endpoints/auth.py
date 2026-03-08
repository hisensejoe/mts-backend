from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    OtpChallengeResponse,
    VerifyOtpRequest,
)
from app.schemas.user import UserRead
from app.services.auth import request_login_otp, verify_login_otp

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> OtpChallengeResponse:
    return request_login_otp(db=db, phone=payload.phone)


@router.post("/verify-otp")
def verify_otp(
    payload: VerifyOtpRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    return verify_login_otp(db=db, phone=payload.phone, otp=payload.otp)


@router.get("/me")
def read_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserRead:
    return UserRead.model_validate(current_user)
