import orjson
import types
from datetime import datetime
from typing import TypeVar, Generator, Union, Any, get_origin, get_args

from pydantic import BaseModel, ConfigDict, model_validator

def _orjson_dumps(val, *, default):
    return orjson.dumps(val, default=default).decode()


class Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def model_serializer(cls, **kwargs):
        kwargs.setdefault('default', lambda obj: obj.__dict__)
        return _orjson_dumps(kwargs.get('obj', {}), default=kwargs['default'])

    @classmethod
    def model_deserializer(cls, data, **kwargs):
        return orjson.loads(data)


class OptionalBaseModel(Base):
    """Автоматически заполняет опциональные поля значениями None, если они отсутствуют."""

    @model_validator(mode='before')
    def fill_optional_fields(cls, data: dict[str, Any]) -> dict[str, Any]:  # noqa B902
        if not isinstance(data, dict):
            return data
        for field_name, field_info in cls.model_fields.items():
            if field_name not in data:
                annotation = field_info.annotation
                origin = get_origin(annotation)
                args = get_args(annotation)
                union_types = (Union, getattr(types, 'UnionType', None))
                if origin in union_types and args and type(None) in args:
                    data[field_name] = None
        return data
