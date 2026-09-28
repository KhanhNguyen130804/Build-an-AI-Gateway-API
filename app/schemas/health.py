from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["alive", "ready"]
