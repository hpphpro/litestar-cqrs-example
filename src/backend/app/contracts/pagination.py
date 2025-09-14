from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal


type SortOrder = Literal["ASC", "DESC"]


@dataclass(frozen=True, slots=True)
class _AsDict:
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OffsetPaginationResult[T](_AsDict):
    items: Sequence[T]
    limit: int | None
    offset: int | None
    total: int


@dataclass(frozen=True, slots=True)
class CursorPaginationResult[C, T](_AsDict):
    items: Sequence[T]
    results_per_page: int
    cursor: C | None


@dataclass(frozen=True, slots=True)
class OffsetPagination(_AsDict):
    offset: int
    limit: int
    order_by: SortOrder


@dataclass(frozen=True, slots=True)
class CursorPagination(_AsDict):
    order_by: SortOrder
    limit: int
    cursor: str | None
