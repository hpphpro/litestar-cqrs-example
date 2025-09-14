from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Final, Required, TypedDict, Unpack

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm.util import LoaderCriteriaOption
from sqlalchemy.sql.selectable import LateralFromClause

from .datastructures import frozendict
from .node import Node
from .tools import get_primary_key, get_table_name, get_table_names


if TYPE_CHECKING:
    from sqlalchemy.orm.strategy_options import _AbstractLoad

DEFAULT_RELATIONSHIP_LOAD_LIMIT: Final[int] = 50


@dataclass(slots=True)
class _LoadSelfParams[T: orm.DeclarativeBase]:
    model: type[T]
    relationship: orm.RelationshipProperty[T]
    self_key: str
    order_by: tuple[str, ...] | None = None
    limit: int | None = None
    load: _AbstractLoad | None = None
    conditions: Mapping[str, Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]] | None = None

    @classmethod
    def from_relation_params(cls, params: _LoadRelationParams[T]) -> _LoadSelfParams[T]:
        assert params.self_key, "`self_key` should be set for self join"

        return cls(
            model=params.model,
            relationship=params.relationship,
            self_key=params.self_key,
            order_by=params.order_by,
            limit=params.limit,
            load=params.load,
            conditions=params.conditions,
        )


@dataclass(slots=True)
class _LoadRelationParams[T: orm.DeclarativeBase]:
    model: type[T]
    relationship: orm.RelationshipProperty[T]
    is_alias: bool = False
    check_tables: bool = False
    order_by: tuple[str, ...] | None = None
    conditions: Mapping[str, Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]] | None = None
    load: _AbstractLoad | None = None
    limit: int | None = None
    self_key: str | None = None

    @classmethod
    def from_construct_loads_params(
        cls,
        params: _ConstructLoadsParams[T],
        relationship: orm.RelationshipProperty[T],
        load: _AbstractLoad | None = None,
        *,
        is_alias: bool,
    ) -> _LoadRelationParams[T]:
        return cls(
            model=params.model,
            conditions=params.conditions,
            order_by=params.order_by,
            limit=params.limit,
            self_key=params.self_key,
            check_tables=params.check_tables,
            relationship=relationship,
            load=load,
            is_alias=is_alias,
        )


@dataclass(slots=True)
class _ConstructLoadsParams[T: orm.DeclarativeBase]:
    model: type[T]
    conditions: Mapping[str, Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]] | None = None
    order_by: tuple[str, ...] | None = None
    self_key: str | None = None
    limit: int | None = None
    check_tables: bool = False

    @classmethod
    def from_params(cls, params: _LoadParams[T]) -> _ConstructLoadsParams[T]:
        return cls(
            model=params.model,
            conditions=params.conditions,
            order_by=params.order_by,
            self_key=params.self_key,
            limit=params.limit,
            check_tables=params.check_tables,
        )


@dataclass(slots=True, frozen=True)
class _LoadParams[T: orm.DeclarativeBase]:
    model: type[T]
    loads: tuple[str, ...] = ()
    node: Node = field(default_factory=Node)
    limit: int | None = field(default=DEFAULT_RELATIONSHIP_LOAD_LIMIT)
    check_tables: bool = field(default=False)
    distinct: bool = field(default=False)
    conditions: Mapping[str, Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]] | None = field(
        default=None
    )
    self_key: str | None = field(default=None)
    order_by: tuple[str, ...] | None = field(default=None)
    query: sa.Select[tuple[T]] | None = field(default=None)


class _LoadParamsType[T: orm.DeclarativeBase](TypedDict, total=False):
    model: Required[type[T]]
    loads: tuple[str, ...]
    node: Node
    check_tables: bool
    conditions: frozendict[str, Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]]
    self_key: str
    order_by: tuple[str, ...]
    query: sa.Select[tuple[T]]
    distinct: bool
    limit: int | None


@lru_cache(maxsize=1028)
def _bfs_search[T: orm.DeclarativeBase](
    start: type[T],
    end: str,
    node: Node,
) -> Sequence[orm.RelationshipProperty[T]]:
    queue: deque[Any] = deque([[start]])
    seen = set()

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current in seen:
            continue
        seen.add(current)

        relations = node.get(current)
        for relation in relations:
            new_path = [*path, relation]

            if relation.key == end:
                return [rel for rel in new_path if isinstance(rel, orm.RelationshipProperty)]

            queue.append([*new_path, relation.mapper.class_])

    return []


def _construct_strategy[T: orm.DeclarativeBase](
    strategy: Callable[..., _AbstractLoad],
    relationship: orm.RelationshipProperty[T],
    current: _AbstractLoad | None = None,
    **kw: Any,
) -> _AbstractLoad:
    _strategy: _AbstractLoad = (
        strategy(relationship, **kw)
        if current is None
        else getattr(current, strategy.__name__)(relationship, **kw)
    )

    return _strategy


def _load_self[T: orm.DeclarativeBase](
    query: sa.Select[tuple[T]],
    params: _LoadSelfParams[T],
) -> tuple[sa.Select[tuple[T]], _AbstractLoad]:
    (
        load,
        relationship,
        order_by,
        relation_cls,
        limit,
        model,
        self_key,
        conditions,
    ) = (
        params.load,
        params.relationship,
        params.order_by,
        params.relationship.mapper.class_,
        params.limit,
        params.model,
        params.self_key,
        params.conditions or {},
    )
    name = f"{get_table_name(relation_cls)}_{relationship.key}"
    alias: LateralFromClause | type[T]

    alias = orm.aliased(relation_cls, name=name)

    if limit:
        subq = _apply_conditions(
            _apply_order_by(
                sa.select(alias)
                .limit(limit)
                .where(get_primary_key(model) == getattr(alias, self_key)),
                relation_cls,
                order_by,
            ),
            relationship.key,
            conditions,
        )
        lateral = subq.lateral(name=name)
        query = query.outerjoin(lateral, sa.true())
        alias = lateral
    else:
        query = _apply_conditions(
            query.outerjoin(alias, getattr(alias, self_key) == get_primary_key(model)),
            relationship.key,
            conditions,
        )

    load = _construct_strategy(orm.contains_eager, relationship, load, alias=alias)

    return query, load


def _apply_conditions[T: orm.DeclarativeBase](
    query: sa.Select[tuple[T]],
    key: str,
    conditions: Mapping[str, Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]],
) -> sa.Select[tuple[T]]:
    return condition(query) if conditions and (condition := conditions.get(key)) else query


def _apply_order_by[T: orm.DeclarativeBase](
    query: sa.Select[tuple[T]],
    relation_cls: type[T],
    order_by: tuple[str, ...] | None = None,
) -> sa.Select[tuple[T]]:
    ob = (
        (getattr(relation_cls, by).desc() for by in order_by)
        if order_by
        else (pk.desc() for pk in relation_cls.__table__.primary_key)
    )
    return query.order_by(*ob)


def _load_relationship[T: orm.DeclarativeBase](
    query: sa.Select[tuple[T]],
    params: _LoadRelationParams[T],
) -> tuple[sa.Select[tuple[T]], _AbstractLoad]:
    (
        load,
        relationship,
        order_by,
        relation_cls,
        limit,
        model,
        conditions,
        is_alias,
        check_tables,
    ) = (
        params.load,
        params.relationship,
        params.order_by,
        params.relationship.mapper.class_,
        params.limit,
        params.model,
        params.conditions or {},
        params.is_alias,
        params.check_tables,
    )
    if relation_cls is model:
        if relationship.uselist:
            return _load_self(query, _LoadSelfParams.from_relation_params(params))
        else:
            return _load_self(query, _LoadSelfParams.from_relation_params(params))

    if relationship.uselist:
        if limit is None:
            load = _construct_strategy(orm.subqueryload, relationship, load)
        else:
            subq = _apply_conditions(
                _apply_order_by(sa.select(relation_cls).limit(limit), relation_cls, order_by),
                relationship.key,
                conditions,
            )

            if relationship.secondary is not None and relationship.secondaryjoin is not None:
                subq = subq.where(sa.text(str(relationship.secondaryjoin)))
                query = query.outerjoin(relationship.secondary, relationship.primaryjoin)
            else:
                subq = subq.where(sa.text(str(relationship.primaryjoin)))

            lateral_name = (
                f"{get_table_name(relation_cls)}_{relationship.key}"
                if is_alias
                else get_table_name(relation_cls)
            )
            if check_tables and lateral_name in get_table_names(query):
                lateral_name = f"{lateral_name}_alias"

            lateral = subq.lateral(name=lateral_name)

            query = query.outerjoin(lateral, sa.true())
            load = _construct_strategy(orm.contains_eager, relationship, load, alias=lateral)
    elif is_alias:
        load = _construct_strategy(orm.selectinload, relationship, load)
    else:
        query = _apply_conditions(
            query.outerjoin(relation_cls, relationship.primaryjoin),
            relationship.key,
            conditions,
        )
        load = _construct_strategy(orm.contains_eager, relationship, load)

    return query, load


def _construct_loads[T: orm.DeclarativeBase](
    query: sa.Select[tuple[T]],
    excludes: set[type[T] | str],
    relationships: Sequence[orm.RelationshipProperty[T]],
    params: _ConstructLoadsParams[T],
) -> tuple[sa.Select[tuple[T]], list[_AbstractLoad | LoaderCriteriaOption] | None]:
    if not relationships:
        return query, None

    load: _AbstractLoad | None = None
    load_criteria = []
    for relationship in relationships:
        relation_cls = relationship.mapper.class_
        key = relationship.key
        if (
            params.conditions
            and (condition := params.conditions.get(key))
            and (
                (relationship.uselist and params.limit is None)
                or (relation_cls in excludes and key not in excludes)
            )
        ) and (clause := condition(sa.select(relation_cls)).whereclause) is not None:
            load_criteria.append(orm.with_loader_criteria(relation_cls, clause))

        if relation_cls in excludes:
            if key not in excludes:
                query, load = _load_relationship(
                    query,
                    _LoadRelationParams.from_construct_loads_params(
                        params, relationship, load, is_alias=True
                    ),
                )
            continue

        excludes.update({relation_cls, key})
        query, load = _load_relationship(
            query,
            _LoadRelationParams.from_construct_loads_params(
                params, relationship, load, is_alias=False
            ),
        )

    return query, [load, *load_criteria] if load else None


@lru_cache(maxsize=1028)
def _select_with_relationships[T: orm.DeclarativeBase](
    params: _LoadParams[T],
) -> sa.Select[tuple[T]]:
    loads, model, query, node = (
        list(params.loads),
        params.model,
        params.query,
        params.node,
    )
    assert orm.DeclarativeBase not in model.__bases__, "model must not be orm.DeclarativeBase"
    assert model is not orm.DeclarativeBase, "model must not be orm.DeclarativeBase"

    if query is None:
        query = sa.select(model)

    options = []
    excludes: set[type[T] | str] = set()
    while loads:
        result = _bfs_search(model, loads.pop(), node)
        if not result:
            continue
        query, load = _construct_loads(
            query, excludes, result, _ConstructLoadsParams.from_params(params)
        )
        if load:
            options += load

    if options:
        query = query.options(*options)

    return query.distinct() if params.distinct else query


def select_with_relationships[T: orm.DeclarativeBase](
    **params: Unpack[_LoadParamsType[T]],
) -> sa.Select[tuple[T]]:
    if conditions := params.get("conditions"):
        params["conditions"] = frozendict(conditions)

    return _select_with_relationships(_LoadParams[T](**params))
