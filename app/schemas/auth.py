from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=256)


class TokenResult(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int = Field(gt=0)


class AuthenticatedUser(BaseModel):
    id: UUID
    username: str
