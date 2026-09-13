"""SQLAlchemy custom types tailored for PostgreSQL and PostGIS."""

from __future__ import annotations

import json
from typing import Any
from sqlalchemy import String, Text, TypeDecorator, JSON, Uuid
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, UUID as PG_UUID
from sqlalchemy.types import TypeEngine
from geoalchemy2 import Geometry as PostGISGeometry
from geoalchemy2.elements import WKTElement


class PlatformUUID(TypeDecorator):
    """PostgreSQL native UUID type."""
    impl = Uuid
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        return dialect.type_descriptor(PG_UUID(as_uuid=True))


class PlatformJSON(TypeDecorator):
    """PostgreSQL JSON type."""
    impl = JSON
    cache_ok = True


class ArrayOrJSON(TypeDecorator):
    """PostgreSQL native ARRAY type."""
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
        return dialect.type_descriptor(PG_ARRAY(self.item_type))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return []
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
    """PostGIS Geometry type for spatial features."""
    impl = Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, spatial_index: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry_type = geometry_type
        self.srid = srid
        self.spatial_index = spatial_index

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        return dialect.type_descriptor(
            PostGISGeometry(
                geometry_type=self.geometry_type,
                srid=self.srid,
                spatial_index=self.spatial_index,
            )
        )

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return WKTElement(value, srid=self.srid)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        return value
