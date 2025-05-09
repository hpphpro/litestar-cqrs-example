from __future__ import annotations

import abc

from src.database._util import is_typevar
from src.database.alchemy.dao import DAO
from src.database.alchemy.entity.base.core import Entity
from src.database.alchemy.tools import get_entity_from_generic
from src.database.interfaces.manager import TransactionManager


class InternalService[E: Entity](abc.ABC):
    _entity: type[E]
    __slots__ = ("_manager", "_dao")

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "_entity") or is_typevar(cls._entity):
            cls._entity = get_entity_from_generic(cls, ensure_exists=True)

        return super().__init_subclass__()

    def __init__(self, manager: TransactionManager, dao: DAO[E] | None = None) -> None:
        self._manager = manager
        self._dao = dao or DAO[E](manager, entity=self.__class__._entity)

    @property
    def manager(self) -> TransactionManager:
        return self._manager
