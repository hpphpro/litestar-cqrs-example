from dataclasses import dataclass, is_dataclass
from typing import Any, ClassVar, dataclass_transform

from litestar import MediaType, status_codes
from litestar.openapi.datastructures import ResponseSpec
from litestar.openapi.spec import Example


@dataclass_transform()
class BaseDoc:
    message: str
    status_code: ClassVar[int] = status_codes.HTTP_500_INTERNAL_SERVER_ERROR
    media_type: ClassVar[MediaType] = MediaType.JSON

    def __init_subclass__(cls, **kw: Any) -> None:
        if not is_dataclass(cls):
            dataclass(frozen=kw.pop("frozen", True), **kw)(cls)

    @classmethod
    def to_spec(
        cls,
        status_code: int | None = None,
        message: str | None = None,
        examples: list[Example] | None = None,
        media_type: MediaType = MediaType.JSON,
    ) -> dict[int, ResponseSpec]:
        status_code = status_code or cls.status_code
        media_type = media_type or cls.media_type
        return {
            status_code: ResponseSpec(
                cls,
                generate_examples=True,
                description=cls.message,
                media_type=media_type,
                examples=[
                    Example(
                        summary=message or cls.message,
                        value={"message": message or cls.message},
                    ),
                ]
                + (examples or []),
            ),
        }


class UnAuthorized(BaseDoc):
    message: str = "Unauthorized"
    status_code: ClassVar[int] = status_codes.HTTP_401_UNAUTHORIZED


class NotFound(BaseDoc):
    message: str = "Not found"
    status_code: ClassVar[int] = status_codes.HTTP_404_NOT_FOUND


class BadRequest(BaseDoc):
    message: str = "Bad Request"
    status_code: ClassVar[int] = status_codes.HTTP_400_BAD_REQUEST


class TooManyRequests(BaseDoc):
    message: str = "Too many requests"
    status_code: ClassVar[int] = status_codes.HTTP_429_TOO_MANY_REQUESTS


class ServiceUnavailable(BaseDoc):
    message: str = "Service temporary unavailable"
    status_code: ClassVar[int] = status_codes.HTTP_503_SERVICE_UNAVAILABLE


class Forbidden(BaseDoc):
    message: str = "You have no permission"
    status_code: ClassVar[int] = status_codes.HTTP_403_FORBIDDEN


class ServiceNotImplemented(BaseDoc):
    message: str = "Service not implemented"
    status_code: ClassVar[int] = status_codes.HTTP_501_NOT_IMPLEMENTED


class Conflict(BaseDoc):
    message: str = "Conflict"
    status_code: ClassVar[int] = status_codes.HTTP_409_CONFLICT


class Timeout(BaseDoc):
    message: str = "Timeout"
    status_code: ClassVar[int] = status_codes.HTTP_408_REQUEST_TIMEOUT


class InternalServer(BaseDoc):
    message: str = "Internal Server Error"
    status_code: ClassVar[int] = status_codes.HTTP_500_INTERNAL_SERVER_ERROR
