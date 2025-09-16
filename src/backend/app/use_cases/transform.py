from dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform()
def handler[T](cls: type[T]) -> type[T]:
    return dataclass(slots=True, frozen=True)(cls)
