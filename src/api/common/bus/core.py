from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, cast

from src.api.common.bus.middlewares.manager import HandlerMiddlewareManager
from src.api.common.interfaces.dto import DTO
from src.api.common.interfaces.event import Event, EventHandler
from src.api.common.interfaces.handler import Handler, HandlerType
from src.api.common.interfaces.middleware import MiddlewareType
from src.api.common.interfaces.proxy import AwaitableProxy


if TYPE_CHECKING:
    from src.api.common.bus.builder import BusBuilder

type HandlerLike = Callable[[], HandlerType] | HandlerType
type EventHandlerLike = Callable[[], EventHandler[Any]] | EventHandler[Any]


class UnregisteredHandlerError(Exception): ...


def _resolve_factory[T](v: Callable[[], T] | T, compare_with: type[Any]) -> T:
    if isinstance(v, compare_with):
        return cast(T, v)

    return v() if callable(v) else v


async def _safe_invoke[E: Event](event: E, handler: EventHandler[E], /, **kw: Any) -> None:
    try:
        await handler(event, **kw)
    except Exception as e:
        logging.exception(
            f"Error occurred in handler: {type(handler).__name__}"
            f"\nError: {type(e).__name__} -> {e.args}"
        )


class QCBus:
    __slots__ = (
        "_data",
        "manager",
    )

    def __init__(self, *middlewares: MiddlewareType) -> None:
        self._data: dict[type[DTO], HandlerLike] = {}
        self.manager: Final[HandlerMiddlewareManager] = HandlerMiddlewareManager(*middlewares)

    def __call__[T, Q: DTO](
        self, request: T, qce: Q, /, **kw: Any
    ) -> AwaitableProxy[Handler[T, Q, Any]]:
        handler: Handler[Any, Any, Any] = self._get_handler(qce)
        middleware = cast(
            Handler[Any, Any, Any],
            self.manager.wrap_middleware(handler),
        )

        return AwaitableProxy(middleware, request, qce, **kw)

    def register[T, Q: DTO, R: DTO | None](
        self, qc: type[Q], handler: Callable[[], Handler[T, Q, R]] | Handler[T, Q, R]
    ) -> QCBus:
        self._data[qc] = handler

        return self

    def send_unwrapped[T, Q: DTO](
        self, request: T, qc: Q, /, **kw: Any
    ) -> AwaitableProxy[Handler[T, Q, Any]]:
        return AwaitableProxy(self._get_handler(qc), request, qc, **kw)

    def _get_handler[T, Q: DTO, R: DTO | None](self, qc: Q) -> Handler[T, Q, R]:
        try:
            return _resolve_factory(self._data[type(qc)], Handler)
        except KeyError as e:
            raise UnregisteredHandlerError(f"Handler for `{type(qc)}` is not registered") from e

    @staticmethod
    def builder() -> BusBuilder:
        from .builder import BusBuilder

        return BusBuilder()


class EventBus:
    __slots__ = ("_events",)

    def __init__(self) -> None:
        self._events: defaultdict[type[Event], list[EventHandlerLike]] = defaultdict(list)

    def register[E: Event](
        self, event_type: type[E], *handlers: Callable[[], EventHandler[E]] | EventHandler[E]
    ) -> EventBus:
        for handler in handlers:
            self._events[event_type].append(handler)

        return self

    def register_any(
        self, *handlers: Callable[[], EventHandler[Event]] | EventHandler[Event]
    ) -> EventBus:
        self.register(Event, *handlers)

        return self

    async def publish[E: Event](self, event: E, /, **kw: Any) -> None:
        handlers = self._events.get(type(event), []) or self._events.get(Event, [])
        asyncio.gather(
            *(_safe_invoke(event, _resolve_factory(task, EventHandler), **kw) for task in handlers)
        )
