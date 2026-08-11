from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    full_name: str
    username: str
    email: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, underscores, and dashes")
        return v


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: str

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    origin: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
