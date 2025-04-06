import time

from litestar.constants import HTTP_RESPONSE_START
from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware.base import ASGIMiddleware
from litestar.types import ASGIApp, Message, Receive, Scope, Send


class ProcessTimeMiddleware(ASGIMiddleware):
    def __init__(self, scopes: tuple[ScopeType, ...] = (ScopeType.HTTP,)) -> None:
        self.scopes = scopes

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == HTTP_RESPONSE_START:
                process_time = time.perf_counter() - start_time
                headers = MutableScopeHeaders.from_message(message=message)
                headers["X-Process-Time"] = f"{process_time:.5f}"

            await send(message)

        await next_app(scope, receive, send_wrapper)
