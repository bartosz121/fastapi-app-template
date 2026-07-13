from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel as BaseModel_, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class BaseSchema(BaseModel_):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )


# Just to make `id` appear first in openapi schema
class BaseSchemaId[T](BaseSchema):
    id: T


class Timestamp(BaseSchema):
    created_at: datetime
    updated_at: datetime


__all__ = (
    "BaseSchema",
    "BaseSchemaId",
    "Timestamp",
)
