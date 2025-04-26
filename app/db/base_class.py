from typing import Any

from sqlalchemy import MetaData, inspect
from sqlalchemy.ext.declarative import as_declarative


meta = MetaData()


@as_declarative(metadata=meta)
class Base:
    id: Any
    __name__: str

    def _asdict(self):
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
