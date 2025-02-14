from src.api.common.dto import BaseDTO as BaseDTO
from src.api.v1.dto import healthcheck as healthcheck
from src.api.v1.dto import user as user


class OffsetResult[T](BaseDTO):
    items: list[T]
    limit: int
    offset: int
    total: int


class Status(BaseDTO):
    status: bool
