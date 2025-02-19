from __future__ import annotations

import base64
import uuid
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Final, overload

from sqlalchemy import ColumnExpressionArgument, Select, select, true
from sqlalchemy.orm import RelationshipProperty, aliased, contains_eager, subqueryload

from src.database._util import frozendict
from src.database.alchemy import types
from src.database.alchemy.entity import MODELS_RELATIONSHIPS_NODE, Entity


if TYPE_CHECKING:
    from sqlalchemy.orm.strategy_options import _AbstractLoad

DEFAULT_RELATIONSHIP_LOAD_LIMIT: Final[int] = 20


def _bfs_search[E: Entity](
    start: type[E],
    end: str,
    node: frozendict[type[Entity], tuple[RelationshipProperty[type[Entity]]]] | None = None,
) -> list[RelationshipProperty[E]]:
    if node is None:
        node = MODELS_RELATIONSHIPS_NODE

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
                q = (
                    select(origin)
                    .order_by(*(getattr(origin, by).desc() for by in order_by))
                    .limit(limit)
                )
                if relationship.secondary is not None and relationship.secondaryjoin is not None:
                    query = query.outerjoin(relationship.secondary, relationship.primaryjoin)
                else:
                    if origin is entity and self_key:
                        alias = aliased(origin)
                        query = query.join(alias, entity.id == getattr(alias, self_key))
                        load = _construct_strategy(contains_eager, relationship, load, alias=alias)
                        continue

                    q = q.where(relationship.primaryjoin)
                    for key, condition in (subquery_cond or {}).items():
                        if relationship.key == key:
                            q = condition(q)

                lateral = q.lateral().alias()
                query = query.outerjoin(lateral, true())
                load = _construct_strategy(contains_eager, relationship, load, alias=lateral)
        else:
            query = query.outerjoin(origin, relationship.primaryjoin)
            load = _construct_strategy(contains_eager, relationship, load)

    return query, load


@lru_cache(typed=True)
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
    value: tuple[datetime, uuid.UUID], encoder: types.JsonDumps, type: types.CursorUUIDType
) -> str: ...
def cursor_encoder(
    value: tuple[datetime, uuid.UUID] | int, encoder: types.JsonDumps, type: types.CursorType
) -> str:
    if type.lower() == "uuid" and isinstance(value, tuple):
        created_at, guid = value
        encoded = base64.urlsafe_b64encode(encoder([created_at.timestamp(), guid.hex]).encode())
    else:
        encoded = base64.urlsafe_b64encode(encoder(value).encode())

    return encoded.decode()


@overload
def cursor_decoder(value: str, decoder: types.JsonLoads, type: types.CursorIntegerType) -> int: ...
@overload
def cursor_decoder(
    value: str, decoder: types.JsonLoads, type: types.CursorUUIDType
) -> tuple[datetime, uuid.UUID]: ...
def cursor_decoder(
    value: str, decoder: types.JsonLoads, type: types.CursorType
) -> tuple[datetime, uuid.UUID] | int:
    if type.lower() == "uuid":
        decoded = decoder(base64.urlsafe_b64decode(value).decode())
        created_at, guid = decoded

        return datetime.fromtimestamp(created_at, UTC), uuid.UUID(guid)

    result: int = decoder(base64.urlsafe_b64decode(value).decode())

    return int(result)
