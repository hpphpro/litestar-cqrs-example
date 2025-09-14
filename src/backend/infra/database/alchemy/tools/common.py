from __future__ import annotations

import base64
import uuid
from typing import Any, get_args

from sqlalchemy import orm

from backend.infra.database.alchemy import types
from backend.shared.types import JsonDumps, JsonLoads, is_typevar


def cursor_encoder(value: uuid.UUID | int, encoder: JsonDumps, typ: types.CursorType) -> str:
    if typ.lower() == "uuid" and isinstance(value, uuid.UUID):
        encoded = base64.urlsafe_b64encode(encoder(value.hex).encode())
    else:
        encoded = base64.urlsafe_b64encode(encoder(value).encode())

    return encoded.decode()


def cursor_decoder(value: str, decoder: JsonLoads, typ: types.CursorType) -> uuid.UUID | int:
    decoded = decoder(base64.urlsafe_b64decode(value).decode())
    if typ.lower() == "uuid":
        return uuid.UUID(decoded)

    return int(decoded)


def get_entity_from_generic[E: orm.DeclarativeBase](
    self: Any, *, ensure_exists: bool = False
) -> type[E]:
    orig_bases = getattr(self, "__orig_bases__", None)

    assert orig_bases, "Generic type must be set"

    entity: type[E]

    for base in orig_bases:
        if args := get_args(base):
            entity, *other = args

            if not entity:
                continue

            if not ensure_exists:
                return entity

            if (
                not is_typevar(entity)
                and isinstance(entity, type)
                and issubclass(entity, orm.DeclarativeBase)
            ):
                return entity

            arg: type[E]
            for arg in other:
                if not arg:
                    continue
                if (
                    not is_typevar(arg)
                    and isinstance(arg, type)
                    and issubclass(arg, orm.DeclarativeBase)
                ):
                    entity = arg

                    return entity

    raise AttributeError(f"Entity is not present in any generic bases for class: {self}")
