from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class OffsetPaginationResult[T]:
    items: Sequence[T]
    limit: int | None
    offset: int | None
    total: int


@dataclass(frozen=True)
class CursorPaginationResult[C, T]:
    items: Sequence[T]
    results_per_page: int
    cursor: C | None


OrderBy = Literal["ASC", "DESC"]
JsonLoads = Callable[..., Any]
JsonDumps = Callable[..., str]
CursorIntegerType = Literal["INTEGER"]
CursorUUIDType = Literal["UUID"]
CursorType = Literal[CursorUUIDType, CursorIntegerType]
