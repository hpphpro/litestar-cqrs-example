from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from litestar import Litestar, Router
from litestar.config.app import AppConfig
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.stores.redis import RedisStore
from litestar.stores.registry import StoreRegistry
from redis.asyncio.client import Redis

from backend.app.common.tools import ClosableProxy
from backend.http.common.exceptions import exc_handlers
from backend.http.common.middlewares import middlewares
from backend.http.common.tools.route_rule import collect_rules
from config.core import BackendConfig

from .dependencies import create_rules, setup_dependencies


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:
    try:
        yield
    finally:
        for v in app.state.values():
            if isinstance(v, ClosableProxy):
                await v.close()


def security_components() -> list[Components]:
    return [
        Components(
            security_schemes={
                "BearerToken": SecurityScheme(
                    type="http",
                    scheme="Bearer",
                    name="Authorization",
                    bearer_format="JWT",
                    description=None,
                ),
            },
        ),
    ]


def _on_app_init(config: BackendConfig, *routers: Router) -> Callable[[AppConfig], AppConfig]:
    def _wrapped(app_config: AppConfig) -> AppConfig:
        app_config.exception_handlers.update(exc_handlers())
        app_config.middleware.extend(middlewares())
        app_config.route_handlers.extend(routers)
        setup_dependencies(app_config, config)

        if config.api.debug and config.api.debug_detailed:
            app_config.middleware.append(LoggingMiddlewareConfig().middleware)
        if config.api.metrics:
            from litestar.contrib.prometheus import PrometheusConfig, PrometheusController

            app_config.middleware.append(
                PrometheusConfig(
                    app_name="_".join(config.api.title.split()).replace("-", "_")
                    if config.api.title
                    else "Example",
                    prefix="_".join(config.api.title.split()).replace("-", "_")
                    if config.api.title
                    else "Example",
                ).middleware,
            )
            PrometheusController.get.include_in_schema = False

            app_config.route_handlers.append(PrometheusController)

        return app_config

    return _wrapped


def init_app(config: BackendConfig, *routers: Router) -> Litestar:
    app = Litestar(
        path=config.api.root_path,
        openapi_config=(
            OpenAPIConfig(
                title=config.api.title,
                version=config.api.version,
                render_plugins=(SwaggerRenderPlugin(), ScalarRenderPlugin()),
                components=security_components(),
            )
        )
        if config.api.title and config.api.swagger
        else None,
        debug=config.api.debug,
        lifespan=[lifespan],
        on_app_init=[_on_app_init(config, *routers)],
        stores=StoreRegistry(
            default_factory=RedisStore(
                Redis(**config.redis.model_dump(), decode_responses=False),
                handle_client_shutdown=True,
            ).with_namespace,
        ),
    )

    app.on_startup.append(create_rules(collect_rules(app)))

    return app
