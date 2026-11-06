from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    full_name: str | None = None

    @field_validator("username", "email")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Username và email không được chỉ chứa khoảng trắng")
        return value

    @field_validator("password")
    @classmethod
    def bcrypt_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72 or "\x00" in value:
            raise ValueError("Mật khẩu tối đa 72 byte UTF-8 và không chứa NUL")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"