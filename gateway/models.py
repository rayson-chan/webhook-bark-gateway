from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Notification(BaseModel):
    """Provider-neutral notification produced by every adapter."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    group: str = Field(min_length=1, max_length=100)
    level: Literal["active", "timeSensitive", "passive"] = "active"
    url: HttpUrl | None = None

