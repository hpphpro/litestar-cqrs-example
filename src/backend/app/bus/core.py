from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from backend.app.contracts.dto import DTO

from .interfaces.bus import AwaitableProxy
from .interfaces.event import Event, EventHandler
from .interfaces.handler import Handler, HandlerType
from .interfaces.middleware import MiddlewareType
from .middlewares import wrap_middleware


if TYPE_CHECKING:
    from .builder import BusBuilder

type HandlerLike = Callable[[], HandlerType] | HandlerType
type EventHandlerLike = Callable[[], EventHandler[Any]] | EventHandler[Any]
logger = logging.getLogger(__name__)


class UnregisteredHandlerError(Exception): ...


def _resolve_factory[T](v: Callable[[], T] | T, compare_with: type[Any]) -> T:
    return v if isinstance(v, compare_with) or not callable(v) else v()


async def _safe_invoke[E: Event](event: E, handler: EventHandler[E], /, **kw: Any) -> None:
    try:
        await handler(event, **kw)
    except Exception as e:
        logger.exception(
            "Error occurred in handler: %s\nError: %s -> %s",
            type(handler).__name__,
            type(e).__name__,
            e.args,
        )


class QCBus:
    __slots__ = (
        "_data",
        "_dispatch_fn",
    )

    def __init__(self, *middlewares: MiddlewareType) -> None:
        self._data: dict[type[DTO], HandlerLike] = {}
        self._dispatch_fn = self._make_dispatch(*middlewares)

    def _make_dispatch(self, *middlewares: MiddlewareType) -> HandlerType:
        async def dispatch[T, Q: DTO, R](context: T, qce: Q, /) -> R:
            handler: Handler[T, Q, R] = self._get_handler(qce)

            return await handler(context, qce)

        return cast(HandlerType, wrap_middleware(dispatch, *middlewares))

    def __call__[T, Q: DTO, R](self, context: T, qc: Q, /) -> AwaitableProxy[Handler[T, Q, R]]:
        return AwaitableProxy(self._dispatch_fn, context, qc)

    def register[T, Q: DTO, R](
        self,
        qc: type[Q],
        handler: Callable[[], Handler[T, Q, R]] | Handler[T, Q, R],
    ) -> QCBus:
        self._data[qc] = handler

        return self

    def send_unwrapped[T, Q: DTO, R](
        self,
        context: T,
        qc: Q,
        /,
    ) -> AwaitableProxy[Handler[T, Q, R]]:
        return AwaitableProxy(self._get_handler(qc), context, qc)

    def _get_handler[T, Q: DTO, R](self, qc: Q) -> Handler[T, Q, R]:
        try:
            return _resolve_factory(self._data[type(qc)], Handler)
        except KeyError as e:
            raise UnregisteredHandlerError(f"Handler for `{type(qc)}` is not registered") from e

    @staticmethod
    def builder() -> BusBuilder:
        from .builder import BusBuilder

        return BusBuilder()


class AnyEventMarker:
    def name(self) -> str:
        return "any_event"

    def serialize(self) -> bytes:
        return b""


class EventBus:
    __slots__ = ("_events",)

    def __init__(self) -> None:
        self._events: defaultdict[type[Event], list[EventHandlerLike]] = defaultdict(list)

    def register[E: Event](
        self,
        event_type: type[E],
        *handlers: Callable[[], EventHandler[E]] | EventHandler[E],
    ) -> EventBus:
        self._events[event_type].extend(handlers)

        return self

    def register_any(
        self,
        *handlers: Callable[[], EventHandler[Event]] | EventHandler[Event],
    ) -> EventBus:
        self.register(AnyEventMarker, *handlers)

        return self

    async def publish[E: Event](self, event: E, /, **kw: Any) -> None:
        handlers = self._events.get(type(event), []) or self._events.get(AnyEventMarker, [])
        if not handlers:
            return

        asyncio.gather(
            *(_safe_invoke(event, _resolve_factory(task, EventHandler), **kw) for task in handlers)
        )
