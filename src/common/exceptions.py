from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str = "App exception",
        headers: dict[str, Any] | None = None,
    ) -> None:
        self.content = {"message": message}
        self.headers = headers

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__


class DetailedError(AppException):
    def __init__(
        self,
        message: str,
        headers: dict[str, Any] | None = None,
        **additional: Any,
    ) -> None:
        super().__init__(message=message, headers=headers)
        self.content |= additional

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.content}\nHeaders: {self.headers or ''}"


class UnAuthorizedError(DetailedError):
    pass


class NotFoundError(DetailedError):
    pass


class BadRequestError(DetailedError):
    pass


class TooManyRequestsError(DetailedError):
    pass


class ServiceUnavailableError(DetailedError):
    pass


class ForbiddenError(DetailedError):
    pass


class ServiceNotImplementedError(DetailedError):
    pass


class ConflictError(DetailedError):
    pass


class RequestTimeoutError(DetailedError):
    pass
