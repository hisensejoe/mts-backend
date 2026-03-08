from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MTS Fleet API"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["local", "development", "staging", "production"] = Field(
        default="local",
        alias="ENVIRONMENT",
    )

    database_url: str = Field(alias="DATABASE_URL")

    jwt_secret: SecretStr = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    auth_max_failed_attempts: int = Field(default=5, alias="AUTH_MAX_FAILED_ATTEMPTS")
    auth_lockout_minutes: int = Field(default=15, alias="AUTH_LOCKOUT_MINUTES")
    auth_otp_expire_minutes: int = Field(default=10, alias="AUTH_OTP_EXPIRE_MINUTES")
    auth_otp_length: int = Field(default=6, alias="AUTH_OTP_LENGTH")

    sms_username: SecretStr = Field(default=SecretStr(""), alias="SMS_USERNAME")
    sms_password: SecretStr = Field(default=SecretStr(""), alias="SMS_PASSWORD")
    sms_from: str = Field(default="", alias="SMS_FROM")
    sms_base_url: str = Field(
        default="http://sms.hisense.com.gh/api/sms/send",
        alias="SMS_BASE_URL",
    )

    admin_seed_phone: str = Field(default="+233245550001", alias="ADMIN_SEED_PHONE")
    admin_seed_pin: SecretStr = Field(default=SecretStr("1234"), alias="ADMIN_SEED_PIN")
    admin_seed_full_name: str = Field(default="Ama Korantema", alias="ADMIN_SEED_FULL_NAME")
    admin_seed_role: str = Field(default="super_admin", alias="ADMIN_SEED_ROLE")

    default_page_size: int = 25
    max_page_size: int = 100
    cors_allow_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
