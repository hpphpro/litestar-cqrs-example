from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any


def _compute_hash[K, V](value: dict[K, V]) -> int:
    h = 0
    for k, v in value.items():
        h ^= hash((k, v))

    return h


class frozendict[K, V](Mapping[K, V]):  # noqa: N801
    __slots__ = ("_dict", "_hash")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._dict: dict[K, V] = dict(*args, **kwargs)
        self._hash = _compute_hash(self._dict)

    def __getitem__(self, key: K) -> V:
        return self._dict[key]

    def __contains__(self, key: Any) -> bool:
        return key in self._dict

    def copy(self, **add_or_replace: Any) -> frozendict[K, V]:
        return type(self)(self, **add_or_replace)

    def __iter__(self) -> Iterator[K]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self._dict!r}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, frozendict):
            return self._dict == other._dict

        if isinstance(other, dict):
            return self._dict == other

        return NotImplemented

    def __hash__(self) -> int:
        return self._hash
