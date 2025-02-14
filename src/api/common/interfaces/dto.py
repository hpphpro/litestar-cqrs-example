from collections.abc import Mapping
from typing import Any, Protocol, Self, runtime_checkable


@runtime_checkable
class Serializable(Protocol):
    def as_string(self, exclude_none: bool = False, exclude: set[str] | None = None) -> str: ...
    def as_mapping(
        self, exclude_none: bool = False, exclude: set[str] | None = None
    ) -> Mapping[str, Any]: ...
    def as_bytes(self, exclude_none: bool = False, exclude: set[str] | None = None) -> bytes: ...


@runtime_checkable
class Deserializable(Protocol):
    @classmethod
    def from_string(cls, value: str) -> Self: ...
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self: ...
    @classmethod
    def from_bytes(cls, value: bytes) -> Self: ...
    @classmethod
    def from_attributes(cls, value: Any) -> Self: ...


@runtime_checkable
class DTO(Serializable, Deserializable, Protocol): ...
