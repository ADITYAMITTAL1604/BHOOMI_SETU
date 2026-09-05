"""Cross-dialect SQLAlchemy types supporting PostgreSQL, PostGIS, and SQLite."""

from __future__ import annotations

import json
from typing import Any
from sqlalchemy import String, Text, TypeDecorator, JSON, Uuid
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, UUID as PG_UUID
from sqlalchemy.types import TypeEngine
from geoalchemy2 import Geometry as PostGISGeometry


class PlatformUUID(TypeDecorator):
    """Platform-independent UUID type."""
    impl = Uuid
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        if dialect is not None and hasattr(dialect, "name") and dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(Uuid()) if dialect is not None else Uuid()


class PlatformJSON(TypeDecorator):
    """Platform-independent JSON type."""
    impl = JSON
    cache_ok = True


class ArrayOrJSON(TypeDecorator):
    """Platform-independent Array type.
    Uses PostgreSQL's native ARRAY on Postgres, JSON on SQLite.
    """
    impl = JSON
    cache_ok = True

    class comparator_factory(TypeDecorator.Comparator):
        def any(self, other, **kwargs):
            from sqlalchemy import cast, String
            return cast(self.expr, String).like(f"%{other}%")

        def any_(self, other, **kwargs):
            from sqlalchemy import cast, String
            return cast(self.expr, String).like(f"%{other}%")

        def contains(self, other, **kwargs):
            from sqlalchemy import cast, String
            return cast(self.expr, String).like(f"%{other}%")

    def __init__(self, item_type=String(100), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        if dialect is not None and hasattr(dialect, "name") and dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        return dialect.type_descriptor(JSON()) if dialect is not None else JSON()

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        is_pg = dialect is not None and hasattr(dialect, "name") and dialect.name == "postgresql"
        if value is None:
            return [] if not is_pg else []
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [value]
        return list(value)


class PlatformGeometry(TypeDecorator):
    """Platform-independent Geometry type.
    Uses PostGIS Geometry when available on PostgreSQL, Text representation on SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, spatial_index: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry_type = geometry_type
        self.srid = srid
        self.spatial_index = spatial_index

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        if dialect is not None and hasattr(dialect, "name") and dialect.name == "postgresql":
            return dialect.type_descriptor(
                PostGISGeometry(
                    geometry_type=self.geometry_type,
                    srid=self.srid,
                    spatial_index=self.spatial_index,
                )
            )
        return dialect.type_descriptor(Text()) if dialect is not None else Text()

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        is_pg = dialect is not None and hasattr(dialect, "name") and dialect.name == "postgresql"
        if is_pg:
            from geoalchemy2.elements import WKTElement
            if isinstance(value, str):
                return WKTElement(value, srid=self.srid)
            return value
        if hasattr(value, "data"):
            return str(value.data)
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        return value
