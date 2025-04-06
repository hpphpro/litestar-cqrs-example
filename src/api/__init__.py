from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.stores.redis import RedisStore
from litestar.stores.registry import StoreRegistry
from redis.asyncio.client import Redis

from src.api.common.exceptions import current_common_exc_handlers
from src.api.common.middlewares import current_common_middlewares
from src.api.common.tools import ClosableProxy, RouterState
from src.config.core import Config


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:
    try:
        yield
    finally:
        for value in app.state.values():
            if isinstance(value, ClosableProxy):
                await value.close()


def on_app_init(config: Config, *router_state: RouterState) -> Callable[[AppConfig], AppConfig]:
    def wrapped(app_config: AppConfig) -> AppConfig:
        app_config.exception_handlers.update(current_common_exc_handlers())
        app_config.middleware.extend(current_common_middlewares())

        if config.app.debug and config.app.debug_detailed:
            app_config.middleware.append(LoggingMiddlewareConfig().middleware)

        if config.app.metrics:
            from litestar.contrib.prometheus import PrometheusConfig, PrometheusController

            app_config.middleware.append(
                PrometheusConfig(
                    app_name="_".join(config.app.title.split()) if config.app.title else "Example",
                    prefix="_".join(config.app.title.split()) if config.app.title else "Example",
                ).middleware
            )
            PrometheusController.get.include_in_schema = False

            app_config.route_handlers.append(PrometheusController)

        for r_state in router_state:
            app_config.route_handlers.append(r_state.router)
            app_config.state.update(r_state.state.dict())
            app_config.on_startup.extend(r_state.on_startup)
            app_config.on_shutdown.extend(r_state.on_shutdown)

        return app_config

    return wrapped


def init_app(config: Config, *router_state: RouterState) -> Litestar:
    app = Litestar(
        path=config.app.root_path,
        openapi_config=(
            OpenAPIConfig(
                title=config.app.title,
                version=config.app.version,
                render_plugins=(SwaggerRenderPlugin(),),
            )
        )
        if config.app.title and config.app.swagger
        else None,
        debug=config.app.debug,
        lifespan=[lifespan],
        on_app_init=[on_app_init(config, *router_state)],
        stores=StoreRegistry(
            default_factory=lambda _: RedisStore(
                Redis(**config.redis.model_dump(), decode_responses=False),
                handle_client_shutdown=True,
            )
        ),
    )

    return app
