import uuid
from typing import Final

from litestar import Request, types
from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware.base import AbstractMiddleware


class XRequestIdMiddleware(AbstractMiddleware):
    scopes = {ScopeType.HTTP}
    header_name: Final[str] = "X-Request-Id"

    async def __call__(
        self,
        scope: types.Scope,
        receive: types.Receive,
        send: types.Send,
    ) -> None:
        async def send_wrapper(message: types.Message) -> None:
            if message["type"] == "http.response.start":
                request_id: str | None = Request(scope).headers.get(self.header_name)
                headers = MutableScopeHeaders.from_message(message=message)
                headers[self.header_name] = request_id or uuid.uuid4().hex

            await send(message)

        await self.app(scope, receive, send_wrapper)
