from litestar import Request, types
from litestar.enums import ScopeType
from litestar.middleware.base import ASGIMiddleware

from backend.http.common.tools.context import context_from_request


class ContextMiddleware(ASGIMiddleware):
    def __init__(self, scopes: tuple[ScopeType, ...] = (ScopeType.HTTP, ScopeType.ASGI)) -> None:
        self.scopes = scopes

    async def handle(
        self, scope: types.Scope, receive: types.Receive, send: types.Send, next_app: types.ASGIApp
    ) -> None:
        scope.setdefault("state", {}).update({
            "ctx": await context_from_request(Request(scope, receive, send))
        })

        await next_app(scope, receive, send)
