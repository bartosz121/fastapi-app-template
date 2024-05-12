from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel as BaseModel_
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class BaseModel(BaseModel_):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )


# Just to make `id` appear first in openapi schema
class BaseModelId(BaseModel, Generic[T]):
    id: T


class Timestamp(BaseModel):
    created_at: datetime
    updated_at: datetime


__all__ = (
    "BaseModel",
    "BaseModelId",
    "Timestamp",
)
