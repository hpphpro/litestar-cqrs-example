from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm


@lru_cache
def _get_primary_key[T: orm.DeclarativeBase](model: type[T]) -> sa.ColumnElement[Any]:
    return next(iter(model.__table__.primary_key))


@lru_cache
def _get_table_name[T: orm.DeclarativeBase](model: type[T]) -> str:
    result = getattr(
        model,
        "__tablename__",
        model.__table__.description,
    )
    if not result:
        raise ValueError(f"Cannot determine tablename for {model}")

    return result


def get_table_name[T: orm.DeclarativeBase](model: type[T]) -> str:
    return _get_table_name(model)


def get_primary_key[T: orm.DeclarativeBase](model: type[T]) -> sa.ColumnElement[Any]:
    return _get_primary_key(model)


def get_table_names[T: orm.DeclarativeBase](query: sa.Select[tuple[T]]) -> Sequence[str]:
    seen = set()
    out: list[str] = []

    for root in query.get_final_froms():
        if type(root) is sa.Table:
            name = root.name
            if name not in seen:
                seen.add(name)
                out.append(name)
            continue

        if not isinstance(root, (sa.Join | sa.Alias)):
            continue

        stack: list[sa.FromClause | sa.Join | sa.Alias] = [root]

        while stack:
            node = stack.pop()

            if isinstance(node, sa.Table):
                name = node.name
                if name not in seen:
                    seen.add(name)
                    out.append(name)
            elif isinstance(node, sa.Join):
                stack.extend((node.left, node.right))
            elif isinstance(node, sa.Alias):
                stack.append(node.element)

    return out


def add_conditions[T: orm.DeclarativeBase](
    *conditions: sa.ColumnExpressionArgument[bool],
) -> Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]:
    def _add(query: sa.Select[tuple[T]]) -> sa.Select[tuple[T]]:
        return query.where(*conditions)

    return _add
