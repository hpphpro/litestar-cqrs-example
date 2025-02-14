from typing import Final

from sqlalchemy.orm import RelationshipProperty

from src.database._util import frozendict
from src.database.alchemy.entity.base import Entity
from src.database.alchemy.entity.user import User


__all__ = (
    "Entity",
    "User",
)


def _retrieve_relationships() -> dict[type[Entity], tuple[RelationshipProperty[type[Entity]], ...]]:
    return {
        mapper.class_: tuple(mapper.relationships.values()) for mapper in Entity.registry.mappers
    }


MODELS_RELATIONSHIPS_NODE: Final[
    frozendict[type[Entity], tuple[RelationshipProperty[type[Entity]]]]
] = frozendict(_retrieve_relationships())
