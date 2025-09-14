from __future__ import annotations

from typing import Any, ClassVar


class AppError(Exception):
    message: ClassVar[str] = "App exception"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
    ) -> None:
        self.content: dict[str, Any] = {"message": message or self.message}
        if code:
            self.content["code"] = code

    def as_dict(self) -> dict[str, Any]:
        return {"content": self.content.copy()}

    @property
    def raw_message(self) -> str:
        return self.content.get("message", self.message) or self.message

    @property
    def raw_code(self) -> str | None:
        return self.content.get("code")

    def __repr__(self) -> str:
        content = ", ".join(f"{key}={value!r}" for key, value in self.as_dict().items())
        return f"{type(self).__name__}({content})"


class DetailedError(AppError):
    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        **context: Any,
    ) -> None:
        super().__init__(message=message, code=code)
        self.content = {**self.content, **context}

    @classmethod
    def from_other(cls, other: AppError) -> AppError:
        return cls(
            message=cls.message,
            code=other.raw_code,
            detail=other.raw_message,
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.content!r}"


class UnAuthorizedError(DetailedError):
    message: ClassVar[str] = "Unauthorized"


class NotFoundError(DetailedError):
    message: ClassVar[str] = "Not Found"


class BadRequestError(DetailedError):
    message: ClassVar[str] = "Bad Request"


class TooManyRequestsError(DetailedError):
    message: ClassVar[str] = "Too Many Requests"


class ServiceUnavailableError(DetailedError):
    message: ClassVar[str] = "Service Unavailable"


class ForbiddenError(DetailedError):
    message: ClassVar[str] = "Forbidden"


class ServiceNotImplementedError(DetailedError):
    message: ClassVar[str] = "Not Implemented"


class ConflictError(DetailedError):
    message: ClassVar[str] = "Conflict"


class RequestTimeoutError(DetailedError):
    message: ClassVar[str] = "Request Timeout"


class UnprocessableEntityError(DetailedError):
    message: ClassVar[str] = "Unprocessable Entity"
