from collections.abc import Awaitable, Callable
from dataclasses import asdict

from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.di import Provide

from backend.app.bus.core import QCBus
from backend.app.bus.middlewares.cache import CacheInvalidateMiddleware, CacheMiddleware
from backend.app.common.tools import (
    ClosableProxy,
    lazy_single,
    msgspec_decoder,
    msgspec_encoder,
    singleton,
)
from backend.app.contracts.auth import Authenticator, JwtVerifier
from backend.app.contracts.cache import StrCache
from backend.app.contracts.manager import TransactionManager
from backend.app.contracts.shared_lock import SharedLock
from backend.app.use_cases.commands import CommandBus
from backend.app.use_cases.queries import QueryBus
from backend.http.common.tools.context import cache_request_key_builder
from backend.http.common.tools.route_rule import RouteRule
from backend.infra.cache.redis import RedisCache
from backend.infra.database.alchemy import entity, queries
from backend.infra.database.alchemy.connection import ConnectionFactory
from backend.infra.database.alchemy.repositories import RepositoryGatewayImpl
from backend.infra.database.manager import ManagerFactory
from backend.infra.security.auth import AuthenticatorImpl
from backend.infra.security.hasher import Argon2
from backend.infra.security.jwt import JwtImpl, RefreshStoreImpl
from backend.infra.shared.shared_lock import RedisSharedLock
from backend.shared.di import DependencyContainer, FromScope, inject
from config.core import BackendConfig


def create_rules(rules: list[RouteRule]) -> Callable[[Litestar], Awaitable[None]]:
    @inject
    async def _inner(
        _: Litestar, lock: type[SharedLock] = FromScope(SharedLock), cache: StrCache = FromScope()
    ) -> None:
        @inject
        async def _create(manager: TransactionManager = FromScope()) -> None:
            await manager.with_transaction()

            for rule in rules:
                permission = await manager.send(
                    queries.base.CreateOrIgnore[entity.Permission](
                        **{
                            k: v for k, v in asdict(rule.permission).items() if k not in ("fields",)
                        },
                    ),
                )
                if not permission:
                    permission = await manager.send(
                        queries.base.GetOne[entity.Permission](key=rule.permission.key()),
                    )
                    assert permission, "Permission not found"

                fields = [
                    {"permission_id": permission.id, "src": src, "name": name}
                    for src, names in rule.permission.fields.items()
                    for name in names
                ]

                if not fields:
                    continue
                await manager.send(queries.base.BatchCreate[entity.PermissionField](data=fields))

        async with lock("temp", timeout=20):
            key = await cache.get("create_rules")
            if key:
                return
            await cache.set("create_rules", "1", expire=30)
            await _create()

    return _inner


def setup_dependencies(app_config: AppConfig, backend_config: BackendConfig) -> None:
    m_conf = backend_config.compute_min_max_connections_per_worker()
    r_conf = backend_config.compute_min_max_connections_per_worker(
        total_max=backend_config.db.replica_max_connections
    )

    m_conn = ConnectionFactory.from_url(
        backend_config.db.url(use_replica=False),
        pool_size=m_conf.min_connections,
        max_overflow=m_conf.max_connections,
        pool_timeout=min(30, backend_config.db.connection_timeout),
        pool_pre_ping=backend_config.db.ping_connection,
        json_serializer=msgspec_encoder,
        json_deserializer=msgspec_decoder,
        future=True,
    )
    r_conn = ConnectionFactory.from_url(
        backend_config.db.url(use_replica=True),
        pool_size=r_conf.min_connections,
        max_overflow=r_conf.max_connections,
        pool_timeout=min(30, backend_config.db.connection_timeout),
        pool_pre_ping=backend_config.db.ping_connection,
        json_serializer=msgspec_encoder,
        json_deserializer=msgspec_decoder,
        future=True,
    )
    jwt = JwtImpl.from_config(backend_config.security)
    cache = RedisCache.from_url(backend_config.redis.url)
    shared_lock = RedisSharedLock.create(cache._redis)  # noqa: SLF001
    master_manager = ManagerFactory(m_conn)
    slave_manager = ManagerFactory(r_conn)

    query_lazy_gw = lazy_single(RepositoryGatewayImpl, slave_manager.make_transaction_manager)
    refresh_store = RefreshStoreImpl(cache, jwt, shared_lock)
    hasher = Argon2.default()
    authenticator = AuthenticatorImpl(hasher)
    command_lazy_gw = lazy_single(RepositoryGatewayImpl, master_manager.make_transaction_manager)
    query_bus = (
        QCBus.builder()
        .dependencies(gateway=query_lazy_gw, lock=singleton(shared_lock))
        .bus(QueryBus)
        .middleware(CacheMiddleware(cache=cache, cache_key_builder=cache_request_key_builder))
        .build()
    )
    command_bus = (
        QCBus.builder()
        .dependencies(
            gateway=command_lazy_gw,
            lock=singleton(shared_lock),
            authenticator=authenticator,
            jwt_issuer=jwt,
            jwt_verifier=jwt,
            refresh_store=refresh_store,
            cache=cache,
            hasher=hasher,
        )
        .bus(CommandBus)
        .middleware(CacheInvalidateMiddleware(cache=cache))
        .build()
    )
    app_config.dependencies["query_bus"] = Provide(
        singleton(query_bus),
        use_cache=True,
        sync_to_thread=False,
    )
    app_config.dependencies["command_bus"] = Provide(
        singleton(command_bus),
        use_cache=True,
        sync_to_thread=False,
    )
    app_config.dependencies["cache"] = Provide(
        singleton(cache),
        use_cache=True,
        sync_to_thread=False,
    )
    container = DependencyContainer({
        TransactionManager: master_manager.make_manager_context,
        JwtVerifier: jwt,
        Authenticator: authenticator,
        SharedLock: singleton(shared_lock),
        StrCache: cache,
    })

    app_config.state.master_pool = ClosableProxy(m_conn.engine, m_conn.engine.dispose)
    app_config.state.slave_pool = ClosableProxy(r_conn.engine, r_conn.engine.dispose)
    app_config.state.cache = ClosableProxy(cache, cache.close)
    app_config.state.dep = ClosableProxy(container, container.reset)
