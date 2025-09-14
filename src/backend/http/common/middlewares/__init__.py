from litestar import Router
from litestar.types.composite_types import Middleware

from .context import ContextMiddleware
from .process_time import ProcessTimeMiddleware
from .x_request_id import XRequestIdMiddleware


__all__ = (
    "ProcessTimeMiddleware",
    "XRequestIdMiddleware",
    "setup_middlewares",
)


def middlewares() -> tuple[Middleware, ...]:
    return (ProcessTimeMiddleware(), XRequestIdMiddleware(), ContextMiddleware())


def setup_middlewares(app: Router) -> None:
    app.middleware.extend(middlewares())
