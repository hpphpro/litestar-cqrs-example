from collections.abc import Mapping
from typing import Any, Self, override

import msgspec

from backend.app.common.tools import (
    convert_from,
    convert_to,
    msgpack_decoder,
    msgpack_encoder,
    msgspec_decoder,
    msgspec_encoder,
)


class BaseDTO(msgspec.Struct):
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self:
        return convert_to(cls, value, strict=False)

    @classmethod
    def from_string(cls, value: str) -> Self:
        return convert_to(cls, msgspec_decoder(value, strict=False), strict=False)

    @classmethod
    def from_attributes(cls, value: Any) -> Self:
        return convert_to(cls, value, strict=False, from_attributes=True)

    @classmethod
    def from_bytes(cls, value: bytes) -> Self:
        return convert_to(cls, msgpack_decoder(value, strict=False), strict=False)

    def as_mapping(
        self,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> Mapping[str, Any]:
        exclude = exclude or set()
        return {
            k: v
            for k, v in convert_from(self).items()
            if k not in exclude and (not exclude_none or v is not None)
        }

    def as_string(self, *, exclude_none: bool = False, exclude: set[str] | None = None) -> str:
        return msgspec_encoder(
            self.as_mapping(exclude_none=exclude_none, exclude=exclude)
            if exclude_none or exclude
            else self,
        )

    def as_bytes(self, *, exclude_none: bool = False, exclude: set[str] | None = None) -> bytes:
        return msgpack_encoder(
            self.as_mapping(exclude_none=exclude_none, exclude=exclude)
            if exclude_none or exclude
            else self,
        )


class ExcludeDefaultsDTO(BaseDTO, omit_defaults=True): ...


class StrictBaseDTO(BaseDTO):
    @override
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self:
        return convert_to(cls, value, strict=True)

    @override
    @classmethod
    def from_string(cls, value: str) -> Self:
        return convert_to(cls, msgspec_decoder(value, strict=True), strict=True)

    @override
    @classmethod
    def from_attributes(cls, value: Any) -> Self:
        return convert_to(cls, value, strict=True, from_attributes=True)

    @override
    @classmethod
    def from_bytes(cls, value: bytes) -> Self:
        return convert_to(cls, msgpack_decoder(value, strict=True), strict=True)
