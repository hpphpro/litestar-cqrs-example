from __future__ import annotations

from backend.app.contracts.manager import TransactionManager
from backend.infra.database.alchemy.dao import DAO
from backend.infra.database.alchemy.entity import Entity
from backend.infra.database.alchemy.tools import get_entity_from_generic
from backend.shared.types import is_typevar


class UnboundRepository:
    __slots__ = ("_manager",)

    def __init__(self, manager: TransactionManager) -> None:
        self._manager = manager

    @property
    def manager(self) -> TransactionManager:
        return self._manager


class BoundRepository[E: Entity](UnboundRepository):
    _entity: type[E]
    __slots__ = ("_dao",)

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "_entity") or is_typevar(cls._entity):
            cls._entity = get_entity_from_generic(cls, ensure_exists=True)

        return super().__init_subclass__()

    def __init__(self, manager: TransactionManager, dao: DAO[E] | None = None) -> None:
        super().__init__(manager)
        self._dao = dao or DAO[E](manager, entity=self.entity)

    @property
    def entity(self) -> type[E]:
        return self._entity
