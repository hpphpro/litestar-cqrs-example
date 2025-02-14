from typing import Any, Protocol, runtime_checkable

from src.api.common.interfaces.handler import Handler
from src.api.common.interfaces.proxy import AwaitableProxy


@runtime_checkable
class QCBusType(Protocol):
    def __call__(
        self, request: Any, qc: Any, /, **kw: Any
    ) -> AwaitableProxy[Handler[Any, Any, Any]]: ...
    def send_unwrapped(
        self, request: Any, qc: Any, /, **kw: Any
    ) -> AwaitableProxy[Handler[Any, Any, Any]]: ...


@runtime_checkable
class EventBusType(Protocol):
    async def publish(self, event: Any, /, **kw: Any) -> None: ...
