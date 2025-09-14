import re
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Final, TypedDict, override

from backend.app.contracts import exceptions as exc

from .base import BaseData


MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 32
EMAIL_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+)*@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])$",
)


@dataclass(slots=True)
class CreateUserData(BaseData):
    email: str
    password: str

    @override
    def _validate(self) -> None:
        if not (MIN_PASSWORD_LENGTH <= len(self.password) <= MAX_PASSWORD_LENGTH):
            raise exc.BadRequestError(
                f"Password must be between {MIN_PASSWORD_LENGTH} "
                f"and {MAX_PASSWORD_LENGTH} characters",
            )

        if not EMAIL_REGEX.match(self.email):
            raise exc.BadRequestError("Invalid email address")


@dataclass(slots=True)
class UpdateUserData(BaseData):
    email: str | None = None
    password: str | None = None

    @override
    def _validate(self) -> None:
        if self.password is not None and not (
            MIN_PASSWORD_LENGTH <= len(self.password) <= MAX_PASSWORD_LENGTH
        ):
            raise exc.BadRequestError(
                f"Password must be between {MIN_PASSWORD_LENGTH} "
                f"and {MAX_PASSWORD_LENGTH} characters",
            )

        if self.email is not None and not EMAIL_REGEX.match(self.email):
            raise exc.BadRequestError("Invalid email address")


class FilterOneUser(TypedDict, total=False):
    id: uuid.UUID
    email: str


class FilterManyUser(TypedDict, total=False):
    email: str
    from_date: date
    to_date: date
