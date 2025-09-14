from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from litestar import Litestar
from litestar.handlers.base import BaseRouteHandler

from backend.app.contracts.auth import Context, Permission, PermissionSpec, Scope
from backend.app.contracts.manager import TransactionManager


async def _default_resolve_scope(
    manager: TransactionManager | None,
    ctx: Context,
    scope: Scope,
) -> None: ...


def _allow_all(p: Permission, ctx: Context) -> None: ...


@dataclass(slots=True, frozen=True)
class RouteRule:
    permission: PermissionSpec
    check_fields: Callable[[Permission, Context], None] = field(default=_allow_all)
    check_scope: Callable[[TransactionManager, Context, Scope], Awaitable[None]] = field(
        default=_default_resolve_scope,
    )


def add_rule(rule: RouteRule) -> Callable[[BaseRouteHandler], BaseRouteHandler]:
    def _wrapper(handler: BaseRouteHandler) -> BaseRouteHandler:
        setattr(handler.fn, "rule", rule)  # noqa: B010

        return handler

    return _wrapper


def collect_rules(app: Litestar) -> list[RouteRule]:
    return [
        rule
        for route in app.route_handler_method_map.values()
        for handler in route.values()
        if (rule := getattr(handler.fn, "rule", None))
    ]
