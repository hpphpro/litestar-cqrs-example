from __future__ import annotations

from backend.app.contracts.auth import Context, Scope
from backend.app.contracts.manager import TransactionManager

from .default import raise_not_allowed


async def resolve_by_user_id(_: TransactionManager, ctx: Context, scope: Scope) -> None:
    if scope == Scope.OWN and (not ctx.user or ctx.user.id != ctx.request_path_params["user_id"]):
        raise_not_allowed(ctx)


async def resolve_by_user_email(_: TransactionManager, ctx: Context, scope: Scope) -> None:
    if scope == Scope.OWN and (
        not ctx.user
        or not ctx.user.email
        or ctx.user.email.lower() != ctx.request_query_params["email"].lower()
    ):
        raise_not_allowed(ctx)
