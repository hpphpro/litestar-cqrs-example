from litestar import Router
from litestar.datastructures import State
from litestar.di import Provide

from src.api.common import tools
from src.api.common.bus import QCBus
from src.api.common.bus.middlewares.cache import CacheInvalidateMiddleware, CacheMiddleware
from src.api.v1.commands import CommandBus
from src.api.v1.queries import QueryBus
from src.config.core import Config
from src.database.alchemy.core import ConnectionFactory
from src.database.manager import ManagerFactory
from src.services.cache.redis import RedisCache
from src.services.gateway import ServiceGatewayImpl


def setup_v1_dependencies(router: Router, config: Config) -> State:
    connection = ConnectionFactory.from_url(
        config.db.url(),
        pool_size=config.db.connection_pool_size,
        max_overflow=config.db.connection_max_overflow,
        pool_pre_ping=config.db.connection_pool_pre_ping,
        json_serializer=tools.msgspec_encoder,
        json_deserializer=tools.msgspec_decoder,
        future=True,
    )

    manager = ManagerFactory(connection)
    cache = RedisCache.from_config(config.redis)

    lazy_gw = tools.lazy_single(ServiceGatewayImpl, manager.make_transaction_manager)
    query_bus = (
        QCBus.builder()
        .dependencies(gateway=lazy_gw)
        .bus(QueryBus)
        .middleware(CacheMiddleware(cache=cache))
        .build()
    )
    command_bus = (
        QCBus.builder()
        .dependencies(gateway=lazy_gw)
        .bus(CommandBus)
        .middleware(CacheInvalidateMiddleware(cache=cache))
        .build()
    )

    router.dependencies["query_bus"] = Provide(
        tools.singleton(query_bus), use_cache=True, sync_to_thread=False
    )
    router.dependencies["command_bus"] = Provide(
        tools.singleton(command_bus), use_cache=True, sync_to_thread=False
    )
    router.dependencies["cache"] = Provide(
        tools.singleton(cache), use_cache=True, sync_to_thread=False
    )

    return State(
        {
            "engine": tools.ClosableProxy(connection.engine, connection.engine.dispose),
            "cache": tools.ClosableProxy(cache, cache.close),
        }
    )
