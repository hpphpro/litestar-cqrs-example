from __future__ import annotations

import traceback
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, Literal, NamedTuple, overload

from sqlalchemy.exc import SQLAlchemyError

from backend.app.contracts.exceptions import AppError


class ResultImpl[T, E: Exception](NamedTuple):
    data: T | None
    err: E | None

    def __bool__(self) -> bool:
        return self.is_ok()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResultImpl):
            return NotImplemented

        return self.data == other.data and self.err == other.err

    def __hash__(self) -> int:
        return hash((self.data, self.err))

    def map_err[O: Exception](self, f: Callable[[E], O]) -> ResultImpl[T, O]:
        return (
            ResultImpl[T, O](self.data, f(self.err))
            if self.err is not None
            else ResultImpl[T, O](self.data, None)
        )

    def map[R](self, f: Callable[[T], R]) -> ResultImpl[R, E]:
        return (
            ResultImpl[R, E](f(self.data), self.err)
            if self.data is not None
            else ResultImpl[R, E](None, self.err)
        )

    def map_or[R](self, default: R, f: Callable[[T], R]) -> R:
        return f(self.data) if self.data is not None else default

    def unwrap(self) -> T:
        if self.data is None:
            if self.err is not None and isinstance(self.err, AppError):
                raise self.err
            raise AppError("\n".join(self.err.args) if self.err else "Empty result") from self.err

        return self.data

    def and_then[R](self, f: Callable[[T], R | None]) -> ResultImpl[R, E]:
        return (
            ResultImpl[R, E](f(self.data), self.err)
            if self.data is not None
            else ResultImpl[R, E](None, self.err)
        )

    def unwrap_or(self, default: T) -> T:
        return default if self.data is None else self.data

    def unwrap_or_raise(self, err: E) -> T:
        if self.data is None:
            raise err from self.err

        return self.data

    def unwrap_or_else(self, f: Callable[[E | None], T]) -> T:
        return f(self.err) if self.data is None else self.data

    def is_ok(self) -> bool:
        return self.data is not None

    def is_err(self) -> bool:
        return self.data is None


def _normalize_exc(e: Exception) -> AppError:
    if isinstance(e, AppError):
        return e

    if isinstance(e, SQLAlchemyError):
        ae = AppError(e._message().split(":", 1)[-1].strip())  # noqa: SLF001
    else:
        ae = AppError("\n".join(e.args) if e.args else None)

    tb = traceback.TracebackException.from_exception(e, capture_locals=False)
    formatted = "".join(tb.format())
    ae.add_note(f"\n\nOriginal traceback:\n{formatted}")

    return ae


def as_result_async[T, **P](
    f: Callable[P, Coroutine[Any, Any, T | None]], /
) -> Callable[P, Coroutine[Any, Any, ResultImpl[T, AppError]]]:
    @wraps(f)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> ResultImpl[T, AppError]:
        try:
            result = await f(*args, **kwargs)
            return ResultImpl(result, None if result is not None else AppError("Empty result"))
        except Exception as e:  # noqa: BLE001
            return ResultImpl(None, _normalize_exc(e))

    return _wrapper


def as_result_sync[T, **P](f: Callable[P, T | None], /) -> Callable[P, ResultImpl[T, AppError]]:
    @wraps(f)
    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> ResultImpl[T, AppError]:
        try:
            result = f(*args, **kwargs)
            return ResultImpl(result, None if result is not None else AppError("Empty result"))
        except Exception as e:  # noqa: BLE001
            return ResultImpl(None, _normalize_exc(e))

    return _wrapper


@overload
def as_result[T, E: Exception, **P](
    *,
    is_async: Literal[True] = True,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T | None]]],
    Callable[P, Coroutine[Any, Any, ResultImpl[T, AppError]]],
]: ...
@overload
def as_result[T, E: Exception, **P](
    *,
    is_async: Literal[False] = False,
) -> Callable[[Callable[P, T | None]], Callable[P, ResultImpl[T, AppError]]]: ...
def as_result[T, E: Exception, **P](
    *,
    is_async: bool = True,
) -> (
    Callable[[Callable[P, T | None]], Callable[P, ResultImpl[T, AppError]]]
    | Callable[
        [Callable[P, Coroutine[Any, Any, T | None]]],
        Callable[P, Coroutine[Any, Any, ResultImpl[T, AppError]]],
    ]
):
    if is_async:
        return as_result_async
    else:
        return as_result_sync
