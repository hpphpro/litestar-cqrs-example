import enum
from dataclasses import dataclass
from typing import Annotated

from litestar.params import Parameter

from backend.app.contracts.pagination import CursorPagination, OffsetPagination, SortOrder
from backend.app.dto import BaseDTO
from backend.http.common.constants import MAX_PAGINATION_LIMIT, MIN_PAGINATION_LIMIT
from backend.http.common.tools import page_to_offset


@dataclass(slots=True, frozen=True)
class HealthCheck:
    status: bool


@enum.unique
class PaginationKind(enum.StrEnum):
    OFFSET = enum.auto()
    CURSOR = enum.auto()


class PagedOffsetPagination(BaseDTO):
    page: Annotated[int, Parameter(description="Current `page`")] = 1
    limit: Annotated[
        int,
        Parameter(ge=MIN_PAGINATION_LIMIT, le=MAX_PAGINATION_LIMIT, description="Items limit"),
    ] = MIN_PAGINATION_LIMIT
    order_by: Annotated[SortOrder, Parameter(description="`sorting` strategy")] = "ASC"

    def to_offset_pagination(self) -> OffsetPagination:
        return OffsetPagination(
            offset=page_to_offset(self.page, self.limit),
            limit=self.limit,
            order_by=self.order_by,
        )


class CombinedPagination(BaseDTO):
    kind: Annotated[
        PaginationKind,
        Parameter(description="Either `offset` or `cursor`", required=True),
    ]
    page: Annotated[int, Parameter(description="Current `page`")] = 1
    order_by: Annotated[SortOrder, Parameter(description="`sorting` strategy")] = "ASC"
    limit: Annotated[
        int,
        Parameter(ge=MIN_PAGINATION_LIMIT, le=MAX_PAGINATION_LIMIT, description="Items `limit`"),
    ] = MIN_PAGINATION_LIMIT
    cursor: Annotated[str | None, Parameter(description="Current `cursor`")] = None

    def to_offset_pagination(self) -> OffsetPagination:
        return OffsetPagination(
            offset=page_to_offset(self.page, self.limit),
            limit=self.limit,
            order_by=self.order_by,
        )

    def to_cursor_pagination(self) -> CursorPagination:
        return CursorPagination(order_by=self.order_by, limit=self.limit, cursor=self.cursor)
