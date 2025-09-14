from __future__ import annotations

import uuid
from dataclasses import dataclass

from backend.app.contracts.dto import DTO
from backend.app.contracts.pagination import CursorPaginationResult, OffsetPaginationResult

from . import rbac, user
from .base import BaseDTO, ExcludeDefaultsDTO, StrictBaseDTO


__all__ = (
    "BaseDTO",
    "CursorResult",
    "ExcludeDefaultsDTO",
    "OffsetResult",
    "Status",
    "StrictBaseDTO",
    "rbac",
    "user",
)


class Status(BaseDTO):
    status: bool


@dataclass(frozen=True, slots=True)
class Id[T: uuid.UUID | int | str]:
    id: T


@dataclass(frozen=True, slots=True)
class OffsetResult[T]:
    items: list[T]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_[E, O: DTO](cls, result: OffsetPaginationResult[E], typ: type[O]) -> OffsetResult[O]:
        return OffsetResult[O](
            items=[typ.from_attributes(item) for item in result.items],
            limit=result.limit or 0,
            offset=result.offset or 0,
            total=result.total,
        )


@dataclass(frozen=True, slots=True)
class CursorResult[C, T]:
    items: list[T]
    results_per_page: int
    cursor: C | None

    @classmethod
    def from_[I, E, O: DTO](
        cls,
        result: CursorPaginationResult[I, E],
        typ: type[O],
    ) -> CursorResult[I, O]:
        return CursorResult[I, O](
            items=[typ.from_attributes(item) for item in result.items],
            results_per_page=result.results_per_page,
            cursor=result.cursor,
        )
