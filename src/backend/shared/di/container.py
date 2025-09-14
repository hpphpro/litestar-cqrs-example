from __future__ import annotations

from typing import Any, ClassVar, final


@final
class DependencyContainer:
    __slots__ = ()
    __dependencies: ClassVar[dict[Any, Any]] = {}
    __instance: ClassVar[DependencyContainer | None] = None
    __generation: ClassVar[int] = 0

    def __new__(cls, dependencies: dict[Any, Any] | None = None) -> DependencyContainer:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        instance = cls.__instance
        dependencies = dependencies or {}
        for k, v in dependencies.items():
            instance.bind(k, v)

        return instance

    def bind(self, key: Any, value: Any) -> DependencyContainer:
        self.__dependencies[key] = self.__dependencies[getattr(key, "__name__", key)] = value

        return self

    def get(self, key: Any) -> Any | None:
        try:
            return self.__dependencies[key]
        except KeyError:
            return self.__dependencies.get(getattr(key, "__name__", key))

    def __getitem__(self, key: Any) -> Any:
        return self.get(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        self.bind(key, value)

    @classmethod
    def generation(cls) -> int:
        return cls.__generation

    @classmethod
    def reset(cls) -> None:
        cls.__dependencies.clear()
        cls.__instance = None
        cls.bump_generation()

    @classmethod
    def bump_generation(cls) -> None:
        cls.__generation += 1


def get_generation() -> int:
    return DependencyContainer.generation()


def reset_dependencies() -> None:
    DependencyContainer.reset()
