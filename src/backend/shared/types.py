from collections.abc import Callable
from typing import Any


def is_typevar[T: Any](t: T) -> bool:
    return hasattr(t, "__bound__") or hasattr(t, "__constraints__")


type JsonLoads = Callable[..., Any]
type JsonDumps = Callable[..., str]
