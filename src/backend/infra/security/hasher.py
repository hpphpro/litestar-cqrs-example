from __future__ import annotations

from typing import Literal

from argon2 import Parameters, PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from argon2.profiles import (
    CHEAPEST,
    PRE_21_2,
    RFC_9106_HIGH_MEMORY,
    RFC_9106_LOW_MEMORY,
)

from backend.infra.shared.result import as_result


ProfileType = Literal[
    "RFC_9106_LOW_MEMORY", "RFC_9106_HIGH_MEMORY", "CHEAPEST", "PRE_21_2", "DEFAULT"
]
PROFILES: dict[str, Parameters] = {
    "RFC_9106_LOW_MEMORY": RFC_9106_LOW_MEMORY,
    "RFC_9106_HIGH_MEMORY": RFC_9106_HIGH_MEMORY,
    "CHEAPEST": CHEAPEST,
    "PRE_21_2": PRE_21_2,
}


class Argon2:
    __slots__ = ("_hasher",)

    def __init__(self, hasher: PasswordHasher) -> None:
        self._hasher = hasher

    @classmethod
    def default(cls) -> Argon2:
        return cls(PasswordHasher())

    @as_result(is_async=False)
    def hash_password(self, plain: str) -> str:
        return self._hasher.hash(plain)

    @as_result(is_async=False)
    def verify_password(self, hashed: str, plain: str) -> bool:
        try:
            return self._hasher.verify(hashed, plain)
        except (VerificationError, VerifyMismatchError):
            return False
