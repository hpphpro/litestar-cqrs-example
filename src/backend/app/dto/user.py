from __future__ import annotations

import uuid
from datetime import datetime

from msgspec import field

from backend.app.contracts.types.user import EMAIL_REGEX

from . import rbac
from .base import ExcludeDefaultsDTO


class UserPublic(ExcludeDefaultsDTO):
    id: uuid.UUID
    email: str
    created_at: datetime
    updated_at: datetime

    # relation
    roles: list[rbac.Role] = field(default_factory=list)


class LoginUser(ExcludeDefaultsDTO):
    fingerprint: str
    email: str
    password: str

    def __post_init__(self) -> None:
        if not EMAIL_REGEX.match(self.email):
            raise ValueError("Invalid email address")


class LogoutUser(ExcludeDefaultsDTO):
    fingerprint: str


class RefreshUser(ExcludeDefaultsDTO):
    fingerprint: str
