from __future__ import annotations

import linecache
from contextlib import AsyncExitStack, ExitStack
from enum import StrEnum
from typing import Any, Final, Literal, Protocol, cast, overload


class FactoryType(StrEnum):
    SYNC_CALL = "factory"
    ASYNC_CALL = "async_factory"
    VALUE = "value"
    ASYNC_CONTEXT = "async_context"
    SYNC_CONTEXT = "context"


class CompiledFactory[T](Protocol):
    def __call__(
        self,
        exits: ExitStack | AsyncExitStack,
    ) -> T: ...


class AsyncCompiledFactory[T](Protocol):
    async def __call__(
        self,
        exits: AsyncExitStack,
    ) -> T: ...


SYNC_CALL: Final[str] = """
def resolve(exits):
    return dependency()
"""

SYNC_CONTEXT: Final[str] = """
def resolve(exits):
    return exits.enter_context(dependency())
"""

ASYNC_CALL: Final[str] = """
async def resolve(exits):
    return await dependency()
"""

ASYNC_CONTEXT: Final[str] = """
async def resolve(exits):
    return await exits.enter_async_context(dependency())
"""

VALUE: Final[str] = """
def resolve(exits):
    return dependency
"""


TEMPLATES: Final[dict[FactoryType, str]] = {
    FactoryType.SYNC_CALL: SYNC_CALL,
    FactoryType.SYNC_CONTEXT: SYNC_CONTEXT,
    FactoryType.ASYNC_CALL: ASYNC_CALL,
    FactoryType.ASYNC_CONTEXT: ASYNC_CONTEXT,
    FactoryType.VALUE: VALUE,
}


@overload
def compile_factory[T](
    factory: FactoryType,
    dependency: Any,
    *,
    is_async: Literal[False],
) -> CompiledFactory[T]: ...
@overload
def compile_factory[T](
    factory: FactoryType,
    dependency: Any,
    *,
    is_async: Literal[True],
) -> AsyncCompiledFactory[T]: ...
def compile_factory[T](
    factory: FactoryType,
    dependency: Any,
    *,
    is_async: bool,
) -> CompiledFactory[T] | AsyncCompiledFactory[T]:
    if factory not in TEMPLATES:
        raise ValueError(f"Unsupported factory type: {factory}")

    template = TEMPLATES[factory]

    source_file_name = f"__dependency_factory_{id(dependency)}_{'async' if is_async else 'sync'}"

    globals_dict: dict[str, Any] = {"dependency": dependency}

    lines = template.splitlines(keepends=True)
    linecache.cache[source_file_name] = (
        len(template),
        None,
        lines,
        source_file_name,
    )

    compiled = compile(template, source_file_name, "exec")
    exec(compiled, globals_dict)  # noqa: S102

    return cast(AsyncCompiledFactory[T] | CompiledFactory[T], globals_dict["resolve"])
