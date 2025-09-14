from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Final, Literal, NoReturn

from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context, Permission, Source


SOURCES: Final[Mapping[Source, Callable[[Context], frozenset[str]]]] = {
    Source.QUERY: lambda ctx: ctx.request_query_keys(),
    Source.JSON: lambda ctx: ctx.request_json_keys(),
}


def raise_not_allowed(ctx: Context) -> NoReturn:
    raise exc.ForbiddenError(
        message="You are not allowed to access this resource.",
        path=ctx.request_path,
        method=ctx.request_method,
        request_id=ctx.request_id,
    )


def raise_fields_not_allowed(
    data: frozenset[str],
    source: Source,
    ctx: Context,
) -> Literal[True]:
    if not data:
        return True

    raise exc.ForbiddenError(
        message="Some request fields are not allowed for your role.",
        fields=sorted(data),
        method=ctx.request_method,
        path=ctx.request_path,
        request_id=ctx.request_id,
        source=source,
    )


def resolve_keys_allowed_denylist(p: Permission, ctx: Context) -> None:
    if not p.deny_fields or all(
        not denied or raise_fields_not_allowed(keys & denied, src, ctx)
        for src, denied in p.deny_fields.items()
        if (keys := SOURCES[src](ctx))
    ):
        return


def resolve_keys_allowed_allowlist(p: Permission, ctx: Context) -> None:
    if not p.allow_fields or all(
        not allowed or raise_fields_not_allowed(keys - allowed, src, ctx)
        for src, allowed in p.allow_fields.items()
        if (keys := SOURCES[src](ctx))
    ):
        return


def resolve_keys_allowed_mixed(p: Permission, ctx: Context) -> None:
    resolve_keys_allowed_denylist(p, ctx)
    resolve_keys_allowed_allowlist(p, ctx)
