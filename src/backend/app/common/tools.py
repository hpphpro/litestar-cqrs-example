from __future__ import annotations

import inspect
import uuid
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import (
    Any,
)

import msgspec


def convert_to[T](cls: type[T], value: Any, **kw: Any) -> T:
    return msgspec.convert(
        value,
        cls,
        dec_hook=kw.pop("dec_hook", None),
        builtin_types=(bytes, bytearray, datetime, time, date, timedelta, uuid.UUID, Decimal),
        **kw,
    )


def convert_from(value: Any, **kw: Any) -> Any:
    return msgspec.to_builtins(
        value,
        builtin_types=(
            datetime,
            date,
            timedelta,
            Decimal,
            uuid.UUID,
            bytes,
            bytearray,
            memoryview,
            time,
        ),
        **kw,
    )


def msgpack_encoder(obj: Any, *args: Any, **kw: Any) -> bytes:
    return msgspec.msgpack.encode(obj, *args, **kw)


def msgpack_decoder(obj: Any, *args: Any, **kw: Any) -> Any:
    return msgspec.msgpack.decode(
        obj,
        *args,
        strict=kw.pop("strict", False),
        **kw,
    )


def msgspec_encoder(obj: Any, *args: Any, **kw: Any) -> str:
    return msgspec.json.encode(obj, *args, **kw).decode(encoding="utf-8")


def msgspec_decoder(obj: Any, *args: Any, **kw: Any) -> Any:
    return msgspec.json.decode(obj, *args, **kw)


def singleton[T](value: T) -> Callable[[], T]:
    def _factory() -> T:
        return value

    return _factory


type _AnyDependency = Callable[[], Any] | Any


def lazy[T](v: Callable[..., T], *args: _AnyDependency, **deps: _AnyDependency) -> Callable[[], T]:
    def _factory() -> T:
        return v(
            *(arg() if callable(arg) else arg for arg in args),
            **{k: dep() if callable(dep) else dep for k, dep in deps.items()},
        )

    return _factory


def lazy_single[T, D](v: Callable[[D], T], dep: Callable[[], D]) -> Callable[[], T]:
    return lazy(v, dep)


class ClosableProxy:
    __slots__ = (
        "_close_fn",
        "_target",
    )

    def __init__(self, target: Any, close_fn: Callable[[], Any]) -> None:
        self._target = target
        self._close_fn = close_fn

    async def close(self) -> None:
        if inspect.iscoroutinefunction(self._close_fn):
            await self._close_fn()
        else:
            res = self._close_fn()
            if inspect.isawaitable(res):
                await res

    def __getattr__(self, key: str) -> Any:
        return getattr(self._target, key)

    def __repr__(self) -> str:
        return f"{self._target!r}"
