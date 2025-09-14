import uuid

from litestar import Request
from litestar.datastructures.state import State
from litestar.enums import ScopeType
from litestar.middleware.base import ASGIMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send

from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Authenticator, AuthUser, Context, JwtVerifier
from backend.app.contracts.manager import TransactionManager
from backend.http.common.tools.resolvers.default import raise_not_allowed
from backend.http.common.tools.route_rule import RouteRule
from backend.shared.di import FromScope, inject


class JWTAuthMiddleware(ASGIMiddleware):
    def __init__(
        self,
        auth_header: str = "Authorization",
        exclude: str | tuple[str] | None = None,
        exclude_from_auth_key: str = "exclude_from_auth",
        scopes: tuple[ScopeType, ...] | None = None,
    ) -> None:
        self.exclude_opt_key = exclude_from_auth_key
        self.exclude_path_pattern = exclude
        self.auth_header = auth_header

        if scopes:
            self.scopes = scopes

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        await self.authenticate_request(Request(scope, receive, send))

        await next_app(scope, receive, send)

    async def authenticate_request(
        self,
        request: Request[None, None, State],
    ) -> None:
        auth_header = request.headers.get(self.auth_header)
        if not auth_header:
            raise exc.UnAuthorizedError("Token is missing")

        scheme, sep, encoded_token = auth_header.partition(" ")
        if scheme.lower() != "bearer":
            raise exc.UnAuthorizedError("Invalid token provided")

        await self.authenticate_token(encoded_token, request=request)

    @inject
    async def authenticate_token(
        self,
        encoded_token: str,
        request: Request[None, None, State],
        jwt: JwtVerifier = FromScope(),
        manager: TransactionManager = FromScope(),
        authenticator: Authenticator = FromScope(),
    ) -> None:
        claims = (
            jwt.verify(encoded_token)
            .and_then(lambda c: c if c.typ == "access" else None)
            .unwrap_or_raise(exc.UnAuthorizedError("Token is invalid or expired"))
        )

        request.scope["auth"] = claims

        user = await self.authenticate_user(
            sub=claims.sub, request=request, manager=manager, authenticator=authenticator
        )
        ctx = request.state.ctx
        ctx.update_user(user)

        if not user.roles:
            raise exc.ForbiddenError("Permission denied, role is required")

        if user.is_superuser:
            return

        rule: RouteRule | None = getattr(request.scope["route_handler"].fn, "rule", None)
        if not rule:
            return

        await self._ensure_permissions(ctx, user, rule, manager, authenticator)

    async def _ensure_permissions(
        self,
        ctx: Context,
        user: AuthUser,
        rule: RouteRule,
        manager: TransactionManager,
        authenticator: Authenticator,
    ) -> None:
        p = await authenticator.get_permission_for(user, rule.permission, manager)
        if p.is_err():
            raise_not_allowed(ctx)

        permission = p.unwrap()

        await rule.check_scope(manager, ctx, permission.scope)
        rule.check_fields(permission, ctx)

    async def authenticate_user(
        self,
        sub: str,
        request: Request[None, None, State],
        manager: TransactionManager,
        authenticator: Authenticator,
    ) -> AuthUser:
        user = (await authenticator.authenticate(manager, user_id=uuid.UUID(sub))).unwrap_or_raise(
            exc.UnAuthorizedError("Unauthorized")
        )

        request.scope["user"] = user

        return user
