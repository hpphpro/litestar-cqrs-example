import enum
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypedDict


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


type OrderBy = Literal["ASC", "DESC"]
type JsonLoads = Callable[..., Any]
type JsonDumps = Callable[..., str]
type CursorIntegerType = Literal["INTEGER"]
type CursorUUIDType = Literal["UUID"]
type CursorType = Literal[CursorUUIDType, CursorIntegerType]


class UserCreate(TypedDict):
    login: str
    password: str


class UserUpdate(TypedDict, total=False):
    login: str
    password: str


class UnsetType(enum.Enum):
    UNSET = enum.auto()
