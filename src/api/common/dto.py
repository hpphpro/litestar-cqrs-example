import uuid
from collections.abc import Mapping
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Self, override

import msgspec
from litestar.serialization.msgspec_hooks import default_deserializer, default_serializer

from src.api.common.tools import (
    msgpack_decoder,
    msgpack_encoder,
    msgspec_decoder,
    msgspec_encoder,
)


def _convert_to[T](cls: type[T], value: Any, **kw: Any) -> T:
    return msgspec.convert(
        value,
        cls,
        dec_hook=default_deserializer,
        builtin_types=(bytes, bytearray, datetime, time, date, timedelta, uuid.UUID, Decimal),
        **kw,
    )


def _convert_from(value: Any, **kw: Any) -> Any:
    return msgspec.to_builtins(
        value,
        enc_hook=default_serializer,
        builtin_types=(
            datetime,
            date,
            timedelta,
            Decimal,
            uuid.UUID,
            bytes,
            bytearray,
            memoryview,
            time,
        ),
        **kw,
    )


class BaseDTO(msgspec.Struct):
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self:
        return _convert_to(cls, value, strict=False)

    @classmethod
    def from_string(cls, value: str) -> Self:
        return _convert_to(cls, msgspec_decoder(value, strict=False), strict=False)

    @classmethod
    def from_attributes(cls, value: Any) -> Self:
        return _convert_to(cls, value, strict=False, from_attributes=True)

    @classmethod
    def from_bytes(cls, value: bytes) -> Self:
        return _convert_to(cls, msgpack_decoder(value, strict=False), strict=False)

    def as_mapping(
        self, exclude_none: bool = False, exclude: set[str] | None = None
    ) -> Mapping[str, Any]:
        result: dict[str, Any] = _convert_from(self)
        if exclude_none:
            result = {k: v for k, v in result.items() if v is not None}
        if exclude:
            result = {k: v for k, v in result.items() if k not in exclude}

        return result

    def as_string(self, exclude_none: bool = False, exclude: set[str] | None = None) -> str:
        return msgspec_encoder(
            self.as_mapping(exclude_none=exclude_none, exclude=exclude)
            if exclude_none or exclude
            else self
        )

    def as_bytes(self, exclude_none: bool = False, exclude: set[str] | None = None) -> bytes:
        return msgpack_encoder(
            self.as_mapping(exclude_none=exclude_none, exclude=exclude)
            if exclude_none or exclude
            else self
        )


class StrictBaseDTO(BaseDTO):
    @override
    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self:
        return _convert_to(cls, value, strict=True)

    @override
    @classmethod
    def from_string(cls, value: str) -> Self:
        return _convert_to(cls, msgspec_decoder(value, strict=True), strict=True)

    @override
    @classmethod
    def from_attributes(cls, value: Any) -> Self:
        return _convert_to(cls, value, strict=True, from_attributes=True)

    @override
    @classmethod
    def from_bytes(cls, value: bytes) -> Self:
        return _convert_to(cls, msgpack_decoder(value, strict=True), strict=True)
