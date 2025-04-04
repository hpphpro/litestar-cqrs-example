from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import msgspec
from litestar import Router
from litestar.datastructures import State
from litestar.types import LifespanHook


def msgpack_encoder(obj: Any, *args: Any, **kw: Any) -> bytes:
    return msgspec.msgpack.encode(obj, *args, **kw)


def msgpack_decoder(obj: Any, *args: Any, **kw: Any) -> Any:
    return msgspec.msgpack.decode(obj, *args, strict=kw.pop("strict", False), **kw)


def msgspec_encoder(obj: Any, *args: Any, **kw: Any) -> str:
    return msgspec.json.encode(obj, *args, **kw).decode(encoding="utf-8")


def msgspec_decoder(obj: Any, *args: Any, **kw: Any) -> Any:
    return msgspec.json.decode(obj, *args, **kw)


def page_to_offset(page: int, limit: int) -> int:
    if page <= 0:
        return 0

    return (page - 1) * limit


def singleton[T](value: T) -> Callable[[], T]:
    def _factory() -> T:
        return value

    return _factory


type _AnyDependency = Callable[[], Any]


def lazy[T](v: Callable[..., T], *args: _AnyDependency, **deps: _AnyDependency) -> Callable[[], T]:
    def _factory() -> T:
        return v(*(arg() for arg in args), **{k: dep() for k, dep in deps.items()})

    return _factory


def lazy_single[T, D](v: Callable[[D], T], dep: Callable[[], D]) -> Callable[[], T]:
    return lazy(v, dep)


class ClosableProxy:
    __slots__ = (
        "_target",
        "_close_fn",
    )

    def __init__(self, target: Any, close_fn: Callable[[], Any]) -> None:
        self._target = target
        self._close_fn = close_fn

    async def close(self) -> None:
        if inspect.isawaitable(self._close_fn) or inspect.iscoroutinefunction(self._close_fn):
            await self._close_fn()
        else:
            self._close_fn()

    def __getattr__(self, key: str) -> Any:
        return getattr(self._target, key)

    def __repr__(self) -> str:
        return f"{self._target!r}"


@dataclass(frozen=True)
class RouterState:
    router: Router
    state: State
    on_startup: Sequence[LifespanHook] = field(default_factory=list)
    on_shutdown: Sequence[LifespanHook] = field(default_factory=list)
