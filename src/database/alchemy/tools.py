from __future__ import annotations

import base64
import uuid
from collections import deque
from collections.abc import Callable
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Final, get_args, overload

from sqlalchemy import ColumnExpressionArgument, Select, select
from sqlalchemy.orm import (
    RelationshipProperty,
    aliased,
    contains_eager,
    subqueryload,
)

from src.database._util import frozendict, is_typevar
from src.database.alchemy import types
from src.database.alchemy.entity import MODELS_RELATIONSHIPS_NODE, Entity
from src.database.alchemy.entity.base.core import pascal_to_snake


if TYPE_CHECKING:
    from sqlalchemy.orm.strategy_options import _AbstractLoad

DEFAULT_RELATIONSHIP_LOAD_LIMIT: Final[int] = 20


def _bfs_search[E: Entity](
    start: type[E],
    end: str,
    node: frozendict[type[Entity], tuple[RelationshipProperty[type[Entity]]]],
) -> list[RelationshipProperty[E]]:
    queue = deque([[start]])
    checked = set()

    while queue:
        path = queue.popleft()
        current_node = path[-1]

        if current_node in checked:
            continue
        checked.add(current_node)

        current_relations = node.get(current_node)

        for relation in current_relations or []:
            new_path: list[Any] = list(path)
            new_path.append(relation)

            if relation.key == end:
                return [rel for rel in new_path if isinstance(rel, RelationshipProperty)]

            queue.append(new_path + [relation.mapper.class_])

    return []


def _construct_strategy[EntityT: Entity](
    strategy: Callable[..., _AbstractLoad],
    relationship: RelationshipProperty[EntityT],
    current: _AbstractLoad | None = None,
    **kw: Any,
) -> _AbstractLoad:
    _strategy: _AbstractLoad = (
        strategy(relationship, **kw)
        if current is None
        else getattr(current, strategy.__name__)(relationship, **kw)
    )

    return _strategy


def _construct_loads[E: Entity](
    entity: type[E],
    query: Select[tuple[E]],
    relationships: list[RelationshipProperty[E]],
    order_by: tuple[str, ...],
    exclude: set[type[E]],
    subquery_cond: frozendict[
        str,
        Callable[[Select[tuple[E]]], Select[tuple[E]]],
    ]
    | None = None,
    self_key: str | None = None,
    limit: int | None = None,
) -> tuple[Select[tuple[E]], _AbstractLoad | None]:
    if not relationships:
        return query, None

    load: _AbstractLoad | None = None
    for relationship in relationships:
        origin = relationship.mapper.class_

        if origin in exclude:
            continue

        exclude.add(origin)

        if relationship.uselist:
            if limit is None:
                load = _construct_strategy(subqueryload, relationship, load)
            else:
                if origin is entity and self_key:
                    alias = aliased(origin)
                    query = query.outerjoin(alias, entity.id == getattr(alias, self_key))
                    load = _construct_strategy(contains_eager, relationship, load, alias=alias)
                    continue

                q = (
                    select(origin)
                    .order_by(*(getattr(origin, by).desc() for by in order_by))
                    .limit(limit)
                )
                for key, condition in (subquery_cond or {}).items():
                    if relationship.key == key:
                        q = condition(q)

                lateral = q.lateral(name=pascal_to_snake(origin))

                if relationship.secondary is not None and relationship.secondaryjoin is not None:
                    query = query.outerjoin(
                        relationship.secondary, relationship.primaryjoin
                    ).outerjoin(lateral, relationship.secondaryjoin)
                else:
                    q = q.where(relationship.primaryjoin)
                    query = query.outerjoin(lateral, relationship.primaryjoin)

                load = _construct_strategy(contains_eager, relationship, load, alias=lateral)
        else:
            query = query.outerjoin(origin, relationship.primaryjoin)
            load = _construct_strategy(contains_eager, relationship, load)

    return query, load


@lru_cache(typed=True)
def _select_with_relations[E: Entity](
    *_should_load: str,
    entity: type[E],
    query: Select[tuple[E]] | None = None,
    order_by: tuple[str, ...] = ("id",),
    limit: int | None = DEFAULT_RELATIONSHIP_LOAD_LIMIT,
    self_key: str | None = None,
    subquery_cond: frozendict[
        str,
        Callable[[Select[tuple[E]]], Select[tuple[E]]],
    ]
    | None = None,
    _node: frozendict[type[Entity], tuple[RelationshipProperty[type[Entity]]]] | None = None,
) -> Select[tuple[E]]:
    if _node is None:
        _node = MODELS_RELATIONSHIPS_NODE
    if query is None:
        query = select(entity)

    options = []
    to_load = list(_should_load)
    exclude: set[type[E]] = set()
    while to_load:
        result = _bfs_search(entity, to_load.pop(), _node)

        if not result:
            continue
        query, construct = _construct_loads(
            entity,
            query,
            result,
            subquery_cond=subquery_cond,
            exclude=exclude,
            order_by=order_by,
            limit=limit,
            self_key=self_key,
        )
        if construct:
            options += [construct]

    if options:
        query = query.options(*options)

    return query


def select_with_relations[E: Entity](
    *_should_load: str,
    entity: type[E],
    query: Select[tuple[E]] | None = None,
    order_by: tuple[str, ...] = ("id",),
    limit: int | None = DEFAULT_RELATIONSHIP_LOAD_LIMIT,
    self_key: str | None = None,
    subquery_cond: frozendict[
        str,
        Callable[[Select[tuple[E]]], Select[tuple[E]]],
    ]
    | None = None,
    _node: frozendict[type[Entity], tuple[RelationshipProperty[type[Entity]]]] | None = None,
) -> Select[tuple[E]]:
    return _select_with_relations(
        *_should_load,
        entity=entity,
        query=query,
        order_by=order_by,
        limit=limit,
        self_key=self_key,
        subquery_cond=subquery_cond,
        _node=_node,
    )


def add_conditions[E: Entity](
    *conditions: ColumnExpressionArgument[bool],
) -> Callable[[Select[tuple[E]]], Select[tuple[E]]]:
    def _add(query: Select[tuple[E]]) -> Select[tuple[E]]:
        return query.where(*conditions)

    return _add


@overload
def cursor_encoder(value: int, encoder: types.JsonDumps, type: types.CursorIntegerType) -> str: ...
@overload
def cursor_encoder(
    value: uuid.UUID, encoder: types.JsonDumps, type: types.CursorUUIDType
) -> str: ...
def cursor_encoder(value: uuid.UUID | int, encoder: types.JsonDumps, type: types.CursorType) -> str:
    if type.lower() == "uuid" and isinstance(value, uuid.UUID):
        encoded = base64.urlsafe_b64encode(encoder(value.hex).encode())
    else:
        encoded = base64.urlsafe_b64encode(encoder(value).encode())

    return encoded.decode()


@overload
def cursor_decoder(value: str, decoder: types.JsonLoads, type: types.CursorIntegerType) -> int: ...
@overload
def cursor_decoder(
    value: str, decoder: types.JsonLoads, type: types.CursorUUIDType
) -> uuid.UUID: ...
def cursor_decoder(value: str, decoder: types.JsonLoads, type: types.CursorType) -> uuid.UUID | int:
    decoded = decoder(base64.urlsafe_b64decode(value).decode())
    if type.lower() == "uuid":
        return uuid.UUID(decoded)

    return int(decoded)


def get_entity_from_generic[E: Entity](self: Any, ensure_exists: bool = False) -> type[E]:
    orig_bases = getattr(self, "__orig_bases__", None)

    assert orig_bases, "Generic type must be set"

    query, *_ = orig_bases

    entity: type[E]

    if args := get_args(query):
        entity, *other = args

        if not ensure_exists:
            return entity

        if not is_typevar(entity) and isinstance(entity, type) and issubclass(entity, Entity):
            return entity

        for arg in other:
            if not is_typevar(arg) and isinstance(entity, type) and issubclass(arg, Entity):
                entity = arg

                return entity

        raise AttributeError(f"Entity is not present in args: {args}")

    raise AttributeError(f"Generic args were not specified for class: {self}")
