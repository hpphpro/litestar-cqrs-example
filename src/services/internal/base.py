from typing import get_args

from src.database._util import is_typevar
from src.database.alchemy.dao import DAO
from src.database.alchemy.entity.base.core import Entity
from src.database.interfaces.manager import TransactionManager


class InternalService[E: Entity]:
    __slots__ = ("_manager", "_dao")

    def __init__(self, manager: TransactionManager, dao: DAO[E] | None = None) -> None:
        self._manager = manager
        self._dao = dao or DAO[E](manager, entity=self._type_from_generic())

    @property
    def manager(self) -> TransactionManager:
        return self._manager

    def _type_from_generic(self) -> type[E]:
        entity: type[E]

        bases = getattr(self, "__orig_bases__", None)

        assert bases, "Generic type must be set"

        service, *_ = bases

        (entity,) = get_args(service)

        assert not is_typevar(entity) and issubclass(entity, Entity), "Generic type must be Entity"

        return entity
