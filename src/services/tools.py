from __future__ import annotations

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, NoReturn

from src.common.exceptions import AppException


def _raise_error(
    error: type[AppException] | AppException,
    reason: str,
    base_message: str,
    **additional: Any,
) -> NoReturn:
    if callable(error):
        if "{reason}" in base_message:
            message = base_message.format(reason=reason)
        else:
            message = f"{base_message}: <{reason}>"

        raise error(message, **additional)

    raise error


def on_error[**P, R](
    *uniques: str,
    should_raise: type[AppException] | AppException = AppException,
    base_message: str = "{reason} already in use",
    **additional: Any,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]],
    Callable[P, Coroutine[Any, Any, R]],
]:
    def _wrapper(
        coro: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(coro)
        async def _inner_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                if isinstance(e, AppException):
                    raise e
                origin = str(e.args[0]) if e.args else "Unknown"
                if not uniques:
                    _raise_error(should_raise, origin, base_message, **additional)

                for uniq in set(uniques):
                    if uniq in origin:
                        _raise_error(should_raise, uniq, base_message, **additional)

                raise AppException(message=origin) from e

        return _inner_wrapper

    return _wrapper
