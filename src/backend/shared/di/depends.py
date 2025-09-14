from __future__ import annotations

import inspect
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
    ExitStack,
    asynccontextmanager,
    contextmanager,
)
from typing import Annotated, Any, final, get_args, get_origin

from .compile import AsyncCompiledFactory, CompiledFactory, FactoryType, compile_factory
from .container import DependencyContainer, get_generation


@final
class Depends[T]:
    __slots__ = (
        "_generation",
        "dependency",
        "get_compiled",
        "get_compiled_async",
    )

    def __init__(self, dependency: T | None = None) -> None:
        self.dependency = dependency
        self.get_compiled: CompiledFactory[T] | None = None
        self.get_compiled_async: AsyncCompiledFactory[T] | None = None
        self._generation: int = get_generation()

    def __str__(self) -> str:
        return f"{type(self).__name__}[{self.dependency}]"

    def __repr__(self) -> str:
        return f"<{self}>"

    def resolve_sync(self, container: DependencyContainer, exits: ExitStack) -> T:
        if self._generation != (generation := container.generation()):
            self.get_compiled = self.get_compiled_async = None
            self._generation = generation
        elif self.get_compiled:
            return self.get_compiled(exits)

        dependency = container.get(self.dependency)

        assert dependency, f"No dependency {self.dependency} in scope"

        if not callable(dependency):
            self.get_compiled = compile_factory(FactoryType.VALUE, dependency, is_async=False)
        elif inspect.isgeneratorfunction(dependency):
            self.get_compiled = compile_factory(
                FactoryType.SYNC_CONTEXT,
                contextmanager(dependency),
                is_async=False,
            )
        else:
            resolved: T = dependency()
            if isinstance(resolved, AbstractContextManager):
                self.get_compiled = compile_factory(
                    FactoryType.SYNC_CONTEXT,
                    dependency,
                    is_async=False,
                )
                resolved = exits.enter_context(resolved)
            else:
                self.get_compiled = compile_factory(
                    FactoryType.SYNC_CALL,
                    dependency,
                    is_async=False,
                )

            return resolved

        return self.get_compiled(exits)

    async def resolve_async(self, container: DependencyContainer, exits: AsyncExitStack) -> T:
        if self._generation != (generation := container.generation()):
            self.get_compiled = self.get_compiled_async = None
            self._generation = generation
        elif self.get_compiled_async:
            return await self.get_compiled_async(exits)
        elif self.get_compiled:
            return self.get_compiled(exits)

        dependency = container.get(self.dependency)

        assert dependency, f"No dependency {self.dependency} in scope"

        if not callable(dependency):
            self.get_compiled = compile_factory(FactoryType.VALUE, dependency, is_async=False)
        elif inspect.iscoroutinefunction(dependency):
            self.get_compiled_async = compile_factory(
                FactoryType.ASYNC_CALL,
                dependency,
                is_async=True,
            )
        elif inspect.isasyncgenfunction(dependency):
            self.get_compiled_async = compile_factory(
                FactoryType.ASYNC_CONTEXT,
                asynccontextmanager(dependency),
                is_async=True,
            )
        elif inspect.isgeneratorfunction(dependency):
            self.get_compiled = compile_factory(
                FactoryType.SYNC_CONTEXT,
                contextmanager(dependency),
                is_async=False,
            )
        else:
            resolved: T = dependency()
            if isinstance(resolved, AbstractContextManager):
                self.get_compiled = compile_factory(
                    FactoryType.SYNC_CONTEXT,
                    dependency,
                    is_async=False,
                )
                resolved = exits.enter_context(resolved)
            elif isinstance(resolved, AbstractAsyncContextManager):
                self.get_compiled_async = compile_factory(
                    FactoryType.ASYNC_CONTEXT,
                    dependency,
                    is_async=True,
                )
                resolved = await exits.enter_async_context(resolved)
            else:
                self.get_compiled = compile_factory(
                    FactoryType.SYNC_CALL,
                    dependency,
                    is_async=False,
                )

            return resolved

        return await self.resolve_async(container, exits)


def extract_depends(param: inspect.Parameter) -> Depends[Any] | None:
    default = param.default
    annotation = param.annotation

    if isinstance(default, Depends):
        if default.dependency is None:
            default.dependency = annotation

        return default

    if default is Depends:
        return Depends(annotation)

    return _from_annotation(annotation)


def _from_annotation(annotation: Any) -> Depends[Any] | None:
    origin = get_origin(annotation)

    if origin in (Depends, Annotated):
        args = get_args(annotation)

        if not args:
            return None

        if origin is Depends:
            return Depends(args[0] if args else None)

        if len(args) > 1:
            first = args[1]
            if first is Depends:
                return Depends(args[0])

            if isinstance(first, Depends):
                if first.dependency is None:
                    first.dependency = args[0]

                return first

    return None


def remove_depends(
    signature: inspect.Signature,
) -> tuple[dict[str, Any], inspect.Signature]:
    new_sig = {k: v for k, v in signature.parameters.items() if extract_depends(v) is None}

    return {k: v.annotation for k, v in new_sig.items()}, inspect.Signature(
        [v for _, v in signature.parameters.items() if extract_depends(v) is None],
        return_annotation=signature.return_annotation,
    )
