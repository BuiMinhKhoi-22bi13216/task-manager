from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="TASK_MANAGER_",
        extra="ignore",
        hide_input_in_errors=True,
    )

    db_path: Path
    jwt_secret: SecretStr = Field(min_length=1)
    token_expire_minutes: int = Field(gt=0)
    upload_dir: Path
    sql_echo: bool
    cors_origins: list[str]
    external_api_url: AnyHttpUrl
    external_api_timeout_seconds: float = Field(gt=0, allow_inf_nan=False)


def load_settings() -> Settings:
    # BaseSettings nạp các trường bắt buộc từ môi trường và .env.
    return Settings()  # type: ignore[call-arg]