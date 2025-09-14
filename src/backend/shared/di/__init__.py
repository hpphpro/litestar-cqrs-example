import inspect
from collections.abc import Callable, Coroutine
from contextlib import AsyncExitStack, ExitStack
from functools import wraps
from typing import TYPE_CHECKING, Any, overload

from . import depends
from .container import DependencyContainer, get_generation, reset_dependencies


__all__ = (
    "DependencyContainer",
    "Depends",
    "FromScope",
    "get_generation",
    "inject",
    "is_injected",
    "reset_dependencies",
)


if TYPE_CHECKING:
    type Depends[T] = T
else:
    Depends = depends.Depends


def FromScope(dependency: Any | None = None) -> Any:  # noqa: N802
    return depends.Depends(dependency)


def is_injected(obj: Any) -> bool:
    return hasattr(obj, "__injected__")


def _wrap_sync_injection[**P, R](
    func: Callable[P, R],
    container: DependencyContainer,
    cache: dict[str, depends.Depends[Any]],
) -> Callable[P, R]:
    @wraps(func)
    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with ExitStack() as exits:
            return func(
                *args,
                **kwargs,
                **{k: v.resolve_sync(container, exits) for k, v in cache.items()},
            )

    return _wrapper


def _wrap_async_injection[**P, R](
    coro: Callable[P, Coroutine[Any, Any, R]],
    container: DependencyContainer,
    cache: dict[str, depends.Depends[Any]],
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(coro)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        async with AsyncExitStack() as exits:
            result = await coro(
                *args,
                **kwargs,
                **{k: await v.resolve_async(container, exits) for k, v in cache.items()},
            )

        return result  # noqa: RET504

    return _wrapper


@overload
def inject[**P, R](__func: Callable[P, R], /) -> Callable[P, R]: ...
@overload
def inject[**P, R](
    __coro: Callable[P, Coroutine[Any, Any, R]],
    /,
) -> Callable[P, Coroutine[Any, Any, R]]: ...
def inject(__func_or_coro: Any, /) -> Any:
    if is_injected(__func_or_coro):
        return __func_or_coro

    container = DependencyContainer()
    signature = inspect.signature(__func_or_coro)
    annotations, new_sig = depends.remove_depends(signature)
    cache = {
        v.name: dep for _, v in signature.parameters.items() if (dep := depends.extract_depends(v))
    }

    if inspect.iscoroutinefunction(__func_or_coro):
        _wrapper = _wrap_async_injection(__func_or_coro, container=container, cache=cache)
    else:
        _wrapper = _wrap_sync_injection(__func_or_coro, container=container, cache=cache)

    _wrapper.__injected__ = True  # type: ignore[attr-defined]
    _wrapper.__annotations__ = annotations
    _wrapper.__signature__ = new_sig  # type: ignore[attr-defined]

    return _wrapper
