from dataclasses import asdict, dataclass
from typing import Any


def _filter_none(values: list[tuple[str, Any]]) -> dict[str, Any]:
    return {k: v for k, v in values if v is not None}


@dataclass(slots=True)
class BaseData:
    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        return

    def as_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        return asdict(self) if not exclude_none else asdict(self, dict_factory=_filter_none)
