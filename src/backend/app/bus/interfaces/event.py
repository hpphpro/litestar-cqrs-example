import abc
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Event(Protocol):
    def name(self) -> str: ...
    def serialize(self) -> bytes: ...


class EventHandler[E: Event](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__(self, event: E, /, **kw: Any) -> None:
        raise NotImplementedError
