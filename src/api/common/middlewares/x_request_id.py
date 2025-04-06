from typing import Final

from litestar import Request, types
from litestar.constants import HTTP_RESPONSE_START
from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware.base import ASGIMiddleware
from uuid_utils import uuid7


class XRequestIdMiddleware(ASGIMiddleware):
    header_name: Final[str] = "X-Request-Id"

    def __init__(self, scopes: tuple[ScopeType, ...] = (ScopeType.HTTP,)) -> None:
        self.scopes = scopes

    async def handle(
        self, scope: types.Scope, receive: types.Receive, send: types.Send, next_app: types.ASGIApp
    ) -> None:
        async def send_wrapper(message: types.Message) -> None:
            if message["type"] == HTTP_RESPONSE_START:
                request_id: str | None = Request(scope).headers.get(self.header_name)
                headers = MutableScopeHeaders.from_message(message=message)
                headers[self.header_name] = request_id or uuid7().hex

            await send(message)

        await next_app(scope, receive, send_wrapper)
