from __future__ import annotations

import uuid

from msgspec import field

from backend.app.contracts.auth import Action, Source

from . import user
from .base import ExcludeDefaultsDTO


class Role(ExcludeDefaultsDTO):
    id: uuid.UUID
    name: str

    # relation
    permissions: list[Permission] = field(default_factory=list)
    users: list[user.UserPublic] = field(default_factory=list)


class PermissionField(ExcludeDefaultsDTO):
    id: uuid.UUID
    permission_id: uuid.UUID
    name: str
    src: Source

    # relation
    permission: Permission | None = field(default=None)


class Permission(ExcludeDefaultsDTO):
    id: uuid.UUID
    resource: str
    action: Action
    operation: str
    description: str

    # relation
    fields: list[PermissionField] = field(default_factory=list)
