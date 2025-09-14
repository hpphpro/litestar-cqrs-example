from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import ClassVar, final

from sqlalchemy import orm

from .datastructures import frozendict


@final
class Node:
    __instance: ClassVar[Node | None] = None
    _node: Mapping[
        type[orm.DeclarativeBase], Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]
    ]

    def __new__(
        cls,
        node: Mapping[
            type[orm.DeclarativeBase], Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]
        ]
        | None = None,
    ) -> Node:
        if cls.__instance is None:
            instance = super().__new__(cls)
            if node is not None:
                instance.set_node(node)

            cls.__instance = instance

        if not getattr(cls.__instance, "_node", None):
            raise RuntimeError("Node is not initialized or empty")

        return cls.__instance

    def get(
        self, model: type[orm.DeclarativeBase]
    ) -> Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]:
        return self.node.get(model, ())

    def __getitem__(
        self, model: type[orm.DeclarativeBase]
    ) -> Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]:
        return self.node[model]

    @property
    def node(
        self,
    ) -> Mapping[
        type[orm.DeclarativeBase], Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]
    ]:
        return self._node

    def set_node(
        self,
        node: Mapping[
            type[orm.DeclarativeBase], Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]
        ],
    ) -> None:
        self._node = node


def get_node(
    base: type[orm.DeclarativeBase],
) -> Mapping[
    type[orm.DeclarativeBase], Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]
]:
    assert orm.DeclarativeBase in base.__bases__, "base must be a subclass of orm.DeclarativeBase"

    return frozendict({
        mapper.class_: tuple(mapper.relationships.values()) for mapper in base.registry.mappers
    })


def init_node(
    node: Mapping[
        type[orm.DeclarativeBase], Sequence[orm.RelationshipProperty[type[orm.DeclarativeBase]]]
    ],
) -> None:
    Node(node)
