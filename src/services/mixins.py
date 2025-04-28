from collections.abc import Callable
from typing import Any


class CacheableServiceMixin:
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def _get_or_create[**P, S](
        self, key: str, factory: Callable[P, S], *args: P.args, **kw: P.kwargs
    ) -> S:
        if not (service := self._cache.get(key)):
            service = factory(*args, **kw)

            self._cache[key] = service

        return service
