from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Literal, Protocol, overload, runtime_checkable

from backend.app.contracts.manager import TransactionManager

from .result import AppResult


AUTH_KEY_PREFIX = "auth:{user_id}"


@enum.unique
class Scope(enum.StrEnum):
    OWN = enum.auto()
    ANY = enum.auto()


@enum.unique
class Action(enum.StrEnum):
    READ = enum.auto()
    CREATE = enum.auto()
    DELETE = enum.auto()
    UPDATE = enum.auto()


@enum.unique
class Source(enum.StrEnum):
    QUERY = enum.auto()
    JSON = enum.auto()


@enum.unique
class Effect(enum.StrEnum):
    ALLOW = enum.auto()
    DENY = enum.auto()


@dataclass(slots=True, frozen=True)
class PermissionSpec:
    resource: str
    action: Action
    operation: str
    description: str | None = None
    fields: Mapping[Source, frozenset[str]] = field(default_factory=dict)

    def key(self) -> str:
        return f"{self.resource}:{self.action.value}:{self.operation}".lower()


@dataclass(slots=True, frozen=True, eq=False)
class Permission:
    resource: str
    action: Action
    operation: str
    scope: Scope
    description: str | None = None
    deny_fields: Mapping[Source, frozenset[str]] = field(default_factory=dict)
    allow_fields: Mapping[Source, frozenset[str]] = field(default_factory=dict)

    def key(self) -> str:
        return f"{self.resource}:{self.action.value}:{self.operation}".lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return NotImplemented

        return self.key() == other.key()

    def __hash__(self) -> int:
        return hash(self.key())


@dataclass(slots=True, frozen=True)
class Role:
    name: str


@dataclass(slots=True, frozen=True)
class AuthUser:
    id: uuid.UUID
    is_superuser: bool
    email: str | None = None
    password: str | None = None
    roles: tuple[Role, ...] = field(default_factory=tuple)


_SCALARS: tuple[type, ...] = (str, bytes, bytearray, memoryview)


def _is_container(x: Any) -> bool:
    return isinstance(x, Mapping) or (isinstance(x, Sequence) and not isinstance(x, _SCALARS))


def _collect_keys(
    data: Mapping[str, Any] | Sequence[Any],
    *,
    max_depth: int | None = 15,
) -> frozenset[str]:
    if not data:
        return frozenset()

    keys: set[str] = set()
    stack: list[tuple[Any, int]] = [(data, 0)]

    while stack:
        current, depth = stack.pop()

        if max_depth is not None and depth > max_depth:
            raise ValueError("keys collection max_depth exceeded")

        if isinstance(current, Mapping):
            keys.update(current.keys())
            stack.extend((v, depth + 1) for v in current.values() if _is_container(v))
        elif isinstance(current, Sequence) and not isinstance(current, _SCALARS):
            stack.extend((v, depth + 1) for v in current if _is_container(v))

    return frozenset(keys)


@dataclass(slots=True, frozen=True)
class Context:
    user: AuthUser | None
    request_id: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    request_path_params: Mapping[str, Any] = field(default_factory=dict)
    request_query_params: Mapping[str, Any] = field(default_factory=dict)
    request_json_params: Mapping[str, Any] = field(default_factory=dict)
    request_url: str | None = None

    def update_user(self, user: AuthUser) -> None:
        object.__setattr__(self, "user", user)

    def request_path_keys(self) -> frozenset[str]:
        return _collect_keys(self.request_path_params)

    def request_query_keys(self) -> frozenset[str]:
        return _collect_keys(self.request_query_params)

    def request_json_keys(self) -> frozenset[str]:
        return _collect_keys(self.request_json_params)


@runtime_checkable
class Authenticator(Protocol):
    @overload
    async def authenticate(
        self,
        manager: TransactionManager,
        *,
        email: str,
    ) -> AppResult[AuthUser]: ...
    @overload
    async def authenticate(
        self,
        manager: TransactionManager,
        *,
        user_id: uuid.UUID,
    ) -> AppResult[AuthUser]: ...
    async def get_permission_for(
        self,
        user: AuthUser,
        permission: PermissionSpec,
        manager: TransactionManager,
    ) -> AppResult[Permission]: ...


type TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    typ: TokenType
    iat: datetime | None = None
    exp: datetime | None = None
    iss: str | None = None
    aud: str | None = None
    jti: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class JwtToken:
    token: str

    def __str__(self) -> str:
        return self.token


@dataclass(slots=True, frozen=True)
class Fingerprint:
    fingerprint: str

    def __str__(self) -> str:
        return self.fingerprint


@dataclass(slots=True, frozen=True)
class TokenPair:
    access_token: JwtToken
    refresh_token: JwtToken
    expires_in: int


@runtime_checkable
class JwtIssuer(Protocol):
    def issue_pair(
        self,
        sub: str,
        *,
        ttl: int | timedelta | None = None,
        refresh_ttl: int | timedelta | None = None,
        jti: str | None = None,
        iss: str | None = None,
        aud: str | None = None,
        **extra: Any,
    ) -> AppResult[TokenPair]: ...


@runtime_checkable
class JwtVerifier(Protocol):
    def verify(
        self,
        token: str,
        iss: str | None = None,
        aud: str | None = None,
    ) -> AppResult[TokenClaims]: ...


@runtime_checkable
class RefreshStore(Protocol):
    async def make_token(
        self,
        user_id: uuid.UUID,
        fingerprint: Fingerprint,
    ) -> AppResult[TokenPair]: ...
    async def rotate(self, fingerprint: Fingerprint, token: JwtToken) -> AppResult[TokenPair]: ...
    async def revoke(self, fingerprint: Fingerprint, token: JwtToken) -> AppResult[bool]: ...


@runtime_checkable
class Hasher(Protocol):
    def hash_password(self, plain: str) -> AppResult[str]: ...
    def verify_password(self, hashed: str, plain: str) -> AppResult[bool]: ...
