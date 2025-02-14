from __future__ import annotations

import inspect
from collections.abc import Callable
from itertools import chain
from typing import TYPE_CHECKING, Any, Literal, get_args, get_origin, get_overloads

from src.api.common.interfaces.bus import QCBusType
from src.api.common.interfaces.dto import DTO
from src.api.common.interfaces.handler import Handler, HandlerType
from src.api.common.interfaces.middleware import MiddlewareType
from src.api.common.interfaces.proxy import AwaitableProxy


if TYPE_CHECKING:
    from src.api.common.bus.core import HandlerLike


type BusKind = Literal["query", "command", "auto"]
type Dependency = Callable[[], Any] | Any


def is_typevar[T: Any](t: T) -> bool:
    return hasattr(t, "__bound__") or hasattr(t, "__constraints__")


def _predict_dependency_or_raise(
    actual: dict[str, Any],
    expectable: dict[str, Any],
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    if not exclude:
        exclude = set()

    missing = [k for k in actual if k not in expectable and k not in exclude]
    if missing:
        details = ", ".join(f"`{k}`:`{actual[k]}`" for k in missing)
        raise TypeError(f"Did you forget to set dependency for {details}?")

    return {k: value if (value := expectable.get(k)) else actual[k] for k in actual}


def _retrieve_handler_params(handler: HandlerType) -> dict[str, Any]:
    return {k: v.annotation for k, v in inspect.signature(handler).parameters.items()}


def get_handlers_map(
    *buses: type[QCBusType], kind: BusKind = "auto"
) -> dict[type[DTO], dict[str, HandlerLike]]:
    data = {}

    for func in chain.from_iterable(get_overloads(bus.send_unwrapped) for bus in buses):
        sig = inspect.signature(func)
        params = {k: v.annotation for k, v in sig.parameters.items() if v.kind == v.POSITIONAL_ONLY}
        proxy = sig.return_annotation
        if kind == "auto":
            _, _, value, *_ = params.values()
            if not value or is_typevar(value) or not issubclass(value, DTO):
                kinds = ", ".join(v for v in get_args(BusKind) if v != kind)
                raise ValueError(
                    f"Could not determine param automatically in any kind of `{kinds}`. "
                    "Try to use one of it directly"
                )
            else:
                query_or_command = value
        else:
            query_or_command = params.get(kind)

        if not query_or_command or not proxy:
            raise TypeError(
                "Did you forget to annotate your overloads? "
                f"It should contain :{kind}: param and :return: AwaitableProxy generic"
            )

        origin = get_origin(proxy)

        if origin is not AwaitableProxy:
            raise TypeError("Return type must be a type of AwaitableProxy.")

        args = get_args(proxy)
        if not args:
            raise TypeError("AwaitableProxy must have generic parameter")

        handler = args[0]
        if not issubclass(handler, Handler):
            raise TypeError("handler must inherit from base Handler class.")

        data[query_or_command] = {"handler": handler, **_retrieve_handler_params(handler)}

    return data


def create_handler_factory[D: Dependency](
    handler: type[HandlerType], **dependencies: D
) -> Callable[[], HandlerType]:
    def _factory() -> HandlerType:
        return handler(**{k: v() if callable(v) else v for k, v in dependencies.items()})

    return _factory


class BusBuilder:
    def __init__(self) -> None:
        self._buses: list[type[QCBusType]] = []
        self._kind: BusKind = "auto"
        self._dependencies: dict[str, Callable[[], Any] | Any] = {}
        self._middlewares: list[MiddlewareType] = []

    def bus[T: type[QCBusType] | Any](self, v: T, /) -> BusBuilder:
        self._buses.append(v)

        return self

    def kind(self, value: BusKind, /) -> BusBuilder:
        self._kind = value

        return self

    def middleware(self, middleware: MiddlewareType, /) -> BusBuilder:
        self._middlewares.append(middleware)

        return self

    def middlewares(self, *middlewares: MiddlewareType) -> BusBuilder:
        for middleware in middlewares:
            self.middleware(middleware)

        return self

    def dependency[D: Dependency](self, key: str, value: D, /) -> BusBuilder:
        self._dependencies[key] = value

        return self

    def dependencies[D: Dependency](self, **dependencies: D) -> BusBuilder:
        for key, value in dependencies.items():
            self.dependency(key, value)

        return self

    def build(self) -> QCBusType:
        from .core import QCBus

        impl = QCBus(*self._middlewares)

        for qc, handler_data in get_handlers_map(*self._buses, kind=self._kind).items():
            impl.register(
                qc=qc,
                handler=create_handler_factory(
                    **_predict_dependency_or_raise(handler_data, self._dependencies, {"handler"})
                ),
            )

        return impl
