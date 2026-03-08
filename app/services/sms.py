import requests
from fastapi import HTTPException, status

from app.core.config import get_settings


def send_sms_message(phone: str, message: str) -> None:
    settings = get_settings()
    username = settings.sms_username.get_secret_value()
    password = settings.sms_password.get_secret_value()

    if not username or not password or not settings.sms_from:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS gateway credentials are not configured.",
        )

    response = requests.get(
        settings.sms_base_url,
        params={
            "username": username,
            "password": password,
            "from": settings.sms_from,
            "to": phone,
            "text": message,
        },
        timeout=15,
    )
    print(response.text)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SMS gateway rejected the OTP request.",
        )
