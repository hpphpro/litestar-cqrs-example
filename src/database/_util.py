from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any


def is_typevar[T: Any](t: T) -> bool:
    return hasattr(t, "__bound__") or hasattr(t, "__constraints__")


class frozendict[K, V](Mapping[K, V]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._dict = dict(*args, **kwargs)
        self._hash: int | None = None

    def __getitem__(self, key: Any) -> Any:
        return self._dict[key]

    def __contains__(self, key: Any) -> Any:
        return key in self._dict

    def copy(self, **add_or_replace: Any) -> frozendict[K, V]:
        return type(self)(self, **add_or_replace)

    def __iter__(self) -> Iterator[K]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self._dict!r}"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, frozendict):
            return self._dict == other._dict

        if isinstance(other, dict):
            return self._dict == other

        return NotImplemented

    def __hash__(self) -> int:
        if self._hash is None:
            h = 0
            for key, value in self._dict.items():
                h ^= hash((key, value))
            self._hash = h

        return self._hash
