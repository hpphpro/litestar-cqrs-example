from litestar import Router
from litestar.types.composite_types import Middleware

from src.api.common.middlewares.process_time import ProcessTimeMiddleware
from src.api.common.middlewares.x_request_id import XRequestIdMiddleware


__all__ = ("ProcessTimeMiddleware",)


def current_common_middlewares() -> tuple[Middleware, ...]:
    return (ProcessTimeMiddleware(), XRequestIdMiddleware())


def setup_common_middlewares(app: Router) -> None:
    app.middleware.extend(current_common_middlewares())
